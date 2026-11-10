# value/ : the one value number

One number for the CFO, with everything needed to attack it.

**Run:** `python3 value/value.py` from the repo root. It prints the worksheet and rewrites `value/VALUE_WORKSHEET.md`, byte for byte the same on every run over the same data.

**Options:** `--data <dir>` reads another bundle of the same shape. In that case the committed worksheet is left untouched and the result goes to stdout only, unless `--out <file>` is given.

## What it claims

An amount at risk, not a saving: one row in the Software & SaaS category of the P&L looks like a repeat of another row. The status is always "suspected, unconfirmed". The script cannot confirm anything, because the bundle holds no invoice, and it never upgrades the status.

## How it works

1. Reads the P&L through the shared parser (`pipeline/importer.py`) and keeps the rows of the category named in `config.json`.
2. Adds the line items and compares the result with the stated subtotal row. If they differ it says so and uses the sum of the rows.
3. Flags a row as a suspected repeat when an earlier row in the category has a near-identical label (identical, one label is the other plus extra words, or an abbreviation: the importer's own tests) and an equal amount.
4. Looks in the markdown files for a message that names the pair together with a suspicion term, and quotes that whole thread verbatim. It does not interpret the messages.
5. Writes the worksheet: headline, baseline, arithmetic, inputs tagged SOURCED or ASSUMPTION, the value under each reading, could not verify, objections.

Citations are computed from the parsed files at run time, in the format of `pipeline/02_task.md` section 5.

## Files

| File | What |
|---|---|
| `value.py` | The script. No amounts, names or line numbers in it. |
| `config.json` | All vocabulary: column names, category, subtotal and suspicion terms. |
| `VALUE_WORKSHEET.md` | Generated. Do not edit by hand. |
| `JUDGMENTS.md` | Judgment calls and dead ends, timestamped. |

## Behaviour on a fresh file

- No pair meets the rule: the worksheet says "No candidate found" and prints no number.
- A different pair, or different amounts: new number, new citations.
- A message that names the pair and is dated after the last flag: the status on line 1 becomes "suspected, later message found, read it", section 1 opens with the message quoted verbatim, and the worksheet says the number may be out of date. The script does not decide whether the message confirms or clears the duplicate. With no such message the status stays "suspected, unconfirmed".
- Similar labels with different amounts: listed for a person to check, never counted.
- An amount written with a $ sign or thousands separators: read as plain USD and listed as "read from currency formatting".
- Any other amount format (for example a euro figure): left out of every sum, named, and the baseline is marked PARTIAL at the top. Nothing is converted.
- A row whose field count differs from the header (shifted columns): named, left out of every sum, baseline marked PARTIAL at the top.
- P&L missing, empty or without the expected columns: one plain line saying what is needed, exit code 0, no traceback.

## Limits

- The rule finds lookalike rows. It cannot tell a double entry from a double payment from two real contracts. Section 5 of the worksheet values each.
- Label similarity is word based. A repeat entered under an unrelated name would be missed. Two different products that share a first word and a price would be flagged.
- Only the configured category is scanned.
- Any later message that names the label triggers the "later message" status, even if it is about something else. That is deliberate: a person reads it. Messages are ordered by month, day and time within one year (ruling C1).
- Evidence search depends on the terms in `config.json`. A thread that discusses the pair in other words is not found, and the worksheet then says the candidate rests on the rule alone.
- A quoted message that contains a backtick has it replaced by an apostrophe, so that only citations are backticked in the worksheet.
- Minimum Python 3.8, standard library only. The source parses under the 3.8 grammar and uses no call newer than 3.8. Run on Linux with Python 3.13 only, so 3.8 and 3.9 are checked by syntax and audit, not by a run.
