# Chat logs and review logs

Everything here is kept verbatim, in the language it was written in.

| Path | What it is |
|---|---|
| `external_review_2026-11-10/AUDIT_LOG.md` | Independent audit of commit `934d741`, run by Tony in a second AI assistant (ChatGPT, per the file paths inside the log) on Windows with Python 3.12. In Russian. |
| `external_review_2026-11-10/CHAT_LOG.md` | The prompts and replies of that audit session. In Russian. |
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
