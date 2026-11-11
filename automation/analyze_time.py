#!/usr/bin/env python3
"""Q3 evidence: where is the most time wasted, and what to automate first.

Reads the ticket log and the Slack and meeting-note text from the data folder,
builds one row per candidate workflow, tags each MEASURED or ASSERTED, and
writes out/time_waste.md. Nothing about the data is typed into this file:
file names, columns, categories, keywords and assumptions are in rules.json.

Usage: python3 automation/analyze_time.py [--data DIR] [--category NAME] [--out DIR]
(run.py calls this first, then routes the queue.) Standard library only.
"""
import sys
sys.dont_write_bytecode = True  # keep the repo free of __pycache__
import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from datetime import date  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import importer  # noqa: E402  shared parser: one definition of a citable line

NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}


class CannotRun(Exception):
    """The input does not have the expected shape. Message says what is needed."""


# ---------- loading ----------

def load_rules(category=None):
    rules = json.loads((HERE / "rules.json").read_text(encoding="utf-8"))
    if category:
        if category not in rules["known_categories"]:
            raise CannotRun(f"--category {category!r} is not in rules.json known_categories: "
                            + ", ".join(rules["known_categories"]))
        rules["target_overridden"] = category != rules["target_category"]
        rules["target_category"] = category
    return rules


def load_tickets(data, rules):
    """Every data row of the ticket file becomes one ticket. Nothing is dropped.
    'problems' send a ticket to the exception queue. 'flags' are only reported."""
    cfg, col, pilot = rules["tickets"], rules["tickets"]["columns"], rules["pilot"]
    optional = [col[k] for k in cfg.get("optional_columns", [])]
    required = [c for c in col.values() if c not in optional]
    need = (f"need a file matching {cfg['file_pattern']} with a header row and columns: {', '.join(required)}"
            + (f" (optional: {', '.join(optional)})" if optional else ""))
    found = sorted(p for p in data.glob(cfg["file_pattern"]) if p.is_file()) if data.is_dir() else []
    if not found:
        raise CannotRun(f"no file matching {cfg['file_pattern']} in {data}; {need}")
    path = found[-1]  # several matches: the last by name is used, the others are reported
    cfg["file"], cfg["others"] = path.name, [p.name for p in found[:-1]]
    try:
        lines = importer.read_lines(path)
    except (OSError, UnicodeDecodeError) as e:
        raise CannotRun(f"cannot read {path} ({type(e).__name__}); {need}, saved as UTF-8")
    if not lines:
        raise CannotRun(f"{path} is empty; {need}")
    header = importer.parse_row(lines[0])
    missing = [c for c in required if c not in header]
    if missing:
        raise CannotRun(f"{cfg['file']} has no column {', '.join(missing)}; {need}")
    cfg["absent"] = [c for c in optional if c not in header]  # run anyway, skip the flags that need them
    cfg["has_outcome"] = pilot["outcome_column"] in header    # only a pilot export has this column
    resolved, returned = ({v.lower() for v in pilot[k]} for k in ("resolved_values", "returned_values"))

    units, flags = [], []
    importer.import_csv(path, cfg["file"], units, flags)
    wrong_width = {n for _, n, msg in flags if "fields, header has" in msg}
    known, seen, tickets = rules["known_categories"], set(), []
    cap = rules["assumptions"]["max_plausible_minutes"]
    for u in units:
        if u["kind"] != "row":
            continue
        f = u["fields"]
        t = {"line": u["line"], "id": f[col["id"]], "date": f[col["date"]],
             "category": f[col["category"]], "raw_minutes": f[col["minutes"]],
             "minutes": None, "week": None, "problems": [], "flags": [], "outcome": None}
        if cfg["has_outcome"] and t["category"] == rules["target_category"]:  # outcome is read for target tickets only
            v = f.get(pilot["outcome_column"], "").lower()
            t["outcome"] = "resolved" if v in resolved else "returned" if v in returned else "unknown"
        if u["line"] in wrong_width:
            t["problems"].append("row has a different number of fields than the header")
        repeat = bool(t["id"]) and t["id"] in seen
        if not t["id"]:
            t["problems"].append(f"blank {col['id']}")
        elif repeat:
            t["problems"].append(f"repeated {col['id']}: first occurrence counts, minutes on this row ({t['raw_minutes']!r}) not counted")
        seen.add(t["id"])
        if not t["category"]:
            t["problems"].append(f"blank {col['category']}")
        elif t["category"] not in known:
            t["problems"].append(f"unknown {col['category']}: {t['category']!r}")
        if importer.ISO_DATE.match(t["date"]) and importer.valid_date(t["date"]):
            iso = date.fromisoformat(t["date"]).isocalendar()
            t["week"] = f"{iso[0]}-W{iso[1]:02d}"
        else:
            t["problems"].append(f"blank or invalid {col['date']}: {t['date']!r}")
        is_num = bool(importer.NUM.match(t["raw_minutes"]))
        if t["outcome"] == "resolved" and (not t["raw_minutes"] or (is_num and float(t["raw_minutes"]) == 0)):
            if not repeat:  # pilot export: resolved by self-serve with no handling, so 0 or blank minutes is correct
                t["minutes"] = 0.0
        elif is_num and float(t["raw_minutes"]) > cap:
            t["problems"].append(f"implausible {col['minutes']}: {t['raw_minutes']} is above the upper bound of {cap} "
                                 "(ASSUMPTION in rules.json), not counted")
        elif is_num and float(t["raw_minutes"]) > 0:
            if not repeat:
                t["minutes"] = float(t["raw_minutes"])
        elif not t["raw_minutes"]:
            t["problems"].append(f"blank {col['minutes']}")
        else:
            t["problems"].append(f"{col['minutes']} is not a positive number: {t['raw_minutes']!r}")
        if col["assignee"] in f and not f[col["assignee"]]:
            t["flags"].append(f"no {col['assignee']}")
        if col["status"] in f and f[col["status"]] != cfg["closed_status"]:
            t["flags"].append(f"{col['status']} is {f[col['status']]!r}")
        tickets.append(t)
    if not tickets:
        raise CannotRun(f"{cfg['file']} has a header but no data rows; {need}")
    return tickets


def fixture_banner(data, rules):
    """Banner for a made-up demo input, recognised by the first line of a marker file named in rules.json."""
    m = rules["pilot"].get("fixture_marker")
    p = data / m["file"] if m else None
    try:
        first = p.read_text(encoding="utf-8").splitlines()[0] if p and p.is_file() else ""
    except (OSError, UnicodeDecodeError, IndexError):
        first = ""
    if not m or m["first_line_contains"] not in first:
        return None
    return (f"**SYNTHETIC TEST FIXTURE. The input folder says so in line 1 of `{m['file']}`: it was invented for a demo. "
            f"{m.get('banner', 'The figures below demonstrate the method, not a result.')}**")


def load_text(data, rules=None):
    """Slack messages and note lines from every .md file, as importer units.
    A fixture marker file (rules.json pilot.fixture_marker) is not evidence and is skipped."""
    units = []
    m = rules["pilot"].get("fixture_marker") if rules else None
    skip = (data / m["file"]).resolve() if m and fixture_banner(data, rules) else None
    for p in sorted(data.rglob("*.md")):
        if skip and p.resolve() == skip:
            continue
        try:
            importer.import_md(p, p.relative_to(data).as_posix(), units, [])
        except (OSError, UnicodeDecodeError):
            print(f"NOTE: could not read {p.name}, skipped as evidence")
    return [u for u in units if u["kind"] in ("message", "line")]


# ---------- small helpers ----------

def write_text(path, text):
    """Same bytes on every OS: UTF-8 with LF line endings (Path.write_text would give CRLF on Windows)."""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def absent_notes(rules):
    """One sentence per optional column that this ticket file does not have."""
    cfg, col = rules["tickets"], rules["tickets"]["columns"]
    what = {col["assignee"]: "tickets with no assignee", col["status"]: f"tickets whose status is not {cfg['closed_status']!r}"}
    return [f"Column `{c}` is absent from this ticket file. It is optional, so the run went ahead. Skipped: the flag for {what.get(c, 'that column')}."
            for c in cfg.get("absent", [])]


def num(x):
    """1234.0 -> '1,234', 12.5 -> '12.5'."""
    if x is None:
        return "n/a"
    s = f"{x:,.1f}"
    return s[:-2] if s.endswith(".0") else s


def hrs(minutes):
    return f"{minutes / 60:.1f}"


def cite(u):
    """Citation for a text unit, in the format of pipeline/02_task.md section 5."""
    if u["kind"] == "message":
        return f"`{u['file']}:L{u['line']} [{u['channel']} | {u['author']} | {u['when']}]`"
    return f"`{u['file']}:L{u['line']}`"


def cite_row(t, rules):
    return f"`{rules['tickets']['file']}:L{t['line']}` ({rules['tickets']['columns']['id']}: {t['id']})"


def quote(u, limit=150):
    text = u["text"] if len(u["text"]) <= limit else u["text"][:limit].rsplit(" ", 1)[0] + " ..."
    return f'"{text}"'


def find(text_units, spec):
    if not spec or "find" not in spec:
        return []
    files, pat = re.compile(spec["files"]), re.compile(spec["find"], re.I)
    return [u for u in text_units if files.search(u["file"]) and pat.search(u["text"])]


def quantities(found, spec):
    """Numbers stated in the matched text, for example '3' from '~3 days'. One per (line, value)."""
    out = []
    for u in found:
        for v in sorted({float(NUMBER_WORDS.get(m.lower(), m)) for m in re.findall(spec.get("quantity", "$^"), u["text"], re.I)}):
            out.append((v, u))
    return out


def stats(tickets):
    mins = [t["minutes"] for t in tickets if t["minutes"] is not None]
    return {"n": len(tickets), "n_timed": len(mins), "minutes": sum(mins),
            "min": min(mins) if mins else None, "max": max(mins) if mins else None,
            "mean": sum(mins) / len(mins) if mins else None}


def peak_week(tickets):
    weeks = {}
    for t in tickets:
        if t["week"]:
            weeks[t["week"]] = weeks.get(t["week"], 0) + 1
    return max(weeks.items(), key=lambda kv: kv[1]) if weeks else (None, 0)


# ---------- analysis ----------

def analyse(tickets, text_units, rules):
    """One row per candidate workflow, all in hours per quarter."""
    a = rules["assumptions"]
    by_cat = {}
    for t in tickets:
        by_cat.setdefault(t["category"] or "(blank)", []).append(t)
    specs = {c.get("category"): c for c in rules["candidates"] if c.get("category")}
    rows = []
    for cat, ts in by_cat.items():  # every category in the file gets a row, configured or not
        spec = specs.get(cat, {"id": cat, "area": "Support", "workflow": f"{cat} tickets"})
        rows.append({"spec": spec, "tag": "MEASURED", "tickets": ts, "stats": stats(ts),
                     "hours": stats(ts)["minutes"] / 60, "category": cat})
    for spec in rules["candidates"]:
        if spec.get("category"):
            if spec["category"] not in by_cat:  # configured but absent from this file
                rows.append({"spec": spec, "tag": "MEASURED", "tickets": [], "stats": stats([]),
                             "hours": 0.0, "category": spec["category"]})
            continue
        if spec.get("all_tickets"):
            rows.append({"spec": spec, "tag": "MEASURED", "tickets": tickets, "stats": stats(tickets),
                         "hours": stats(tickets)["minutes"] / 60, "umbrella": True})
        else:
            rows.append({"spec": spec, "tag": "ASSERTED", "hours": None})
    for r in rows:
        r["found"] = find(text_units, r["spec"])
        r["claims"] = quantities(r["found"], r["spec"])
        unit = r["spec"].get("quantity_unit")
        vals = sorted({v for v, _ in r["claims"]})
        r["claim_values"] = vals
        r["claim_lines"] = list({(u["file"], u["line"]): u for _, u in r["claims"]}.values())
        hedge = re.compile(r["spec"].get("approx", "$^"), re.I)
        r["approx_n"] = sum(1 for u in r["claim_lines"] if hedge.search(u["text"]))
        r["about"] = "about " if r["approx_n"] else ""  # the sources hedge the figure, so we do too
        if vals and unit == "days_per_month":
            r["claim_hours"] = [v * a["months_in_period"] * a["hours_per_work_day"] for v in (vals[0], vals[-1])]
            if r["tag"] == "ASSERTED":
                r["hours"] = r["claim_hours"][-1]
        elif vals and unit == "hours_per_week":
            r["claim_hours"] = [v * a["weeks_in_period"] for v in (vals[0], vals[-1])]
    rows.sort(key=lambda r: (r["hours"] is None, -(r["hours"] or 0)))
    return rows


def row_by(rows, **kv):
    key, val = next(iter(kv.items()))
    return next((r for r in rows if r.get(key) == val or r["spec"].get(key) == val), None)


def provenance(row):
    """Who said it: distinct source lines carrying the number, split by kind, plus the note from rules.json."""
    units = row["claim_lines"]
    msgs = [u for u in units if u["kind"] == "message"]
    return (f"{len(units)} source lines (cited below), {row['approx_n']} of which give the figure as approximate: "
            f"{len(msgs)} Slack messages, distinct authors: "
            f"{len({u['author'] for u in msgs})}. Meeting-note lines: {len(units) - len(msgs)}. "
            f"{row['spec'].get('provenance', 'Count the people behind them before trusting the number.')}")


def span(vals, unit):
    return f"{num(vals[0])} {unit}" if vals[0] == vals[-1] else f"{num(vals[0])} to {num(vals[-1])} {unit}"


# ---------- report ----------

def render(tickets, text_units, rules, data_label):
    a, col, tfile = rules["assumptions"], rules["tickets"]["columns"], rules["tickets"]["file"]
    target = rules["target_category"]
    rows = analyse(tickets, text_units, rules)
    cats = [r for r in rows if "category" in r]
    allq = stats(tickets)
    pick = row_by(rows, category=target) or {"stats": stats([]), "tickets": [], "found": [], "claims": [], "spec": {}}
    ps = pick["stats"]
    dates = sorted(t["date"] for t in tickets if t["week"])
    period = f"{dates[0]} to {dates[-1]}" if dates else "no valid dates"
    rank_n = 1 + sum(1 for r in cats if r["stats"]["n"] > ps["n"])
    rank_m = 1 + sum(1 for r in cats if r["stats"]["minutes"] > ps["minutes"])
    lead_m = max(cats, key=lambda r: r["stats"]["minutes"])
    lead_n = max(cats, key=lambda r: r["stats"]["n"])
    asserted = [r for r in rows if r["tag"] == "ASSERTED" and r["hours"] is not None]
    top_claim = asserted[0] if asserted else None
    umbrella = next((r for r in rows if r.get("umbrella")), None)
    # Weeks in the period. The case data is a full quarter: the configured weeks (ASSUMPTION).
    # A pilot export covers its own dates: weeks come from its first and last date.
    if rules["tickets"].get("has_outcome") and dates:
        days = (date.fromisoformat(dates[-1]) - date.fromisoformat(dates[0])).days + 1
        n_weeks, weeks_basis = days / 7, "from the export's first and last date"
    else:
        n_weeks, weeks_basis = a["weeks_in_period"], "ASSUMPTION"
    weeks_txt = num(round(n_weeks, 1))
    weekly = allq["minutes"] / 60 / n_weeks
    L = []
    w = L.append

    w("# Q3. Where is the most time wasted, and what to automate first")
    w("")
    if rules.get("fixture_banner"):
        w(rules["fixture_banner"])
        w("")
    w(f"Generated by `python3 automation/run.py` from `{data_label}`. Every figure below is computed at run time.")
    if rules["tickets"].get("others"):
        w(f"Ticket file used: {tfile}. Also matching the pattern and not read: {', '.join(rules['tickets']['others'])}.")
    w("MEASURED: summed from logged rows. ASSERTED: someone said it, no log behind it. ASSUMPTION: our own input, not in the bundle.")
    w("")
    w("## Answer")
    w("")
    if top_claim:
        s = top_claim["spec"]
        w(f"1. **Largest claimed time sink: {s['area']}, {s['workflow']}.** ASSERTED at "
          f"{top_claim['about']}{span(top_claim['claim_values'], 'days a month')} in {provenance(top_claim)} "
          f"Converted: {span(top_claim['claim_values'], 'days')} x {a['months_in_period']} months x "
          f"{a['hours_per_work_day']} hours a day (ASSUMPTION) = {top_claim['about']}{span(top_claim['claim_hours'], 'hours a quarter')}. "
          "There is no time log and its input files are not in the bundle, so it cannot be measured or run here.")
    else:
        w("1. **Largest claimed time sink:** no claim with a stated quantity was found in the text sources.")
    w(f"2. **Largest measured time sink: the creator support queue.** MEASURED {num(allq['minutes'])} minutes "
      f"({hrs(allq['minutes'])} hours) logged on {allq['n_timed']} tickets, {period}. That is {weekly:.1f} hours a week "
      f"over {weeks_txt} weeks ({weeks_basis}).")
    w(f"3. **Automate first: {target} tickets.** MEASURED {num(ps['minutes'])} minutes ({hrs(ps['minutes'])} hours) "
      f"on {ps['n_timed']} tickets. Rank {rank_n} of {len(cats)} categories by ticket count, rank {rank_m} of {len(cats)} "
      "by logged minutes. The router is built and running: see `before_after.md` in this folder. What it delivers today is "
      f"routing, not saved time: minutes saved by the run alone are 0, the measured ceiling is {num(ps['minutes'])} minutes, "
      "and the bundle does not support a measured after figure in minutes.")
    if top_claim and ps["minutes"]:
        w(f"4. **Plainly:** the largest claim, {top_claim['spec']['workflow']} ({top_claim['about']}{num(top_claim['hours'])} hours a quarter, ASSERTED), is "
          f"{top_claim['about']}{top_claim['hours'] / (ps['minutes'] / 60):.1f} times the measured time of the workflow we built "
          f"({hrs(ps['minutes'])} hours a quarter). It was not built because the number is a self-report and its "
          "inputs are absent: building it would mean inventing data. What is needed is listed below.")
    w("")
    w("## All candidates, ranked by hours a quarter")
    w("")
    w("| Rank | Area | Workflow | Tag | Hours a quarter | Basis | Runnable from the bundle? |")
    w("|---|---|---|---|---|---|---|")
    k = 0
    for r in rows:
        s = r["spec"]
        if r["hours"] is None:
            rank, hours = "not rankable", "no figure in the bundle"
        else:
            k += 1
            rank, hours = str(k), r["about"] + num(round(r["hours"], 1))
        if r["tag"] == "MEASURED":
            st = r["stats"]
            basis = f"{num(st['minutes'])} logged minutes on {st['n']} tickets"
            if r.get("umbrella"):
                basis += " (sum of the category rows, not additive to them)"
            runnable = "Yes: ticket log present"
        else:
            basis = "no quantity stated" if r["hours"] is None else (
                f"claim of {r['about']}{span(r['claim_values'], 'days a month')}, 1 day = {a['hours_per_work_day']} hours (ASSUMPTION)")
            runnable = "No: no input file in the bundle"
        mark = " **(pick)**" if r.get("category") == target else ""
        w(f"| {rank} | {s['area']} | {s['workflow']}{mark} | {r['tag']} | {hours} | {basis} | {runnable} |")
    w("")
    w("## Evidence per candidate")
    for r in rows:
        s = r["spec"]
        w("")
        w(f"**{s['workflow']}** ({r['tag']})")
        if r["tag"] == "MEASURED" and r["stats"]["n"]:
            st = r["stats"]
            w(f"- Log: {st['n']} tickets, {num(st['minutes'])} minutes, {num(st['min'])} to {num(st['max'])} per ticket, "
              f"mean {num(round(st['mean'], 1)) if st['mean'] else 'n/a'}. Every row is cited in the last section.")
        for u in r["found"]:
            w(f"- {cite(u)} {quote(u)}")
        if not r["found"]:
            w("- No statement about this workflow found in Slack or the meeting notes.")
        if s.get("why_not") and r.get("category") != target:
            w(f"- Why not first: {s['why_not']}")
    w("")
    w("## Claims checked against the log")
    w("")
    pl = find(text_units, rules["context"]["period_line"])
    rng_dates = re.findall(r"\d{4}-\d{2}-\d{2}", pl[0]["text"]) if pl else []
    w(f"- **Period.** The ticket log covers {period}. The claims come from Slack: {cite(pl[0]) + ' ' + quote(pl[0]) if pl else 'range line not found'}. "
      + ("The log ends before the Slack range starts, so no claim can be checked against tickets from its own weeks. "
         if dates and rng_dates and dates[-1] < min(rng_dates) else "Compare the two ranges before reading the rows below. ")
      + "Each comparison below is claim period versus log period, not like for like.")
    if umbrella and umbrella["claims"]:
        v, u = umbrella["claims"][0]
        w(f"- **Hours a week.** Claimed {num(v)} hours a week: {cite(u)}. Measured {weekly:.1f} hours a week "
          f"({num(allq['minutes'])} minutes / 60 / {weeks_txt} weeks, {weeks_basis}), which is {weekly / v:.0%} of the claim. "
          "The claim is challenged in its own thread (citations above).")
    pw_t, pw_all = peak_week(pick["tickets"]), peak_week(tickets)
    for v, u in pick["claims"]:
        w(f"- **Tickets a week.** Claimed {num(v)} in one week: {cite(u)}. Busiest ISO week in the log: "
          f"{pw_t[1]} {target} tickets ({pw_t[0]}), {pw_all[1]} tickets of all categories ({pw_all[0]}).")
    for u in find(text_units, {"files": pick["spec"].get("files", "$^"), "find": pick["spec"].get("share_claim", "$^")}):
        w(f"- **Share of tickets.** Claim: {cite(u)} {quote(u)}. Log: {ps['n']} of {allq['n']} tickets = "
          f"{ps['n'] / allq['n']:.1%} by count, {num(ps['minutes'])} of {num(allq['minutes'])} minutes = "
          f"{(ps['minutes'] / allq['minutes'] if allq['minutes'] else 0):.1%} by time.")
    for u in find(text_units, {"files": pick["spec"].get("files", "$^"), "find": pick["spec"].get("per_ticket_claim", "$^")}):
        w(f"- **Minutes per ticket.** Claim: {cite(u)} {quote(u)}. Log: {num(ps['min'])} to {num(ps['max'])} minutes "
          f"per ticket, mean {num(round(ps['mean'], 1)) if ps['mean'] else 'n/a'}.")
    w(f"- **Count versus minutes.** By ticket count the leader is {lead_n['category']} ({lead_n['stats']['n']} tickets). "
      f"By logged minutes the leader is {lead_m['category']} ({num(lead_m['stats']['minutes'])} minutes). "
      "The question asks about time, so the ranking above uses minutes. Count is shown only as volume.")
    w("")
    w(f"## Why {target} first")
    w("")
    w("- It has both a measured before figure and its input file in the bundle. Only the ticket categories do (table above).")
    w(f"- Volume: rank {rank_n} of {len(cats)} by tickets ({ps['n']}). Time: rank {rank_m} of {len(cats)} by minutes ({num(ps['minutes'])}).")
    if ps["n_timed"]:
        w(f"- Handle time per ticket sits in a {num(ps['max'] - ps['min'])} minute band ({num(ps['min'])} to {num(ps['max'])}); "
          f"the leader by minutes, {lead_m['category']}, spans {num(lead_m['stats']['max'] - lead_m['stats']['min'])} "
          f"({num(lead_m['stats']['min'])} to {num(lead_m['stats']['max'])}).")
    if rules.get("target_overridden"):
        w("- Target category was overridden on the command line. The qualitative reasons in rules.json are written for the default target and are not repeated here.")
    else:
        for reason in rules["pick_reasons"]:
            w(f"- {reason['text']} " + ", ".join(cite(u) for u in find(text_units, reason)))
    if lead_m.get("category") != target:
        w(f"- Stated plainly: {lead_m['category']} has more logged minutes ({num(lead_m['stats']['minutes'])} versus "
          f"{num(ps['minutes'])}). {lead_m['spec'].get('why_not', '')}")
    w("")
    if top_claim:
        s = top_claim["spec"]
        w("## Why the largest claim was not built, and what it needs")
        w("")
        w(f"- {s['workflow']}: {s.get('why_not', '')}")
        w("- To build and measure it we need these files. Column lists are our proposal: no such file is in the bundle to confirm them.")
        for item in s.get("needed", []):
            w(f"  - {item}")
        w("")
    w("## Not verified")
    w("")
    fives = sum(1 for t in tickets if t["minutes"] is not None and t["minutes"] % 5 == 0)
    w(f"- What `{col['minutes']}` means. The bundle has no definition (hands-on time or elapsed, timed or estimated). "
      f"{fives} of {allq['n_timed']} values are multiples of five, which suggests estimates. Needed: the ticketing tool's field definition.")
    w("- Whether all support work is ticketed. Untracked work (chat, email, follow-ups) would not appear in the log. Needed: a one week time sample from the support team.")
    w("- Ticket volume in the weeks the claims were made. The bundle has no ticket rows for those weeks. Needed: the same export for the following quarter.")
    for r in rows:
        if r["tag"] == "ASSERTED":
            needed = "the files listed in the section above" if r is top_claim else "; ".join(r["spec"].get("needed", ["a time log"]))
            w(f"- {r['spec']['workflow']}: {'self-reported, no log' if r['hours'] is not None else 'no effort figure at all'}. Needed: {needed}.")
    flagged = [t for t in tickets if t["flags"]]
    if flagged:
        w(f"- {len(flagged)} tickets carry a flag (no assignee, or not closed) and are counted because minutes are logged on them: "
          + ", ".join(f"{cite_row(t, rules)} {'; '.join(t['flags'])}" for t in flagged) + ".")
    for note in absent_notes(rules):
        w(f"- {note}")
    bad = [t for t in tickets if t["problems"]]
    if bad:
        w(f"- {len(bad)} rows could not be fully read and went to the exception queue (listed in `before_after.md`). "
          "Rows with unreadable or implausible minutes, and repeats of a ticket ID, add nothing to the minute totals above. Other exception rows with readable minutes are still counted.")
    w("")
    w("## Rows behind each measured total")
    w("")
    w("Re-add any total by hand from these. Format: citation = minutes.")
    for r in sorted(cats, key=lambda r: -r["stats"]["minutes"]):
        w("")
        w(f"**{r['category']}**: {num(r['stats']['minutes'])} minutes, {r['stats']['n']} tickets")
        w("")
        w(", ".join(f"`{tfile}:L{t['line']}` = {num(t['minutes']) if t['minutes'] is not None else 'not counted'}"
                    for t in sorted(r["tickets"], key=lambda t: t["line"])))
    w("")
    w(f"**All categories**: {num(allq['minutes'])} minutes, {allq['n']} tickets (sum of the category totals above).")
    return "\n".join(L) + "\n"


def label(path):
    """Path as shown in reports: relative to the repo when inside it."""
    try:
        return path.resolve().relative_to(ROOT).as_posix() + "/"
    except ValueError:
        return path.as_posix()


def write_report(data, rules, out):
    tickets = load_tickets(data, rules)
    rules["fixture_banner"] = fixture_banner(data, rules)
    text_units = load_text(data, rules)
    out.mkdir(parents=True, exist_ok=True)
    write_text(out / "time_waste.md", render(tickets, text_units, rules, label(data)))
    return tickets, text_units


def parse_args(doc):
    ap = argparse.ArgumentParser(description=doc)
    ap.add_argument("--data", default=str(ROOT / "data"), help="folder holding the bundle files (default: data/)")
    ap.add_argument("--category", help="target category to automate (default: target_category in rules.json)")
    ap.add_argument("--out", default=str(HERE / "out"), help="output folder (default: automation/out/)")
    return ap


def safe_out(args):
    """Committed outputs are only ever written from the committed data. With a
    different --data and no explicit --out, write to a scratch folder instead."""
    data, out = Path(args.data), Path(args.out)
    if data.resolve() != (ROOT / "data").resolve() and out.resolve() == (HERE / "out").resolve():
        import tempfile
        out = Path(tempfile.mkdtemp(prefix="automation_out_"))
        print(f"NOTE: --data is not the committed data and no --out was given. Writing to {out}, not automation/out/.")
    return out


if __name__ == "__main__":
    args = parse_args(__doc__).parse_args()
    args.out = str(safe_out(args))
    try:
        write_report(Path(args.data), load_rules(args.category), Path(args.out))
        print(f"wrote {Path(args.out) / 'time_waste.md'}")
    except CannotRun as e:
        print(f"CANNOT RUN: {e}")
