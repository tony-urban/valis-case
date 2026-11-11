#!/usr/bin/env python3
"""Independent checks over the three deliverables (tester stage).

Run from anywhere:  python3 tests/check.py
Prints one PASS or FAIL line per check. Exit code 0 only if every check passes.
Standard library only. Written without reading figures from the deliverables' own
self-checks: arithmetic is redone here from the raw CSVs with the csv module.

Checks:
  1  data/ matches data/CHECKSUMS.txt
  2  each deliverable command exits 0 and regenerates its outputs (twice, same bytes)
  3  every citation in the generated outputs resolves against units built at run time
  4  independent arithmetic from the raw CSVs equals the printed figures
  5  cross-stream consistency (ask versus value, time_waste versus before_after)
  6  fresh-file smoke test on a perturbed copy of data/
  7  hygiene: em dashes, imports, Python 3.8 and 3.9 compatibility, hardcoded names and amounts
  8  regression cases for the round 1 defects, plus new adversarial cases (round 2)
  9  regression cases for the external audit of 2026-11-10 (chat_logs/external_review_2026-11-10/)
"""
import ast
import csv
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "pipeline"))
import importer  # noqa: E402  (shared parser, used here only to build citable units)

EM = "\u2014"
SAAS = "Software & SaaS"
TARGET = "Thumbnail re-upload"
STATUS = "suspected, unconfirmed"

ASK_OUT = [ROOT / "ask" / "out" / "q1.md", ROOT / "ask" / "out" / "q2.md"]
VALUE_OUT = [ROOT / "value" / "VALUE_WORKSHEET.md"]
AUTO_OUT = [ROOT / "automation" / "out" / n for n in ("time_waste.md", "before_after.md", "routed_queue.csv")]
COMMANDS = [
    ("ask", ["ask/ask.py"], ASK_OUT),
    ("value", ["value/value.py"], VALUE_OUT),
    ("automation", ["automation/run.py", "--check"], AUTO_OUT),
]

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    line = f"{'PASS' if ok else 'FAIL'}  {name}"
    if detail:
        line += f"  [{detail}]"
    print(line, flush=True)
    return bool(ok)


def run(args, timeout=180):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    p = subprocess.run([sys.executable] + [str(a) for a in args], cwd=str(ROOT), env=env,
                       capture_output=True, timeout=timeout)
    # Text mode stdout on Windows ends lines with CRLF. Normalise so every parser sees LF on every OS.
    # (Found by the second external audit: checks 9d to 9f failed on Windows on parsing alone.)
    out = p.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
    err = p.stderr.decode("utf-8", "replace").replace("\r\n", "\n")
    return p.returncode, out, err


def read(p):
    return Path(p).read_text(encoding="utf-8")


def write(p, text):
    with open(p, "w", encoding="utf-8", newline="\n") as f:   # Path.write_text(newline=) needs Python 3.10
        f.write(text)


def snapshot(paths):
    return {str(p): (Path(p).read_bytes() if Path(p).exists() else None) for p in paths}


def n(x):
    return f"{x:,}"


def short(items, k=4):
    items = [str(i) for i in items]
    return "; ".join(items[:k]) + (f"; and {len(items) - k} more" if len(items) > k else "")


# ---------- 1. checksums ----------

def check_checksums():
    listed, bad = {}, []
    for line in read(DATA / "CHECKSUMS.txt").splitlines():
        if line.strip():
            digest, rel = line.split(None, 1)
            listed[rel.strip().lstrip("./")] = digest
    actual = {p.relative_to(DATA).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in DATA.rglob("*") if p.is_file() and p.name not in ("CHECKSUMS.txt", ".DS_Store")}
    for rel, digest in listed.items():
        if actual.get(rel) != digest:
            bad.append(f"{rel} changed or missing")
    bad += [f"{rel} not in CHECKSUMS.txt" for rel in actual if rel not in listed]
    check("1 data/ matches data/CHECKSUMS.txt", not bad, short(bad) or f"{len(listed)} files")


# ---------- 3. citation resolver ----------

TOKEN = re.compile(r"`([^`\n]+)`")
LOOKS = re.compile(r"^[A-Za-z0-9_./-]+\.(md|csv):L")
LINE = re.compile(r"^(?P<file>[A-Za-z0-9_./-]+\.(md|csv)):L(?P<a>[1-9][0-9]*)(-L(?P<b>[1-9][0-9]*))?$")
SLACK = re.compile(r"^(?P<file>[A-Za-z0-9_./-]+\.md):L(?P<n>[1-9][0-9]*) "
                   r"\[(?P<channel>[^|\]]+) \| (?P<author>[^|\]]+) \| (?P<when>[^\]]+)\]$")
KEY = re.compile(r"^ \((?P<k>[^:()`]+): ")


def build_units(data_dir):
    units, flags = [], []
    for p in sorted(Path(data_dir).rglob("*")):
        if not p.is_file() or p.name in ("CHECKSUMS.txt", ".DS_Store"):
            continue
        rel = p.relative_to(data_dir).as_posix()
        try:
            if p.suffix.lower() == ".csv":
                importer.import_csv(p, rel, units, flags)
            elif p.suffix.lower() == ".md":
                importer.import_md(p, rel, units, flags)
        except Exception:
            pass
    return units


def unit_at(units, file, line):
    for u in units:
        if u["file"] == file and (u["line"] == line or
                                  (u["kind"] == "message" and u["line"] <= line <= u.get("end_line", u["line"]))):
            return u
    return None


def resolve_text(text, units, label):
    """Returns (count, problems) for every citation-shaped backticked token."""
    count, problems = 0, []
    for m in TOKEN.finditer(text):
        tok = m.group(1)
        if not LOOKS.match(tok):
            continue
        count += 1
        s, l = SLACK.match(tok), LINE.match(tok)
        if s:
            u = unit_at(units, s["file"], int(s["n"]))
            if not u or u["kind"] != "message" or u["line"] != int(s["n"]):
                problems.append(f"{label}: no message header at {tok}")
            elif (u["channel"], u["author"], u["when"]) != (s["channel"], s["author"], s["when"]):
                problems.append(f"{label}: channel, author or time differ at {tok}")
        elif l:
            a, b = int(l["a"]), l["b"] and int(l["b"])
            ua = unit_at(units, l["file"], a)
            if not ua:
                problems.append(f"{label}: no unit at {tok}")
                continue
            if b is not None:
                if not a < b or not unit_at(units, l["file"], b):
                    problems.append(f"{label}: bad range {tok}")
                continue
            if ua["kind"] == "message":
                problems.append(f"{label}: Slack message cited as a bare line {tok}")
                continue
            k = KEY.match(text[m.end():m.end() + 200])
            if k and ua["kind"] == "row" and k["k"] in ua.get("fields", {}):
                want = ua["fields"][k["k"]] + ")"
                if not text[m.end() + k.end():].startswith(want):
                    problems.append(f"{label}: row key after {tok} is not {k['k']}: {ua['fields'][k['k']]}")
        else:
            problems.append(f"{label}: malformed citation {tok}")
    return count, problems


def resolve_queue(path, units):
    """routed_queue.csv: the source column is an unquoted citation, the ticket id must match."""
    count, problems = 0, []
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            count += 1
            l = LINE.match(row.get("source", ""))
            u = l and unit_at(units, l["file"], int(l["a"]))
            if not u or row.get("ticket_id", "") not in u.get("fields", {}).values():
                problems.append(f"routed_queue.csv: {row.get('ticket_id')} source {row.get('source')!r} does not resolve to that ticket")
    return count, problems


def check_citations():
    units = build_units(DATA)
    total, problems, per = 0, [], []
    for p in ASK_OUT + VALUE_OUT + AUTO_OUT[:2] + [ROOT / "automation" / "BUILDER_SPEC.md"]:
        c, pr = resolve_text(read(p), units, p.name)
        total, problems = total + c, problems + pr
        per.append(f"{p.name} {c}")
    check("3a every backticked citation in the outputs resolves", not problems and total > 0,
          short(problems) or f"{total} citations, 0 unresolved: " + ", ".join(per))
    c, pr = resolve_queue(AUTO_OUT[2], units)
    check("3b every routed_queue.csv source resolves to its own ticket row", not pr and c > 0, short(pr) or f"{c} rows")
    return units


# ---------- 4. independent arithmetic ----------

def words_prefix(a, b):
    wa, wb = a.lower().split(), b.lower().split()
    return wa == wb or (len(wa) < len(wb) and wb[:len(wa)] == wa)


def pnl_facts(data_dir):
    path = next(Path(data_dir).glob("pnl_*.csv"))
    rows, stated = [], None
    with open(path, encoding="utf-8-sig", newline="") as f:
        r = csv.reader(f)
        header = next(r)
        ci, li = header.index("Category"), header.index("Line Item")
        ai = next(i for i, h in enumerate(header) if h.endswith("_USD"))
        for row in r:
            if len(row) <= ai or row[ci].strip() != SAAS:
                continue
            amt = row[ai].strip()
            if re.search(r"total", row[li], re.I):
                stated = int(amt) if amt.isdigit() else None
            elif amt.isdigit():
                rows.append((r.line_num, row[li].strip(), int(amt)))
    dup = 0
    for i, (_, la, xa) in enumerate(rows):
        if any(xa == xb and (words_prefix(lb, la) or words_prefix(la, lb)) for _, lb, xb in rows[:i]):
            dup += xa
    total = sum(x for _, _, x in rows)
    return {"file": path.name, "rows": rows, "total": total, "stated": stated, "dup": dup, "net": total - dup}


def ticket_facts(data_dir):
    path = next(Path(data_dir).glob("support_tickets_*.csv"))
    f_ = {"file": path.name, "count": 0, "minutes": 0, "t_count": 0, "t_minutes": 0, "by_line": {}}
    with open(path, encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            f_["count"] += 1
            mins = (row.get("Handle_Minutes") or "").strip()
            m = int(mins) if mins.isdigit() else 0
            f_["minutes"] += m
            f_["by_line"][r.line_num] = (row.get("Ticket_ID"), row.get("Category"), m)
            if (row.get("Category") or "").strip() == TARGET:
                f_["t_count"] += 1
                f_["t_minutes"] += m
    return f_


def check_arithmetic(units):
    P, T = pnl_facts(DATA), ticket_facts(DATA)
    q1, ws = read(ASK_OUT[0]), read(VALUE_OUT[0])
    tw, ba = read(AUTO_OUT[0]), read(AUTO_OUT[1])
    check("4a raw P&L: SaaS rows add up to the stated subtotal row", P["total"] == P["stated"],
          f"sum {n(P['total'])}, stated {P['stated'] and n(P['stated'])}, {len(P['rows'])} rows")

    bad = []
    for want, text, label in [
        (f"As listed: {n(P['total'])} USD", q1, "q1 as listed"),
        (f"Without the suspected duplicate: {n(P['net'])} USD ({n(P['total'])} - {n(P['dup'])})", q1, "q1 without duplicate"),
        (f"= {n(P['total'])} USD.", q1, "q1 arithmetic line"),
        (f"# Value number: {n(P['dup'])} USD", ws, "worksheet headline"),
        (f"{n(P['total'])} - {n(P['dup'])} = {n(P['net'])} USD", ws, "worksheet subtraction"),
        (f"| Computed sum of the {len(P['rows'])} numeric rows above | {n(P['total'])} |", ws, "worksheet computed sum"),
    ]:
        if want not in text:
            bad.append(f"{label}: expected text {want!r} not found")
    # every SaaS row is itemised in both outputs with the raw amount next to its own citation
    for line, item, amt in P["rows"]:
        cite = f"`{P['file']}:L{line}` (Line Item: {item})"
        if f"| {item} | {n(amt)} |" not in q1 or cite not in q1:
            bad.append(f"q1 table: row L{line} {item} {n(amt)} missing or wrong")
        if f"| {cite} | {n(amt)} |" not in ws:
            bad.append(f"worksheet baseline: row L{line} {item} {n(amt)} missing or wrong")
    check("4b SaaS as listed, duplicate and net figures printed equal the raw recomputation", not bad,
          short(bad) or f"as listed {n(P['total'])}, duplicate {n(P['dup'])}, without {n(P['net'])}")

    bad = []
    for want, text, label in [
        (f"{n(T['minutes'])} minutes ({T['minutes'] / 60:.1f} hours) logged on {n(T['count'])} tickets", tw, "time_waste queue total"),
        (f"{n(T['t_minutes'])} minutes ({T['t_minutes'] / 60:.1f} hours) on {n(T['t_count'])} tickets", tw, "time_waste target"),
        (f"{n(T['t_minutes'])} minutes ({T['t_minutes'] / 60:.1f} hours) of handling logged on {n(T['t_count'])} {TARGET} tickets", ba, "before_after headline"),
        (f"| SELF_SERVE | {n(T['t_count'])} | {n(T['t_minutes'])} |", ba, "before_after self-serve row"),
        (f"| Total | {n(T['count'])} | {n(T['minutes'])} |", ba, "before_after total row"),
    ]:
        if want not in text:
            bad.append(f"{label}: expected text {want!r} not found")
    check("4c ticket totals (all rows, automated category) printed equal the raw recomputation", not bad,
          short(bad) or f"{T['count']} tickets {n(T['minutes'])} min, target {T['t_count']} tickets {n(T['t_minutes'])} min")

    # rows cited one by one behind sums: each "cite = minutes" pair must match the raw row
    pairs = re.findall(r"`(%s):L(\d+)` = (\d+)" % re.escape(T["file"]), tw)
    bad = [f"L{l} printed {m}, raw {T['by_line'].get(int(l), ('?', '?', '?'))[2]}" for _, l, m in pairs
           if T["by_line"].get(int(l), (None, None, None))[2] != int(m)]
    lines = [int(l) for _, l, _ in pairs]
    if sorted(lines) != sorted(T["by_line"]):
        bad.append(f"{len(lines)} rows cited behind the sums, {len(T['by_line'])} rows in the raw file")
    if sum(int(m) for _, _, m in pairs) != T["minutes"]:
        bad.append("cited minutes do not add up to the raw total")
    check("4d time_waste.md cites every ticket row once with its raw minutes", not bad, short(bad) or f"{len(pairs)} rows")

    rows_ba = re.findall(r"\| `%s:L(\d+)` \(Ticket_ID: ([^)]+)\) \| [^|]+ \| (\d+) \| SELF_SERVE \|" % re.escape(T["file"]), ba)
    bad = [f"L{l}" for l, tid, m in rows_ba if T["by_line"].get(int(l)) != (tid, TARGET, int(m))]
    ok = not bad and len(rows_ba) == T["t_count"] and sum(int(m) for _, _, m in rows_ba) == T["t_minutes"]
    check("4e rows behind the before number re-add to it and are all the target category", ok,
          short(bad) or f"{len(rows_ba)} rows, {n(sum(int(m) for _, _, m in rows_ba))} minutes")

    with open(AUTO_OUT[2], encoding="utf-8", newline="") as f:
        q = list(csv.DictReader(f))
    ss = [r for r in q if r["action"] == "SELF_SERVE"]
    ok = (len(q) == T["count"] and len(ss) == T["t_count"]
          and sum(int(r["handle_minutes"]) for r in ss) == T["t_minutes"]
          and all(r["category"] == TARGET for r in ss))
    check("4f routed_queue.csv: one row per ticket, self-serve rows equal the target category", ok,
          f"{len(q)} rows, {len(ss)} self-serve")
    return P, T


# ---------- 5. cross-stream consistency ----------

def check_consistency(P):
    q1, ws = read(ASK_OUT[0]), read(VALUE_OUT[0])
    tw, ba = read(AUTO_OUT[0]), read(AUTO_OUT[1])
    shared = dict(re.findall(r"^\| (Software & SaaS, as listed|Suspected duplicate|Software & SaaS, without the suspected duplicate) \| ([\d,]+) \|$", ws, re.M))
    a = re.search(r"As listed: ([\d,]+) USD", q1)
    b = re.search(r"Without the suspected duplicate: ([\d,]+) USD \(([\d,]+) - ([\d,]+)\)", q1)
    bad = []
    if len(shared) != 3 or not a or not b:
        bad.append("shared figures not found in one of the two files")
    else:
        if shared["Software & SaaS, as listed"] != a.group(1):
            bad.append("as listed differs")
        if shared["Suspected duplicate"] != b.group(3):
            bad.append("duplicate amount differs")
        if shared["Software & SaaS, without the suspected duplicate"] != b.group(1):
            bad.append("figure without duplicate differs")
    check("5a ask q1 and value worksheet agree on the three shared amounts", not bad,
          short(bad) or ", ".join(f"{k}: {v}" for k, v in shared.items()))
    check('5b both use the status wording "suspected, unconfirmed"', STATUS in q1 and STATUS in ws,
          f"q1 {STATUS in q1}, worksheet {STATUS in ws}")
    head = ws.splitlines()[0]
    check("5c worksheet first line has exactly one figure, with unit, period and status",
          len(re.findall(r"\d[\d,]*(?:\.\d+)? USD", head)) == 1 and re.search(r"Q[1-4] \d{4}", head) and "unconfirmed" in head, head[:110])

    def figs(text):
        t = re.search(r"([\d,]+) minutes \(([\d.]+) hours\)[^.\n]*? on (\d+) (?:%s )?tickets" % re.escape(TARGET), text)
        return t.groups() if t else None
    f_tw = re.search(r"Automate first:.*?MEASURED ([\d,]+) minutes \(([\d.]+) hours\) on (\d+) tickets", tw)
    f_ba = re.search(r"Before \(MEASURED\): ([\d,]+) minutes \(([\d.]+) hours\) of handling logged on (\d+)", ba)
    tot_tw = re.search(r"MEASURED ([\d,]+) minutes \([\d.]+ hours\) logged on (\d+) tickets", tw)
    tot_ba = re.search(r"\| Total \| (\d+) \| ([\d,]+) \|", ba)
    ok = bool(f_tw and f_ba and tot_tw and tot_ba) and f_tw.groups() == f_ba.groups() \
        and (tot_tw.group(2), tot_tw.group(1)) == tot_ba.groups()
    check("5d time_waste.md and before_after.md agree on target and queue totals", ok,
          f"target {f_tw and f_tw.groups()} vs {f_ba and f_ba.groups()}; queue {tot_tw and tot_tw.groups()} vs {tot_ba and tot_ba.groups()}")

    # modelled rows must follow from the measured row and the printed shares
    m = re.search(r"\| Share of those tickets[^|]*\| ASSUMPTION \| (\d+)% \| (\d+)% \|", ba)
    s = re.search(r"\| Minutes saved[^|]*\| MODELLED \| ([\d,.]+) \| ([\d,.]+) \|", ba)
    aft = re.search(r"\| After = before - saved \| MODELLED \| ([\d,.]+) \| ([\d,.]+) \|", ba)
    ok = False
    if m and s and aft and f_ba:
        before = int(f_ba.group(1).replace(",", ""))
        lo, hi = (before * int(x) / 100 for x in m.groups())
        num = lambda x: float(x.replace(",", ""))
        ok = (abs(num(s.group(1)) - lo) < 0.06 and abs(num(s.group(2)) - hi) < 0.06
              and abs(num(aft.group(1)) - (before - lo)) < 0.06 and abs(num(aft.group(2)) - (before - hi)) < 0.06)
    check("5e modelled saving equals measured minutes times the printed ASSUMPTION shares", ok,
          f"shares {m and m.groups()}, saved {s and s.groups()}, after {aft and aft.groups()}")


# ---------- 6. fresh-file smoke test ----------

NEW_SAAS = ("Miro", 1234)
BUMP = ("HubSpot", 500)
NEW_WHEN = "Wed Jun 17, 9:00 AM"
NEW_MSG = ("**Dana Whitfield** " + EM + " " + NEW_WHEN + "\n"
           "Update on Sales hiring: Q2 pipeline has recovered, so we are lifting the freeze. "
           "REQ-114 is approved to move forward again and Tom\u00e1s can restart the search.")


def perturb(dst):
    p = next(dst.glob("pnl_*.csv"))
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        cells = line.split(",")
        if len(cells) > 2 and cells[0] == SAAS and cells[1] == BUMP[0]:
            cells[2] = str(int(cells[2]) + BUMP[1])
            line = ",".join(cells)
        if len(cells) > 1 and cells[0] == SAAS and "subtotal" in cells[1].lower():
            out.append(f"{SAAS},{NEW_SAAS[0]},{NEW_SAAS[1]},Whiteboard")
        out.append(line)
    write(p, "\n".join(out) + "\n")

    t = next(dst.glob("support_tickets_*.csv"))
    body = t.read_text(encoding="utf-8").rstrip("\n")
    body += "\nTCK-9001,2026-03-30,Billing dispute,creator_newcase,Ops Support,30,Closed"
    body += f"\nTCK-9002,2026-03-30,{TARGET},creator_blankcase,Ops Support,,Closed\n"
    write(t, body)

    s = next(dst.glob("slack_export*.md"))
    lines = s.read_text(encoding="utf-8").splitlines()
    k = lines.index("## #finance")          # insert at the end of #leadership, before its closing rule
    while lines[k - 1].strip() in ("", "---"):
        k -= 1
    lines[k:k] = ["", "---", ""] + NEW_MSG.split("\n")
    write(s, "\n".join(lines) + "\n")


def no_trace(code, out, err):
    return code == 0 and "Traceback" not in out and "Traceback" not in err


def check_fresh(P0, T0):
    committed = snapshot(ASK_OUT + VALUE_OUT + AUTO_OUT)
    ask_clobbered, ask_out_ok = False, False
    tmp = Path(tempfile.mkdtemp(prefix="valis_check_"))
    try:
        d = tmp / "data"
        shutil.copytree(DATA, d)
        perturb(d)
        units = build_units(d)
        P, T = pnl_facts(d), ticket_facts(d)
        assert P["total"] == P0["total"] + BUMP[1] + NEW_SAAS[1] and T["count"] == T0["count"] + 2

        # ask: --out redirects its files (added after round 1). Committed outputs must stay untouched.
        ao = tmp / "ask_out"
        code, out, err = run(["ask/ask.py", "--data", d, "--out", ao])
        ask_out_ok = all((ao / f).exists() and read(ao / f).strip() for f in ("q1.md", "q2.md"))
        ask_clobbered = snapshot(ASK_OUT) != {k: v for k, v in committed.items() if k in map(str, ASK_OUT)}
        q1, _, q2 = out.partition("# Q2.")
        q2 = "# Q2." + q2
        check("6a ask on perturbed data: exit 0, no traceback", no_trace(code, out, err), (err or "")[-160:].strip())
        bad = []
        if f"As listed: {n(P['total'])} USD" not in q1 and f"{n(P['total'])} USD" not in q1:
            bad.append(f"new sum {n(P['total'])} not printed")
        if f"| {NEW_SAAS[0]} | {n(NEW_SAAS[1])} |" not in q1:
            bad.append("added row not itemised")
        if f"**As listed, {n(P0['total'])} USD" in q1:
            bad.append("old headline figure repeated")
        if not re.search(r"(?i)(does not|do not|no longer|not) (match|equal|reconcile)", q1):
            bad.append("no statement that rows and stated subtotal differ")
        if n(P["net"]) not in q1:
            bad.append(f"figure without duplicate {n(P['net'])} not printed")
        check("6b ask Q1 moved the right way (new sum, new row, subtotal mismatch stated)", not bad, short(bad) or f"as listed {n(P['total'])}, without duplicate {n(P['net'])}")
        state = next((l for l in q2.splitlines() if l.startswith("**2. Current state")), "")
        cur0 = next((l for l in committed[str(ASK_OUT[1])].decode("utf-8").splitlines() if l.startswith("**2. Current state")), "")
        bad = []
        if NEW_WHEN not in q2:
            bad.append("new #leadership message not cited")
        if not state or state == cur0 or re.search(r"Current state: frozen", state):
            bad.append("current state still reads frozen")
        if NEW_WHEN not in state and "2026-06-17" not in state:
            bad.append("current state line does not rest on the new message")
        check("6c ask Q2 current state follows the later message that lifts the freeze", not bad, short(bad) or state[:120])
        c, pr = resolve_text(out, units, "ask stdout")
        check("6d ask citations on perturbed data resolve against the perturbed files", not pr and c > 0, short(pr) or f"{c} citations")

        code, out, err = run(["value/value.py", "--data", d])
        check("6e value on perturbed data: exit 0, no traceback", no_trace(code, out, err), (err or "")[-160:].strip())
        bad = []
        if f"| {n(P['total'])} |" not in out:
            bad.append(f"new computed sum {n(P['total'])} not printed")
        if f"{n(P['total'])} - {n(P['dup'])} = {n(P['net'])} USD" not in out:
            bad.append("subtraction not redone on the new sum")
        if "DOES NOT match" not in out and not re.search(r"(?i)(does not|do not) (match|reconcile)", out):
            bad.append("subtotal mismatch not stated")
        if NEW_SAAS[0] not in out:
            bad.append("added row not in the baseline")
        c, pr = resolve_text(out, units, "value stdout")
        check("6f value moved the right way and its citations resolve", not bad and not pr and c > 0, short(bad + pr) or f"{c} citations, sum {n(P['total'])}")
        check("6g value left the committed worksheet untouched with --data", snapshot(VALUE_OUT) == {k: v for k, v in committed.items() if k in map(str, VALUE_OUT)})

        o = tmp / "auto_out"
        code, out, err = run(["automation/run.py", "--data", d, "--out", o, "--check"])
        check("6h automation on perturbed data: exit 0 with --check, no traceback", no_trace(code, out, err), ((err or out) or "")[-200:].strip().replace("\n", " / "))
        bad, pr, c = [], [], 0
        if (o / "routed_queue.csv").exists():
            with open(o / "routed_queue.csv", encoding="utf-8", newline="") as f:
                q = {r["ticket_id"]: r for r in csv.DictReader(f)}
            if len(q) != T["count"]:
                bad.append(f"{len(q)} queue rows, {T['count']} input rows")
            for tid in ("TCK-9001", "TCK-9002"):
                if q.get(tid, {}).get("action") != "EXCEPTION":
                    bad.append(f"{tid} action is {q.get(tid, {}).get('action')}")
            ba = read(o / "before_after.md")
            if "caught 2 exceptions" not in ba:
                bad.append("report does not say 2 exceptions")
            if f"| Total | {T['count']} |" not in ba:
                bad.append("total ticket count did not change")
            if f"| Total | {T['count']} | {n(T['minutes'])} |" not in ba:
                bad.append(f"total minutes not {n(T['minutes'])} (unknown category minutes kept, blank minutes add nothing)")
            for name in ("time_waste.md", "before_after.md"):
                ci, pi = resolve_text(read(o / name), units, name)
                c, pr = c + ci, pr + pi
        else:
            bad.append("no routed_queue.csv written")
        check("6i automation: unknown category and blank minutes go to EXCEPTION, totals change, citations resolve", not bad and not pr, short(bad + pr) or f"{c} citations")
        check("6j automation left committed outputs untouched with --out", snapshot(AUTO_OUT) == {k: v for k, v in committed.items() if k in map(str, AUTO_OUT)})

        # degenerate bundles: plain message, exit 0, no number invented
        d2 = tmp / "no_pnl"
        shutil.copytree(DATA, d2)
        next(d2.glob("pnl_*.csv")).unlink()
        next(d2.glob("support_tickets_*.csv")).unlink()
        r1, r2, r3 = run(["ask/ask.py", "--q", "q1", "--data", d2]), run(["value/value.py", "--data", d2]), run(["automation/run.py", "--data", d2, "--out", tmp / "o2"])
        bad = [nm for nm, r in (("ask", r1), ("value", r2), ("automation", r3)) if not no_trace(*r)]
        if n(P0["total"]) in r1[1] or n(P0["dup"]) + " USD" in r2[1]:
            bad.append("old figure printed without its source file")
        if not re.search(r"(?i)cannot answer", r1[1]):
            bad.append("ask does not say it cannot answer")
        if "CANNOT RUN" not in r3[1] + r3[2]:
            bad.append("automation does not say CANNOT RUN")
        check("6k source file removed: plain message, exit 0, no stale figure", not bad, short(bad))

        d3 = tmp / "no_pair"
        shutil.copytree(DATA, d3)
        p3 = next(d3.glob("pnl_*.csv"))
        keep = [l for l in p3.read_text(encoding="utf-8").splitlines() if not l.startswith(f"{SAAS},Amplitude Analytics,")]
        write(p3, "\n".join(keep) + "\n")
        code, out, err = run(["value/value.py", "--data", d3])
        check("6l duplicate row removed: value reports no candidate and no number", no_trace(code, out, err) and "No candidate found" in out and "# Value number: " + n(P0["dup"]) not in out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        # restore committed outputs with the default commands, then verify
        for _, cmd, _ in COMMANDS:
            run(cmd)
        restored = snapshot(ASK_OUT + VALUE_OUT + AUTO_OUT) == committed
    check("6m ask --data --out writes there and does not overwrite its committed outputs (round 1 M3)", not ask_clobbered and ask_out_ok,
          "ask/out/ was overwritten by the perturbed run" if ask_clobbered else ("" if ask_out_ok else "q1.md or q2.md not written to --out"))
    check("6n committed outputs are back to what the default commands produce", restored)


# ---------- 8. regression and new adversarial cases (round 2) ----------

def slack_add(d, before_heading, author, when, text):
    """Insert one message at the end of the channel that precedes `before_heading`."""
    s = next(d.glob("slack_export*.md"))
    lines = read(s).splitlines()
    k = lines.index(before_heading)
    while lines[k - 1].strip() in ("", "---"):
        k -= 1
    lines[k:k] = ["", "---", "", f"**{author}** {EM} {when}", text]
    write(s, "\n".join(lines) + "\n")


def swap(d, glob, a, b):
    p = next(d.glob(glob))
    t = read(p)
    assert a in t, a
    write(p, t.replace(a, b))


def state_line(out):
    return next((l for l in out.splitlines() if l.startswith("**2. Current state")), "")


def check_regressions(P0, T0):
    q2_default = state_line(read(ASK_OUT[1]))
    ba = read(AUTO_OUT[1])
    head = ba.split("## Before (MEASURED)")[0]
    bad = []
    if "Minutes saved by this run alone: 0" not in head:
        bad.append("headline does not say the run alone saves 0 minutes")
    if re.search(r"\d+ before, \d+ after routing", ba):
        bad.append("the '140 before, 77 after routing' claim is back")
    if not re.search(r"Scenario, not a result", head) or "ASSUMPTION" not in head:
        bad.append("modelled after is not labelled a scenario resting on an ASSUMPTION in the headline")
    if re.search(r"\*\*After \(MODELLED\)", head):
        bad.append("a modelled after figure is still a bold headline")
    check("8a automation headline: run alone saves 0, modelled after is a labelled scenario (round 1 M4)", not bad, short(bad))

    tmp = Path(tempfile.mkdtemp(prefix="valis_check_"))
    FIN, DANA, D17 = "## #finance", "Dana Whitfield", "Wed Jun 17, 9:00 AM"

    def q2_case(name, build):
        d = tmp / name
        shutil.copytree(DATA, d)
        build(d)
        code, out, err = run(["ask/ask.py", "--q", "q2", "--data", d])
        return no_trace(code, out, err), state_line(out), out

    lifted = lambda l: bool(re.search(r"Current state: [^*]*lifted", l))
    frozen = lambda l: bool(re.search(r"Current state: frozen", l))
    unsure = lambda l: "NOT CERTAIN" in l

    try:
        # --- round 1 M1 cases
        ok, l, out = q2_case("reworded", lambda d: slack_add(d, FIN, DANA, D17, "Pipeline looks better. The hold on Sales hiring is over, Tomás go ahead and make the offer on REQ-114."))
        check("8b Q2 reworded lift by the CEO: not reported as certainly frozen, message shown (round 1 M1)",
              ok and (unsure(l) or lifted(l)) and D17 in out and not re.search(r"Nothing in the bundle[^.]*later than 2026-06-15", out), l[:110])
        ok, l, out = q2_case("negated", lambda d: slack_add(d, FIN, DANA, D17, "To kill the rumour: we are NOT lifting the freeze on Sales hiring. REQ-114 stays where it is."))
        check("8c Q2 negated lift by the CEO: not reported as lifted (round 1 M1)", ok and not lifted(l), l[:110])
        ok, l, out = q2_case("opinion", lambda d: slack_add(d, FIN, "Tomás Reyes", D17, "I think the freeze should be lifted, we should resume hiring for REQ-114 now."))
        check("8d Q2 opinion from a non-owner: state unchanged, message still shown (round 1 M1)", ok and frozen(l) and D17 in out, l[:110])

        # --- new in round 2
        def note(d):
            write(d / "meeting_notes" / "leadership_sync_2026-06-17.md",
                  f"# Leadership Sync {EM} 2026-06-17\n\n**Date:** 2026-06-17 (Wed)\n**Attendees:** Dana Whitfield (CEO), Priya Raman (CFO)\n\n"
                  "## 1. Sales headcount  *(decision)*\n\n- Priya showed Q2 pipeline coverage back at target.\n"
                  "- **DECISION:** Lift the Sales headcount freeze. REQ-114 (AE) is reopened and recruiting resumes. Decision made by Dana (CEO).\n")
        ok, l, out = q2_case("note", note)
        check("8e Q2 later meeting note with a decision record reversing the freeze: reported as lifted or not certain",
              ok and (lifted(l) or unsure(l)) and "leadership_sync_2026-06-17.md" in out, l[:110])
        ok, l, out = q2_case("farneg", lambda d: slack_add(d, FIN, DANA, D17, "We are not, despite what Tomás has been telling people in the hallway all week, lifting the freeze on Sales hiring."))
        check("8f Q2 negation far from the status word: not reported as lifted", ok and not lifted(l), l[:110])
        ok, l, out = q2_case("conditional", lambda d: slack_add(d, FIN, DANA, D17, "If July conversion holds we will be lifting the freeze on Sales hiring, REQ-114 first in line."))
        check("8g Q2 conditional future lift: not reported as lifted", ok and not lifted(l), l[:110])
        ok, l, out = q2_case("othertopic", lambda d: slack_add(d, FIN, DANA, D17, "We are lifting the freeze on Engineering contractor spend as of today."))
        check("8h Q2 CEO lifts a different freeze (no mention of Sales): Sales state not reported as lifted", ok and not lifted(l), l[:110])
        ok, l, out = q2_case("order", lambda d: slack_add(d, FIN, DANA, "Tue Jun 9, 5:00 PM", "Before tomorrow: for now Sales hiring stays open and REQ-114 is approved as is."))
        check("8i Q2 older message placed out of order in the file: later decision still governs", ok and frozen(l), l[:110])

        def refreeze(d):
            slack_add(d, FIN, DANA, D17, "Update: we are lifting the freeze on Sales hiring, REQ-114 is approved to proceed.")
            slack_add(d, FIN, DANA, "Wed Jun 17, 4:00 PM", "Scratch that. After the forecast call Sales hiring is frozen again, REQ-114 back on hold.")
        ok, l, out = q2_case("refreeze", refreeze)
        check("8j Q2 lift then refreeze on the same day: last statement governs", ok and frozen(l) and "4:00 PM" in l, l[:110])

        # --- round 1 M2: a later message about the duplicate
        d = tmp / "resolved"
        shutil.copytree(DATA, d)
        slack_add(d, "## #ops", "Maya Fortin", "Tue Jun 16, 9:00 AM", "Invoice is back. Amplitude and Amplitude Analytics are two separate contracts, not a duplicate. Both lines are real.")
        r1, r2 = run(["ask/ask.py", "--q", "q1", "--data", d]), run(["value/value.py", "--data", d])
        bad = [nm for nm, r in (("ask", r1), ("value", r2)) if not no_trace(*r)]
        if re.search(r"latest (word|message) on it is `[^`]*Mon Jun 2, 10:47 AM", r1[1]):
            bad.append("ask still calls the Jun 2 message the latest")
        if "Tue Jun 16, 9:00 AM" not in r1[1] or "later message" not in r1[1].split("## Evidence")[0]:
            bad.append("ask answer block does not flag the later message")
        vh = r2[1].splitlines()[0] if r2[1] else ""
        if "later message" not in vh or "closed by one invoice" in vh:
            bad.append("value headline does not flag the later message")
        check("8k later message about the duplicate is flagged at the top by ask and value (round 1 M2)", not bad, short(bad) or vh[:110])

        # --- round 1 m5 plus cross-stream agreement on the same file
        d = tmp / "currency"
        shutil.copytree(DATA, d)
        swap(d, "pnl_*.csv", f"{SAAS},Looker,11000", f'{SAAS},Looker,"$11,000"')
        r1, r2 = run(["ask/ask.py", "--q", "q1", "--data", d]), run(["value/value.py", "--data", d])
        a = re.search(r"\*\*(PARTIAL\. )?As listed, ([\d,.]+) USD", r1[1])
        check("8l ask reads a $ and comma formatted amount, or marks the headline PARTIAL (round 1 m5)",
              no_trace(*r1) and bool(a) and (a.group(2) == n(P0["total"]) or bool(a.group(1))), a.group(0) if a else "headline not found")
        v = re.search(r"\| Computed sum of the \d+ numeric rows above \| ([\d,.]+) \|", r2[1])
        check("8m ask and value give the same as-listed total on that same file (cross-stream)",
              no_trace(*r2) and bool(a and v) and a.group(2) == v.group(1), f"ask {a and a.group(2)}, value {v and v.group(1)}")

        # --- round 1 m6: implausible minutes and a repeated ticket ID
        d = tmp / "tickets"
        shutil.copytree(DATA, d)
        t = next(d.glob("support_tickets_*.csv"))
        first_id = read(t).splitlines()[1].split(",")[0]
        write(t, read(t).rstrip("\n") + f"\nTCK-9005,2026-03-30,{TARGET},creator_x,Ops Support,9999,Closed\n{first_id},2026-03-30,{TARGET},creator_y,Ops Support,20,Closed\n")
        o = tmp / "tickets_out"
        r = run(["automation/run.py", "--data", d, "--out", o, "--check"])
        bad = [] if no_trace(*r) else ["run failed"]
        if (o / "routed_queue.csv").exists():
            with open(o / "routed_queue.csv", encoding="utf-8", newline="") as f:
                q = list(csv.DictReader(f))
            if [x["action"] for x in q if x["ticket_id"] == "TCK-9005"] != ["EXCEPTION"]:
                bad.append("9,999 minute ticket not in EXCEPTION")
            if [x["action"] for x in q if x["ticket_id"] == first_id][1:] != ["EXCEPTION"]:
                bad.append("repeated ticket ID not in EXCEPTION")
            if f"**Before (MEASURED): {n(T0['t_minutes'])} minutes" not in read(o / "before_after.md"):
                bad.append("before number moved: excluded minutes were counted")
        else:
            bad.append("no routed_queue.csv")
        check("8n implausible minutes and a repeated ticket ID go to EXCEPTION and are not counted (round 1 m6)", not bad, short(bad))

        # --- new: renamed column, second lookalike pair
        d = tmp / "renamed"
        shutil.copytree(DATA, d)
        swap(d, "support_tickets_*.csv", "Handle_Minutes", "Minutes")
        r = run(["automation/run.py", "--data", d, "--out", tmp / "renamed_out"])
        check("8o ticket file with a renamed column: plain CANNOT RUN naming the column, no traceback, nothing written",
              "Traceback" not in r[1] + r[2] and "CANNOT RUN" in r[1] + r[2] and "Handle_Minutes" in r[1] + r[2] and not (tmp / "renamed_out" / "routed_queue.csv").exists())
        d = tmp / "pairs"
        shutil.copytree(DATA, d)
        swap(d, "pnl_*.csv", f"{SAAS},Zoom,1800,Video calls", f"{SAAS},Zoom,1800,Video calls\n{SAAS},Zoom Phone,1800,Telephony")
        r1, r2 = run(["ask/ask.py", "--q", "q1", "--data", d]), run(["value/value.py", "--data", d])
        want = n(P0["dup"] + 1800)
        check("8p second lookalike pair in the category: both tools show both pairs and the same combined amount",
              no_trace(*r1) and no_trace(*r2) and r2[1].startswith(f"# Value number: {want} USD") and f"- {want})" in r1[1]
              and "Zoom Phone" in r1[1] and "detected by rule only" in r1[1], f"expected {want}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    check("8q committed outputs untouched by the regression runs", q2_default == state_line(read(ASK_OUT[1])) and ba == read(AUTO_OUT[1]))


# ---------- 7. hygiene ----------

SKIP_DIRS = {".git", "__pycache__", "data", "chat_logs"}
TEXT_EXT = {".md", ".py", ".json", ".csv", ".txt", ".sh", ""}
NETWORK = {"socket", "ssl", "http", "urllib", "ftplib", "smtplib", "poplib", "imaplib", "telnetlib", "xmlrpc",
           "socketserver", "asyncio", "webbrowser", "subprocess", "requests", "httpx", "aiohttp", "openai", "anthropic"}


def repo_files():
    for p in sorted(ROOT.rglob("*")):
        if p.is_file() and not (set(p.relative_to(ROOT).parts[:-1]) & SKIP_DIRS) and p.suffix in TEXT_EXT:
            yield p


def check_hygiene():
    # an em dash is allowed on a line with a quotation mark or a citation, or where the text around
    # the dash is found word for word in a source file (for example a source heading listed verbatim)
    source = "\n".join(read(p) for p in sorted(DATA.rglob("*")) if p.suffix in (".md", ".csv"))

    def verbatim(line):
        return all(line[max(0, m.start() - 6):m.end() + 6] in source for m in re.finditer(EM, line))
    bad = []
    for p in repo_files():
        try:
            lines = read(p).splitlines()
        except UnicodeDecodeError:
            continue
        for i, line in enumerate(lines, 1):
            if EM in line and not any(q in line for q in ('"', "\u201c", "\u201d", "`")) and not verbatim(line):
                bad.append(f"{p.relative_to(ROOT).as_posix()}:{i}")
    check("7a no em dash outside a quoted, cited or verbatim source line (authored files and outputs)", not bad, short(bad, 8))

    local = {p.stem for p in ROOT.rglob("*.py")}
    std = getattr(sys, "stdlib_module_names", None)
    bad, seen = [], 0
    for p in sorted(ROOT.rglob("*.py")):
        if set(p.relative_to(ROOT).parts) & {".git", "__pycache__"}:
            continue
        shipped = p.relative_to(ROOT).parts[0] != "tests"
        src = read(p)
        for node in ast.walk(ast.parse(src)):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                mods = [node.module.split(".")[0]]
            for m in mods:
                seen += 1
                if m in local:
                    continue
                if std is not None and m not in std:
                    bad.append(f"{p.name}: third-party import {m}")
                if shipped and m in NETWORK:
                    bad.append(f"{p.name}: network or shell module {m}")
        if shipped and re.search(r"urlopen|os\.system|os\.popen|__import__\(", src):
            bad.append(f"{p.name}: network or shell call in text")
    check("7b .py files import only the standard library, and shipped code has no network or shell module", not bad,
          short(bad) or f"{seen} imports scanned" + ("" if std is not None else ", stdlib list needs Python 3.10+, network scan only"))

    # the stated target is macOS, whose stock python3 is 3.9, and the READMEs promise 3.8 or later.
    # Static check: 3.8 grammar, plus calls and modules that only exist from 3.9 or 3.10.
    new_attrs = {"removeprefix": "3.9", "removesuffix": "3.9", "bit_count": "3.10", "pairwise": "3.10", "is_relative_to": "3.9",
                 "readlink": "3.9", "with_stem": "3.9", "randbytes": "3.9", "to_thread": "3.9"}
    new_mods = {"zoneinfo": "3.9", "graphlib": "3.9", "tomllib": "3.11"}
    generic = {"list", "dict", "tuple", "set", "frozenset", "type"}
    bad = []
    shipped_py = [p for p in sorted(ROOT.rglob("*.py")) if not (set(p.relative_to(ROOT).parts) & {".git", "__pycache__"})]
    for p in shipped_py:
        rel = p.relative_to(ROOT).as_posix()
        try:
            tree = ast.parse(read(p), feature_version=(3, 8))
        except SyntaxError as e:
            bad.append(f"{rel}: syntax newer than Python 3.8 (line {e.lineno})")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                kw = {k.arg for k in node.keywords}
                if node.func.attr == "write_text" and "newline" in kw:
                    bad.append(f"{rel}:{node.lineno} Path.write_text(newline=) needs Python 3.10")
                if node.func.attr in new_attrs:
                    bad.append(f"{rel}:{node.lineno} .{node.func.attr}() needs Python {new_attrs[node.func.attr]}")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "zip" \
                    and "strict" in {k.arg for k in node.keywords}:
                bad.append(f"{rel}:{node.lineno} zip(strict=) needs Python 3.10")
            if isinstance(node, ast.Attribute) and node.attr in ("week", "weekday") and isinstance(node.value, ast.Call) \
                    and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == "isocalendar":
                bad.append(f"{rel}:{node.lineno} isocalendar().{node.attr} needs Python 3.9")
            if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id in generic:
                bad.append(f"{rel}:{node.lineno} {node.value.id}[...] needs Python 3.9")
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for m in ([a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]):
                    if m.split(".")[0] in new_mods:
                        bad.append(f"{rel}:{node.lineno} module {m} needs Python {new_mods[m.split('.')[0]]}")
    old_py = next((w for w in (shutil.which("python3.8"), shutil.which("python3.9")) if w), None)
    ran = "no python3.8 or python3.9 on this machine: STATIC ONLY, no real run on those versions happened"
    if old_py:
        tmp = Path(tempfile.mkdtemp(prefix="valis_check_"))
        try:
            for cmd in (["ask/ask.py", "--out", tmp / "a"], ["value/value.py", "--out", tmp / "v.md"], ["automation/run.py", "--out", tmp / "o", "--check"]):
                pr = subprocess.run([old_py] + [str(c) for c in cmd], cwd=str(ROOT), capture_output=True, timeout=180)
                if pr.returncode != 0 or b"Traceback" in pr.stderr:
                    bad.append(f"{cmd[0]} fails under {old_py}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        ran = f"also run for real under {old_py}"
    check("7d code is compatible with Python 3.8 and 3.9 (round 1 B1)", not bad, short(bad) or f"{len(shipped_py)} files, {ran}")

    # hardcoded names, vendors, categories and amounts in deliverable code (vocabulary files are checked for people and vendors only)
    people, vendors, cats = set(), set(), set()
    with open(DATA / "headcount_roster.csv", encoding="utf-8", newline="") as f:
        for row in csv.reader(f):
            if len(row) == 6 and re.match(r"^\d{4}-|^$", row[4]) and row[3] == "Active":
                people.add(row[0])
    P, T = pnl_facts(DATA), ticket_facts(DATA)
    vendors = {item for _, item, _ in P["rows"] if item.lower() not in ("slack", "notion", "zoom")}
    cats = {c for _, c, _ in T["by_line"].values()}
    amounts = {str(P["total"]), n(P["total"]), str(P["dup"]), n(P["dup"]), str(P["net"]), n(P["net"]),
               str(T["minutes"]), n(T["minutes"]), str(T["t_minutes"]), n(T["t_minutes"]), "REQ-114"}
    first = {x.split()[0] for x in people if len(x.split()[0]) > 3}
    bad = []
    for folder in ("ask", "value", "automation"):
        for p in sorted((ROOT / folder).glob("*.py")) + sorted((ROOT / folder).glob("*.json")):
            src = read(p)
            terms = people | first | vendors | (set() if p.suffix == ".json" else cats | amounts)
            hits = sorted(t for t in terms if re.search(r"(?<![\w-])" + re.escape(t) + r"(?![\w-])", src))
            if hits:
                bad.append(f"{folder}/{p.name}: {', '.join(hits[:5])}")
    check("7c no person, vendor, category or amount from the bundle is typed into deliverable code", not bad, short(bad))


# ---------- 9. regression cases from the external audit of 2026-11-10 ----------
#
# Each scenario below reproduces a finding of chat_logs/external_review_2026-11-10/AUDIT_LOG.md.
# Every check fails on the behaviour of commit 934d741 and passes only on the corrected behaviour.
# Assertions are on figures and labels, not on sentences, because the wording of the outputs moves.

WORD = r"(?<![A-Za-z0-9])(%s)(?![A-Za-z0-9])"


def _abbrev(a, b):
    """Own implementation of the abbreviation rule in the deliverable READMEs: word for word
    equal except that one word is a subsequence of the other, same first letter, 3+ letters."""
    wa, wb = a.lower().split(), b.lower().split()
    if len(wa) != len(wb) or wa == wb:
        return False
    for x, y in zip(wa, wb):
        x, y = x.rstrip("."), y.rstrip(".")
        if x == y:
            continue
        s, l = sorted((x, y), key=len)
        it = iter(l)
        if len(s) < 3 or s[0] != l[0] or not all(c in it for c in s):
            return False
    return True


def _similar(a, b):
    return a.lower().split() == b.lower().split() or words_prefix(a, b) or words_prefix(b, a) or _abbrev(a, b)


def saas_expected(data_dir):
    """Expected Q1 and worksheet figures, recomputed here from the raw rows (pipeline/shared.py is not used).
    SaaS row: category label contains the word SaaS. Subtotal or total rows are left out.
    Repeat: a later row with a near-identical label and an equal amount to some earlier row, counted once."""
    path = next(Path(data_dir).glob("pnl_*.csv"))
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        r = csv.reader(f)
        header = next(r)
        ci, li = header.index("Category"), header.index("Line Item")
        ai = next(i for i, h in enumerate(header) if h.endswith("_USD"))
        for row in r:
            if len(row) <= ai or not re.search(WORD % "saas", row[ci], re.I):
                continue
            if re.search(WORD % "subtotal|total", row[li], re.I) or not row[ai].strip().isdigit():
                continue
            rows.append((row[li].strip(), int(row[ai].strip())))
    dup = 0
    for j, (lb, xb) in enumerate(rows):
        if any(xa == xb and _similar(la, lb) for la, xa in rows[:j]):
            dup += xb
    total = sum(x for _, x in rows)
    return {"total": total, "dup": dup, "net": total - dup}


def _num(s):
    return int(s.replace(",", "")) if s else None


def ask_q1_figures(text):
    """As-listed figure from the answer block (bullet, or the bold headline when the bullet is replaced by a
    reconciliation note). Repeats: the sum of the amounts subtracted in '(total - a - b ...)'."""
    a = re.search(r"(?im)^- As listed: ([\d,]+) USD", text) or re.search(r"\*\*(?:PARTIAL\. )?As listed, ([\d,]+) USD", text)
    b = re.search(r"(?im)^- Without the suspected [^:\n]*: ([\d,]+) USD(?: \(([\d,]+)((?: - [\d,]+)+)\))?", text)
    dup = sum(_num(x) for x in re.findall(r"[\d,]+", b.group(3))) if b and b.group(3) else None
    return {"total": _num(a and a.group(1)), "net": _num(b and b.group(1)), "dup": dup}


def value_figures(text):
    """The shared-figures table of the worksheet: two-column rows whose label says as listed, suspected, without."""
    got = {"total": None, "dup": None, "net": None}
    for label, val in re.findall(r"(?m)^\| ([^|`]+?) \| ([\d,]+) \|$", text):
        low = label.lower()
        key = "net" if "without" in low else "total" if "as listed" in low else "dup" if "suspected" in low else None
        if key and got[key] is None:
            got[key] = _num(val)
    return got


def pnl_edit(d, insert_before_subtotal=(), append=(), subtotal=None):
    p = next(d.glob("pnl_*.csv"))
    out = []
    for line in read(p).splitlines():
        cells = line.split(",")
        if len(cells) > 2 and cells[0] == SAAS and "subtotal" in cells[1].lower():
            out += list(insert_before_subtotal)
            if subtotal is not None:
                cells[2] = str(subtotal)
                line = ",".join(cells)
        out.append(line)
    write(p, "\n".join(out + list(append)) + "\n")


def tickets_write(d, header, rows):
    t = next(d.glob("support_tickets_*.csv"))
    with open(t, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def tickets_read(d):
    with open(next(d.glob("support_tickets_*.csv")), encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    return rows[0], rows[1:]


def state_value(line):
    """The value after 'Current state:' up to the end of the bold span."""
    m = re.search(r"Current state:\s*(.*?)(\*\*|$)", line)
    return m.group(1) if m else ""


def state_confidence(out):
    m = re.search(r"Current state[^\n:]*: \**(HIGH|MEDIUM|LOW)\b", out)
    return m.group(1) if m else None


def text_writers(path):
    """Calls in a .py file that write text without an explicit newline argument (platform line endings)."""
    bad = []
    for node in ast.walk(ast.parse(read(path))):
        if not isinstance(node, ast.Call):
            continue
        kw = {k.arg for k in node.keywords}
        f = node.func
        # Path.write_text(data): one positional argument. A module helper write_text(path, text) takes two.
        if isinstance(f, ast.Attribute) and f.attr == "write_text" and "newline" not in kw \
                and (len(node.args) == 1 or (not node.args and "data" in kw)):
            bad.append(f"{node.lineno} .write_text() without newline=")
            continue
        is_open = (isinstance(f, ast.Name) and f.id == "open") or (isinstance(f, ast.Attribute) and f.attr == "open")
        if not is_open or "newline" in kw:
            continue
        pos = 1 if isinstance(f, ast.Name) or (isinstance(f.value, ast.Name) and f.value.id in ("io", "codecs")) else 0
        mode = next((k.value for k in node.keywords if k.arg == "mode"), node.args[pos] if len(node.args) > pos else None)
        m = mode.value if isinstance(mode, ast.Constant) and isinstance(mode.value, str) else ""
        if any(c in m for c in "wax") and "b" not in m:
            bad.append(f"{node.lineno} open(..., {m!r}) without newline=")
    return bad


SKIPPED = []


def skip(name, why):
    """A check that cannot run on this machine. Printed, counted separately, never counted as a pass."""
    SKIPPED.append(name)
    print(f"SKIP  {name}  [{why}]", flush=True)


def find_py38():
    """A Python 3.8 interpreter: this one if it is 3.8, else uv, else python3.8 on PATH, else the Windows launcher."""
    if sys.version_info[:2] == (3, 8):
        return sys.executable
    try:
        p = subprocess.run(["uv", "python", "find", "3.8"], capture_output=True, timeout=60)
        cand = p.stdout.decode("utf-8", "replace").strip().splitlines()
        if p.returncode == 0 and cand and Path(cand[-1]).is_file():
            return cand[-1]
    except (OSError, subprocess.SubprocessError):
        pass
    if shutil.which("python3.8"):
        return shutil.which("python3.8")
    if shutil.which("py"):
        try:
            p = subprocess.run(["py", "-3.8", "-c", "import sys; print(sys.executable)"], capture_output=True, timeout=60)
            cand = p.stdout.decode("utf-8", "replace").strip()
            if p.returncode == 0 and cand and Path(cand).is_file():
                return cand
        except (OSError, subprocess.SubprocessError):
            pass
    return None


def check_audit():
    committed = snapshot(ASK_OUT + VALUE_OUT + AUTO_OUT)
    tmp = Path(tempfile.mkdtemp(prefix="valis_check_"))

    def copy(name):
        d = tmp / name
        shutil.copytree(DATA, d)
        return d

    def q2(d):
        code, out, err = run(["ask/ask.py", "--q", "q2", "--data", d])
        return no_trace(code, out, err), state_line(out), out

    def note(d, heading, decision):
        write(d / "meeting_notes" / "leadership_sync_2026-06-17.md",
              "# Leadership Sync 2026-06-17\n\n**Date:** 2026-06-17\n**Attendees:** Dana Whitfield (CEO), Priya Raman (CFO)\n\n"
              f"{heading}\n\n- **DECISION:** {decision}\n")

    try:
        # --- 9a to 9c: Q2 decision records must be tied to Sales (audit finding 3)
        d = copy("eng_note")
        note(d, "## 1. Engineering staffing", "Engineering hiring freeze is lifted. Engineering hiring may resume.")
        ok, l, out = q2(d)
        v = state_value(l).lower()
        check("9a Q2 decision record lifting the Engineering freeze: Sales state not lifted, still frozen (audit 3)",
              ok and l and "lifted" not in v and "frozen" in v, l[:140] or "no current state line")

        d = copy("teamless_note")
        note(d, "## 1. Headcount", "The hiring freeze is lifted.")
        ok, l, out = q2(d)
        v, conf = state_value(l), state_confidence(out)
        unsure_ = bool(re.search(r"(?i)not certain|cannot (tell|say|determine)|unclear|ambiguous", v))
        check("9b Q2 decision record with no team named: not lifted, NOT CERTAIN, current-state confidence LOW (audit 3)",
              ok and "lifted" not in re.sub(r"(?i)not certain.*", "", v).lower() and unsure_ and conf == "LOW",
              f"state {l[:110]!r}; confidence {conf}")

        d = copy("sales_note")
        note(d, "## 1. Sales hiring", "Sales hiring freeze is lifted. Sales hiring may resume.")
        ok, l, out = q2(d)
        v = state_value(l)
        check("9c Q2 decision record lifting the Sales freeze: still reported lifted (guard against over-correction)",
              ok and "lifted" in v.lower() and "NOT CERTAIN" not in v and "leadership_sync_2026-06-17.md" in out, l[:140])

        # --- 9d to 9f: ask Q1 and the value worksheet share one definition (audit finding 4)
        def both(d):
            r1 = run(["ask/ask.py", "--q", "q1", "--data", d])
            r2 = run(["value/value.py", "--data", d])
            return no_trace(*r1) and no_trace(*r2), ask_q1_figures(r1[1]), value_figures(r2[1])

        d = copy("boundary")
        pnl_edit(d, append=["Software implementation services,Migration contractor,1000,One-off professional services"])
        ok, a, w = both(d)
        exp = saas_expected(d)
        check("9d row in 'Software implementation services' is not SaaS: ask Q1 and worksheet both 81,000 (audit 4)",
              ok and exp["total"] == 81000 and a["total"] == w["total"] == 81000,
              f"expected {n(exp['total'])}, ask {a['total']}, worksheet {w['total']}")

        d = copy("three")
        pnl_edit(d, insert_before_subtotal=[f"{SAAS},Amplitude Analytics Pro,7500,Product analytics"], subtotal=88500)
        ok, a, w = both(d)
        exp = saas_expected(d)
        want = {"total": 88500, "dup": 15000, "net": 73500}
        check("9e three Amplitude lookalikes: as listed 88,500, repeats 15,000, without 73,500, same in both tools (audit 4)",
              ok and exp == want and a == want and w == want, f"expected {want}, own recompute {exp}, ask {a}, worksheet {w}")

        cases = [
            ("exact duplicate label", dict(insert_before_subtotal=[f"{SAAS},Figma,3600,Design"])),
            ("abbreviation pair", dict(insert_before_subtotal=[f"{SAAS},Google Wrkspc,6000,Email"])),
            ("lookalike with a different amount", dict(insert_before_subtotal=[f"{SAAS},Zoom Webinars,900,Webinars"])),
            ("second category label containing SaaS", dict(append=["SaaS tools,Canva,1200,Design templates"])),
            ("lowercase saas in another category label", dict(append=["Marketing saas,Mailchimp,700,Email campaigns"])),
        ]
        bad, seen = [], []
        for i, (label, kw) in enumerate(cases):
            d = copy(f"perturb{i}")
            pnl_edit(d, **kw)
            ok, a, w = both(d)
            exp = saas_expected(d)
            seen.append(f"{label}: {n(exp['total'])}/{n(exp['net'])}")
            if not ok:
                bad.append(f"{label}: a command failed")
            elif not (a["total"] == w["total"] == exp["total"] and a["net"] == w["net"] == exp["net"]):
                bad.append(f"{label}: expected as listed {exp['total']} without {exp['net']}, ask {a['total']}/{a['net']}, worksheet {w['total']}/{w['net']}")
        check("9f SaaS perturbations: ask Q1 and worksheet print the same as-listed and without-repeat totals, equal to a raw recompute (audit 4)",
              not bad, short(bad, 5) or "; ".join(seen))

        # --- 9g, 9h: pilot acceptance must look at the target category and the pilot window (audit finding 2)
        header, rows = tickets_read(DATA)
        ci = header.index("Category")
        d = copy("irrelevant")
        tickets_write(d, header, [r for r in rows if r[ci] == "Login issue"][:2])
        code, out, err = run(["automation/run.py", "--data", d, "--out", tmp / "irrelevant_out", "--check", "--max-target-minutes", "0"])
        check("9g pilot acceptance on two non-target rows with --max-target-minutes 0: no ACCEPTANCE: PASS, exit non-zero (audit 2)",
              "ACCEPTANCE: PASS" not in out and code != 0 and "Traceback" not in err, f"exit {code}")

        pilot = json_rules().get("pilot") or {}
        oc, res, ret = pilot.get("outcome_column"), pilot.get("resolved_values"), pilot.get("returned_values")
        if not (oc and res and ret):
            check("9h pilot acceptance with an outcome column: ceiling below returned minutes FAILs, above PASSes", False,
                  "outcome column not implemented (automation/rules.json has no pilot.outcome_column with resolved and returned values)")
        else:
            idx = {h: i for i, h in enumerate(header)}
            prow = []
            returned_min = 0
            for k in range(15):  # 2026-07-01 to 2026-07-15: 15 days, one target ticket a day
                r = [""] * len(header)
                back = k % 5 == 0
                r[idx["Ticket_ID"]], r[idx["Date"]], r[ci] = f"TCK-7{k:03d}", f"2026-07-{k + 1:02d}", TARGET
                r[idx["Submitted_By"]], r[idx["Assigned_To"]], r[idx["Status"]] = f"creator_pilot{k}", "Ops Support", "Closed"
                r[idx["Handle_Minutes"]] = "10" if back else "0"
                returned_min += 10 if back else 0
                prow.append(r + [ret[0] if back else res[0]])
            for k in range(3):
                r = [""] * len(header)
                r[idx["Ticket_ID"]], r[idx["Date"]], r[ci] = f"TCK-7{100 + k}", f"2026-07-{2 * k + 2:02d}", "Login issue"
                r[idx["Submitted_By"]], r[idx["Assigned_To"]], r[idx["Status"]], r[idx["Handle_Minutes"]] = f"creator_other{k}", "Ops Support", "Closed", "20"
                prow.append(r + [""])
            d = copy("pilot")
            tickets_write(d, header + [oc], prow)
            lo = run(["automation/run.py", "--data", d, "--out", tmp / "pilot_lo", "--check", "--max-target-minutes", str(returned_min - 1)])
            hi = run(["automation/run.py", "--data", d, "--out", tmp / "pilot_hi", "--check", "--max-target-minutes", str(returned_min + 1)])
            ok = ("ACCEPTANCE: PASS" not in lo[1] and lo[0] != 0 and "ACCEPTANCE: PASS" in hi[1] and hi[0] == 0
                  and "Traceback" not in lo[2] + hi[2])
            fails = [l for l in hi[1].splitlines() if l.startswith("FAIL")]
            check("9h pilot export (15 days, outcome column, 3 returned tickets): ceiling below returned minutes FAILs, above PASSes",
                  ok, f"returned minutes {returned_min}; below: exit {lo[0]}; above: exit {hi[0]}" + (f"; above failed on: {short(fails, 3)}" if fails else ""))

        # --- 9j: optional columns are optional (audit finding 6)
        d = copy("optional")
        keep = [i for i, h in enumerate(header) if h not in ("Assigned_To", "Status")]
        tickets_write(d, [header[i] for i in keep], [[r[i] for i in keep] for r in rows])
        o = tmp / "optional_out"
        code, out, err = run(["automation/run.py", "--data", d, "--out", o])
        said = out + "".join(read(p) for p in sorted(o.glob("*.md"))) if o.is_dir() else out
        named = [c for c in ("Assigned_To", "Status")
                 if re.search(r"(?im)^[^\n]*%s[^\n]*\b(absent|missing|not present|not in|does not have|no column|without)\b" % c, said)
                 or re.search(r"(?im)^[^\n]*\b(absent|missing|not present|no column|without)\b[^\n]*%s" % c, said)]
        check("9j ticket file without Assigned_To and Status: runs (no CANNOT RUN) and names the absent columns (audit 6)",
              no_trace(code, out, err) and "CANNOT RUN" not in out + err and (o / "routed_queue.csv").exists() and len(named) == 2,
              f"exit {code}, named {named}" + (", CANNOT RUN printed" if "CANNOT RUN" in out + err else ""))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # --- 9i: LF only in every file the default commands write (audit finding 5)
    for _, cmd, _ in COMMANDS:
        run(cmd)
    inv = [ROOT / "pipeline" / "01_inventory.md", ROOT / "pipeline" / "index.json"]
    inv_before = snapshot(inv)
    code_imp = run(["pipeline/importer.py"])[0]
    inv_moved = [Path(k).name for k, v in snapshot(inv).items() if v != inv_before[k]]
    files = sorted(set((ROOT / "ask" / "out").glob("*.md")) | set(VALUE_OUT) | set(p for p in (ROOT / "automation" / "out").iterdir() if p.is_file())) + inv
    cr = b"\r"
    crlf = ["%s (%d CR)" % (p.relative_to(ROOT).as_posix(), p.read_bytes().count(cr)) for p in files if p.exists() and cr in p.read_bytes()]
    missing = [p.name for p in files if not p.exists()]
    check("9i every file written by the default commands (incl. routed_queue.csv and the importer outputs) has no carriage return",
          not crlf and not missing and code_imp == 0,
          short(crlf + [f"missing {m}" for m in missing], 6) or f"{len(files)} files LF only"
          + (f"; note: importer rewrote {inv_moved}, committed copies were stale" if inv_moved else ""))
    bad = []
    for folder in ("ask", "value", "automation", "pipeline"):
        for p in sorted((ROOT / folder).glob("*.py")):
            bad += [f"{folder}/{p.name}:{x}" for x in text_writers(p)]
    check("9i no shipped .py writes text with Path.write_text or open(..., 'w') without an explicit newline argument",
          not bad, short(bad, 6))

    # --- 9k: no claim that nobody timed the work (audit finding 6)
    bad = []
    for p in ASK_OUT + VALUE_OUT + AUTO_OUT + [ROOT / "answers" / "REPORT.md"]:
        if p.exists():
            for i, line in enumerate(read(p).splitlines(), 1):
                if re.search(r"(?i)nobody timed|never timed", line):
                    bad.append(f"{p.relative_to(ROOT).as_posix()}:{i}")
    check('9k no generated output and not answers/REPORT.md says "Nobody timed" or "never timed" (audit 6)', not bad, short(bad))

    # --- 9l: line endings pinned for checkouts (audit finding 5)
    ga = ROOT / ".gitattributes"
    rules = [l.split("#")[0].split() for l in read(ga).splitlines()] if ga.exists() else []
    check('9l .gitattributes exists and disables line-ending conversion ("* -text")', ["*", "-text"] in rules,
          "missing" if not ga.exists() else "")

    # --- 9m: a real run under Python 3.8 (audit finding 5: 3.8 and 3.9 were never run)
    py38 = find_py38()
    if not py38:
        skip("9m default commands and the citation check run under Python 3.8",
             "no Python 3.8 found (this interpreter, uv, python3.8, py -3.8). Optional: install Python 3.8 to run it")
    else:
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
        ref = snapshot(ASK_OUT + VALUE_OUT + AUTO_OUT)
        bad = []
        for cmd in (["ask/ask.py"], ["value/value.py"], ["automation/run.py", "--check"], ["tests/check.py", "--citations-only"]):
            pr = subprocess.run([py38] + cmd, cwd=str(ROOT), env=env, capture_output=True, timeout=300)
            if pr.returncode != 0 or b"Traceback" in pr.stderr:
                bad.append(f"{' '.join(cmd)} exit {pr.returncode}: {pr.stderr.decode('utf-8', 'replace').strip()[-120:]}")
        differ = [Path(k).name for k, v in snapshot(ASK_OUT + VALUE_OUT + AUTO_OUT).items() if v != ref[k]]
        bad += [f"{x} differs from the python3 output" for x in differ]
        ver = subprocess.run([py38, "--version"], capture_output=True).stdout.decode().strip()
        check("9m default commands and the citation check run under Python 3.8, exit 0, same bytes as python3", not bad,
              short(bad) or f"{ver} at {py38}")

    # leave committed outputs exactly as the default commands produce them
    for _, cmd, _ in COMMANDS:
        run(cmd)
    check("9z committed outputs are back to what the default commands produce after section 9",
          snapshot(ASK_OUT + VALUE_OUT + AUTO_OUT) == committed)


def check_audit2():
    """Section 10: regression checks for the second external audit (chat_logs/external_review_2026-11-11_round2/)."""
    committed = snapshot(ASK_OUT + VALUE_OUT + AUTO_OUT)
    tmp = Path(tempfile.mkdtemp(prefix="valis_check2_"))
    demo = ROOT / "automation" / "demo_pilot"
    try:
        # --- 10a: one decision line naming two teams with different states (round 2, Q2)
        for i, line in enumerate(("Engineering hiring freeze is lifted. Sales hiring remains frozen.",
                                  "Sales hiring remains frozen. Engineering hiring freeze is lifted.")):
            d = tmp / f"mixed_{i}"
            shutil.copytree(DATA, d)
            write(d / "meeting_notes" / "leadership_sync_2026-06-17.md",
                  "# Leadership Sync 2026-06-17\n\n**Date:** 2026-06-17\n\n## 1. Staffing decisions\n\n- **DECISION:** " + line + "\n")
            code, out, err = run(["ask/ask.py", "--q", "q2", "--data", d])
            l = state_line(out)
            v = state_value(l).lower()
            check(f"10a Q2 one decision line, Engineering lifted and Sales kept frozen (order {i + 1}): Sales still frozen (round 2)",
                  no_trace(code, out, err) and l and "lifted" not in v and "frozen" in v, l[:140] or "no current state line")

        def pilot(name, edit, ceiling):
            d = tmp / name
            shutil.copytree(demo, d)
            h, rows = tickets_read(d)
            edit(h, rows)
            tickets_write(d, h, rows)
            return run(["automation/run.py", "--data", d, "--out", tmp / (name + "_out"), "--check", "--max-target-minutes", str(ceiling)])

        def where(h, rows, outcome_prefix):
            o = h.index("Self_Serve_Outcome")
            return [r for r in rows if r[o].lower().startswith(outcome_prefix)]

        # --- 10b to 10d: incomplete pilot rows must never become a measured 0 (round 2, pilot acceptance)
        for tag, bad in (("blank", ""), ("not a number", "not recorded"), ("above the bound", "999"), ("negative", "-20")):
            def edit(h, rows, bad=bad):
                for r in where(h, rows, "returned"):
                    r[h.index("Handle_Minutes")] = bad
            code, out, err = pilot("bad_" + tag.replace(" ", "_"), edit, 0)
            check(f"10b pilot: minutes {tag} on tickets that came back to a person: ACCEPTANCE FAIL, not a measured 0 (round 2)",
                  code != 0 and "ACCEPTANCE: FAIL" in out and "Traceback" not in err, out.strip().splitlines()[-2][:140] if out.strip() else err[-140:])

        def heavy(h, rows):
            for r in where(h, rows, "resolved"):
                r[h.index("Handle_Minutes")] = "200"
        code, out, err = pilot("resolved_heavy", heavy, 105)
        check("10c pilot: 200 minutes logged on each ticket marked resolved count in the after figure, so a 105 ceiling FAILs (round 2)",
              code != 0 and "ACCEPTANCE: FAIL" in out and "1,900" in out, out.strip().splitlines()[-2][:140] if out.strip() else "")

        def bad_date(h, rows):
            for r in where(h, rows, "returned"):
                r[h.index("Date")] = "2026-13-01"
        code, out, err = pilot("bad_date", bad_date, 105)
        check("10d pilot: an invalid date on target rows FAILs acceptance (round 2)",
              code != 0 and "ACCEPTANCE: FAIL" in out, out.strip().splitlines()[-2][:140] if out.strip() else "")

        # --- 10e, 10f: the demo stays labelled without its README, and cannot pass mixed into real rows (round 2)
        lone = tmp / "lone_csv"
        lone.mkdir()
        shutil.copy(next(demo.glob("*.csv")), lone / "support_tickets_q2_2026.csv")
        code, out, err = run(["automation/run.py", "--data", lone, "--out", tmp / "lone_out", "--check", "--max-target-minutes", "105"])
        ba = (tmp / "lone_out" / "before_after.md").read_text(encoding="utf-8") if (tmp / "lone_out" / "before_after.md").is_file() else ""
        q = (tmp / "lone_out" / "routed_queue.csv").read_text(encoding="utf-8") if (tmp / "lone_out" / "routed_queue.csv").is_file() else ""
        check("10e demo CSV copied alone and renamed: the synthetic banner is still in stdout, before_after.md and the routed queue (round 2)",
              "SYNTHETIC TEST FIXTURE" in ba and "synthetic" in out.lower() and "SYNTHETIC TEST FIXTURE" in q, "")
        d = tmp / "mixed_rows"
        shutil.copytree(DATA, d)
        h_demo, demo_rows = tickets_read(demo)
        h_real, real_rows = tickets_read(d)
        rows = [[dict(zip(h_real, r)).get(c, "") for c in h_demo] for r in real_rows] + demo_rows
        tickets_write(d, h_demo, rows)
        code, out, err = run(["automation/run.py", "--data", d, "--out", tmp / "mixed_out", "--check", "--max-target-minutes", "999999"])
        check("10f demo rows mixed into the case tickets: synthetic warning shown and ACCEPTANCE FAIL (round 2)",
              code != 0 and "ACCEPTANCE: FAIL" in out and "synthetic" in out.lower(), out.strip().splitlines()[-2][:140] if out.strip() else "")

        # --- 10g: program output with CRLF line ends is parsed like LF (round 2: 9d to 9f failed on Windows only)
        code, out, err = run(["-c", "import sys; sys.stdout.buffer.write(b'| a |\\r\\n| b |\\r\\n')"])
        check("10g the test runner normalises CRLF in program output, as Windows produces", "\r" not in out and out.count("\n") == 2, repr(out))

        # --- 10h: the report separates what was charged from what was paid (round 2, finding 6)
        rep = read(ROOT / "answers" / "REPORT.md")
        check("10h REPORT.md: payment closes with the ledger and the bank or card statement, not with invoices (round 2)",
              "bank or card statement" in rep and "invoices or the AP ledger" not in rep and "Billed or paid twice" not in rep, "")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        for _, cmd, _ in COMMANDS:
            run(cmd)
    check("10z committed outputs are back to what the default commands produce after section 10",
          snapshot(ASK_OUT + VALUE_OUT + AUTO_OUT) == committed)


def json_rules():
    import json
    return json.loads(read(ROOT / "automation" / "rules.json"))


# ---------- main ----------

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if "--citations-only" in sys.argv:      # used by check 9m to run the resolver under another interpreter
        check_citations()
        return 0 if all(RESULTS) else 1
    check_checksums()

    all_out = ASK_OUT + VALUE_OUT + AUTO_OUT
    before = snapshot(all_out)
    ok_all = True
    for name, cmd, outs in COMMANDS:
        for p in outs:                      # delete first, so "regenerates" is a real test
            if p.exists():
                p.unlink()
        code, out, err = run(cmd)
        first = snapshot(outs)
        code2, _, _ = run(cmd)
        missing = [p.name for p in outs if not p.exists()]
        same = first == snapshot(outs)
        ok = code == 0 and code2 == 0 and not missing and same and "Traceback" not in err
        ok_all &= check(f"2 {name}: `{' '.join(cmd)}` exits 0, rewrites its outputs, same bytes on a second run", ok,
                        f"exit {code}/{code2}" + (f", missing {missing}" if missing else "") + ("" if same else ", output differs between runs"))
    changed = [Path(k).name for k, v in before.items() if v is not None and v != snapshot([k])[k]]
    check("2 regenerated outputs equal the files that were on disk before this run", not changed, short(changed))
    if not ok_all:
        print("FAIL  later checks skipped: a deliverable command did not run cleanly")
        return 1

    units = check_citations()
    P, T = check_arithmetic(units)
    check_consistency(P)
    check_fresh(P, T)
    check_regressions(P, T)
    check_hygiene()
    check_audit()
    check_audit2()
    check("1 data/ still matches data/CHECKSUMS.txt after all runs",
          all(hashlib.sha256((DATA / l.split(None, 1)[1].strip()).read_bytes()).hexdigest() == l.split()[0]
              for l in read(DATA / "CHECKSUMS.txt").splitlines() if l.strip()))
    passed = sum(RESULTS)
    extra = f", {len(SKIPPED)} skipped (see SKIP lines)" if SKIPPED else ""
    print(f"\n{passed} of {len(RESULTS)} checks passed, {len(RESULTS) - passed} failed{extra}")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
