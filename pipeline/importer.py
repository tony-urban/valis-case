#!/usr/bin/env python3
"""Stage 1: Importer.

Reads every file under data/, turns it into addressable units (file + line),
and reports structure and mechanical data-quality flags. No interpretation:
flags describe what is in a file, never what it means.

Outputs:
  pipeline/index.json        every unit, addressable by file and line
  pipeline/01_inventory.md   human-readable inventory

Usage: python3 pipeline/importer.py [data_dir]
Standard library only.
"""
import csv
import hashlib
import io
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {"CHECKSUMS.txt", ".DS_Store"}
NUM = re.compile(r"^-?\d+(\.\d+)?$")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SLACK_MSG = re.compile(r"^\*\*(?P<author>[^*]+)\*\* — (?P<when>.+)$")


def read_lines(path):
    return path.read_text(encoding="utf-8-sig").splitlines()


def parse_row(line):
    return next(csv.reader(io.StringIO(line)), [])


def valid_date(s):
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except ValueError:
        return False


# ---------- CSV ----------

def split_sections(lines):
    """A CSV may hold several tables. Supports 'SECTION,<name>' markers and a
    metadata preamble. Returns (preamble, [(name, header_line_no, header, rows)])."""
    if not any(l.startswith("SECTION,") for l in lines):
        header = parse_row(lines[0])
        rows = [(i + 1, parse_row(l)) for i, l in enumerate(lines) if i > 0 and l.strip()]
        return [], [("(single table)", 1, header, rows)]
    preamble, sections, cur = [], [], None
    for i, l in enumerate(lines):
        n = i + 1
        if l.startswith("SECTION,"):
            cur = {"name": parse_row(l)[1], "header": None, "hline": None, "rows": []}
            sections.append(cur)
        elif not l.strip():
            continue
        elif cur is None:
            preamble.append((n, l))
        elif cur["header"] is None:
            cur["header"], cur["hline"] = parse_row(l), n
        else:
            cur["rows"].append((n, parse_row(l)))
    return preamble, [(s["name"], s["hline"], s["header"], s["rows"]) for s in sections]


def profile_table(rel, name, header, rows, units, flags):
    cols = {h: [] for h in header}
    for n, r in rows:
        rec = {h: (r[k].strip() if k < len(r) else "") for k, h in enumerate(header)}
        units.append({"file": rel, "line": n, "kind": "row", "section": name, "fields": rec})
        if len(r) != len(header):
            flags.append((rel, n, f"row has {len(r)} fields, header has {len(header)}"))
        for h, v in rec.items():
            cols[h].append((n, v))
    out = []
    for h, vals in cols.items():
        filled = [(n, v) for n, v in vals if v != ""]
        blanks = [n for n, v in vals if v == ""]
        distinct = sorted({v for _, v in filled})
        numeric = [(n, v) for n, v in filled if NUM.match(v)]
        desc = f"{len(filled)}/{len(vals)} filled, {len(distinct)} distinct"
        # mostly-numeric column: report non-numeric entries
        if filled and len(numeric) >= 0.6 * len(filled):
            desc += ", numeric"
            for n, v in filled:
                if not NUM.match(v):
                    flags.append((rel, n, f"non-numeric value in numeric column {h}: {v!r}"))
        # date-like column: report invalid dates
        datey = [(n, v) for n, v in filled if ISO_DATE.match(v)]
        if filled and len(datey) >= 0.6 * len(filled):
            desc += ", date"
            for n, v in filled:
                if not ISO_DATE.match(v):
                    flags.append((rel, n, f"non-date value in date column {h}: {v!r}"))
                elif not valid_date(v):
                    flags.append((rel, n, f"invalid calendar date in {h}: {v!r}"))
        if blanks and len(blanks) <= 0.5 * len(vals):
            for n in blanks:
                flags.append((rel, n, f"blank {h}"))
        elif blanks:
            desc += f" (blank on lines {compact(blanks)})"
        if 1 < len(distinct) <= 12 and not numeric:
            desc += ": " + ", ".join(f"{d} ({sum(1 for _, v in filled if v == d)})" for d in distinct)
        out.append((h, desc))
    return out


def compact(nums):
    return ",".join(str(n) for n in nums[:8]) + ("..." if len(nums) > 8 else "")


def check_totals(rel, header, rows, flags):
    """Mechanical arithmetic: where a row is labelled total/subtotal, compare the
    stated figure with the sum of the rows it appears to cover. Reports only."""
    if len(header) < 2:
        return
    # find the numeric column and the label column
    for vi, h in enumerate(header):
        vals = [r[vi].strip() for _, r in rows if vi < len(r)]
        if vals and sum(1 for v in vals if NUM.match(v)) >= 0.6 * len([v for v in vals if v]):
            break
    else:
        return
    li = max(0, vi - 1)
    run, group = 0.0, None
    for n, r in rows:
        label = r[li].strip() if li < len(r) else ""
        first = r[0].strip()
        val = r[vi].strip() if vi < len(r) else ""
        is_total = bool(re.search(r"\b(sub)?total\b", label, re.I)) or first.upper() == "TOTAL"
        key = first if li != 0 else None
        if key != group and not is_total:
            group, run = key, 0.0
        if is_total:
            if NUM.match(val):
                state = "matches" if abs(float(val) - run) < 0.005 else "DOES NOT match"
                flags.append((rel, n, f"stated {label or first} {val} {state} sum of preceding numeric rows in group ({run:g})"))
            else:
                flags.append((rel, n, f"{label or first} has no numeric value (cell: {val!r}); sum of preceding numeric rows is {run:g}"))
        elif NUM.match(val):
            run += float(val)


def check_repeats(rel, header, rows, flags):
    """Mechanical: label values that differ only by case/spacing/abbreviation,
    and rows whose label contains another row's label with an identical amount."""
    for ci, h in enumerate(header):
        vals = {}
        for n, r in rows:
            v = r[ci].strip() if ci < len(r) else ""
            if v and not NUM.match(v):
                vals.setdefault(v, []).append(n)
        if not (1 < len(vals) <= 40):
            continue
        names = sorted(vals)
        for a in names:
            for b in names:
                if a < b and (word_prefix(a, b) or word_prefix(b, a) or abbrev(a, b)):
                    # same amounts on the two rows?
                    extra = ""
                    ra = [r for n, r in rows if n in vals[a]]
                    rb = [r for n, r in rows if n in vals[b]]
                    if len(ra) == 1 and len(rb) == 1 and ci + 1 < len(ra[0]) and ci + 1 < len(rb[0]):
                        x, y = ra[0][ci + 1].strip(), rb[0][ci + 1].strip()
                        if x == y and NUM.match(x):
                            extra = f"; both rows carry the same amount {x}"
                    flags.append((rel, vals[b][0], f"similar values in {h}: {a!r} (line {compact(vals[a])}) and {b!r} (line {compact(vals[b])}){extra}"))


def word_prefix(a, b):
    """True when b is a followed by more words ('Amplitude' / 'Amplitude Analytics')."""
    wa, wb = a.lower().split(), b.lower().split()
    return len(wa) < len(wb) and wb[:len(wa)] == wa


def is_subseq(short, long):
    it = iter(long)
    return all(c in it for c in short)


def abbrev(a, b):
    """True when the values match word for word except that one word is an
    abbreviation of the other ('Mgmt' / 'Management')."""
    wa, wb = a.lower().split(), b.lower().split()
    if len(wa) != len(wb) or wa == wb:
        return False
    for x, y in zip(wa, wb):
        x, y = x.rstrip("."), y.rstrip(".")
        if x == y:
            continue
        short, long = sorted((x, y), key=len)
        if len(short) < 3 or short[0] != long[0] or not is_subseq(short, long):
            return False
    return True


def import_csv(path, rel, units, flags):
    lines = read_lines(path)
    if not any(l.strip() for l in lines):
        flags.append((rel, 0, "file is empty"))
        return ["Empty file: nothing to parse."]
    preamble, sections = split_sections(lines)
    info = []
    for n, l in preamble:
        units.append({"file": rel, "line": n, "kind": "meta", "text": l})
    if preamble:
        info.append("Preamble: " + "; ".join(f"L{n} `{l}`" for n, l in preamble))
    for name, hline, header, rows in sections:
        info.append(f"**Table {name}** (header L{hline}, {len(rows)} data rows, L{rows[0][0]}-L{rows[-1][0]})" if rows else f"**Table {name}** (no rows)")
        for h, d in profile_table(rel, name, header, rows, units, flags):
            info.append(f"  - `{h}`: {d}")
        check_totals(rel, header, rows, flags)
        check_repeats(rel, header, rows, flags)
    return info


# ---------- Markdown ----------

def import_md(path, rel, units, flags):
    lines = read_lines(path)
    info, heading, channel = [], "", None
    msgs, per_channel, authors = [], {}, {}
    i = 0
    while i < len(lines):
        l, n = lines[i], i + 1
        if l.startswith("#"):
            heading = l.lstrip("#").strip()
            if l.startswith("## #"):
                channel = heading
            units.append({"file": rel, "line": n, "kind": "heading", "text": heading})
        m = SLACK_MSG.match(l)
        if m and channel:
            body, j = [], i + 1
            while j < len(lines) and lines[j].strip() and not SLACK_MSG.match(lines[j]) and lines[j].strip() != "---":
                body.append(lines[j])
                j += 1
            u = {"file": rel, "line": n, "end_line": j, "kind": "message", "channel": channel,
                 "author": m["author"], "when": m["when"], "text": " ".join(body)}
            units.append(u)
            msgs.append(u)
            per_channel[channel] = per_channel.get(channel, 0) + 1
            authors[m["author"]] = authors.get(m["author"], 0) + 1
            i = j
            continue
        if l.strip() and not l.startswith("#") and l.strip() != "---":
            units.append({"file": rel, "line": n, "kind": "line", "section": heading, "text": l.strip()})
        i += 1
    heads = [u for u in units if u["file"] == rel and u["kind"] == "heading"]
    info.append("Headings: " + "; ".join(f"L{u['line']} {u['text']}" for u in heads))
    if msgs:
        info.append(f"Chat export: {len(msgs)} messages. " + ", ".join(f"{c} ({k})" for c, k in per_channel.items()))
        info.append(f"First message L{msgs[0]['line']} ({msgs[0]['when']}); last in file order L{msgs[-1]['line']} ({msgs[-1]['when']})")
        info.append("Authors: " + ", ".join(f"{a} ({k})" for a, k in sorted(authors.items(), key=lambda x: -x[1])))
        info.append("Note: message timestamps carry weekday, month, day and time but no year.")
    tables = sum(1 for k, l in enumerate(lines) if l.startswith("|") and (k == 0 or not lines[k - 1].startswith("|")))
    if tables:
        info.append(f"Markdown tables: {tables}")
    todo = [k + 1 for k, l in enumerate(lines) if "- [ ]" in l]
    if todo:
        info.append(f"Unchecked action items on lines {compact(todo)}")
    for k, l in enumerate(lines):
        if re.search(r"\|\s*—\s*\|", l) or "(see definitions note)" in l:
            flags.append((rel, k + 1, "table cell has no value (placeholder)"))
    return info


# ---------- main ----------

def main():
    data = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data"
    units, flags, sections = [], [], []
    files = sorted(p for p in data.rglob("*") if p.is_file() and p.name not in SKIP)
    for p in files:
        rel = p.relative_to(data).as_posix()
        raw = p.read_bytes()
        nlines = len(read_lines(p))
        sha = hashlib.sha256(raw).hexdigest()[:12]
        if p.suffix.lower() == ".csv":
            info = import_csv(p, rel, units, flags)
        elif p.suffix.lower() in (".md", ".txt"):
            info = import_md(p, rel, units, flags)
        else:
            info = ["Unrecognised file type: not parsed."]
            flags.append((rel, 0, "file type not parsed"))
        sections.append((rel, len(raw), nlines, sha, info))

    out_dir = ROOT / "pipeline"
    (out_dir / "index.json").write_text(json.dumps(units, ensure_ascii=False, indent=1), encoding="utf-8")

    md = ["# 01 Inventory (Importer)", "",
          "Generated by `python3 pipeline/importer.py`. Do not edit by hand.",
          "Scope: structure and mechanical checks only. No interpretation.", "",
          f"Files: {len(files)}. Addressable units in `pipeline/index.json`: {len(units)}.", "",
          "## Files", "", "| File | Bytes | Lines | SHA-256 (12) |", "|---|---|---|---|"]
    md += [f"| `{r}` | {b} | {n} | `{s}` |" for r, b, n, s, _ in sections]
    md += ["", "## Structure", ""]
    for r, _, _, _, info in sections:
        md += [f"### `{r}`", ""] + [x if x.startswith("  -") else f"- {x}" for x in info] + [""]
    md += ["## Mechanical data-quality flags", "",
           "Each flag states what is in the file at that line. What it means is for later stages.", "",
           "| # | File | Line | Flag |", "|---|---|---|---|"]
    for k, (r, n, f) in enumerate(sorted(set(flags)), 1):
        md.append(f"| {k} | `{r}` | {n or ''} | {f} |")
    (out_dir / "01_inventory.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"files={len(files)} units={len(units)} flags={len(set(flags))}")


if __name__ == "__main__":
    main()
