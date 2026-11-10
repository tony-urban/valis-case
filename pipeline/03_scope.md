# 03 Scope (Scoper)

Plans the work. Contains no solution code and no final answers. Figures quoted here are the scoper's read of the data, given only so the scope is realistic: every worker recomputes them from `data/` at run time. Requirement IDs and citation format are from `repo:pipeline/02_task.md`. All recommendations are proposals for the orchestrator and Tony to confirm.

## 0. Constraints carried into every stream

- Python 3 standard library only. No LLM, API or network. Same behaviour on macOS, Linux, Windows (`pathlib`, UTF-8 explicit, no shell calls).
- `data/` is never edited. Every script takes `--data <dir>` (default `data/`) and parses at run time.
- No hardcoded line numbers, amounts, people or line-item names in code. Column names and category keywords live in one clearly marked config block or JSON file. Citations are computed from the parsed file.
- A fresh file of the same shape must produce a new answer or a plain "could not parse X, need Y". Never a crash, never the old answer.
- Each worker writes only inside its own folder, and records judgment calls and dead ends, timestamped, in `<folder>/JUDGMENTS.md`. The orchestrator merges these into `repo:BUILD_LOG.md` (D4.4, D4.5, R11).
- No em dashes in anything written. Verbatim source quotes are the only exception.

## 1. Work streams

| WS | Folder | Objective | Depends on |
|---|---|---|---|
| WS1 | `ask/` | Ask-with-sources slice answering Q1 and Q2 with citations and calibrated confidence | none |
| WS2 | `automation/` | Q3 time-waste analysis, the one running automation with a before and after number, one-page builder spec | automation choice (section 3) |
| WS3 | `value/` | The one CFO value number: worksheet plus the script that reproduces it | value choice (section 4), rulings C2 to C5 |
| WS4 | `tests/` | Citation resolver and fresh-file smoke test over the outputs of WS1 to WS3 | output paths below only |

All four run in parallel once sections 3 to 5 are confirmed. WS4 is written against the output paths and is run for real after the other three land.

**Shared library: no new one.** `repo:pipeline/importer.py` already is the parser (`read_lines`, `split_sections`, `import_csv`, `import_md` build units in memory without writing files). Each stream imports it and builds units from `--data` at run time. Shipped code must not read `repo:pipeline/index.json`, because it goes stale the moment a fresh file is dropped in. A second library would have to be written by one worker and consumed by three others running in parallel, which the one-folder rule forbids. Workers may not edit the importer: a parser gap is reported in `JUDGMENTS.md` and worked around locally.

## 2. Stream detail

Slack pointers used below (workers must emit this full form, computed at run time):
- S-hire: `slack_export.md:L16 [#leadership | Tomás Reyes | Mon Apr 21, 9:31 AM]`, `slack_export.md:L19 [#leadership | Marcus Lindqvist | Mon Apr 21, 9:40 AM]`, `slack_export.md:L25 [#leadership | Dana Whitfield | Mon Apr 21, 9:52 AM]`
- S-freeze: `slack_export.md:L66 [#leadership | Dana Whitfield | Wed Jun 10, 8:47 AM]`, `slack_export.md:L69 [#leadership | Priya Raman | Wed Jun 10, 8:52 AM]`, `slack_export.md:L72 [#leadership | Tomás Reyes | Wed Jun 10, 9:05 AM]`, `slack_export.md:L75 [#leadership | Marcus Lindqvist | Wed Jun 10, 9:11 AM]`, `slack_export.md:L78 [#leadership | Dana Whitfield | Wed Jun 10, 9:14 AM]`
- S-people: `slack_export.md:L221 [#people | Elena Novak | Fri May 1, 4:30 PM]`, `slack_export.md:L224 [#people | Tomás Reyes | Fri May 1, 4:41 PM]`, `slack_export.md:L229 [#people | Elena Novak | Thu Jun 11, 9:30 AM]`, `slack_export.md:L235 [#people | Elena Novak | Thu Jun 11, 9:41 AM]`, `slack_export.md:L243 [#people | Elena Novak | Mon Jun 15, 2:00 PM]`
- S-saas: `slack_export.md:L44 [#leadership | Priya Raman | Tue May 12, 10:15 AM]`, `slack_export.md:L118 [#finance | Priya Raman | Wed May 14, 11:02 AM]`, `slack_export.md:L143 [#finance | Priya Raman | Mon Jun 2, 10:30 AM]`, `slack_export.md:L146 [#finance | Maya Fortin | Mon Jun 2, 10:38 AM]`, `slack_export.md:L149 [#finance | Priya Raman | Mon Jun 2, 10:45 AM]`, `slack_export.md:L152 [#finance | Maya Fortin | Mon Jun 2, 10:47 AM]`
- S-recon: `slack_export.md:L96 [#finance | Maya Fortin | Tue Apr 22, 9:41 AM]`, `slack_export.md:L99 [#finance | Maya Fortin | Tue Apr 22, 9:43 AM]`, `slack_export.md:L107 [#finance | Maya Fortin | Fri May 2, 5:10 PM]`, `slack_export.md:L110 [#finance | Priya Raman | Fri May 2, 5:18 PM]`, `slack_export.md:L113 [#finance | Maya Fortin | Fri May 2, 5:22 PM]`, `slack_export.md:L157 [#finance | Maya Fortin | Fri Jun 13, 4:55 PM]`
- S-ops: `slack_export.md:L164 [#ops | Liam Doyle | Mon Apr 28, 9:15 AM]`, `slack_export.md:L167 [#ops | Yuki Tanaka | Mon Apr 28, 9:22 AM]`, `slack_export.md:L170 [#ops | Liam Doyle | Mon Apr 28, 9:30 AM]`, `slack_export.md:L192 [#ops | Liam Doyle | Thu May 21, 3:05 PM]`, `slack_export.md:L195 [#ops | Yuki Tanaka | Thu May 21, 3:12 PM]`, `slack_export.md:L200 [#ops | Liam Doyle | Wed Jun 4, 10:10 AM]`, `slack_export.md:L203 [#ops | Elena Novak | Wed Jun 4, 10:25 AM]`
- S-40h: `slack_export.md:L175 [#ops | Liam Doyle | Tue May 6, 11:40 AM]`, `slack_export.md:L178 [#ops | Elena Novak | Tue May 6, 11:52 AM]`, `slack_export.md:L181 [#ops | Liam Doyle | Tue May 6, 11:58 AM]`, `slack_export.md:L184 [#ops | Ben Okoro | Tue May 6, 12:14 PM]`, `slack_export.md:L187 [#ops | Liam Doyle | Tue May 6, 12:20 PM]`
- S-post: `slack_export.md:L33 [#leadership | Yuki Tanaka | Wed Apr 30, 2:05 PM]`, `slack_export.md:L249 [#people | Yuki Tanaka | Mon Jun 15, 2:20 PM]`

### WS1. Ask-with-sources (`ask/`)

Requirements: D1.1 to D1.9, R1 to R9, P7, P8.

Sources for Q1: `pnl_q1_2026.csv:L9-L24` (SaaS rows and stated subtotal), `pnl_q1_2026.csv:L25-L27` (infrastructure, EUR line, blank subtotal), `meeting_notes/finance_review_2026-05-28.md:L23-L25`, `meeting_notes/finance_review_2026-05-28.md:L37`, `meeting_notes/finance_review_2026-05-28.md:L42`, S-saas, `CEO_QUESTIONS.md:L13`.
Sources for Q2: `headcount_roster.csv:L2`, `headcount_roster.csv:L22-L25`, `meeting_notes/leadership_sync_2026-06-11.md:L15-L21`, `meeting_notes/leadership_sync_2026-06-11.md:L42-L43`, `meeting_notes/leadership_sync_2026-06-11.md:L47`, `org_chart.md:L16-L17`, S-hire, S-freeze, S-people, `slack_export.md:L3-L4` (export date and range).

Questions the worker must resolve and log (Q1):
1. Two line items with near-identical names and equal amounts sit inside the stated subtotal. One person suspects a duplicate and says it is unconfirmed. Include, exclude or show both figures? Decide and justify (see C3).
2. One message calls the SaaS line "finalized" and the next message in the same thread flags a problem with it. Which statement stands, and how is that shown?
3. A renewal figure appears in Slack and in the finance review, and the finance review says the posted quarterly figure "looks higher" than the contract implies. Check the arithmetic direction yourself. Also check the renewal date against the quarter. Does it bear on Q1 at all?
4. One P&L amount is in EUR, sits in a different category, and the bundle holds no FX rate. The finance review mentions EU-billed tools and the SaaS subtotal. Is it in scope for "SaaS", and what can honestly be said about its USD value?
5. Cloud hosting sits outside the SaaS category and the CFO says not to fold it in. State the boundary used and what the broader reading would add.
6. The P&L is an accrual extract and the finance note footer calls its own figures illustrative. No invoices or contracts are in the bundle. What does that do to confidence?

Questions the worker must resolve and log (Q2):
1. The roster snapshot and later sources give different statuses for the same requisition. Which governs, on what rule (date, explicit supersession), and are both shown side by side?
2. The decision is recorded in Slack and in a meeting note with different dates, and a third message says "yesterday's leadership call". Reconcile or report as not reconciling.
3. "Who owns it" has at least four candidate roles in the sources: decision maker, enforcer, hiring manager, backfill reviewers. Name each role separately with its source.
4. Wording differs: frozen, paused, on hold, "not killed". Scope differs: net-new versus backfills, Sales versus other teams. State the scope precisely.
5. Three different revisit triggers are given. List them. Do not pick one silently.
6. "Current state" as of when? The last evidence is three days before the export date. Two action items have due dates and no completion evidence, and a late-stage candidate is unresolved. What can and cannot be verified, and what would close it?
7. The open requisitions listed in one Slack message do not match the roster table in teams or count. Tangential, but note it if "other teams unaffected" is claimed.

Method constraint: retrieval and extraction are deterministic (category and keyword filters, regex for requisition IDs and dates, date ordering, the importer's similar-label logic for duplicate detection). Confidence is computed from stated rules (for example number of independent sources, agreement, presence of unresolved flags), not typed in per question.

Files: `ask/ask.py`, `ask/README.md` (how it works, limits), `ask/JUDGMENTS.md`, generated `ask/out/q1.md` and `ask/out/q2.md`.
Run: `python3 ask/ask.py` (both answers to stdout and to `ask/out/`). Options: `--q q1|q2`, `--data <dir>`.

Done (binary):
- [ ] The command exits 0 from a fresh clone and writes both output files.
- [ ] Each answer is ordered: answer, sources, confidence with reason, not verified.
- [ ] Every citation in both outputs resolves under WS4. Slack is cited only in the full form.
- [ ] Q1 lists every SaaS line item with its amount and row citation, and its total equals the shown sum of those rows.
- [ ] Q1 shows the as-listed figure and the conflict around it. It does not print one silent clean number.
- [ ] Q2 covers decision, current state with an as-of date, and owner, each with at least one citation, and shows the stale source next to the superseding one.
- [ ] The confidence levels or reasons differ between Q1 and Q2 and come from code.
- [ ] `grep` finds no literal amounts, person names, vendor names or line numbers in `ask/ask.py`.
- [ ] Copy `data/` to a temp dir, change one SaaS amount, add one SaaS row, delete one Slack message: output changes accordingly, citations still resolve, no traceback. With the P&L removed: a plain "cannot answer, need X" and exit 0.

### WS2. Time-waste analysis, automation, builder spec (`automation/`)

Requirements: D3.1 to D3.9, Q3, R1 to R9, P7, P8.

Sources: `support_tickets_q1_2026.csv:L2-L141` (columns `Category`, `Handle_Minutes`, `Date`, `Status`, `Assigned_To`), S-ops, S-40h, S-recon, S-post, `meeting_notes/finance_review_2026-05-28.md:L11-L13`, `meeting_notes/finance_review_2026-05-28.md:L36`, `meeting_notes/leadership_sync_2026-06-11.md:L35`, `org_chart.md:L39`, `headcount_roster.csv:L14`.

Questions the worker must resolve and log:
1. A weekly hours figure for support is claimed, challenged in the same thread as possibly "a vibe", and a ticket log with handle minutes exists. Compute the measured figure and show claim and measurement side by side.
2. The ticket log covers January to March. The claims were made in April to June, including a specific weekly ticket count. State the period mismatch. Compare the claimed weekly count with the highest weekly count in the log.
3. `Handle_Minutes` has no definition in the bundle (touch time or elapsed, logged or estimated) and all values are multiples of five. Is all support work ticketed? List under not verified.
4. One speaker says each swap takes "a few minutes". What does the log show per ticket?
5. Ranking categories by ticket count and by total minutes gives a different leader. Which metric answers "most time", and why?
6. Four tickets have no assignee and two are open but carry handle minutes. Include or exclude (see C7)?
7. The finance reconciliation effort is stated in days per month by the person doing it, repeated across three closes and echoed by the CFO. It is a self-report, not a log. Its three input systems are not in the bundle. Put it in the same unit as the ticket data, with the conversion labelled as an assumption, and say what would be needed to measure it.
8. Content: post-production is called the bottleneck twice with no volume or effort data. Say so.
9. "Half my tickets would vanish" is a checkable claim. Check it by count and by minutes.
10. Which part of the "after" number did the run actually execute, and which part is modelled? Print them separately.

Files: `automation/analyze_time.py` (evidence table for Q3: every candidate, measured versus asserted, cited), `automation/run.py` (the automation), `automation/rules.json` (category to action mapping, the only place a category name may appear), `automation/BUILDER_SPEC.md` (one page: scope, data contract with real files and columns, answer-complete acceptance test, in and out), `automation/README.md`, `automation/JUDGMENTS.md`, generated `automation/out/time_waste.md`, `automation/out/routed_queue.csv`, `automation/out/before_after.md`.
Run: `python3 automation/run.py` (runs the analysis, then the automation, writes all three outputs). Options: `--data <dir>`, `--category <name>`.

Done (binary):
- [ ] The command exits 0 from a fresh clone and writes the three outputs.
- [ ] `time_waste.md` has one row per candidate workflow covering ops, finance, content and support, each tagged MEASURED or ASSERTED with citations, and names exactly one pick with the reason and the runners-up.
- [ ] The before number equals the sum of `Handle_Minutes` over the rows cited for it. A tester can re-add it by hand.
- [ ] The after number is printed with its executed and modelled parts separated, and every modelled input is labelled ASSUMPTION with a low and high case.
- [ ] `routed_queue.csv` has one row per input ticket with ticket ID, source line, action and reason. Row count equals input row count.
- [ ] Rows with an unknown category, a blank field or non-numeric minutes go to a human or exception queue. Nothing is dropped or invented.
- [ ] `BUILDER_SPEC.md` is at most one page (about 60 lines), names the real file and columns, and its acceptance test is a command with a pass or fail result.
- [ ] No amounts, names or line numbers in the `.py` files. Category names appear only in `rules.json`.
- [ ] Fresh-file test: add a ticket with a new category and one with blank minutes. No traceback, both are reported, totals change.

### WS3. Value number (`value/`)

Requirements: D2.1 to D2.8, R1 to R9, P7, P8.

Sources for the recommended candidate: `pnl_q1_2026.csv:L12`, `pnl_q1_2026.csv:L13`, `pnl_q1_2026.csv:L24`, `slack_export.md:L146 [#finance | Maya Fortin | Mon Jun 2, 10:38 AM]`, `slack_export.md:L149 [#finance | Priya Raman | Mon Jun 2, 10:45 AM]`, `slack_export.md:L152 [#finance | Maya Fortin | Mon Jun 2, 10:47 AM]`. Context only: `pnl_q1_2026.csv:L9`, `meeting_notes/finance_review_2026-05-28.md:L23`, `meeting_notes/finance_review_2026-05-28.md:L37`, `slack_export.md:L118 [#finance | Priya Raman | Wed May 14, 11:02 AM]`.

Questions the worker must resolve and log:
1. The duplicate is suspected by the analyst and the CFO, and explicitly not confirmed against the invoice. How is an unconfirmed figure presented as a headline without overclaiming? (Status label, range, or condition.)
2. Is it a cash leak (paid twice) or a reporting overstatement (entered twice, paid once)? The bundle cannot tell. State both readings and what each is worth.
3. Is the unit per quarter or per year? Annualising needs an assumption about the other three quarters. Keep the headline to what the rows support and show any annual figure as a labelled assumption.
4. The stated subtotal already includes both rows. Show baseline (as listed), adjustment and result with each row cited.
5. Name the document or person that would close each unverified item.

Files: `value/value.py`, `value/VALUE_WORKSHEET.md` (generated by the script, committed), `value/README.md`, `value/JUDGMENTS.md`.
Run: `python3 value/value.py` (prints the worksheet and rewrites `value/VALUE_WORKSHEET.md`). Option: `--data <dir>`.

Done (binary):
- [ ] The command exits 0 and regenerates the worksheet byte for byte.
- [ ] Exactly one headline number, with unit, period and status stated on the first line.
- [ ] The worksheet has these sections: baseline, arithmetic step by step, inputs table with every input tagged SOURCED (with citation) or ASSUMPTION (with effect if wrong), could not verify (each item with who or what closes it).
- [ ] A tester reproduces the headline with a calculator from the cited rows only.
- [ ] The duplicate candidate is detected by rule (similar label plus equal amount), not by name. With the pair removed from a copy of the P&L the script reports "no candidate found" instead of a number.
- [ ] Every figure shared with WS1 is identical in both outputs (checked by WS4).

### WS4. Checks (`tests/`)

Requirements: D1.4, D1.9, R8, R9, P6, P9 and final check items 2 and 3 in `repo:pipeline/README.md`.

Files: `tests/check.py`, `tests/README.md`, `tests/JUDGMENTS.md`. Run: `python3 tests/check.py`.

Done (binary):
- [ ] Runs the three stream commands, extracts every backticked citation from `ask/out/`, `automation/out/`, `automation/BUILDER_SPEC.md`, `value/VALUE_WORKSHEET.md`, and resolves each against units built in memory by the importer, using the three regex forms in section 5 of the task file.
- [ ] Verifies `data/` against `data/CHECKSUMS.txt`.
- [ ] Fresh-file smoke test: copies `data/` to a temp dir, perturbs it (shift lines, change an amount, add a row), reruns the three commands with `--data`, and asserts exit 0, changed output and resolving citations.
- [ ] Asserts the cross-stream figures in C3 match. Prints PASS or FAIL per check and exits non-zero on any FAIL.

## 3. Automation choice (proposal)

| Candidate workflow | Evidence of time wasted | Measured or asserted | Inputs present in bundle? |
|---|---|---|---|
| A. Month-end brand-deal three-way reconciliation | About 3 days per close, one analyst: S-recon, `meeting_notes/finance_review_2026-05-28.md:L11-L13`, `meeting_notes/leadership_sync_2026-06-11.md:L35` | Asserted. Self-reported, consistent over three closes, endorsed by the CFO. No time log. | No. CRM export, invoicing sheet and payout tracker are not in the bundle, and the manual steps are not yet documented (`meeting_notes/finance_review_2026-05-28.md:L36`). |
| B. Thumbnail re-upload requests | 63 of 140 Q1 tickets, about 23 hours logged: `support_tickets_q1_2026.csv:L2-L141`. Claims in S-ops. | Measured (`Handle_Minutes`), plus claims that the log does not support at the stated scale. | Ticket log yes. CMS and assets no. |
| C. Tax form (W-9/W-8) handling | 36 tickets, about 26 hours logged, the largest category by minutes. Claims in S-ops. | Measured. | Ticket log yes. Form status and creator contact data no. |
| D. "Support is drowning, 40 hrs/week" | S-40h | Claim asserted and challenged in thread. The log shows about 70 hours for the whole quarter. | Ticket log yes. |
| E. SaaS line hygiene at close (duplicate, FX, contract check) | `meeting_notes/finance_review_2026-05-28.md:L23-L25`, S-saas | No time figure anywhere. | P&L yes. Invoices and contracts no. |
| F. Post-production bottleneck | S-post | Asserted, no numbers. | None. |

**Recommendation: the creator support ticket queue, automating thumbnail re-upload requests first (B), built as a rule-driven router so the target category is one line in `rules.json`.**
Reason: B and C are the only candidates where the before figure is measured and the input file exists, which is what D3.3, D3.4 and the D3 gold standard require. B has the highest volume, the narrowest handle-time spread, needs no compliance judgment, and is the one the ops lead asks for by name.
Runners-up: A is the loudest and most credible claim, and on the scoper's read is the same order of magnitude per quarter as the whole support queue, but it is asserted and its three inputs are absent. Building it would mean manufacturing data (R3). It goes in the report as "strongest claim, cannot be run or measured from this bundle, here is what we need". C leads B on total minutes by a small margin, but the People lead has already pointed to cheap off-the-shelf services and deferred it to Q3, and the log carries no form status to drive a chaser. D is the measurement behind B and C, not a workflow. E and F have no effort evidence.
Honesty limit to state in the deliverable: with no CMS in the bundle, the run can classify and route tickets for real, while the minutes avoided are the logged minutes of routed tickets multiplied by a deflection assumption. Before is measured, after is partly modelled, and the output must say so.

## 4. Value number (proposal)

| Candidate | Supporting rows | Main attack from finance |
|---|---|---|
| V1. Suspected duplicate SaaS line: 7,500 USD in Q1 | `pnl_q1_2026.csv:L12`, `pnl_q1_2026.csv:L13`, `pnl_q1_2026.csv:L24`, `slack_export.md:L146 [#finance | Maya Fortin | Mon Jun 2, 10:38 AM]`, `slack_export.md:L149 [#finance | Priya Raman | Mon Jun 2, 10:45 AM]`, `slack_export.md:L152 [#finance | Maya Fortin | Mon Jun 2, 10:47 AM]` | Unconfirmed against the invoice. May be a double entry, not a double payment. Annualising is an assumption. |
| V2. Support hire not supported by the log: claimed 40 hours a week versus about 5.4 measured | `support_tickets_q1_2026.csv:L2-L141`, S-40h, `pnl_q1_2026.csv:L7`, `headcount_roster.csv:L18` | No requisition for this hire exists, so it is avoidance of a cost nobody approved. Blended loaded cost is not a support salary. Ticket coverage is unknown. Periods differ. |
| V3. Hours saved by the automation (about 23 hours a quarter for B) | `support_tickets_q1_2026.csv:L2-L141` | Small. Depends on a deflection assumption. A dollar value needs a rate that is not in the bundle. |
| V4. Reconciliation days recovered (about 3 days a month) | S-recon, `meeting_notes/finance_review_2026-05-28.md:L11` | Self-reported. No rows to reproduce it from. No automation exists to recover it. |

**Recommendation: V1, stated as "7,500 USD of Q1 SaaS spend is a suspected duplicate, unconfirmed, closed by one invoice".** Every input is a P&L row, the arithmetic is one subtraction, and the unverified part is specific and cheap to close.
It is deliberately not the same figure as the automation's before and after number. That one is in minutes from the ticket log and rests on a deflection assumption. V1 is in dollars from the P&L. Converting the automation's hours to dollars would add a wage assumption and produce a smaller, weaker number. The worksheet may mention the automation's hours in one line as a separate, non-additive item.

## 5. Cross-stream consistency rulings (each is a judgment call to log)

- C1 Slack year. Treat all messages as 2026 and order by month and day. Reason: the export header gives the range (`slack_export.md:L3-L4`). 43 of 66 weekday labels do not match the 2026 calendar (they match 2025), so never derive a date from the weekday. Quote `when` verbatim.
- C2 SaaS boundary. "SaaS" means rows in the P&L software and SaaS category, excluding its subtotal row. Infrastructure is reported separately and never folded in. Reason: the CEO says to use the P&L line items and the CFO draws the same line.
- C3 Duplicate pair. WS1 and WS3 both show the as-listed figure and the figure without the suspected duplicate, with the same amounts and the status "suspected, unconfirmed". Neither silently deduplicates. Reason: the source says it is unconfirmed (R5).
- C4 EUR line. Not converted, not added to any USD total, shown in EUR and listed under could not verify. Reason: no FX rate exists in the bundle and inventing one breaks R3.
- C5 Renewal versus Q1. The Q1 P&L amount stands as posted. The renewal is reported as later context with the arithmetic shown. No stream adjusts Q1 for it. Reason: the renewal closed after the quarter ended.
- C6 Time units. Q1 is 13 weeks. A work day is 8 hours and is always labelled ASSUMPTION. Reason: the bundle defines neither, and both streams that convert must match.
- C7 Ticket rows. All 140 rows count towards measured totals, including the four with no assignee and the two open ones, which are flagged. Reason: minutes are logged on them, and excluding them understates measured effort.
- C8 "Current" and "as of". The as-of date for any current-state claim is the Slack export date, not today's date. Reason: nothing in the bundle is later.
- C9 Hours to dollars. No stream puts a dollar value on hours in a headline. If shown, it uses salaries row divided by total headcount, labelled ASSUMPTION. Reason: no salary by role exists in the bundle.
- C10 Parsing. All streams build units through the importer at run time. Reason: one parser, one definition of a citable line.
- C11 Names. People and teams are printed exactly as the source row has them. No stream normalises the two spellings of one team. Reason: no stream needs the merge, and unneeded cleaning is unlogged risk.

## 6. Risks and open decisions for Tony (5)

1. **Automation target and the modelled "after".** Confirm B (thumbnails) over C (tax forms, slightly more minutes) and over A (strongest claim, no data). Accept that the after number is measured before minus a labelled deflection assumption. The alternative is a number with no assumption but no time saving in it.
2. **Value number.** Confirm V1. Its core fact is unconfirmed by the source itself. The fallback is V2, which is bigger but softer.
3. **Importer as shared library.** Shipped scripts would import `repo:pipeline/importer.py`, while `repo:pipeline/README.md` says the pipeline is not shipped code. Approve, and the orchestrator updates the README wording (or moves the parser later).
4. **Confidentiality (P11).** Still open from stage 2: the bundle footer says NDA, and the repo is planned as public.
5. **Time.** The clock started at 15:39 with an 8 hour cap. Four parallel workers plus up to two tester rounds. If WS2 fails twice, R13 applies and the report says the data does not support a runnable automation beyond routing.
