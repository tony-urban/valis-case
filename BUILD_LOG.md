# Build log

Times are Europe/London, 2026-11-10. Clock started 15:39.

| Time | Type | Entry |
|---|---|---|
| 15:39 | Prompt | Tony: read START_HERE and the Valis email instructions, set up the environment, align on deliverables, come back with a plan and questions. Explicitly no solving yet. |
| 15:40 | Action | Read START_HERE, CEO_CONTEXT, CEO_QUESTIONS, org_chart, slack_export and the three CSVs from the Claude project. |
| 15:42 | Finding | `meeting_notes/` listed in START_HERE but absent from the project upload (4 docs, 3 CSVs only). Asked Tony for the full archive. |
| 15:42 | Blocker | GitHub account not linked to the Claude session. Cannot list or push to repos. |
| 15:50 | Dead-end | Claude included first-pass observations on the three questions in its planning reply. Out of sequence: Tony had asked for setup only. Those observations are discarded and will be re-derived through the pipeline. |
| 15:55 | Decision (Tony) | New dedicated repo instead of a branch in an existing one. Reason: repo is shared with Valis from day one, and GitHub shares per repo. |
| 15:55 | Decision (Tony) | No LLM API in the shipped code. Python script first. Reason: faster to build, more stable in a live demo, no API credits. Upgrade to an LLM layer only if the algorithm proves brittle on a fresh file. |
| 15:55 | Decision (Tony) | Platform agnostic. Reviewers run macOS. Python standard library only. |
| 15:55 | Decision (Tony) | Solve the case with a multi-agent pipeline: importer, task-setter, scoper, orchestrator, workers, tester, reviewer, presenter, final check. Keep it lean, the dataset is small. |
| 16:03 | Prompt | Tony supplied the repo URL, the full archive and the three meeting notes. |
| 16:03 | Decision (Tony) | Merge final reviewer and final check into one last step after the presenter. It must confirm the report answers the task-setter's questions, every source links to an imported file, and no data is manufactured. |
| 16:03 | Decision (Tony) | Tester loop capped at 2 rounds. Reason: if two rounds cannot produce a result, the likely answer is that the data is not there. |
| 16:05 | Action | Extracted archive. 11 content files, matching the START_HERE list including all three meeting notes. Copied unmodified into `data/`. Dropped macOS metadata (`.DS_Store`, `__MACOSX/`). Wrote `data/CHECKSUMS.txt`. |
| 16:08 | Action | Created repo scaffold: README, pipeline definition, empty deliverable folders, this log. |
