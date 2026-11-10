# Agent pipeline

Used to solve the case. The stage files here are working documents, not deliverables. One exception: `importer.py` is the shared parser that the shipped scripts import, so every deliverable uses one definition of a citable line. Each stage writes one short handoff file here. Tony approves each stage before the next runs.

| # | Agent | Job | Output |
|---|---|---|---|
| 1 | Importer | Structure every source file. Row counts, fields, data quality flags. No interpretation. | `01_inventory.md` |
| 2 | Task-setter | Extract requirements, the gold standard for each deliverable, and the rules. | `02_task.md` |
| 3 | Scoper | Define work streams, assign workers, set done criteria. | `03_scope.md` |
| 4 | Orchestrator | Give each worker only the context it needs. Collect results. | `04_runs.md` |
| 5 | Workers | One per work stream. | deliverable folders |
| 6 | Tester | Check each work stream against task and scope. Owns `tests/`. | `06_test.md` |
| 7 | Presenter | Report to the CEO plus packaged code. | `answers/` |
| 8 | Final check | Guard against drift in the final report. | `08_final_check.md` |

## Rules

- **Tester loop:** maximum 2 rounds back to the scoper. If a work stream still fails, the conclusion is that the data does not support an answer, and the report says so.
- **Final check** verifies three things only:
  1. Every question and deliverable in `02_task.md` is answered in the report.
  2. Every citation resolves to a file and line listed in `01_inventory.md`.
  3. Every number in the report is either in a cited source or produced by shown arithmetic on cited sources. Nothing manufactured.
- The report follows the pyramid principle (answer first, then support) and is MECE.
