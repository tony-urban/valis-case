# Submission: Valis build exercise, Northwind Media

Tony Urban. Repo: https://github.com/tony-urban/valis-case (branch `main`, tag `submission`).

## Start here

1. **Read the answer:** `answers/REPORT.md`, the report to Dana. Answer first, then evidence, every figure cited to a file and line in `data/`.
2. **Run it:** `python3 tests/check.py` (Windows: `py tests/check.py`). One command runs every deliverable, resolves every citation against the raw data, recomputes every figure independently and confirms `data/` is untouched. Step-by-step guides: `RUN_ON_MAC.md`, `RUN_ON_WINDOWS.md`.
3. **See how it was built:** `BUILD_LOG.md` (timestamped, every judgment call on the dirty data), `chat_logs/` (my prompts verbatim, and three independent audits with their own logs).

Python 3.8 or later, standard library only. No installs, no API keys, no network.

## The four deliverables

| # | Deliverable | Where | Command |
|---|---|---|---|
| 1 | Ask with sources, Q1 SaaS spend and Q2 Sales hiring, each with citations and a computed confidence level | `ask/`, output in `ask/out/` | `python3 ask/ask.py` |
| 2 | One value number, CFO grade: baseline, arithmetic, source rows, what could not be verified, objections | `value/VALUE_WORKSHEET.md` | `python3 value/value.py` |
| 3 | One automation, running: support ticket router with a measured before, and a pilot measurement that turns the after into a measured figure; plus the one-page builder spec | `automation/`, spec in `automation/BUILDER_SPEC.md` | `python3 automation/run.py --check` |
| 4 | Build log | `BUILD_LOG.md` | |

Pilot measurement demo, on a synthetic test fixture that labels itself as such in its output:

```
python3 automation/run.py --data automation/demo_pilot --out /tmp/pilot_demo --check --max-target-minutes 105
```

## The answers in short

- **Q1 SaaS spend.** The Q1 2026 P&L lists 81,000 USD across 15 Software & SaaS lines. 73,500 USD if the suspected Amplitude duplicate is confirmed. HIGH confidence that this is what the P&L says, LOW that it is what was paid: the bundle has no invoice or payment record. AWS (Infrastructure) and the EUR Cloudflare line are kept out.
- **Q2 Sales hiring.** Frozen. Dana decided (Slack, 10 June; leadership sync notes, 11 June), Priya enforces on requisitions, REQ-114 is paused not killed, the 1 May roster showing it approved is stale. HIGH on the decision and owner, MEDIUM on the current state: last evidence is 15 June, two follow-up actions are past due with no completion mark.
- **Q3 time waste.** Largest claimed sink: the finance brand-deal reconciliation, about 72 hours a quarter, self-reported, inputs not in the bundle, so not built. Largest measured: the creator support queue, 70.5 hours in Q1 (5.4 a week against a claimed 40). Automated first: thumbnail re-upload tickets, 63 tickets and 1,365 logged minutes.
- **Value number.** 7,500 USD at risk in Q1 2026: a suspected duplicate SaaS line, unconfirmed. One invoice settles whether it is a duplicate line; whether it was paid twice needs the AP ledger and a bank statement. Not presented as a saving.

## Limitations, stated plainly

1. **Automation after figure.** On the case data the router runs and the before is measured, but the after in minutes is not measured: no thumbnail is swapped (the CMS is not in the bundle) and no post-launch data exists. The pilot path measures it from an export with an outcome column per ticket; its acceptance test fails on incomplete or mixed data. The demo file is synthetic and labelled as such everywhere it appears. Its figures are not Northwind results.
2. **The biggest time sink was not automated.** The finance reconciliation needs the CRM export, invoicing sheet and payout tracker, none of which is in the bundle. Building it would have meant inventing data. `answers/REPORT.md` lists what is needed.
3. **The value number is small.** 7,500 USD, and Finance had already flagged it. Chosen because every input is a cited row and one document settles it.
4. **Rule-based text reading.** No LLM at run time, by design: reproducible and stable in a live demo. Phrasing outside its rules can still be misread. The rules prefer "NOT CERTAIN, read this yourself" over a guess. Three audit rounds found such cases; each is fixed and kept as a regression check.
5. **Assumptions** (each labelled in the outputs): Slack year taken from the export header (weekday labels do not match 2026); 13 weeks a quarter; 8 hours a day for the finance claim; 14 day pilot window.
6. **Platforms.** Run on Linux with Python 3.8 and 3.13, and on Windows with Python 3.12 by the independent auditor (all checks pass, one optional Python 3.8 check skipped). Not yet run on macOS.
7. **Logs.** My prompts to Claude are verbatim. Claude's replies and its prompts to its own sub-agents are summarised in `BUILD_LOG.md`, not reproduced. Some early build log times were estimated and are marked as such; git commit times are authoritative.

## How it was built

Claude (Fable, then Opus) as orchestrator, with separate agents for each stage: importer, task-setter, scoper, three workers, tester (two rounds), presenter, final check (`pipeline/README.md`, `pipeline/04_runs.md`). I set direction and made the calls that were mine: scope, the automation framing, what goes in the logs. Then three independent audit rounds in a second AI assistant (ChatGPT, on Windows) against exported snapshots. Each round's findings were reproduced, fixed, and turned into regression checks: `tests/check.py` grew from 37 to 84 checks.

Active time: about 1 h 40 on 10 November (15:39 to 17:18), then about 1 h 15 on 11 November across the audit fix rounds, plus the audit runs themselves. Within the 8 hour box. Detail in `BUILD_LOG.md` and the commit history.
