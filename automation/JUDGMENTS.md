# automation/ judgment calls and dead ends (worker WS2)

Times are `date -u +%H:%M` in the worker's sandbox (Europe/London equals UTC today). The sandbox
clock read 16:27 at the first check, earlier than the launch time in `repo:BUILD_LOG.md`, so
treat these as order of events, and re-time against the commit if exact times matter.
Figures quoted here are from the run on the unmodified bundle. Every one is recomputed at run
time and printed with its rows in `out/`.
Inside these tables the pipe in a Slack citation is written `\|` so the table renders. The machine-checked citations are the ones in `out/`.

## Scope questions (WS2, 1 to 10)

| Time | Issue | Decision | Reason | Source |
|---|---|---|---|---|
| 16:27 | Q1. Support is claimed at 40 hours a week, challenged in the same thread, and a ticket log exists. | Show claim and measurement side by side: 40 claimed, 5.4 measured (4,230 minutes / 60 / 13 weeks). Tag the claim ASSERTED and the log MEASURED. | The log is the only timed source. The claim is called a possible "vibe" by a colleague. | `slack_export.md:L175 [#ops \| Liam Doyle \| Tue May 6, 11:40 AM]`, `slack_export.md:L178 [#ops \| Elena Novak \| Tue May 6, 11:52 AM]`, `support_tickets_q1_2026.csv:L2-L141` |
| 16:27 | Q2. The log covers January to March. The claims are from April to June, including "request #47 this week". | State the mismatch in the report and never present it as like for like. Compare 47 with the busiest ISO week in the log: 6 tickets of the target category, 12 of all categories. | Different periods cannot confirm or refute each other, but a gap this size has to be shown. | `slack_export.md:L4`, `slack_export.md:L192 [#ops \| Liam Doyle \| Thu May 21, 3:05 PM]` |
| 16:27 | Q3. `Handle_Minutes` is undefined and every value is a multiple of five. Unknown whether all support work is ticketed. | Use it as logged, call totals MEASURED (meaning: summed from logged rows), and list both gaps under "Not verified" with what would close them. | It is the only effort data. Rounding suggests estimates, which the reader must know. | `support_tickets_q1_2026.csv:L2-L141` (column `Handle_Minutes`) |
| 16:27 | Q4. One speaker says each swap takes "only a few minutes". | Report the log next to the quote: 15 to 25 minutes a ticket, mean 21.7. Do not pick a side. | The two may measure different things (the re-export step versus the whole ticket). | `slack_export.md:L167 [#ops \| Yuki Tanaka \| Mon Apr 28, 9:22 AM]` |
| 16:27 | Q5. By count the leader is thumbnail re-uploads (63). By minutes it is tax forms (1,555 versus 1,365). | Rank by minutes, because the question is about time. Show count as volume only. Say plainly that the pick is second on minutes. | "Most time" is a time question. Hiding that the pick is not first would be dishonest. | `support_tickets_q1_2026.csv:L2-L141`, `CEO_QUESTIONS.md:L23` |
| 16:27 | Q6. Four tickets have no assignee and two are open with minutes logged. | Count all 140 (ruling C7). Flag the six in both reports and in the `flags` column. Route them normally. | Minutes are logged on them. An assignee is an output of routing, not an input it needs. | `support_tickets_q1_2026.csv:L14`, `support_tickets_q1_2026.csv:L39`, `support_tickets_q1_2026.csv:L69`, `support_tickets_q1_2026.csv:L101`, `support_tickets_q1_2026.csv:L128`, `support_tickets_q1_2026.csv:L129` |
| 16:27 | Q7. Reconciliation effort is self-reported in days a month. Its inputs are absent. | Convert to hours a quarter: 3 days x 3 months x 8 hours = 72, with the 8 hour day labelled ASSUMPTION (ruling C6). Tag ASSERTED. Rank it first. List the files and columns needed. | Same unit lets the reader compare. It is larger than the whole measured support queue (70.5 hours), and the report says so. | `slack_export.md:L107 [#finance \| Maya Fortin \| Fri May 2, 5:10 PM]`, `slack_export.md:L113 [#finance \| Maya Fortin \| Fri May 2, 5:22 PM]`, `meeting_notes/finance_review_2026-05-28.md:L11`, `meeting_notes/leadership_sync_2026-06-11.md:L35` |
| 16:27 | Q8. Post-production is called the bottleneck twice, with no numbers. | One row, tagged ASSERTED, "no figure in the bundle", not rankable. | No volume or effort data exists. Inventing a figure breaks R3. | `slack_export.md:L33 [#leadership \| Yuki Tanaka \| Wed Apr 30, 2:05 PM]`, `slack_export.md:L249 [#people \| Yuki Tanaka \| Mon Jun 15, 2:20 PM]` |
| 16:27 | Q9. "Half my tickets would vanish." | Checked both ways: 63 of 140 = 45.0% by count, 1,365 of 4,230 = 32.3% by minutes. Roughly true by count, not by time. | The claim is about tickets. Time is what the CEO asked about. | `slack_export.md:L192 [#ops \| Liam Doyle \| Thu May 21, 3:05 PM]` |
| 16:27 | Q10. Which part of "after" did the run execute? | Three separate blocks in `out/before_after.md`: before MEASURED (1,365 minutes), EXECUTED (63 routed, 77 left with a person, 0 exceptions), MODELLED (minutes saved = routed minutes x deflection share). | The CMS is not in the bundle, so the run cannot swap a thumbnail. Routing is real, the saving is a model. | `repo:pipeline/03_scope.md` section 3 |

## Other calls

| Time | Issue | Decision | Reason | Source |
|---|---|---|---|---|
| 16:27 | Deflection share has no source in the bundle. | ASSUMPTION, low 50%, high 90%, in `rules.json`. The report also states that at 0% after equals before. | Any single figure would be invented. A range with the floor stated cannot be mistaken for a measurement. | none in bundle |
| 16:27 | Tax forms have more logged minutes than the pick. | Keep thumbnails as confirmed by the orchestrator. Print the tax figure next to it and the reasons. The target is one line in `rules.json` or `--category`. | Tax needs form status and contact data that the log lacks, and the thread defers it to Q3 with off-the-shelf services. | `slack_export.md:L200 [#ops \| Liam Doyle \| Wed Jun 4, 10:10 AM]`, `slack_export.md:L203 [#ops \| Elena Novak \| Wed Jun 4, 10:25 AM]` |
| 16:27 | "No money or compliance decision in a thumbnail swap" is not in any source. | Printed as our judgment, labelled as such in the report. | R7: separate fact from opinion. | `repo:automation/rules.json` (`pick_reasons`) |
| 16:27 | Column lists for the three reconciliation files. | Listed as our proposal, labelled as not confirmed by any file. | The sources name the three systems and what drifts, not their columns. | `slack_export.md:L99 [#finance \| Maya Fortin \| Tue Apr 22, 9:43 AM]`, `meeting_notes/finance_review_2026-05-28.md:L12` |
| 16:27 | Which bad rows are exceptions? | Blank or duplicate ID, blank or unknown category, blank or invalid date, minutes blank, non-numeric or not above zero, wrong field count. Blank assignee and non-closed status are flags only. | A rule may act only on a row it can fully read. Assignee and status are not needed to route. | `repo:automation/BUILDER_SPEC.md` section 2 |
| 16:27 | Do exception rows count in the totals? (Narrowed at 16:50: repeats and implausible values no longer count.) | Yes when their minutes are readable (they stay in their category total and in the before number). No minutes are invented for unreadable cells. The modelled saving uses only rows actually routed to self-serve. | Nothing dropped, nothing invented. | `repo:pipeline/03_scope.md` WS2 done list |
| 16:27 | An unknown category in a fresh file. | It gets its own MEASURED row in the ranking and its tickets go to EXCEPTION. | It is real logged time, but no rule exists for it. | `repo:automation/rules.json` |
| 16:27 | Weeks in the quarter. | 13, from `rules.json`, labelled ASSUMPTION (ruling C6). Busiest week uses ISO weeks from the `Date` column. | Matches the other streams. The log itself touches 14 ISO weeks because the quarter starts and ends mid-week. | `repo:pipeline/03_scope.md` C6 |
| 16:27 | Slack year. | Not needed: `when` is quoted verbatim and the period comes from the export range line (ruling C1). No date is derived from a weekday. | Avoids the weekday mismatch trap entirely. | `slack_export.md:L4` |
| 16:28 | Citing rows behind sums. | Every summed row is cited individually in the last section of each report. The range form is not used for sums. | Task file section 5: cite individual rows when summing. | `repo:pipeline/02_task.md` section 5 |
| 16:28 | Evidence retrieval without hardcoding. | Keyword and number patterns per candidate live in `rules.json`. Citations and quoted numbers are computed from whatever matches. | Deterministic, and survives a fresh file. Limit: a new topic needs a new keyword. | `repo:automation/rules.json` (`candidates`) |
| 16:30 | Exit code when the input cannot be read. | Plain `CANNOT RUN` message naming the file and columns needed, exit 0, nothing written. With `--check` the exit code is 1. | Scope: never a crash, say what is needed. An acceptance test must be able to fail. | `repo:pipeline/03_scope.md` section 0 |
| 16:30 | A file that is not UTF-8. | Whole run stops with `CANNOT RUN ... saved as UTF-8`. | The shared importer reads strictly as UTF-8. Guessing an encoding risks silently wrong names. | `repo:pipeline/importer.py` (`read_lines`) |
| 16:31 | No dollar value on hours. | None anywhere in the outputs (ruling C9). | No support wage in the bundle. | `repo:pipeline/03_scope.md` C9 |
| 16:32 | Acceptance test placement. | `--check` flag on `run.py`, re-summing with the `csv` module, not the importer. | One command, and two code paths that check each other. | `repo:automation/BUILDER_SPEC.md` section 3 |

## Fix round after tester round 1 (`repo:pipeline/06_test.md`)

| Time | Issue | Decision | Reason | Source |
|---|---|---|---|---|
| 16:49 | M4. The headline read stronger than what ran. | Headline now leads with the measured before, what the run executed, and "Minutes saved by this run alone: 0". The modelled figure is labelled "Scenario, not a result" with an explicit 0% column. | Routing removes no handling time, and the self-serve replacement does not exist. | `repo:pipeline/06_test.md` M4 |
| 16:49 | M4. "140 before, 77 after" line. | Removed. | It implied a result that did not happen and contradicted the returning share. | `repo:pipeline/06_test.md` M4 |
| 16:49 | M4. Is there a fully measured and executed before and after pair? | No, and the report says so. None is invented. | `Category` is already a column in the export, so the run saves no categorisation work, and no triage or assignment time is logged. | `support_tickets_q1_2026.csv:L2-L141` (columns `Category`, `Assigned_To`) |
| 16:49 | M4. Wording "classified and routed" suggested by the orchestrator. | Printed as "validated and routed". | The run does not classify: it reads the existing category. | `repo:automation/run.py` |
| 16:49 | M4. Source of the 50% and 90% values. | Report states they have no source in the bundle and that a two week pilot would measure the share. | R7. | none in bundle |
| 16:50 | m4. "6 statements" overcounted. | Count distinct source lines carrying the number (5: 3 Slack messages from 1 author, 2 meeting-note lines) and print that all trace to one person's self-report plus the CFO repeating it. | One message matched the pattern twice. Five lines are still one witness. | `slack_export.md:L107 [#finance \| Maya Fortin \| Fri May 2, 5:10 PM]`, `meeting_notes/leadership_sync_2026-06-11.md:L35` |
| 16:50 | m6. Implausible minutes were accepted. | Upper bound per ticket in `rules.json` (`max_plausible_minutes`, 480, labelled ASSUMPTION: one 8 hour work day). Rows above it go to EXCEPTION and are not counted. | One mistyped cell must not move the before number. The bound is our input, so it is configurable and labelled. | none in bundle (largest logged value is 55) |
| 16:50 | m6. A repeated ticket ID was counted twice. | First occurrence counts. The repeat goes to EXCEPTION, is listed with its raw minutes, and adds nothing to any total. | Double counting inflates the before number. | `repo:pipeline/06_test.md` m6 |
| 16:51 | m8. Spec too long, second acceptance step was prose. | Rewritten to 60 lines or fewer. Three steps, each a command with a pass or fail result. Step 3 uses a new `--max-target-minutes N` check so the builder's own piece has a binary test on a pilot export. The spec now says the builder's job is the missing self-serve replacement. | A builder must know when to stop. | `repo:automation/BUILDER_SPEC.md` section 3 |
| 16:51 | Python version and bytecode. | Audited: no `write_text(newline=)`, `match`, run-time unions, `removeprefix` or `zip(strict=)`. Minimum stated as 3.8 in the README. Both scripts set `sys.dont_write_bytecode`. `__pycache__` removed. | Reviewers use stock macOS python3 3.9. | `repo:pipeline/06_test.md` B1, m9 |

## Final changes after tester round 2 (`repo:pipeline/06_test.md` section 3, N3, N4)

| Time | Issue | Decision | Reason | Source |
|---|---|---|---|---|
| 17:04 | D3.4. The bundle does not support a measured after figure in minutes (R13). | Headline order is now: before (all tickets reach a person), after executed (tickets and logged minutes per path), measured ceiling and floor of 0, not measured. The assumed-share table stays lower down as an illustration and no assumed share appears in the headline. | Only figures the run computes may lead. The ceiling is a sum of cited rows, the 50% and 90% are inputs. | `repo:pipeline/06_test.md` section 3 |
| 17:04 | "Routed to self-serve" could be read as "no longer needs a person". | Headline says the resolution rate of that path is unknown and that exceptions also go to a person. | The path points to a tool that does not exist yet. | `repo:pipeline/06_test.md` section 3 |
| 17:04 | Headline wording versus existing test patterns. | The target-category sentence "Before (MEASURED): ... of handling logged on ..." moved into the "Before (MEASURED)" section, and the headline keeps one line naming the scenario without figures. | `tests/check.py` 4c, 5d, 8a and 8n pin those strings and tests may not be edited. | `repo:tests/check.py` |
| 17:04 | N3. Ticket counts included rows whose minutes are not counted. | Counts printed next to a minutes figure (headline, before line, the answer lines in `time_waste.md`) are counted rows only. The action table still shows all rows. | A count and a sum on one line must describe the same rows. | `repo:pipeline/06_test.md` N3 |
| 17:04 | N4. Exact ticket file name in `rules.json`. | Replaced by `file_pattern` (`support_tickets_*.csv`). Several matches: the last by name is used, and the others are named on stdout and in both reports. | A next-quarter export must run without editing config. Last by name is the newest period under this naming. | `repo:pipeline/06_test.md` N4 |
| 17:04 | `--check` headline assertion. | Now requires the before, after, ceiling, floor, "not measured" and scenario-label phrases in the headline, and fails if an assumed share appears there. | Pins the adopted framing. | `repo:automation/run.py` |

## Dead ends and corrections

| Time | What happened | What changed |
|---|---|---|
| 16:28 | First draft cited each category's rows as a range from its first to its last line. Those ranges span other categories' rows. | Removed. Rows are cited one by one. |
| 16:28 | First draft said the pick has the "narrowest" handle-time spread. Two small categories are narrower. | Report now compares only against the leader by minutes, with both ranges printed. |
| 16:29 | First draft of the before number summed only rows routed to self-serve, so a target row in the exception queue with readable minutes would have vanished from "before" but stayed in the category total. | Before is now all target-category rows with readable minutes. The model applies only to routed rows. |
| 16:30 | Report text in the code named the support team and the reconciliation directly. | Moved to `rules.json` or made generic, so no names sit in `.py` files. |
| 16:31 | Number formatter stripped ".0" anywhere in the string. | Now strips it only at the end. |

## Parser gaps (importer not edited, worked around locally)

- `import_csv` raises `IndexError` on an empty file. Worked around: `load_tickets` checks for an empty file first.
- `import_csv` does not return the header, and a wrong field count is only visible as flag text. Worked around: header read with `importer.parse_row`, wrong-width rows detected from the flag message.
