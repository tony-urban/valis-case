# 08 Final check

**Verdict: FAIL, 2 blocking findings.** Both are one-line fixes. No wrong fact, quote, title, date or number was found in the answers themselves.

Checked: `answers/REPORT.md` and `README.md` against the raw files in `data/`, with units built at run time by `pipeline/importer.py`. `python3 tests/check.py` printed 54 of 54 before and after this check. Generated outputs are byte identical to the default run (hash compared before and after).

## The seven checks

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Coverage | PASS | Q1 (amount, period, what is paid for), Q2 (decision, current state, owner), Q3 (largest time sink, what was automated first and why) and the value number (baseline, arithmetic, sources, could not verify) are all answered, answer first. Nothing asked is left unanswered. |
| 2 | Citations resolve | PASS | 92 citation tokens in the report, 92 resolved, 0 unresolved. Slack channel, author and timestamp match exactly, row keys match the unit fields. README has no data citations. |
| 3 | Citations say what is claimed | PASS, with wording notes | All 92 opened in the raw file. All 15 verbatim quotes match character for character. All titles match `org_chart.md` and `headcount_roster.csv`. All dates match. Notes N1 to N4. |
| 4 | Nothing manufactured | PASS, with one label note | Every number recomputed from the raw CSVs with the csv module. All sums, differences, shares, ratios, day counts, row counts, minimum, maximum and mean values agree. Note N5. |
| 5 | Internal consistency | PASS, with notes | Opening block matches the sections. Confidence levels and check counts match `ask/out/q1.md` and `ask/out/q2.md` exactly (Q2 current state: core 0 of 5, flag 5 of 7). No item conflicts between the two closing lists. Notes N6 to N8. |
| 6 | README accuracy | FAIL | B1 and B2. All four commands run from the repo root and do what is stated. All five walkthrough changes were tried on temp copies and behave as described. Notes N9, N10. |
| 7 | No em dash | PASS | Report: 2 occurrences, lines 46 and 101, both inside verbatim quotes. README: 0. |

## Findings

### BLOCKING

**B1. The `--data` instruction overwrites committed outputs for the automation.** Report line 129 says: "add `--data <folder>` to any of the last three commands. The committed outputs are not touched." README line 71 says: "With `--data <folder>` the committed outputs are not touched." Tested: `python3 automation/run.py --check --data <folder>` with no `--out` rewrote `automation/out/before_after.md`, `routed_queue.csv` and `time_waste.md` with the scratch data. True for `ask/ask.py` and `value/value.py`, false for `automation/run.py`. (Outputs were regenerated with the default command afterwards and match the original hash.)
- Correction, report line 129: "add `--data <folder>` to any of the last three commands. For `automation/run.py` also add `--out <scratch folder>`, otherwise `automation/out/` is overwritten. With that, the committed outputs are not touched."
- Correction, README line 71: "With `--data <folder>` (and `--out <tmp folder>` for `automation/run.py`) the committed outputs are not touched."
- Better fix in code, outside this stage: when `--data` is not the default and `--out` is not given, refuse or write to a temp folder.

**B2. `chat_logs/` is empty.** README line 43 says "`chat_logs/` | Exported LLM chat transcripts." The folder holds only `.gitkeep`. Requirement P3 (chat logs included) is not met as the repo stands.
- Correction: export the transcripts into `chat_logs/` before submission, or change README line 43 to "Exported LLM chat transcripts (added at submission, empty until then)".

### NON-BLOCKING

**N1. "Nobody timed it" is stated as fact.** Report line 9 ("self-reported and never timed") and line 66 ("Nobody timed it."). No source says it was not timed. The bundle only lacks a time log.
- Correction: line 9 "self-reported, with no time log in the bundle". Line 66 "No time log for it is in the bundle."

**N2. The claim drops the approximation.** Report lines 9, 58 and 66 say "3 days a month". Four of the five cited lines say about three: "~3 full days" (`finance_review` L11), "~3 days" (`leadership_sync` L35, Slack L157), "basically three full days" (Slack L107). Only Slack L113 says "three days a month".
- Correction: "about 3 days a month" in lines 9 and 66. The 72 hours then reads "about 72".

**N3. An unsourced reason is stated as fact.** Report line 70: "the work needs a compliance check per form". No line in the bundle says this. The next sentence labels only the thumbnail half as judgment.
- Correction: "the work probably needs a compliance check per form (my judgment, not sourced)".

**N4. Loose date attribution.** Report line 101: "the claims were made from 2026-04-21 on `slack_export.md:L4`". L4 is the export range. The earliest support claim cited is dated Apr 28 (Slack L164, L167).
- Correction: "the Slack export range starts 2026-04-21 `slack_export.md:L4`, after the log ends".

**N5. One assumption is used without its label.** Report line 101: "Measured 5.4 hours a week (4,230 minutes / 60 / 13 weeks)". The 13 weeks is labelled ASSUMPTION at line 75 and in the tool output, not here. The log itself spans 2026-01-02 to 2026-03-31, which is 12.7 weeks.
- Correction: "(4,230 minutes / 60 / 13 weeks, the weeks being an ASSUMPTION)".

**N6. Slack years are inferred and the report does not say so.** The report writes full dates for Slack messages (for example "First recorded 2026-06-10", "first mentioned 2026-05-14", "dated 2026-04-21"). Slack timestamps carry no year. The year comes from the export header L3 to L4, and 13 of the 20 distinct Slack dates carry a weekday that does not match 2026 (for example "Mon Jun 2", and 2026-06-02 is a Tuesday). The ruling is logged in `ask/JUDGMENTS.md` and `pipeline/03_scope.md` C1, so this is a disclosure gap only.
- Correction: add to line 3: "Slack messages carry no year. The year 2026 is taken from the export header `slack_export.md:L4`. Weekday labels are not used."

**N7. Bold headline stronger than the computed level.** Report line 41: "Current state as of 2026-06-18: frozen, no new Sales hiring." The tool rates this MEDIUM and the last evidence is dated 2026-06-15. The opening block and line 44 say so, the bold line does not.
- Correction: "Current state: frozen as of the last evidence, 2026-06-15 (export date 2026-06-18, confidence MEDIUM)."

**N8. Small overlaps between the two closing lists (MECE).** No conflict, but "Each appears once" is not strictly true.
- "Does not reconcile" 2 and "Could not verify" 2 are the same question (is the P&L figure final) and close with the same document. Correction: drop "Could not verify" 2 and add its citation `meeting_notes/finance_review_2026-05-28.md:L42` to "Does not reconcile" 2.
- "Does not reconcile" 4 and "Could not verify" 7 both close with the ATS status. Acceptable, one is the contradiction and one is the execution.
- "Could not verify" opens with "Gaps where the bundle has no source at all", yet items 2, 3 and 4 cite sources. Correction: "Gaps the bundle cannot close."
- "Closed by one invoice" (lines 10, 80) is the worksheet's wording, but line 93 and the worksheet section 7 say that telling entered twice from paid twice also needs the AP ledger and a statement. Correction: "one invoice settles whether it is a duplicate".

**N9. README stage table.** Line 61 says "04 Orchestrator | no separate file". `pipeline/04_runs.md` exists.
- Correction: "04 Orchestrator | `pipeline/04_runs.md`, decisions logged in `BUILD_LOG.md`".

**N10. README paths.** Every path mentioned exists, counting this file. Every function named in the walkthrough table exists in the file named.

## What was verified by hand or by throwaway script

- P&L: 15 Software & SaaS rows sum to 81,000 and equal L24. 81,000 - 7,500 = 73,500. 81,000 + 38,000 = 119,000. 7,500 / 81,000 = 9.26%, shown as 9.3%. 60,000 / 4 = 15,000, posted 12,000, lower by 3,000. 7,500 x 4 = 30,000.
- Tickets: 140 rows, 4,230 minutes (70.5 hours), dates 2026-01-02 to 2026-03-31, 140 of 140 multiples of five. Thumbnail 63 rows, 1,365 minutes (22.75 hours, shown 22.8), 15 to 25, mean 21.67. Tax form 36 rows, 1,555 minutes (25.92 hours). Rank 1 of 6 by count, rank 2 of 6 by minutes. 140 - 63 = 77, 4,230 - 1,365 = 2,865. 1,365 / 4,230 = 32.27%. 1,365 / 13 = 105. 4,230 / 60 / 13 = 5.42, which is 13.6% of 40, shown 14%. 63 / 140 = 45.0%. 72 / 22.75 = 3.16, shown 3.2. Busiest week for thumbnail tickets: 6 (ISO weeks and any rolling 7 days).
- Dates: 2026-06-15 to 2026-06-18 is 3 days. Action due dates 2026-06-13 and 2026-06-12 precede the export date.
- Walkthrough changes on temp copies: a later CEO message lifting the freeze gives NOT CERTAIN, quotes the message, current state LOW. One SaaS amount changed gives a new total and "These do not reconcile" against the subtotal. One lookalike row deleted gives "No candidate found" and no headline number. A new category and a blank minutes cell give 2 EXCEPTION rows with reasons and no traceback. `--category "Tax form (W-9/W-8)"` repoints the router (36 tickets, 1,555 minutes).

## Process note

One read-only `git status` was run by mistake while confirming B1. Nothing was staged, committed or changed by it.

## Orchestrator note after the final check (not written by the final check agent)

- B1 fixed in code: `automation/run.py` now writes to a scratch folder when `--data` is not the committed data and no `--out` is given. Report and README wording updated to match.
- B2 open by design: `chat_logs/` is filled by Tony's export at submission. README now says so.
- N1 to N9 applied to `answers/REPORT.md` and `README.md` as worded above, except the overlap in N8 between "does not reconcile" 4 and "could not verify" 7, which the check itself rated acceptable.
- After the edits: `python3 tests/check.py` 54 of 54, report citations re-resolved (see `BUILD_LOG.md`).
