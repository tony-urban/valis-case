# Chat logs and review logs

Everything here is kept verbatim, in the language it was written in.

| Path | What it is |
|---|---|
| `external_review_2026-11-10/AUDIT_LOG.md` | Independent audit of commit `934d741`, run by Tony in a second AI assistant (ChatGPT, per the file paths inside the log) on Windows with Python 3.12. In Russian. |
| `external_review_2026-11-10/CHAT_LOG.md` | The prompts and replies of that audit session. In Russian. |
| `external_review_2026-11-11_round2/AUDIT_LOG_round2.md` and `CHAT_LOG_round2.md` | Second independent audit, same AI assistant, of the export `b91d8a3` on Windows with Python 3.12. In Russian. |
| `external_review_2026-11-11_round3/AUDIT_LOG_round3.md` and `CHAT_LOG_round3.md` | Third and last independent audit, of export `ae1aebb`, Windows, Python 3.12. In Russian. |
| `claude_session_user_prompts.md` | Every prompt Tony sent to Claude in the main working session, verbatim, with timestamps. Claude's prompts to its own agents are not included, by Tony's decision: they are summarised in `BUILD_LOG.md`. |

## External audit: findings and what Claude found when re-running them

The audit's verdict: the report is correct on the bundle as given, the solution needs fixes before submission. Claude re-ran every finding on scratch copies of `data/` at commit `934d741`. All of them reproduce. None was caught by the two tester rounds or the final check in this repo.

| # | Audit finding | Reproduced | Note |
|---|---|---|---|
| 1 | The automation only routes tickets. No thumbnail is swapped and no after figure is measured. | Yes, already disclosed | Same limit the tester recorded under R13. The audit rates it as an unmet part of deliverable 3. |
| 2 | Pilot acceptance passes on an irrelevant export: two login tickets, `--check --max-target-minutes 0` prints ACCEPTANCE: PASS. | Yes | The check does not test that the export contains the target category or covers the pilot window. |
| 3 | Q2 applies a decision made for another team. A meeting note saying the Engineering hiring freeze is lifted makes the tool print "the Sales freeze is lifted" at MEDIUM. | Yes | Decision records are not tied to the Sales team or its requisition. Same class of defect as tester findings M1 and M1r, on a path those rounds did not cover. |
| 4 | Q1 and the value worksheet disagree on changed input. A row in a category named "Software implementation services" is counted by one tool and not the other (82,000 against 81,000). A third lookalike row is deducted as three pairs by one tool and as two repeats by the other (66,000 against 73,500). | Yes, both | Two definitions of the category and of a repeat. On the bundle as given the tools agree. |
| 5 | On Windows the suite passes 53 of 54: two generated Markdown files are written with CRLF line endings. | Yes, by code inspection | `automation/` writes with the platform default. `ask/` and `value/` already force LF. `pipeline/importer.py` has the same pattern. Not runnable here (Linux). |
| 6 | The builder spec calls `Assigned_To` and `Status` optional, the code refuses a file without them. The generated Q3 text says "Nobody timed it", which no source states. The CFO wording "closed by one invoice" is too broad: an invoice shows the charge, the ledger and bank statement show payment. | Yes | The report was already corrected on the last two points. The generated outputs and the worksheet were not. |
| 7 | `chat_logs/` was empty, some early build log times are estimates, some prompts are summarised, the repo is public while the brief says NDA. | Yes | This folder now holds the audit. The rest is open. |

## Status of the audit findings after the fix round (2026-11-11)

| # | Status | Where |
|---|---|---|
| 1 | Addressed by Tony's decision: the after figure is measured from a pilot export with an outcome column. Case data still has none, and the report says so. Demo on a labelled synthetic fixture. | `automation/`, `automation/demo_pilot/`, report Q3 |
| 2 | Fixed. Pilot acceptance requires target rows, a 14 day window and an outcome column. | `automation/run.py`, check 9g, 9h |
| 3 | Fixed. Only a decision tied to Sales changes the Sales state. Another team's decision is listed, a decision naming no team reads NOT CERTAIN. | `ask/ask.py`, checks 9a to 9c |
| 4 | Fixed at the root: one shared definition of SaaS rows and repeats, `pipeline/shared.py`, used by both tools. | checks 9d to 9f |
| 5 | Fixed. Every file written with LF, `.gitattributes` disables conversion. Not yet rerun on Windows. | check 9i, 9l |
| 6 | Fixed: optional columns honoured, wording corrected in outputs and worksheet. | checks 9j, 9k |
| 7 | Chat logs added (this folder). Repo stays public by Tony's decision. | `chat_logs/` |

Suite: 69 of 69, including a run of every command on Python 3.8.20.

## Second external audit (2026-11-11, round 2): findings and fixes

Verdict of the audit: the earlier finance and line-ending findings are fixed; three new defects and a Windows test problem. Claude reproduced every one on commit `b91d8a3` before fixing. Section 10 of `tests/check.py` holds a regression check for each; run against `b91d8a3` code, 11 of them fail, on the fix all pass.

| Finding | Fix | Check |
|---|---|---|
| Checks 9d to 9f fail on Windows: the test parser did not expect CRLF in program output. The figures themselves agreed. | The test runner normalises line endings of program output. | 10g |
| Check 9m fails when no Python 3.8 is installed, and could not find it through the Windows launcher. | Finds 3.8 via the current interpreter, uv, `python3.8` or `py -3.8`. If none, prints SKIP: never counted as a pass or a fail. Run guides say so. | 9m |
| Q2: one decision line "Engineering hiring freeze is lifted. Sales hiring remains frozen." reported the Sales freeze as lifted. | Each sentence belongs to the team it names (a sentence naming no team follows the last team named). Only the team's own sentences set its state. | 10a |
| Pilot: blank, non-numeric, negative or implausible minutes on tickets that came back to a person became a measured 0 and PASS. | A target row that cannot be read fails pilot acceptance; missing minutes are never counted as 0 (blank or 0 is allowed only on rows marked resolved by self-serve). | 10b |
| Pilot: minutes logged on tickets marked resolved by self-serve were ignored. | The after figure is all person time on target tickets: returned plus any logged on resolved rows. | 10c |
| Pilot: an invalid date on target rows still passed. | Same rule as above: an unreadable target row fails. | 10d |
| The demo CSV copied without its README lost the synthetic label, also when mixed into the case data. | Three independent signals: README line 1, a `Data_Source` column on every row, the `DEMO-` ticket ID prefix. The routed queue carries a `data_source` column. A file mixing synthetic and other rows fails pilot acceptance. | 10e, 10f |
| REPORT.md mixed billing and payment in two places. | Billed twice and paid twice are separate readings; cash paid closes with the AP ledger and the bank or card statement. | 10h |

Not changed, by design: on the case data the after figure in minutes is still not measured, and the report says so (Tony's decision of 2026-11-11 13:14, see `claude_session_user_prompts.md`).

## Third external audit (2026-11-11, round 3)

Verdict: all earlier findings fixed in the scenarios replayed (pilot, demo labelling, SaaS figures, Windows tests: 81 of 81 with one optional Python 3.8 check skipped). One defect left: a single decision sentence joining two teams with "but" or a semicolon ("Engineering hiring freeze is lifted, but Sales hiring remains frozen") still read as the Sales freeze lifted.

Fix: decisions are now read clause by clause: a semicolon, or a comma before a conjunction (but, while, whereas, although, and...), starts a new clause, and each clause belongs to the team it names. "Sales and Engineering freezes are lifted" stays one clause about both teams. Both of the auditor's sentences are in check 10a; on the `ae1aebb` code they fail, on the fix they pass. Suite: 84 of 84.

The auditor's remaining notes are disclosed limitations, not defects: no thumbnail swap in a CMS and no measured after on Northwind data; Claude's replies not reproduced verbatim in the logs.
