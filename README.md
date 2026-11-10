# Valis build exercise: Northwind Media

A first slice for the CEO of Northwind Media: two cited answers, one value number, one running automation and a build log, all computed from the raw bundle in `data/`.
Start with `answers/REPORT.md` (the report to the CEO), then run the commands below to regenerate everything it says.

## The four deliverables

| # | Deliverable | Where it is | The one command that runs it |
|---|---|---|---|
| 1 | Ask-with-sources slice (Q1 SaaS spend, Q2 Sales hiring) | `ask/ask.py`, answers in `ask/out/q1.md` and `ask/out/q2.md` | `python3 ask/ask.py` |
| 2 | One value number, CFO-grade | `value/value.py`, worksheet in `value/VALUE_WORKSHEET.md` | `python3 value/value.py` |
| 3 | One automation, running, plus the builder spec | `automation/run.py`, outputs in `automation/out/`, spec in `automation/BUILDER_SPEC.md` | `python3 automation/run.py --check` |
| 4 | Build log | `BUILD_LOG.md`, plus `JUDGMENTS.md` in each deliverable folder | none, it is a document |

The CEO's third question (where time is wasted, what to automate first) is answered by deliverable 3 in `automation/out/time_waste.md`.

## Quick start

Python 3.8 or later, standard library only. No installs, no API keys, no network. From the repo root:

```
python3 tests/check.py               # 54 checks, one PASS or FAIL line each, exit 0 only if all pass
python3 ask/ask.py                   # deliverable 1
python3 value/value.py               # deliverable 2
python3 automation/run.py --check    # deliverable 3, with its acceptance test
```

The same commands work on macOS, Linux and Windows. On Windows, use `python` or `py -3` if `python3` is not on the PATH.
Every run rewrites the generated outputs byte for byte the same. `tests/check.py` confirms that, and that `data/` still matches `data/CHECKSUMS.txt`.

## Layout

| Path | Contents |
|---|---|
| `data/` | The Northwind-in-a-box bundle, unmodified. Read-only. Checksums in `data/CHECKSUMS.txt`. |
| `answers/` | `REPORT.md`: the report to the CEO, answer first, every figure cited. |
| `ask/` | Deliverable 1: ask-with-sources slice. |
| `value/` | Deliverable 2: the value number worksheet and the script that reproduces it. |
| `automation/` | Deliverable 3: time-waste analysis, ticket router, before and after, one-page builder spec. |
| `BUILD_LOG.md` | Deliverable 4: timestamped build log (prompts, files, dead ends, judgment calls). |
| `pipeline/` | The agent pipeline used to solve the case, one handoff file per stage, plus the shared parser `importer.py`. |
| `tests/` | `check.py`, written by an agent that built none of the work. |
| `chat_logs/` | Exported LLM chat transcripts. |

## Runtime rules

- Python 3, standard library only. No installs, no API keys, no network, no LLM call in the shipped code.
- Reports are Markdown (plus one CSV, the routed ticket queue).
- Nothing in `data/` is ever edited. All cleaning happens in code and is logged.
- No amount, person, vendor or line number is typed into deliverable code. Vocabulary lives in `ask/config.json`, `value/config.json` and `automation/rules.json`. Citations are computed at run time.

## How the pipeline of agents was used

The case was solved by a chain of separate agents, each with its own context and one handoff file. The stages are defined in `pipeline/README.md`.

| Stage | What it produced |
|---|---|
| 01 Importer | `pipeline/importer.py` (a script, not an LLM), `pipeline/01_inventory.md`, `pipeline/index.json`: every citable line in the bundle |
| 02 Task-setter | `pipeline/02_task.md`: requirements, rules R1 to R13, the citation format |
| 03 Scoper | `pipeline/03_scope.md`: work streams, traps, cross-stream rulings |
| 04 Orchestrator | no separate file: its decisions are logged in `BUILD_LOG.md` |
| 05 Workers | one per work stream: `ask/`, `value/`, `automation/`, each with its own `JUDGMENTS.md` |
| 06 Tester | `tests/check.py` and `pipeline/06_test.md`, two rounds, the cap |
| 07 Presenter | `answers/REPORT.md` and this README |
| 08 Final check | `pipeline/08_final_check.md`: report against task, citations, no manufactured numbers |

Human decisions are marked "Decision (Tony)" in `BUILD_LOG.md`. Everything else there is an agent action.

## Walkthrough map for a 30 minute screen share

For any live change, first copy `data/` to a scratch folder and edit the copy. With `--data <folder>` the committed outputs are not touched.

| Tool | File | Functions worth opening | A fresh-file change to make live | Expected effect |
|---|---|---|---|---|
| Shared parser | `pipeline/importer.py` | `import_csv`, `import_md`, `check_totals`, `check_repeats` | none needed | defines what a citable line is for all three tools |
| Ask | `ask/ask.py` | `Bundle`, `confidence`, `q1`, `classify`, `q2` | In the copy of `slack_export.md`, add a later `#leadership` message from the CEO that lifts the Sales freeze. Run `python3 ask/ask.py --q q2 --data <folder>` | State reads NOT CERTAIN, the message is quoted, current-state confidence drops to LOW. Chat never reverses a decision record. |
| Ask | same | `q1` | Change one Software & SaaS amount in the copy of the P&L. Run `python3 ask/ask.py --q q1 --data <folder>` | The total changes and the answer says the rows no longer reconcile with the stated subtotal |
| Value | `value/value.py` | `load_pnl`, `find_repeats`, `find_evidence`, `render` | Delete one of the two lookalike rows in the copy of the P&L. Run `python3 value/value.py --data <folder>` | "No candidate found", and no number is printed |
| Automation | `automation/run.py`, `automation/analyze_time.py` | `load_tickets`, `analyse`, `route`, `check` | In the copy of the ticket log, rename one row's `Category` to something new and blank one `Handle_Minutes` cell. Run `python3 automation/run.py --data <folder> --out <tmp folder>` | Both rows go to `EXCEPTION` with a reason, totals change, no traceback |
| Automation | `automation/rules.json` | `route` | Run `python3 automation/run.py --out <tmp folder> --category "Tax form (W-9/W-8)"` | The router and the before and after report are repointed at the runner-up category |

More fresh-file cases, with the expected result of each, are listed in `ask/README.md`, `value/README.md`, `automation/README.md` and section 8 of `tests/check.py`.

## Known limits

- **Keyword rules, not understanding.** Status, role, duplicate and evidence detection are keyword and pattern rules from the config files. A new way of saying "frozen", a new topic, or a duplicate entered under an unrelated name needs a new term in the config or is missed. Where the ask tool cannot classify a later message it prints it and says NOT CERTAIN. The price of that rule: a real lift of the freeze announced only in chat reads as NOT CERTAIN until a meeting note records it.
- **Two questions only.** `ask/` answers Q1 and Q2. It is not a general question answerer.
- **Python 3.8 and 3.9 are verified by syntax only.** The code parses under the 3.8 grammar and uses no newer call. It has been run on Linux with newer Python versions only. It still has to be run once on a Mac with the stock `python3`, and it has not been run on Windows.
- **Deliverable 3 has no measured after figure in minutes.** The router runs and routes all 140 tickets. The before figure is measured. The run alone saves 0 minutes, because the self-serve thumbnail replacement it points to does not exist yet. The report gives a measured ceiling and a floor of 0, and says the bundle does not support a measured after. A two week pilot export run through the same command produces it (`automation/BUILDER_SPEC.md`, acceptance step 3).
- **The larger claimed time sink was not built.** The finance month-end reconciliation is self-reported and its three input files are not in the bundle.
- **The value number is small and Finance had already flagged it.** It is an amount at risk, suspected and unconfirmed, not a saving. It was chosen because every input is a cited row and one invoice settles it.
- **Nothing is checked against an invoice.** The bundle has no invoice, contract, payment record or FX rate, so "actually spent" stays at LOW confidence.
- **The last fixes were verified by the test suite, not by a third tester round.** `pipeline/06_test.md` records round 2 at 50 of 54. The four failing checks were fixed afterwards and the suite now passes 54 of 54 (`BUILD_LOG.md`, 17:06).
