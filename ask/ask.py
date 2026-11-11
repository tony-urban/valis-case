#!/usr/bin/env python3
"""Ask-with-sources slice: answers the CEO's Q1 (SaaS spend) and Q2 (Sales hiring).

Everything is parsed from the data folder at run time through the shared importer.
No amounts, names or line numbers live in this file. Matching vocabulary lives in
config.json. Each answer is printed as: answer, evidence, confidence, could not verify.

Usage:  python3 ask/ask.py [--q q1|q2] [--data <dir>]
Standard library only. No network, no LLM.
"""
import argparse
import json
import re
import sys
from datetime import date, timedelta
from fnmatch import fnmatch
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # this tool writes inside ask/ only
sys.path.insert(0, str(HERE.parent / "pipeline"))
import importer  # noqa: E402  shared parser: one definition of a citable line
import shared  # noqa: E402  SaaS rows, subtotal rows and repeats: one definition, also used by value/

CFG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
ISO = re.compile(r"\d{4}-\d{2}-\d{2}")
WHEN = re.compile(r"(?P<mon>[A-Z][a-z]{2}) (?P<d>\d{1,2}), (?P<h>\d{1,2}):(?P<mi>\d{2}) (?P<ap>AM|PM)")
MONEY = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)\s?([kKmM])?\b")
PLAIN_USD = re.compile(r"^-?\$?(\d{1,3}(,\d{3})+|\d+)(\.\d+)?$")
PERIOD = re.compile(r"Q([1-4])_(\d{4})")
QUARTERS_PER_YEAR = 4
NEG_WINDOW = 3  # words before a status word that are checked for a negation


# ---------- small helpers ----------

def has(s, terms):
    """First term found in s as a whole word or phrase (case-insensitive), else None."""
    for t in terms:
        pat = (r"(?<!\w)" if t[0].isalnum() else "") + re.escape(t) + (r"(?!\w)" if t[-1].isalnum() else "")
        if re.search(pat, s, re.I):
            return t
    return None


def text(u):
    """Plain text of a unit: Markdown emphasis removed, table pipes turned into slashes."""
    if u["kind"] == "row":
        return " ".join(u["fields"].values())
    t = u.get("text", "").replace("*", "")
    if t.startswith("|"):
        t = " / ".join(c.strip() for c in t.strip("|").split("|"))
    return re.sub(r"^- (\[ \] )?", "", t).strip()


def sentences(t):
    return re.split(r'(?<=[.?!])\s+|(?<=[.?!]["”])\s+', t)


def quote(u, terms=()):
    """Verbatim sentences of a unit that contain one of the terms (whole text if none do)."""
    sents = sentences(text(u))
    keep = [s for s in sents if has(s, terms)] or sents
    q = " ".join(keep)
    return '"' + (q if len(q) <= 420 else q[:417] + "...") + '"'


def cite(u, key=None):
    """Citation token in the format of pipeline/02_task.md section 5, built from the parsed unit."""
    if u["kind"] == "message":
        return f"`{u['file']}:L{u['line']} [{u['channel']} | {u['author']} | {u['when']}]`"
    tail = f" ({key}: {u['fields'][key]})" if key and u.get("fields", {}).get(key) else ""
    return f"`{u['file']}:L{u['line']}`{tail}"


def cites(us, key=None):
    return ", ".join(cite(u, key) for u in us)


def num(v):
    """A number, also when written with a $ sign or thousands separators. Anything else (other currency, text) is None."""
    v = (v or "").strip()
    return float(v.replace("$", "").replace(",", "")) if PLAIN_USD.match(v) else None


def fmt(x):
    return f"{x:,.0f}" if float(x).is_integer() else f"{x:,.2f}"


def iso(s):
    m = ISO.search(s or "")
    try:
        return date.fromisoformat(m[0]) if m else None
    except ValueError:
        return None


def money(s):
    """Dollar figures written in free text, for example $81k or $4,200,000."""
    mult = {"": 1, "k": 1e3, "m": 1e6}
    return [float(a.replace(",", "")) * mult[(b or "").lower()] for a, b in MONEY.findall(s)]


def cannot(title, why, need):
    return f"# {title}\n\n## Answer\n\n**Cannot answer from this data folder.** {why}\n\nNeeded: {need}\n"


# ---------- the parsed bundle ----------

class Bundle:
    def __init__(self, data):
        self.dir, self.units, self.problems, self.flags = data, [], [], []
        self.files = sorted(p.relative_to(data).as_posix() for p in data.rglob("*") if p.is_file())
        for rel in self.files:
            fn = {".csv": importer.import_csv, ".md": importer.import_md}.get(Path(rel).suffix.lower())
            try:
                if fn:
                    fn(data / rel, rel, self.units, self.flags)
            except Exception as e:  # a file of unexpected shape must not stop the run
                self.problems.append(f"could not parse `{rel}` ({type(e).__name__}: {e})")
        # Slack timestamps carry no year: take it from the export header (ruling C1).
        self.export_unit = next((u for u in self.pick("slack", "line")
                                 if has(u["text"], CFG["export_terms"]) and iso(u["text"])), None)
        self.as_of = iso(self.export_unit["text"]) if self.export_unit else None

    def problems_block(self):
        return ["", "## Files this run could not parse", ""] + ["- " + p for p in self.problems] if self.problems else []

    def pick(self, key, kind=None):
        return [u for u in self.units if fnmatch(u["file"], CFG["files"][key]) and kind in (None, u["kind"])]

    def when(self, u):
        """(date, minutes) of a unit: Slack header plus export year, or the ISO date in a file name."""
        if u["kind"] == "message":
            m = WHEN.search(u["when"])
            if not (m and self.as_of and m["mon"] in MONTHS):
                return None
            mins = (int(m["h"]) % 12 + (12 if m["ap"] == "PM" else 0)) * 60 + int(m["mi"])
            try:
                return date(self.as_of.year, MONTHS.index(m["mon"]) + 1, int(m["d"])), mins
            except ValueError:
                return None
        d = iso(u["file"])
        return (d, 0) if d else None

    def day(self, u):
        w = self.when(u)
        return w[0].isoformat() if w else "undated"

    def followers(self, u):
        """Later units in the same thread (channel and day) or the same notes section."""
        if u["kind"] == "message":
            same = lambda x: x["kind"] == "message" and x["channel"] == u["channel"] and self.day(x) == self.day(u)
        else:
            same = lambda x: x["kind"] == "line" and x.get("section") == u.get("section")
        return [x for x in self.units if x["file"] == u["file"] and x["line"] > u["line"] and same(x)]

    def question(self, heading, fallback):
        for u in self.pick("questions", "line"):
            if u.get("section", "").startswith(heading) and u["text"].startswith('**"'):
                return f"{heading}. {text(u)}", f"Question as asked: {cite(u)}."
        return f"{heading}. {fallback}", "Question text not found in the data folder."


def confidence(parts):
    """Rule, same for every question: LOW if a core check fails, MEDIUM if only flag
    checks fail, HIGH if nothing fails. parts = [(claim, [(passed, tier, text)])]."""
    out = ["Rule: HIGH when every check passes. MEDIUM when a flag check fails. LOW when a core check fails "
           "(read LOW as: could not verify).", ""]
    for claim, checks in parts:
        failed = [t for ok, t, _ in checks if not ok]
        level = "LOW" if "core" in failed else "MEDIUM" if failed else "HIGH"
        n_core = sum(1 for _, t, _ in checks if t == "core")
        out.append(f"- **{claim}: {level}** (core checks failed: {failed.count('core')} of {n_core}; "
                   f"flag checks failed: {failed.count('flag')} of {len(checks) - n_core})")
        out += [f"  - {'PASS' if ok else 'FAIL'} ({tier}): {msg}" for ok, tier, msg in checks]
    return out


# ---------- Q1: SaaS spend ----------

def q1(B):
    c, col = CFG["q1"], CFG["q1"]["columns"]
    title, asked = B.question(c["question_heading"], "SaaS spend last quarter")
    rows = B.pick("pnl", "row")
    amt = next((h for h in (rows[0]["fields"] if rows else {}) if col["amount_contains"] in h), None)
    if not rows or not amt or col["category"] not in rows[0]["fields"] or col["item"] not in rows[0]["fields"]:
        return cannot(title, f"No usable P&L found (pattern `{CFG['files']['pnl']}`).",
                      f"a P&L CSV with columns `{col['category']}`, `{col['item']}` and an amount column "
                      f"whose name contains `{col['amount_contains']}`.")
    cat, item = (lambda r: r["fields"][col["category"]]), (lambda r: r["fields"][col["item"]])
    val, key = (lambda r: num(r["fields"][amt])), col["item"]
    is_sub = lambda r: shared.is_subtotal(item(r))
    saas = [r for r in rows if shared.is_saas_category(cat(r)) and (item(r) or r["fields"][amt])]
    if not saas:
        return cannot(title, f"The P&L has no rows whose `{col['category']}` contains a SaaS term {shared.RULES['saas_category_terms']} as a whole word.",
                      "the category label Finance uses for subscriptions, added to `saas_category_terms` in pipeline/shared.json (shared with value/).")
    items, subs = [r for r in saas if not is_sub(r)], [r for r in saas if is_sub(r)]
    broken = {n for f, n, msg in B.flags if f == rows[0]["file"] and "fields, header has" in msg}  # importer flag: columns shifted
    good = [r for r in items if val(r) is not None and r["line"] not in broken]
    bad = [r for r in items if r not in good]
    total = sum(val(r) for r in good)
    stated = val(subs[0]) if subs else None
    labels = list(dict.fromkeys(cat(r) for r in saas))  # every distinct category label the shared rule includes
    cur, cat_name = col["amount_contains"], " + ".join(labels)
    pm = PERIOD.search(amt)
    period = f"Q{pm[1]} {pm[2]}" if pm else amt
    q_end = (date(int(pm[2]) + int(pm[1]) // 4, int(pm[1]) * 3 % 12 + 1, 1) - timedelta(days=1)) if pm else None

    src = B.pick("slack", "message") + B.pick("notes", "line")
    pairs = [(a, b) for a, b, _ in shared.find_repeats(good, item, val)[0]]  # each repeated row once, shared with value/
    dup_amount = sum(val(b) for _, b in pairs)
    dup_lines, dup_status, statuses = [], "", []  # suspected duplicates, by rule. Status comes from the messages, never from a guess
    for a, b in pairs:
        both = lambda u: item(a).lower() in text(u).lower() and item(b).lower() in text(u).lower()
        chain = [x for u in filter(both, src) for x in [u] + B.followers(u)]
        flags = [u for u in chain if has(text(u), c["unconfirmed_terms"]) and B.when(u)]
        last_flag = max(flags, key=B.when) if flags else None
        newer = [u for u in src if last_flag and B.when(u) and B.when(u) > B.when(last_flag) and has(text(u), [item(a), item(b)])]
        chain = sorted({(u["file"], u["line"]): u for u in chain + newer}.values(), key=lambda u: (B.when(u) or (date.min, 0), u["line"]))
        dup_lines.append(f"- Side by side: {cite(a, key)} = {fmt(val(a))} and {cite(b, key)} = {fmt(val(b))}.")
        dup_lines += [f"  - {B.day(u)} {u.get('author', 'notes')}: {quote(u)} {cite(u)}" for u in chain]
        if not chain:
            dup_status = "suspected, detected by rule only"
            dup_lines.append(f"  - Status: **{dup_status}.** No message or note in the bundle discusses it.")
        elif newer or not last_flag:
            dup_status = "suspected, later message found, read it"
            dup_lines.append(f"  - Status: **{dup_status}.** {cite(chain[-1])} is the latest message that mentions these rows. This tool does not "
                             "interpret it as confirming or clearing the duplicate. The P&L file still carries both rows, so both figures stay.")
        else:
            dup_status = "suspected, unconfirmed"
            dup_lines.append(f"  - Status: **{dup_status}.** The latest message on it is {cite(last_flag)}, "
                             "which says it has not been confirmed. The rows stay in the as-listed figure. Nothing is silently removed.")
        statuses.append((dup_status, b))
    if len({st for st, _ in statuses}) > 1:  # several repeats with different message trails: name each
        dup_status = "; ".join(f"{st} for {item(b)} {cite(b)}" for st, b in statuses)
    caveats = [u for u in B.pick("notes", "line") if has(text(u), c["caveat_terms"])]
    docs = [f for f in B.files if has(f, c["primary_doc_terms"])]

    out = [f"# {title}", "", asked, "", "## Answer", ""]
    out.append(("**PARTIAL. " if bad else "**") + f"As listed, {fmt(total)} {cur} for {period}: the sum of {len(good)} {cat_name} line items in the P&L."
               + (f" {len(bad)} more line item(s) have an amount this tool could not read and are NOT in that sum." if bad else "")
               + (f" It would be {fmt(total - dup_amount)} {cur} if the suspected duplicate{'s are' if len(pairs) > 1 else ' is'} confirmed." if pairs else "")
               + (" A later message about that duplicate exists and has to be read by a person (evidence 2)." if "later" in dup_status else "")
               + ("" if docs else " No figure here is checked against an invoice.") + "**")
    out.append("")
    if stated is None:
        out.append(f"- As listed: {fmt(total)} {cur}, the sum of the rows below. The P&L has no numeric subtotal row to compare with.")
    elif abs(stated - total) < 0.005:
        out.append(f"- As listed: {fmt(total)} {cur}. The sum of the rows equals the stated subtotal {cite(subs[0], key)}.")
    else:
        out.append(f"- As listed: {fmt(total)} {cur}, the sum of the rows. **These do not reconcile** with the stated subtotal "
                   f"{cite(subs[0], key)}, which says {fmt(stated)} {cur}. Difference {fmt(total - stated)}. The row sum is used here because each row can be cited.")
    if pairs:
        out.append(f"- Without the suspected duplicate{'s' if len(pairs) > 1 else ''}: {fmt(total - dup_amount)} {cur} "
                   f"({fmt(total)} - {fmt(dup_amount)}). Status: {dup_status} (evidence 2). Both figures are shown because the P&L file carries both rows.")
    if bad:
        out.append(f"- {len(bad)} line item(s) have no usable {cur} amount and are NOT in the total: "
                   + ", ".join(f"{item(r)} = '{r['fields'][amt]}'" + (" (row has the wrong number of fields, for example an unquoted comma)" if r["line"] in broken else "")
                               + f" {cite(r)}" for r in bad) + ".")
    reread = [r for r in good if not importer.NUM.match(r["fields"][amt])]
    if reread:
        out.append(f"- {len(reread)} amount(s) were written with a $ sign or thousands separators and were read as plain {cur}: "
                   + ", ".join(f"{item(r)} '{r['fields'][amt]}' read as {fmt(val(r))} {cite(r)}" for r in reread) + ".")
    out.append("- Whether this was actually paid cannot be checked: see confidence and could not verify.")

    # evidence 1: the rows
    out += ["", "## Evidence", "", f"**1. What we are paying for ({cat_name} rows of the P&L, column `{amt}`)**", "",
            f"| Line item | {cur} | What it is (P&L `{col['notes']}`) | Source row |", "|---|---:|---|---|"]
    for r in items:
        shown = fmt(val(r)) if val(r) is not None else f"'{r['fields'][amt]}' (not counted)"
        out.append(f"| {item(r)} | {shown} | {r['fields'].get(col['notes'], '').replace('|', '/')} | {cite(r, key)} |")
    out += ["", "Arithmetic: " + " + ".join(fmt(val(r)) for r in good) + f" = {fmt(total)} {cur}."]

    out += ["", "**2. Suspected duplicate rows (rule: similar label and equal amount)**", ""] + dup_lines
    if not pairs:
        out.append("No candidate found: no two line items have similar labels and equal amounts.")

    # evidence 3: "finalized" statements and what follows them in the same thread
    finals = [m for m in B.pick("slack", "message") if shared.is_saas_category(text(m)) and has(text(m), c["final_terms"])]
    quoted = [u for u in src if shared.is_saas_category(text(u)) and stated is not None and stated in money(text(u))]
    second = [u for u in quoted if pm and has(text(u), ["Q" + pm[1]])]  # counts only if it names the same quarter as the P&L column
    out += ["", "**3. Is the figure final?**", ""]
    if not finals:
        out.append("No message calls the SaaS figure final.")
    for m in finals:
        later = B.followers(m)
        out.append(f"- Statement: {quote(m, c['final_terms'])} {cite(m)}")
        said = money(quote(m, c["final_terms"]))
        if said and stated is not None:
            out.append(f"  - Figure in that statement: {fmt(said[0])}. P&L subtotal row: {fmt(stated)}. "
                       + ("They match." if said[0] == stated else "**These do not match.**"))
        if later:
            out.append(f"  - Later in the same thread: {cites(later)}.")
        disputed = [x for x in later if has(text(x), c["unconfirmed_terms"])]
        out.append("  - Which governs: " + (
            f"the later messages. {cite(disputed[-1])} leaves an open check on this same line after it was called final, "
            "so 'finalized' describes the state of the file, not a verified number." if disputed
            else "nothing later in the thread disputes it, so the statement stands."))

    # evidence 4: renewals quoted with an annual figure, checked against the posted quarter
    disputes, any_contract = [], False
    out += ["", "**4. Contract figures quoted elsewhere versus the posted amount**", ""]
    for r in good:
        hits = [u for u in src if has(text(u), [item(r)]) and has(text(u), c["renewal_terms"])
                and has(text(u), c["annual_terms"]) and money(text(u))]
        if not hits:
            continue
        annual, any_contract = money(text(hits[0]))[0], True
        per_q, first = annual / QUARTERS_PER_YEAR, min((B.when(u) for u in hits if B.when(u)), default=None)
        word = "LOWER than" if val(r) < per_q else "HIGHER than" if val(r) > per_q else "equal to"
        out.append(f"- {item(r)}: posted {fmt(val(r))} {cur} {cite(r, key)}. Annual figure quoted: {fmt(annual)} in {cites(hits)}.")
        out.append(f"  - Arithmetic: {fmt(annual)} / {QUARTERS_PER_YEAR} = {fmt(per_q)} per quarter. "
                   f"Posted {fmt(val(r))} is {word} that" + (f" by {fmt(abs(val(r) - per_q))}." if val(r) != per_q else "."))
        for way, terms in c["direction_terms"].items():
            for u in (u for u in hits if has(text(u), terms)):
                agrees = way.upper() in word
                disputes.append((r, u))
                out.append(f"  - {cite(u)} reads: {quote(u, terms)} "
                           + ("The arithmetic agrees with that direction." if agrees else
                              f"**That does not reconcile with the arithmetic above**: the source says {way}, the numbers say {word.split()[0].lower()}."))
        if first and q_end:
            out.append(f"  - Timing: first mentioned {first[0].isoformat()}, the quarter ended {q_end.isoformat()}. "
                       + ("The renewal postdates the quarter, so it does not tell us what the quarter was billed under the earlier terms, "
                          "which are not in the bundle. The posted amount is left as posted."
                          if first[0] > q_end else "The mention falls inside the quarter."))
    if not any_contract:
        out.append("No message or note quotes an annual contract figure for a SaaS line item.")

    # evidence 5: the boundary, and amounts that are not plain USD
    adj = [r for r in rows if has(cat(r), c["adjacent_category_terms"])]
    adj_items = [r for r in adj if not is_sub(r)]
    adj_usd = sum(val(r) for r in adj_items if val(r) is not None)
    odd = [r for r in rows if r["fields"][amt] and val(r) is None]
    odd_in = [r for r in odd if r in saas]
    boundary = [u for u in src if shared.is_saas_category(text(u)) and has(text(u), c["adjacent_category_terms"])]
    fx_notes = [u for u in src if has(text(u), c["fx_terms"])]
    out += ["", "**5. Boundary and currency**", "",
            f"- Boundary used: rows whose `{col['category']}` is {cat_name}, excluding the subtotal row. "
            "Reason: the CEO asks for the P&L line items." + (f" The same line is drawn in {cite(boundary[0])}: {quote(boundary[0], c['adjacent_category_terms'])}" if boundary else "")]
    if len(labels) > 1:
        out.append(f"- More than one category label matches the shared SaaS rule (`pipeline/shared.json`), each is included: "
                   + "; ".join(f"'{l}' ({sum(1 for r in items if cat(r) == l)} line items)" for l in labels) + ".")
    words = {w.lower() for l in labels for w in re.findall(r"[A-Za-z]{3,}", l)}
    near_cat = [r for r in rows if r not in saas and words & {w.lower() for w in re.findall(r"[A-Za-z]{3,}", cat(r))}]
    if near_cat:
        out.append("- Outside the boundary by the shared rule, although the category shares a word with it (a SaaS term must appear as a whole word): "
                   + "; ".join(f"{item(r)} ({cat(r)}) {r['fields'][amt]} {cite(r, key)}" for r in near_cat) + ". Not in any total above.")
    if adj_items:
        out.append("- Outside the boundary, shown for the broader reading only: "
                   + "; ".join(f"{item(r)} {fmt(val(r)) if val(r) is not None else repr(r['fields'][amt])} {cite(r, key)}" for r in adj_items)
                   + f". Folding it in would add {fmt(adj_usd)} {cur}"
                   + (f" ({fmt(total)} + {fmt(adj_usd)} = {fmt(total + adj_usd)})" if adj_usd else "")
                   + "".join(f", plus {r['fields'][amt]} that is not in {cur}" for r in adj_items if r in odd) + ".")
    for r in odd:
        out.append(f"- Not plain {cur}: {item(r)} = '{r['fields'][amt]}' ({cat(r)}) {cite(r, key)}. P&L note: \"{r['fields'].get(col['notes'], '')}\". "
                   "Not converted and not added to any total: the bundle holds no FX rate.")
    for u in fx_notes:
        out.append(f"- Currency note elsewhere: {quote(u, c['fx_terms'])} {cite(u)}. Rows inside {cat_name} that are not plain {cur}: {len(odd_in)}. "
                   f"Whether any {cat_name} row was converted before posting cannot be seen from the file.")
    for r in (r for r in adj if is_sub(r) and val(r) is None):
        out.append(f"- The adjacent subtotal is blank: {cite(r, key)}, note \"{r['fields'].get(col['notes'], '')}\".")

    # confidence
    out += ["", "## Confidence", ""] + confidence([
        (f"The P&L as listed says {fmt(total)} {cur}", [
            (not bad, "core", f"every {cat_name} line item has a numeric amount ({len(good)} of {len(items)})"),
            (stated is not None and abs(stated - total) < 0.005, "core", "the row sum equals the stated subtotal row"),
            (bool(second), "flag", "a second source states the same subtotal" + (f": {cite(second[0])}" if second else f" (none found; {len(quoted)} message(s) quote the figure without naming {period.split()[0]})")),
        ]),
        (f"{fmt(total)} {cur} is what was actually spent", [
            (bool(docs), "core", "an invoice or contract file is in the bundle to check posted amounts against" + (f" ({', '.join(docs)})" if docs else " (none found)")),
            (not pairs, "flag", "no suspected duplicate is open" + (f" ({fmt(dup_amount)} {cur}, status: {dup_status})" if pairs else "")),
            (not disputes, "flag", "no source questions a posted amount" + ("".join(f" ({item(r)}: {cite(u)})" for r, u in disputes))),
            (not caveats, "flag", "no finance note marks its own figures as provisional" + (f" ({quote(caveats[0])} {cite(caveats[0])})" if caveats else "")),
        ]),
    ])

    # could not verify
    out += ["", "## Could not verify", ""]
    for a, b in pairs:
        out.append(f"- Whether {item(a)} and {item(b)} are one product entered twice, and if so whether it was also paid twice. "
                   f"Closes with: the vendor invoice or contract for those two rows ({cite(a)}, {cite(b)}).")
    for r, u in disputes:
        out.append(f"- Whether the posted {item(r)} amount matches its contract. Closes with: the signed contract and the invoices for the quarter, as {cite(u)} itself asks.")
    if not docs:
        out.append(f"- Cash actually paid for any row. The bundle has the P&L extract only. Closes with: invoices or the AP ledger for the {len(good)} rows.")
    for r in odd:
        out.append(f"- The {cur} value of {item(r)} ('{r['fields'][amt]}') {cite(r)}. Closes with: the month-end FX rate Finance uses, or the invoice.")
    if fx_notes:
        out.append(f"- Whether any {cat_name} row was billed in another currency and converted before posting, and at what rate. Closes with: Finance's FX working for the quarter.")
    for u in caveats:
        out.append(f"- Whether the figures discussed in the finance notes are final. {cite(u)} reads: {quote(u, c['caveat_terms'])} Closes with: the closed, published P&L.")
    return "\n".join(out + B.problems_block()) + "\n"


# ---------- Q2: Sales hiring ----------

def table_cells(B, key="notes"):
    """Markdown table rows in the notes (or another file group) as {(file, line): {header: cell}}."""
    cells_of, header, prev = {}, None, None
    for u in B.pick(key, "line"):
        if not u["text"].startswith("|"):
            continue
        cells = [x.strip() for x in u["text"].strip("|").split("|")]
        if prev != (u["file"], u["line"] - 1):
            header = cells
        elif not all(set(x) <= set("-: ") for x in cells):
            cells_of[(u["file"], u["line"])] = dict(zip(header, cells))
        prev = (u["file"], u["line"])
    return cells_of


def team_names(B, team, col):
    """Names of the teams other than `team`, from the roster's team summary table and the org chart's team table."""
    names = [r["fields"][col["team"]] for r in B.pick("roster", "row") if r["fields"].get(col["headcount"]) and r["fields"].get(col["team"])]
    names += [t[col["team"]].replace("*", "").strip() for t in table_cells(B, "org").values() if t.get(col["team"])]
    return sorted({n for n in names if n and not shared.is_subtotal(n) and not has(n, [team])}, key=len, reverse=True)


def names_team(t, names):
    """First team name written in t, case-sensitive (team names are proper nouns), spaces around '/' ignored."""
    flat = lambda x: re.sub(r"\s*/\s*", "/", x)
    return next((n for n in names if re.search(r"(?<![A-Za-z0-9])" + re.escape(flat(n)) + r"(?![A-Za-z0-9])", flat(t))), None)


def classify(u, c):
    """(label, matched word) of a unit, sentence by sentence. A status word counts only if its
    sentence is not a question, not hedged and not negated. Otherwise it is UNCLEAR: the tool does not guess."""
    order, best = c["label_order"], ("OTHER", None)
    for s in sentences(text(u)):
        for name, terms in c["labels"]:
            t = has(s, terms)
            if not t:
                continue
            if name in c["status_labels"]:
                clause = re.split(r"[,;:(\u2014\u2013]", s[:re.search(re.escape(t), s, re.I).start()])[-1]
                if s.rstrip('"” ').endswith("?"):
                    name = "QUESTION"
                elif has(" ".join(clause.split()[-NEG_WINDOW:]), c["negation_terms"]):
                    name, t = "UNCLEAR", "negated: " + t
                elif has(s, c["hedge_terms"]):
                    name, t = "UNCLEAR", "hedged: " + t
            if order.index(name) < order.index(best[0]):
                best = (name, t)
            break  # one label per sentence: the first in config priority
    return best


def q2(B):
    c, col, team = CFG["q2"], CFG["q2"]["columns"], CFG["q2"]["team"]
    title, asked = B.question(c["question_heading"], f"{team} hiring: decision, current state, owner")
    roster = B.pick("roster", "row")
    reqs = [r for r in roster if r["fields"].get(col["req_id"]) and has(r["fields"].get(col["team"], ""), [team])]
    people = [r for r in roster if r["fields"].get(col["person"])]
    ids = [r["fields"][col["req_id"]] for r in reqs]
    snap_unit = next((u for u in B.pick("roster", "meta") if u["text"].startswith(c["snapshot_key"])), None)
    snap, as_of, side = (iso(snap_unit["text"]) if snap_unit else None), B.as_of, c["sides"]
    status_terms = [t for name, terms in c["labels"] if name in c["status_labels"] for t in terms]

    # retrieval: a unit is evidence if it names the requisition, or the team plus a hiring word, or uses a
    # status word, or follows such a unit in the same thread or notes section and uses a follow-up word
    src = B.pick("slack", "message") + B.pick("notes", "line")
    topic = lambda u: any(i in text(u) for i in ids) or bool(has(text(u), [team]) and has(text(u), c["hiring_terms"]))
    seed = lambda u: topic(u) or bool(has(text(u), status_terms) and has(text(u), c["hiring_terms"]))
    found = {}
    for u in filter(seed, src):
        for x in [u] + [f for f in B.followers(u) if seed(f) or has(text(f), c["followup_terms"])]:
            found[(x["file"], x["line"])] = x
    ev = [{"u": u, "when": B.when(u)} for u in found.values()] + [{"u": r, "when": (snap, 0) if snap else None} for r in reqs]
    for e in ev:
        e["label"], e["term"] = classify(e["u"], c)
    undated = [e for e in ev if not e["when"]]
    ev = sorted((e for e in ev if e["when"]), key=lambda e: (e["when"], e["u"]["file"], e["u"]["line"]))
    day = lambda e: e["when"][0].isoformat()

    # owners: role patterns from config, first names resolved through the roster, then Slack authors
    org, authors = B.pick("org", "line"), {m["author"] for m in B.pick("slack", "message")}

    def person(first):
        full = [r for r in people if first in (r["fields"][col["person"]], r["fields"][col["person"]].split()[0])]
        if len(full) != 1:
            match = {a for a in authors if first in (a, a.split()[0])}
            return (match.pop() if len(match) == 1 else first), ""
        name, r = full[0]["fields"][col["person"]], full[0]
        o = next((u for u in org if name in text(u) and u["text"].startswith("|")), None)
        return name, f"{r['fields'].get(col['title'], '')}, per {cite(r)}" + (f" and {cite(o)}" if o else "")

    owners = {}  # role -> {name: [title, [units]]}
    for role, patterns in c["roles"].items():
        for e, p in ((e, p) for e in ev for p in patterns):
            for m in re.finditer(p, text(e["u"]), re.I):
                g = m.groupdict()
                for f in filter(None, [e["u"].get("author", "")] if g.get("self") else re.split(r" \+ ", g["who"])):
                    slot = owners.setdefault(role, {}).setdefault(person(f)[0], [person(f)[1], []])
                    slot[1] += [e["u"]] if e["u"] not in slot[1] else []
    authority = {n for role in c["authority_roles"] for n in owners.get(role, {})}

    # which team a statement is about (audit finding 3): the line itself, else its notes heading or, for chat, the earlier
    # messages of its thread. Team names and requisition-to-team mapping come from the roster and org chart at run time.
    others = team_names(B, team, col)
    other_ids = [r["fields"][col["req_id"]] for r in roster if r["fields"].get(col["req_id"]) and r not in reqs]

    def about(t):
        if has(t, [team]) or any(i in t for i in ids):
            return team
        return names_team(t, others) or next((i for i in other_ids if i in t), None)

    def tie(u):
        ctx = u.get("section", "") if u["kind"] == "line" else " ".join(
            text(x) for x in B.pick("slack", "message") if x["channel"] == u["channel"] and B.day(x) == B.day(u) and x["line"] < u["line"])
        return about(text(u)) or about(ctx)

    # who may change the state: a decision owner's message or a decision record in the notes. The roster is
    # the baseline. Everyone else is recorded and listed, never applied.
    for e in ev:
        u = e["u"]
        e["by"] = ("roster" if u["kind"] == "row" else
                   ("record" if has(text(u), c["decision_terms"]) else "other") if u["kind"] == "line" else
                   "owner" if u["author"] in authority else "other")
        if e["by"] in ("record", "owner") and e["label"] in c["status_labels"]:
            t = tie(u)  # tied to the team, about another team only, or no team named anywhere
            e["by"] = e["by"] if t == team else "elsewhere" if t else "unteamed"
            e["about"] = t
    clean = [e for e in ev if e["label"] in c["status_labels"]]
    records, chat = [e for e in clean if e["by"] == "record"], [e for e in clean if e["by"] == "owner"]
    base = [e for e in ev if e["by"] == "roster"]
    now = (records or chat or [e for e in base if e in clean] or [None])[-1]  # a decision record sets the state; chat only if there is none
    if now is None:
        return cannot(title, f"No statement about {team} hiring from a decision owner, a decision record or the roster could be classified. "
                      + (f"{len(ev)} related source(s) exist and need a human read: {cites([e['u'] for e in ev][:8])}." if ev else "No related source was found."),
                      f"a roster CSV with `{col['req_id']}` and `{col['team']}` columns, and the Slack export or meeting notes.")
    same = lambda e: side.get(e["label"]) == side[now["label"]]
    # chat from a decision owner may CONFIRM the state of the decision record, never REVERSE it on keywords
    after = [e for e in chat if records and e["when"] > now["when"]]
    conflict = [e for e in after if not same(e)] if after and not same(after[-1]) else []
    overridden = [e for e in after if not same(e) and e not in conflict]
    first = now
    for e in reversed([e for e in chat if e["when"] <= now["when"]]):  # owner chat that led up to the state, for "first recorded"
        if not same(e):
            break
        first = e
    decisions = [e for e in clean if e["by"] in ("owner", "record") and same(e) and first["when"] <= e["when"] <= now["when"]
                 and has(text(e["u"]), c["decision_terms"])]
    latest = ([e for e in clean if same(e) and e["when"] >= now["when"] and e["by"] not in ("roster", "elsewhere", "unteamed")] or [now])[-1]
    last_clean = clean[-1]
    later = [e for e in ev if e["when"] > last_clean["when"] and e["u"]["kind"] != "row"]
    later += [{"u": u, "when": B.when(u), "label": "OTHER", "term": None, "by": "other"} for u in src if (u["file"], u["line"]) not in found
              and B.when(u) and B.when(u) > last_clean["when"] and (has(text(u), [team]) or has(text(u), status_terms))]
    unread = [e for e in later if e["label"] == "UNCLEAR" and e["by"] != "other" or (e["label"] not in ["UNCLEAR"] + c["status_labels"]
              and (topic(e["u"]) or has(text(e["u"]), [team]) or has(text(e["u"]), status_terms)))]
    elsewhere = [e for e in ev if e["by"] == "elsewhere"]
    unread += [e for e in ev if e["by"] == "unteamed" and e["when"] > now["when"] and e not in unread]  # no team named: not applied, NOT CERTAIN
    opposing = [e for e in ev if e["by"] == "other" and e["when"] > now["when"] and (e["label"] == "UNCLEAR" or e in clean and not same(e))]
    stale = [e for e in base if not same(e) and e["when"] < now["when"]]
    newer_roster = [e for e in base if not same(e) and e["when"] > now["when"]]
    cells = table_cells(B)
    actions = [(e, cells[(e["u"]["file"], e["u"]["line"])]) for e in ev if c["action_columns"]["owner"] in cells.get((e["u"]["file"], e["u"]["line"]), {})]
    loose = [e for e in ev if has(text(e["u"]), c["candidate_terms"]) and e not in [a for a, _ in actions]]
    tag = {"owner": "decision owner in chat", "record": "decision record", "roster": "roster", "other": "not a decision owner, cannot change the state",
           "elsewhere": f"about another team, not applied to {team}", "unteamed": f"names no team, not applied to {team}"}
    said = lambda es: " ".join(f"{day(e)} {e['u'].get('author', 'notes')}: {quote(e['u'])} {cite(e['u'])}" for e in es)

    # ---- answer ----
    state_words = {"FROZEN": f"frozen: no new {team} hiring", "LIFTED": f"the {team} freeze is lifted",
                   "APPROVED": f"{team} hiring is approved to proceed"}
    steps = [e for e in base if e in clean and e["when"] < first["when"]] + [r for r in records if r is not now] + ([first] if first is not now else []) + [now]
    seq = ", then ".join(f"{e['label']} ({tag[e['by']]}, {day(e)})" for e in sorted(steps, key=lambda e: e["when"]))
    out = [f"# {title}", "", asked, "", "## Answer", ""]
    head = ("yes, a decision is on record, and it is" if records else "stated in chat by a decision owner, NOT confirmed by a decision record. It is"
            if chat else "no decision found. The roster alone says")
    out.append(f"**1. Decision: {head} {now['label']}.** First recorded {day(first)}: {quote(first['u'], [first['term']])} {cite(first['u'])}. "
               f"Sequence of positions: {seq}.")
    doubt = ("NOT CERTAIN. Last state set by a decision record: " if conflict else "NOT CERTAIN. Last state this tool could classify: " if unread else "")
    out += ["", f"**2. Current state: {doubt}{state_words[now['label']]}**, as of "
            + (f"the Slack export date {as_of.isoformat()} {cite(B.export_unit)}" if as_of else "an unknown date (no Slack export header found)")
            + f". Set by a {tag[now['by']]} on {day(now)} {cite(now['u'])}. "
            + (f"**A later chat message from a decision owner reads as a different state and is NOT applied: chat can confirm a decision record, "
               f"it cannot reverse one on keywords. Read it yourself:** {said(conflict)} " if conflict else "")
            + f"Latest statement consistent with it, dated {day(latest)}: {quote(latest['u'], [latest['term']])} {cite(latest['u'])}."]
    if unread:
        out.append(f"   - **WARNING: {len(unread)} later message(s) on this topic could not be classified by this tool, or name no team so cannot be tied to {team}. The state above may be out of date. "
                   f"Read them yourself:** {said(unread)}")
    elif as_of and as_of > latest["when"][0] and not later and not conflict and not any(e["when"] > latest["when"] for e in elsewhere):
        out.append(f"   - Nothing in the bundle on this topic is later than {day(latest)}, so the {(as_of - latest['when'][0]).days} day(s) up to the export date are not evidenced.")
    for e in newer_roster:
        out.append(f"   - **Conflict:** a roster snapshot dated {day(e)} is later than the statement that set the state and shows "
                   f"{e['u']['fields'].get(col['status'], '')} {cite(e['u'], col['req_id'])} (evidence 3).")
    if overridden:
        out.append(f"   - A decision owner said otherwise in chat and then restated the decision: {said(overridden)}")
    if elsewhere:
        out.append(f"   - Decisions about other teams, not applied to {team} (evidence 2): {said(elsewhere)}")
    for e in opposing:
        out.append(f"   - Later statement from someone who is not a decision owner, listed and not applied: {said([e])}")
    for r in reqs:
        names_it = lambda es: [e for e in es if r["fields"][col["req_id"]] in text(e["u"])]
        mine = names_it([e for e in clean if e["by"] in ("owner", "record") and same(e)]) or names_it([e for e in clean if e["by"] == "other"])
        out.append(f"   - {r['fields'][col['req_id']]} ({r['fields'].get(col['title'], '')}): roster says {r['fields'].get(col['status'], '')} {cite(r, col['req_id'])}"
                   + (f"; latest source naming it says {mine[-1]['label']} ({day(mine[-1])}, {tag[mine[-1]['by']]}) {cite(mine[-1]['u'])}." if mine else "; no later source names it."))
    if not reqs:
        out.append(f"   - The roster holds no requisition for {team}.")
    out += ["", "**3. Owner: more than one role is named, so each is listed separately.**"]
    for role, names in owners.items():
        for name, (ttl, us) in names.items():
            out.append(f"   - {role}: {name}" + (f" ({ttl})" if ttl else "") + f". Stated in {cites(us)}.")
    for r in reqs:
        out.append(f"   - Hiring manager for {r['fields'][col['req_id']]}: {r['fields'].get(col['manager'], '') or 'blank'}, per {cite(r, col['req_id'])}.")
    if not owners:
        out.append("   - No source names a decision maker or enforcer in wording this tool recognises.")

    # ---- evidence ----
    out += ["", "## Evidence", "", "**1. Timeline of every source found (oldest first). Only a decision owner or a decision record can change the state.**", ""]
    for e in ev + [x for x in later if x not in ev]:
        u = e["u"]
        out.append(f"- {day(e)} {e['label']}" + (f" ('{e['term']}', {tag[e['by']]})" if e["term"] and e["label"] in ["UNCLEAR"] + c["status_labels"] else "")
                   + f", {u.get('author') or ('roster' if u['kind'] == 'row' else 'notes')}: {quote(u)} {cite(u)}")
    for e in undated:
        out.append(f"- undated, not used for ordering: {quote(e['u'])} {cite(e['u'])}")
    out += ["", "**2. Later messages this tool could not classify, or that conflict with the decision record**", ""]
    out += [f"- {said([e])}" for e in unread + conflict] or ["None."]
    if elsewhere:
        out += ["", f"**Decisions about other teams, not applied to {team}**", ""]
        out += [f"- About {e['about']}: {said([e])}" for e in elsewhere]

    out += ["", "**3. Stale source next to the source that supersedes it**", ""]
    supers = [e for e in ev if has(text(e["u"]), c["supersede_terms"])]
    for e in stale:
        out.append(f"- Stale: roster snapshot dated {day(e)}" + (f" {cite(snap_unit)}" if snap_unit else "")
                   + f" shows {e['u']['fields'].get(col['status'], '')} {cite(e['u'], col['req_id'])}.")
    for e in newer_roster:
        out.append(f"- **These do not reconcile:** the roster snapshot dated {day(e)} shows {e['u']['fields'].get(col['status'], '')} {cite(e['u'], col['req_id'])}, "
                   f"which is later than the statement that set the state {cite(now['u'])} and does not match it. The roster does not change the state here.")
    if stale:
        out.append(f"- Governs: {now['label']}, {tag[now['by']]}, dated {day(now)} {cite(now['u'])}.")
        out.append("- Why: (a) it is later than the snapshot" + (
            "; (b) the sources say so explicitly: " + "; ".join(f"{quote(e['u'], c['supersede_terms'])} {cite(e['u'])}" for e in supers)
            if supers else ". No source states the supersession explicitly, so this rests on date order alone."))
    elif not newer_roster:
        out.append("The roster status and the current state are on the same side. Nothing is stale on this point.")

    out += ["", "**4. Dates that do not line up**", ""]
    dates = set()
    for e in decisions:
        rel = next((n for t, n in c["relative_day_terms"].items() if has(text(e["u"]), [t])), None)
        dates.add(e["when"][0] + timedelta(days=rel or 0))
        out.append(f"- Decision record dated {day(e)} {cite(e['u'])}")
    for e in (e for e in clean if e["by"] == "other" and same(e) and e["when"] >= first["when"]):  # hearsay about the decision date, for example "yesterday's call"
        for t, n in c["relative_day_terms"].items():
            if has(text(e["u"]), [t]):
                dates.add(e["when"][0] + timedelta(days=n))
                out.append(f"- Message dated {day(e)} points to {(e['when'][0] + timedelta(days=n)).isoformat()}: {quote(e['u'], [t])} {cite(e['u'])}")
    if len(dates) > 1:
        noted = [f for f in B.files if fnmatch(f, CFG["files"]["notes"]) and min(dates).isoformat() in f]
        out.append(f"- **These do not fully reconcile:** the sources point to {', '.join(sorted(d.isoformat() for d in dates))}. The outcome is the same in each. "
                   f"The earliest, {min(dates).isoformat()}, is used as the decision date because a later record cannot predate the decision. "
                   + ("" if noted else f"The bundle holds no meeting note dated {min(dates).isoformat()}."))
    elif dates:
        out.append(f"- All decision records point to {min(dates).isoformat()}.")
    approvals = []  # a source that says when approval happened, against an earlier message that already calls it approved
    for e in ev:
        m = re.search(c["approval_when_pattern"], text(e["u"]), re.I)
        mon = MONTHS.index(m["mon"][:3].title()) + 1 if m and m["mon"][:3].title() in MONTHS else None
        early = [s for s in ev if mon and s["u"]["kind"] == "message" and has(text(s["u"]), c["approval_terms"])
                 and any(i in text(s["u"]) for i in ids) and (s["when"][0].year, s["when"][0].month) < (e["when"][0].year, mon)]
        if early:
            approvals.append(e)
            out.append(f"- **Approval date does not reconcile:** {cite(e['u'])} says {quote(e['u'], c['approval_terms'])} "
                       f"An earlier message, dated {day(early[0])}, already calls it approved: {quote(early[0]['u'], c['approval_terms'])} {cite(early[0]['u'])}")

    words = {}
    for e, t in ((e, t) for e in ev if e["by"] != "elsewhere" for t in c["wording_terms"]):
        if has(text(e["u"]), [t]):
            words.setdefault(t, []).append(e["u"])
    since = [e for e in ev if e["when"] >= first["when"]]
    out += ["", "**5. Wording and scope, as written**", "",
            "- Status words in use: " + "; ".join(f"'{t}' {cite(us[0])}" + (f" and {len(us) - 1} more" if len(us) > 1 else "") for t, us in words.items()) + "."]
    out += [f"- Scope: {quote(e['u'], c['scope_terms'])} {cite(e['u'])}" for e in since if has(text(e["u"]), c["scope_terms"]) and e["label"] != "QUESTION"]

    revisits = [e for e in since if has(text(e["u"]), c["revisit_terms"])]
    out += ["", "**6. Revisit triggers, all listed, none picked**", ""] + [f"- {quote(e['u'], c['revisit_terms'])} {cite(e['u'])}" for e in revisits]
    for u in (u for u in B.pick("notes", "line") if has(text(u), c["next_meeting_terms"]) and u["file"] in {e["u"]["file"] for e in ev}):
        out.append(f"- Next scheduled meeting in the same notes: {quote(u)} {cite(u)}")

    out += ["", "**7. Open actions and loose ends**", ""]
    overdue, known = [], {}
    for e, t in actions:
        due, owner_col = iso(t.get(c["action_columns"]["due"], "")), c["action_columns"]["owner"]
        body = " ".join(v for k, v in t.items() if k != owner_col)
        named = [a for a in authors if has(body, [a.split()[0]])]
        known[id(e)] = [x for x in ev if x["u"].get("author") in named and x["when"] >= e["when"]]
        if due and as_of and due <= as_of:
            overdue.append(e)
        out.append(f"- {quote(e['u'])} {cite(e['u'])}. " + (f"Due {due.isoformat()}, on or before the export date. " if e in overdue else "")
                   + "The notes carry no completion mark and this tool does not infer completion from chat."
                   + (f" The person named in the action already posts about this decision ({cites([x['u'] for x in known[id(e)]])}), so they know of it. "
                      "What is not evidenced is the action as worded, including any change in the system it names." if known[id(e)] else ""))
    out += [f"- Unresolved in the sources: {quote(e['u'], c['candidate_terms'])} {cite(e['u'])}" for e in loose]

    # the req list in chat versus the roster table (matters for "other teams unaffected")
    all_reqs = [r for r in roster if r["fields"].get(col["req_id"])]
    teams_all = {r["fields"][col["team"]] for r in roster if r["fields"].get(col["headcount"]) and r["fields"].get(col["team"])}
    req_teams, mismatch = [r["fields"].get(col["team"], "") for r in all_reqs], False
    for m in (m for m in B.pick("slack", "message") if snap and snap.isoformat() in text(m) and has(text(m), c["open_req_terms"])):
        named = lambda t: t.lower() in text(m).lower()
        maybe = lambda t: any(importer.abbrev(w.strip(".,()"), t) for w in text(m).split())
        missing, extra = [t for t in req_teams if not named(t)], sorted(t for t in teams_all if named(t) and t not in req_teams)
        mismatch = bool(missing or extra)
        out += ["", "**8. Open requisitions: chat versus roster table**", "",
                f"- Roster table: {len(all_reqs)} open requisitions ({', '.join(req_teams)}) {cites(all_reqs, col['req_id'])}.",
                f"- Chat, same snapshot: {quote(m, c['open_req_terms'])} {cite(m)}",
                "- Roster teams not named in the message as written: " + (", ".join(t + (" (possibly abbreviated in the message)" if maybe(t) else "") for t in missing) or "none")
                + ". Teams named in the message with no roster requisition: " + (", ".join(extra) or "none") + ".",
                "- " + ("**These do not reconcile.** Any claim that other teams' requisitions are unaffected cannot be tied to one agreed list."
                        if mismatch else "The two lists agree on teams.")]

    # ---- confidence ----
    files_of = lambda es: {e["u"]["file"] + e["u"].get("channel", "") for e in es}
    maker = owners.get(next(iter(c["roles"])), {})
    maker_sources = max((len(v[1]) for v in maker.values()), default=0)
    fresh_days = (as_of - latest["when"][0]).days if as_of else None
    out += ["", "## Confidence", ""] + confidence([
        ("What was decided", [
            (bool(decisions), "core", f"an explicit decision statement exists ({len(decisions)} found)"),
            (not conflict, "core", f"no later message from a decision owner reads as a different state ({len(conflict)} found)"),
            (len(files_of(decisions)) > 1, "flag", f"the decision is recorded in more than one place ({len(files_of(decisions))} distinct files or channels)"),
        ]),
        ("Who owns it", [
            (len(maker) == 1, "core", f"exactly one decision maker is named ({', '.join(maker) or 'none'})"),
            (maker_sources > 1, "flag", f"the decision maker is stated in more than one source ({maker_sources})"),
        ]),
        (f"Current state as of {as_of.isoformat() if as_of else 'unknown'}", [
            (bool(records or chat), "core", "the state was set by a decision owner or a decision record, not by the roster alone"),
            (not conflict, "core", f"no later chat message from a decision owner conflicts with the decision record ({len(conflict)} found, see evidence 2)"),
            (bool(records), "flag", "the state rests on a decision record in the notes, not on chat alone"),
            (not unread, "core", f"no later message on the topic is left unclassified ({len(unread)} found, see evidence 2)"),
            (not newer_roster, "core", "no newer roster shows a different status"),
            (fresh_days is not None and fresh_days <= c["stale_after_days"], "core",
             f"the latest consistent statement is within {c['stale_after_days']} days of the export date ({fresh_days} days)"),
            (not opposing, "flag", f"no later statement from a non-owner points the other way ({len(opposing)} found)"),
            (not stale, "flag", "the roster (system of record in the bundle) shows the same status"),
            (len(dates) <= 1, "flag", "all sources give the same decision date"),
            (not overdue, "flag", f"no follow-up action is past its due date without a completion mark ({len(overdue)} are)"),
            (not loose, "flag", f"no loose end is left open in the sources ({len(loose)} found)"),
            (bool(as_of) and latest["when"][0] >= as_of, "flag", "evidence runs up to the export date"),
        ]),
    ])

    # ---- could not verify ----
    out += ["", "## Could not verify", ""]
    out += [f"- What this later message means for the state: {quote(e['u'])} {cite(e['u'])}. Closes with: a person reading it, then the decision maker." for e in unread + conflict]
    if as_of and latest["when"][0] < as_of:
        out.append(f"- Anything after {day((later or [latest])[-1])}. Closes with: the channels after the export date, or a word from the decision maker.")
    if stale:
        out.append("- Whether the requisition status was actually changed in the recruiting system. The only roster is the stale snapshot. Closes with: a current roster export or the ATS status.")
    for e, t in actions:
        out.append(f"- Whether this was carried out as worded: {quote(e['u'])} {cite(e['u'])}. "
                   + ("The person it names already knows of the decision (evidence 7). " if known[id(e)] else "")
                   + f"Closes with: {t.get(c['action_columns']['owner'], 'the owner')}.")
    out += [f"- How this ended: {quote(e['u'], c['candidate_terms'])} {cite(e['u'])}. Closes with: the people named in it." for e in loose]
    if len(dates) > 1:
        out.append("- The exact decision date. Closes with: notes or a calendar entry for the earlier call.")
    for e in approvals:
        out.append(f"- When the requisition was approved: {cite(e['u'])} and an earlier message disagree (evidence 4). Closes with: the approval record in the requisition tracker.")
    if len(revisits) > 1:
        out.append(f"- Which revisit trigger applies: {len(revisits)} statements, worded differently ({cites([e['u'] for e in revisits])}). Closes with: the decision maker.")
    if mismatch:
        out.append("- Which requisitions are open outside the frozen team: chat and roster table disagree (evidence 8). Closes with: a current requisition list from People.")
    return "\n".join(out + B.problems_block()) + "\n"


# ---------- entry point ----------

def main():
    default_data = HERE.parent / "data"
    ap = argparse.ArgumentParser(description="Answer the CEO's Q1 and Q2 from the data folder, with sources.")
    ap.add_argument("--q", choices=["q1", "q2"], help="answer one question only")
    ap.add_argument("--data", default=str(default_data), help="data folder (default: data/)")
    ap.add_argument("--out", help="folder for q1.md and q2.md (default: ask/out/ for the default data folder, stdout only otherwise)")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    B = Bundle(Path(args.data))
    # a run on other data never touches the committed answers in ask/out/ unless --out says so
    out_dir = Path(args.out) if args.out else (HERE / "out" if Path(args.data).resolve() == default_data.resolve() else None)
    for name, fn in (("q1", q1), ("q2", q2)):
        if args.q in (None, name):
            try:
                answer = fn(B)
            except Exception as e:  # last resort: say what broke instead of a traceback
                answer = cannot(name.upper(), f"The data has a shape this tool does not handle ({type(e).__name__}: {e}).",
                                "a file of the same shape as the original bundle. See ask/README.md.")
            if out_dir:
                out_dir.mkdir(parents=True, exist_ok=True)
                with open(out_dir / f"{name}.md", "w", encoding="utf-8", newline="\n") as f:
                    f.write(answer)
            print(answer)


if __name__ == "__main__":
    main()
