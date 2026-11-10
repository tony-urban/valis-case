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
  7  hygiene: em dashes, imports, Python 3.9 compatibility, hardcoded names and amounts
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
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


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
    tmp = Path(tempfile.mkdtemp(prefix="valis_check_"))
    try:
        d = tmp / "data"
        shutil.copytree(DATA, d)
        perturb(d)
        units = build_units(d)
        P, T = pnl_facts(d), ticket_facts(d)
        assert P["total"] == P0["total"] + BUMP[1] + NEW_SAAS[1] and T["count"] == T0["count"] + 2

        # ask: no documented way to redirect its files, so capture stdout and restore afterwards
        code, out, err = run(["ask/ask.py", "--data", d])
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
    check("6m ask does not overwrite its committed outputs when run with --data", not ask_clobbered,
          "ask/out/ was overwritten by the perturbed run (no --out option). Restored by rerunning the default command" if ask_clobbered else "")
    check("6n committed outputs are back to what the default commands produce", restored)


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

    # the stated target is macOS, whose stock python3 is 3.9: flag syntax or calls that need 3.10 or later
    bad = []
    for p in sorted(ROOT.rglob("*.py")):
        if set(p.relative_to(ROOT).parts) & {".git", "__pycache__"}:
            continue
        try:
            tree = ast.parse(read(p), feature_version=(3, 9))
        except SyntaxError as e:
            bad.append(f"{p.name}: syntax newer than Python 3.9 (line {e.lineno})")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "write_text" \
                    and "newline" in {k.arg for k in node.keywords}:
                bad.append(f"{p.relative_to(ROOT).as_posix()}:{node.lineno} Path.write_text(newline=) needs Python 3.10 or later")
    check("7d shipped code avoids calls newer than Python 3.9 (stock macOS python3)", not bad, short(bad))

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


# ---------- main ----------

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
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
    check_hygiene()
    check("1 data/ still matches data/CHECKSUMS.txt after all runs",
          all(hashlib.sha256((DATA / l.split(None, 1)[1].strip()).read_bytes()).hexdigest() == l.split()[0]
              for l in read(DATA / "CHECKSUMS.txt").splitlines() if l.strip()))
    passed = sum(RESULTS)
    print(f"\n{passed} of {len(RESULTS)} checks passed, {len(RESULTS) - passed} failed")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
