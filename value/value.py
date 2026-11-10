#!/usr/bin/env python3
"""Value number worksheet (work stream WS3).

Finds a suspected duplicate line item in one P&L category by rule
(near-identical label plus equal amount), then writes a worksheet a finance
reviewer can redo with a calculator: baseline, arithmetic, inputs, what could
not be verified, and the objections.

The script never confirms anything. It reports an amount at risk.

Usage: python3 value/value.py [--data <dir>] [--out <file>]
Standard library only. Vocabulary lives in value/config.json.
"""
import argparse
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "pipeline"))
sys.dont_write_bytecode = True  # this script writes only inside value/
import importer  # noqa: E402  shared parser: one definition of a citable line

CFG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
STATUS = "suspected, unconfirmed"
STATUS_LATER = "suspected, later message found, read it"
MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")
WHEN = re.compile(r"([A-Za-z]{3})[a-z]* (\d{1,2}), (\d{1,2}):(\d{2}) ?([AP]M)")


class Stop(Exception):
    """A plain-language reason the worksheet cannot be built."""


def money(d):
    return f"{d:,.0f}" if d == d.to_integral_value() else f"{d:,.2f}"


def has_any(text, terms):
    return any(t.lower() in text.lower() for t in terms)


# ---------- parse ----------

def load_pnl(data):
    """Return the configured category of the P&L: line items, subtotal row, period, currency."""
    found = sorted(data.glob(CFG["pnl_file_glob"]))
    if len(found) != 1:
        raise Stop(f"need exactly one file matching {CFG['pnl_file_glob']} in the data folder, found {len(found)}")
    rel = found[0].relative_to(data).as_posix()
    lines = importer.read_lines(found[0])
    if not lines:
        raise Stop(f"{rel} is empty")
    cat_col, label_col = CFG["category_column"], CFG["label_column"]
    for _, _, header, rows in importer.split_sections(lines)[1]:
        header = [h.strip() for h in header or []]
        amount = next((re.match(CFG["amount_column_pattern"], h) for h in header
                       if re.match(CFG["amount_column_pattern"], h)), None)
        if amount and cat_col in header and label_col in header:
            break
    else:
        raise Stop(f"{rel} has no table with columns {cat_col}, {label_col} and an amount column "
                   f"shaped like {CFG['amount_column_pattern']}")
    total_re = re.compile(r"\b(" + "|".join(map(re.escape, CFG["subtotal_terms"])) + r")\b", re.I)
    items, subtotal = [], None
    for n, r in rows:
        rec = {h: (r[k].strip() if k < len(r) else "") for k, h in enumerate(header)}
        if rec[cat_col] != CFG["category"]:
            continue
        raw = rec[amount.group(0)]
        row = {"line": n, "label": rec[label_col], "raw": raw,
               "amount": Decimal(raw) if importer.NUM.match(raw) else None,
               "notes": rec.get(CFG["notes_column"], "")}
        if total_re.search(row["label"]):
            subtotal = row
        else:
            items.append(row)
    if not items:
        raise Stop(f"{rel} has no rows where {cat_col} is {CFG['category']}")
    return {"rel": rel, "items": items, "subtotal": subtotal, "amount_col": amount.group(0),
            "period": amount["period"].replace("_", " "), "cur": amount["currency"]}


def similar(a, b):
    """Why two labels count as near-identical, or None. Uses the importer's own tests."""
    if a.lower().split() == b.lower().split():
        return "the labels are identical"
    if importer.word_prefix(a, b) or importer.word_prefix(b, a):
        return "one label is the other with extra words added"
    if importer.abbrev(a, b):
        return "the labels differ only by an abbreviation"
    return None


def find_repeats(items):
    """A row is a suspected repeat when an earlier row in the category has a
    near-identical label and an equal amount. Similar label with a different
    amount is a near miss: listed, never counted."""
    repeats, near = [], []
    for j, later in enumerate(items):
        for earlier in items[:j]:
            why = similar(earlier["label"], later["label"])
            if not why or earlier["amount"] is None or later["amount"] is None:
                continue
            if earlier["amount"] == later["amount"]:
                repeats.append((earlier, later, why))
                break
            near.append((earlier, later))
    return repeats, near


def load_notes(data):
    """Every markdown unit in the bundle. Messages get a thread id (count of '---' rules above)."""
    units = []
    for p in sorted(data.rglob("*.md")):
        rel = p.relative_to(data).as_posix()
        start = len(units)
        importer.import_md(p, rel, units, [])
        rules = [i + 1 for i, l in enumerate(importer.read_lines(p)) if l.strip() == "---"]
        for u in units[start:]:
            u["thread"] = (rel, sum(1 for r in rules if r < u["line"]))
    return units


def when_key(u):
    """Order messages by month, day and time (ruling C1: one year, never the weekday).
    A timestamp that does not parse sorts by file position only."""
    m = WHEN.search(u["when"])
    if not m or m.group(1).lower() not in MONTHS:
        return (0, 0, 0, u["file"], u["line"])
    hour = int(m.group(3)) % 12 + (12 if m.group(5) == "PM" else 0)
    return (MONTHS.index(m.group(1).lower()) + 1, int(m.group(2)), hour * 60 + int(m.group(4)), u["file"], u["line"])


def find_evidence(units, labels):
    names = re.compile(r"\b(" + "|".join(re.escape(l) for l in labels) + r")\b", re.I)
    msgs = [u for u in units if u["kind"] == "message"]
    hits = sorted((u for u in msgs if names.search(u["text"]) and has_any(u["text"], CFG["suspicion_terms"])), key=when_key)
    # The flag is the earliest thread that raises the pair. Any message that names the pair and is
    # dated after the last flag in that thread is "later". It is never interpreted: a person reads it.
    thread = [u for u in msgs if hits and u["thread"] == hits[0]["thread"]]
    flagged = [u for u in hits if u in thread]
    last_flag = max(map(when_key, flagged)) if flagged else None
    later = sorted((u for u in msgs if names.search(u["text"]) and u not in flagged and last_flag and when_key(u) > last_flag),
                   key=when_key)
    mentions = [u for u in units if u["kind"] in ("message", "line") and names.search(u["text"])
                and u not in thread and u not in later]
    return {"flagged": flagged, "thread": thread, "later": later,
            "renewal": [u for u in mentions if has_any(u["text"], CFG["renewal_terms"])],
            "other": [u for u in mentions if not has_any(u["text"], CFG["renewal_terms"])]}


# ---------- cite ----------

def cite(u):
    if u["kind"] == "message":
        return f"`{u['file']}:L{u['line']} [{u['channel']} | {u['author']} | {u['when']}]`"
    return f"`{u['file']}:L{u['line']}`"


def cite_row(pnl, row):
    return f"`{pnl['rel']}:L{row['line']}` ({CFG['label_column']}: {row['label']})"


def cites(us):
    return ", ".join(cite(u) for u in us)


# ---------- render ----------

def render(data):
    pnl = load_pnl(data)
    cur, period, cat, unit = pnl["cur"], pnl["period"], CFG["category"], CFG["period_unit"]
    items, sub = pnl["items"], pnl["subtotal"]
    counted = [r for r in items if r["amount"] is not None]
    unparsed = [r for r in items if r["amount"] is None]
    base = sum((r["amount"] for r in counted), Decimal(0))
    repeats, near = find_repeats(items)
    at_risk = sum((later["amount"] for _, later, _ in repeats), Decimal(0))
    net = base - at_risk
    units = load_notes(data)
    labels = sorted({r["label"] for pair in repeats for r in pair[:2]})
    ev = find_evidence(units, labels) if repeats else {"flagged": [], "thread": [], "later": [], "renewal": [], "other": []}
    people = list(dict.fromkeys(u["author"] for u in ev["thread"] + ev["later"]))
    later = ev["later"]
    status = STATUS_LATER if later else STATUS
    ask = (", ".join(people) + " (authors of the messages quoted in section 6)") if people \
        else "whoever owns the P&L extract (the bundle names nobody for this pair)"
    out = []
    w = out.append

    if sub is None:
        sub_state = "The category has no subtotal row, so the computed sum is the baseline."
    elif sub["amount"] is None:
        sub_state = f"The stated subtotal {cite_row(pnl, sub)} has no numeric value ({sub['raw']!r}), so the computed sum is the baseline."
    elif sub["amount"] == base:
        sub_state = f"The stated subtotal {cite_row(pnl, sub)} is {money(sub['amount'])} {cur} and matches the computed sum."
    else:
        sub_state = (f"The stated subtotal {cite_row(pnl, sub)} is {money(sub['amount'])} {cur} and DOES NOT match the computed sum "
                     f"of {money(base)} {cur}. These do not reconcile. The computed sum of the cited rows is used as the baseline.")

    def baseline_table():
        w(f"| Row | Amount ({cur}) | Flag |")
        w("|---|---|---|")
        later_of = {id(l): e for e, l, _ in repeats}
        earlier_ids = {id(e) for e, _, _ in repeats}
        for r in items:
            flag = ""
            if id(r) in later_of:
                flag = f"suspected repeat of L{later_of[id(r)]['line']}"
            elif id(r) in earlier_ids:
                flag = "has a suspected repeat below"
            elif r["amount"] is None:
                flag = f"not a plain number ({r['raw']!r}): left out of every sum"
            w(f"| {cite_row(pnl, r)} | {money(r['amount']) if r['amount'] is not None else r['raw']} | {flag} |")
        w(f"| Computed sum of the {len(counted)} numeric rows above | {money(base)} | computed |")
        w("")
        w(sub_state)

    # ----- no candidate: say so, never invent a number -----
    if not repeats:
        w(f"# Value number: none. No candidate found in {period} {cat}.")
        w("")
        w("Generated by python3 value/value.py. Do not edit by hand. Citations are relative to the data folder.")
        w("")
        w(f"The rule looks for two rows in the {cat} category with a near-identical label and an equal amount. "
          "No pair of rows meets it, so there is no headline number. Nothing is carried over from an earlier run.")
        w("")
        w("## Baseline (as listed)")
        w("")
        baseline_table()
        if near:
            w("")
            w("Rows with similar labels but different amounts (not a candidate under the rule, listed for a person to check):")
            for e, l in near:
                w(f"- {cite_row(pnl, e)} at {money(e['amount'])} {cur} and {cite_row(pnl, l)} at {money(l['amount'])} {cur}")
        return "\n".join(out) + "\n"

    n = len(repeats)
    one = n == 1
    thing = "line item" if one else "line items"
    invoice = "one invoice" if one else "one invoice per pair"
    year = at_risk * CFG["periods_per_year"]
    share = (at_risk / base * 100).quantize(Decimal("0.1")) if base else None

    if later:
        w(f"# Value number: {money(at_risk)} {cur} at risk in {period} (one {unit}). "
          f"Status: {STATUS_LATER}. The number may be out of date.")
    else:
        w(f"# Value number: {money(at_risk)} {cur} at risk in {period} (one {unit}). "
          f"Status: suspected duplicate {cat} {thing}, unconfirmed, closed by {invoice}.")
    w("")
    w("Generated by python3 value/value.py. Do not edit by hand. Citations are relative to the data folder.")
    w("")
    w("## 1. The claim")
    w("")
    if later:
        w(f"- **Read this first.** {len(later)} message(s) dated after the last flag also name the pair. The number below may be out of date. "
          "The script does not judge whether a later message confirms or clears the duplicate. A person must read:")
        for u in later:
            w(f"  - {cite(u)}: \"{u['text'].replace('`', chr(39))}\"")
    w(f"- {'One row' if one else str(n) + ' rows'} in the {cat} category of the {period} P&L "
      f"{'looks like a repeat of another row' if one else 'look like repeats of other rows'}: near-identical label, equal amount. "
      f"The amount on {'that row' if one else 'those rows'} is {money(at_risk)} {cur}.")
    w(f"- It is an amount at risk, not a confirmed saving. Depending on what the invoice shows it is worth between 0 and "
      f"{money(at_risk)} {cur} for the {unit} (section 5).")
    w(f"- The action is to pull {invoice}. The script detects the pair by rule and never upgrades the status to confirmed.")
    w("")
    w("## 2. Baseline")
    w("")
    w(f"The baseline is the {cat} category of the P&L for {period}, as listed. Rows in other categories are not folded in.")
    w("")
    baseline_table()
    w("")
    w("## 3. Arithmetic, step by step")
    w("")
    w(f"1. As listed: the {len(counted)} rows in section 2 add up to {money(base)} {cur}.")
    step = 2
    for e, l, why in repeats:
        same_notes = " The Notes text on the two rows is identical." if e["notes"] and e["notes"] == l["notes"] else ""
        w(f"{step}. Candidate pair: {cite_row(pnl, e)} is {money(e['amount'])} {cur} and {cite_row(pnl, l)} is "
          f"{money(l['amount'])} {cur}. The amounts are equal and {why}.{same_notes}")
        step += 1
    if one:
        w(f"{step}. Amount at risk (the headline) = the amount on the later row = {money(at_risk)} {cur}. "
          "The two amounts are equal, so it does not matter which row is treated as the repeat.")
    else:
        w(f"{step}. Amount at risk (the headline) = " + " + ".join(money(l["amount"]) for _, l, _ in repeats) + f" = {money(at_risk)} {cur}.")
    w(f"{step + 1}. Without the suspected duplicate: {money(base)} - {money(at_risk)} = {money(net)} {cur}.")
    if share is not None:
        w(f"{step + 2}. Share of the category: {money(at_risk)} / {money(base)} = {share}%.")
    w("")
    w(f"Not part of the headline: if, and only if, the same repeat sits in every {unit} of a year, the figure is "
      f"{money(at_risk)} x {CFG['periods_per_year']} = {money(year)} {cur} a year. This is ASSUMPTION A3. The bundle holds one {unit} only.")
    w("")
    w("## 4. Inputs")
    w("")
    w("| # | Input | Value | Tag | Source, or effect if wrong |")
    w("|---|---|---|---|---|")
    k = 1
    for e, l, _ in repeats:
        w(f"| I{k} | Amount on the earlier row | {money(e['amount'])} {cur} | SOURCED | {cite_row(pnl, e)} |")
        w(f"| I{k + 1} | Amount on the later row | {money(l['amount'])} {cur} | SOURCED | {cite_row(pnl, l)} |")
        k += 2
    w(f"| I{k} | Other rows of the category | sum to {money(base)} {cur} with the rows above | SOURCED | each row cited in section 2 |")
    k += 1
    if sub is not None and sub["amount"] is not None:
        w(f"| I{k} | Stated subtotal | {money(sub['amount'])} {cur} | SOURCED | {cite_row(pnl, sub)} |")
        k += 1
    w(f"| I{k} | Period and currency | {period}, {cur} | SOURCED | name of the amount column, {pnl['amount_col']}, in the header of {pnl['rel']} (a header is not a citable line) |")
    k += 1
    if ev["flagged"]:
        w(f"| I{k} | The pair is flagged as a possible repeat by people in the business | see section 6 | SOURCED (an opinion, not a fact) | messages listed under this table |")
    w(f"| A1 | The two rows are one product on one contract | not known | ASSUMPTION | If wrong, the headline is 0 and both rows are real cost. |")
    w(f"| A2 | The posted amount equals the invoiced amount | not known | ASSUMPTION | If wrong, the headline becomes the invoiced amount of the repeated row. |")
    w(f"| A3 | The same repeat sits in every {unit} (annual figure only, not the headline) | x {CFG['periods_per_year']} | ASSUMPTION | If wrong, the annual figure falls to as little as {money(at_risk)} {cur}. The headline does not move. |")
    if ev["flagged"]:
        w("")
        w(f"Sources for I{k}: {cites(ev['flagged'])}.")
    w("")
    w("## 5. What it is worth under each reading")
    w("")
    w("The bundle cannot tell these apart.")
    w("")
    w(f"| Reading | What happened | Effect on the {period} P&L | Cash effect | Action |")
    w("|---|---|---|---|---|")
    w(f"| R1 Entered twice, paid once | One charge posted on two rows | Category overstated by {money(at_risk)} {cur}: {money(net)} instead of {money(base)} | None | Correct the P&L. This is a reporting correction, not a saving. |")
    w(f"| R2 Billed or paid twice | Two charges for one product | Cost is real as posted, but {money(at_risk)} {cur} should not have been incurred | Up to {money(at_risk)} {cur} left the business. Recovery depends on the vendor. | Ask for a credit or refund and cancel the second charge. |")
    w(f"| R3 Two real contracts | Two separate products, plans or terms that happen to cost the same | None | None | Relabel the rows so they stop looking like a repeat. The value is 0. |")
    w("")
    w("## 6. Evidence in the bundle (verbatim, not interpreted by the script)")
    w("")
    if ev["thread"]:
        w("Every message in the thread where the pair is named together with a suspicion term:")
        w("")
        for u in ev["thread"]:
            w(f"- {cite(u)}: \"{u['text'].replace('`', chr(39))}\"")
        if any(re.search(r"\d+\s?%", u["text"]) for u in ev["thread"]):
            w("")
            w("A message above states a confidence percentage. It is one person's estimate. It is not used in any arithmetic here.")
    else:
        w("No message in the bundle names the pair together with a suspicion term. The candidate rests on the rule alone.")
    if later:
        w("")
        w("Messages dated after the last flag that name the pair (not interpreted, a person must read them):")
        w("")
        for u in later:
            w(f"- {cite(u)}: \"{u['text'].replace('`', chr(39))}\"")
    if ev["other"] or ev["renewal"]:
        w("")
        w(f"Other lines in the bundle that name the label (listed so nothing is hidden, not used in the arithmetic, a person decides relevance): {cites(ev['renewal'] + ev['other'])}.")
    w("")
    w("## 7. Could not verify")
    w("")
    docs = sorted(p.relative_to(data).as_posix() for p in data.rglob("*") if p.is_file() and has_any(p.name, CFG["closing_document_terms"]))
    if docs:
        w(f"Files whose names suggest a closing document exist in the bundle ({', '.join(docs)}). This script does not read them. A person must check them.")
    else:
        w("No file in the bundle is named as an invoice, contract, ledger, statement or payment record, so none of the items below can be closed from the bundle.")
    w("")
    names = " and ".join(labels)
    k = 1

    def item(what, closes):
        nonlocal k
        w(f"{k}. {what} Closed by: {closes}")
        k += 1

    item("Whether the two rows are one contract or two.",
         f"the vendor invoice or invoices and the order form for {names} covering {period}. Ask: {ask}.")
    item("Whether the charge was entered twice or paid twice.",
         f"the accounts payable ledger for the vendor and the bank or card statement for {period}. Ask: {ask}.")
    item("Whether the posted amount equals the invoiced amount.", "the same invoice.")
    renewal = f" Lines that mention renewal for this label: {cites(ev['renewal'])}. They describe the subscription, not whether the repeat recurs." if ev["renewal"] else ""
    item(f"Whether the same repeat exists in any other {unit}.{renewal}",
         f"the P&L extracts or general ledger vendor detail for the other {unit}s, and the contract term.")
    if ev["thread"]:
        export = [u for u in units if u["kind"] == "line" and re.search(CFG["export_date_pattern"], u["text"])]
        asof = f" The export header {cites(export)} dates the bundle, and nothing in it is later." if export else ""
        if later:
            item(f"What the later message(s) mean for the status: {cites(later)}.{asof}",
                 f"a person reading them, then asking {', '.join(people)}.")
        else:
            item(f"Whether it has been resolved since. The last message in the thread is {cite(ev['thread'][-1])}.{asof}",
                 f"asking {', '.join(people)} whether the invoice came back.")
    caveats = [u for u in units if u["kind"] == "line" and has_any(u["text"], CFG["caveat_terms"])]
    if caveats:
        item("Whether the P&L extract is final. The bundle carries a caveat on finance figures: "
             + ", ".join(f"{cite(u)} \"{u['text'].strip('*')}\"" for u in caveats) + ".",
             f"the published final P&L for {period} from the finance team.")
    item("Whether anything is recoverable under reading R2.", "the contract terms and the vendor account manager.")
    if sub is not None and sub["amount"] != base:
        item(f"Why the stated subtotal {cite_row(pnl, sub)} does not equal the sum of the rows.",
             "the finance team's working for the subtotal.")
    for r in unparsed:
        item(f"The amount on {cite_row(pnl, r)} is not a plain number ({r['raw']!r}) and is left out of every sum.",
             "the finance team stating the amount in " + cur + ".")
    for e, l in near:
        item(f"{cite_row(pnl, e)} and {cite_row(pnl, l)} have similar labels but different amounts. Not counted.",
             "the invoices for both rows.")
    w("")
    w("## 8. Objections a CFO would raise")
    w("")
    w(f"- **Is this a double entry or a double payment?** The bundle cannot say. The P&L is a posted extract and there is no payment record. Section 5 gives the value under each reading. That is why the headline says at risk, not saved.")
    w(f"- **Could the two rows be two real contracts?** Yes. In favour of one contract: equal amounts, near-identical labels"
      + (", identical Notes text" if all(e["notes"] and e["notes"] == l["notes"] for e, l, _ in repeats) else "")
      + (", and the flag raised in section 6" if ev["flagged"] else "")
      + ". Against: "
      + ("the labels are not identical, which is also what a second product or plan would look like" if any(e["label"] != l["label"] for e, l, _ in repeats)
         else "nothing in the bundle, which is not proof")
      + ". If there are two contracts the number is 0.")
    w(f"- **Is annualising justified?** Not from this bundle. It holds one {unit}. The {money(year)} {cur} figure is ASSUMPTION A3 and is kept out of the headline.")
    w(f"- **Is it a saving or a P&L correction?** Under R1 it is a correction with no cash effect. Under R2 it is cash, recoverable only if the vendor agrees. It is not called a saving anywhere in this worksheet.")
    if later:
        w(f"- **Finance already knows this.** Yes, see section 6. Later messages name the pair ({cites(later)}), so it may already be settled. Read them before acting on the number.")
    elif ev["thread"]:
        w(f"- **Finance already knows this.** Yes, see section 6. The value here is not the discovery. It is that the item is still open at the last message in the bundle ({cite(ev['thread'][-1])}), has an exact amount, and closes with {invoice}. The same rule can be rerun on every close.")
    else:
        w("- **Does finance know about this?** No message in the bundle mentions it.")
    if share is not None:
        w(f"- **It is small.** Yes: {share}% of the category. It was chosen because every input is a cited row and one document settles it, not because of its size.")
    w(f"- **Is the baseline right?** {sub_state} The baseline is the {cat} category only"
      + (f", and {len(unparsed)} row(s) without a plain number are excluded and listed in section 7." if unparsed else ", and every row in it is a plain number."))
    w("- **Why is there no probability weighting?** Any confidence stated in the messages is a personal estimate. Multiplying by it would add an input nobody can check.")
    w("")
    w("## 9. Figures shared with the SaaS spend answer")
    w("")
    w(f"| Figure | {cur} |")
    w("|---|---|")
    w(f"| {cat}, as listed | {money(base)} |")
    w(f"| Suspected duplicate | {money(at_risk)} |")
    w(f"| {cat}, without the suspected duplicate | {money(net)} |")
    w("")
    w(f"Status of the duplicate: {status}.")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Regenerate the value number worksheet from the data folder.")
    ap.add_argument("--data", default=str(ROOT / "data"), help="bundle folder (default: data/)")
    ap.add_argument("--out", help="worksheet path (default: value/VALUE_WORKSHEET.md, only when --data is the default)")
    args = ap.parse_args()
    data = Path(args.data).resolve()
    try:
        if not data.is_dir():
            raise Stop(f"data folder not found: {data}")
        text = render(data)
    except Stop as e:
        text = f"# Value number: none. Could not build the worksheet.\n\nReason: {e}.\n"
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.stdout.write(text)
    # A run on another folder must not overwrite the committed worksheet.
    out = Path(args.out) if args.out else (HERE / "VALUE_WORKSHEET.md" if data == (ROOT / "data").resolve() else None)
    if out:
        with open(out, "w", encoding="utf-8", newline="\n") as f:  # same bytes on every OS
            f.write(text)
    else:
        print("note: --data is not the default folder, so value/VALUE_WORKSHEET.md was left untouched (use --out to write a file)", file=sys.stderr)


if __name__ == "__main__":
    main()
