# Valis build exercise: Northwind Media

Working repo for the Valis Principal (GTM) build exercise. Status: environment set up, case work not started.

## Layout

| Path | Contents |
|---|---|
| `data/` | The Northwind-in-a-box bundle, unmodified. Read-only. Checksums in `data/CHECKSUMS.txt`. |
| `pipeline/` | Agent pipeline used to solve the case. One handoff file per stage. |
| `ask/` | Deliverable 1: ask-with-sources slice. |
| `value/` | Deliverable 2: CFO-grade value number worksheet and the script that reproduces it. |
| `automation/` | Deliverable 3: running automation and one-page builder spec. |
| `answers/` | Generated answers to the CEO questions, with citations. |
| `BUILD_LOG.md` | Deliverable 4: timestamped build log. |
| `chat_logs/` | Exported LLM chat transcripts. |
| `tests/` | Checks, including that every citation resolves to a real source line. |

## Runtime rules

- Python 3, standard library only. No installs, no API keys, no network.
- Runs the same on macOS, Linux and Windows: `python3 <script>`.
- Reports are Markdown or a single self-contained HTML file.
- Nothing in `data/` is ever edited. All cleaning happens in code and is logged.
