# 04 Runs (Orchestrator)

The orchestrator is the main Claude session. It launches one agent per stage or work stream, each in its own context, reviews what comes back, reruns the commands itself, and commits. Timings are in `BUILD_LOG.md`.

| Run | Agent | Input given | Output | Orchestrator check |
|---|---|---|---|---|
| 1 | Importer (script, not an agent) | `data/` | `01_inventory.md`, `index.json` | Slack message count verified by a second method |
| 2 | Task-setter | brief, CEO note, CEO questions, inventory | `02_task.md` | read in full |
| 3 | Scoper | task, inventory, full bundle | `03_scope.md` | automation and value proposals confirmed, tests stream moved to the tester |
| 4 | Worker WS1 | task, scope WS1, importer | `ask/` | reran `python3 ask/ask.py` |
| 5 | Worker WS2 | task, scope WS2, importer | `automation/` | reran `python3 automation/run.py --check` |
| 6 | Worker WS3 | task, scope WS3, importer | `value/` | reran `python3 value/value.py` |
| 7 | Tester round 1 | task, scope, all deliverables, raw data | `tests/check.py`, `06_test.md` | 35 of 37, defects sent back to workers 4 to 6 |
| 8 | Workers, fix round 1 | defect list | fixes in each folder | suite 37 of 37 |
| 9 | Tester round 2 (final) | fixed deliverables | `tests/check.py` extended, `06_test.md` rewritten | 50 of 54, remaining defects sent back |
| 10 | Workers, fix round 2 | defect list | fixes in each folder | suite 54 of 54, no third tester round (cap is 2) |
| 11 | Presenter | generated outputs only | `answers/REPORT.md`, root `README.md` | read in full |
| 12 | Final check | task, inventory, report | `08_final_check.md` | see that file |

Rules the orchestrator applied: workers write only inside their own folder, nobody but the orchestrator runs git, no agent edits `data/`, and the agent that tests a piece of work never wrote it.
