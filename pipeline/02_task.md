# 02 Task (Task-setter)

Defines what a correct, complete submission is. Contains no analysis and no answers.
Citations follow section 5. Paths without a prefix are relative to `data/`. `repo:` means relative to the repo root. `email:(a)`, `(b)`, `(c)` are the three Valis cover email requirements. Verbatim quotes keep the source's punctuation, which is the only place an em dash may appear.

## 1. Questions to answer

| ID | Exact quote | Source | Clarification given by the CEO |
|---|---|---|---|
| Q1 | "What did we actually spend on SaaS tools last quarter?" | `CEO_QUESTIONS.md:L11`, repeated `00_START_HERE.md:L31` | Period is Q1 2026, pull from the P&L line items, say what is being paid for (`CEO_QUESTIONS.md:L13`) |
| Q2 | "Did we decide to hire in Sales or freeze hiring — what's the current state, and who owns it?" | `CEO_QUESTIONS.md:L17`, repeated `00_START_HERE.md:L32` | Three parts: where it landed, the situation right now, who is accountable (`CEO_QUESTIONS.md:L19`) |
| Q3 | "Where are we wasting the most time, and what would you automate first?" | `CEO_QUESTIONS.md:L23` | Scope is company wide: ops, finance, content, support. One workflow, and why (`CEO_QUESTIONS.md:L25`) |

Q3 is not in the brief's list of two questions (`00_START_HERE.md:L28-L32`). It is confirmed by `CEO_CONTEXT.md:L9` and maps to D3.

## 2. Deliverables and requirements

### D1. Working ask-with-sources slice (`repo:ask/`)
- D1.1 Runs on the bundle: reads `data/` at run time, no pasted-in values. `00_START_HERE.md:L28`
- D1.2 Returns an answer to Q1. `00_START_HERE.md:L28-L31`
- D1.3 Returns an answer to Q2 covering all three parts (decision, current state, owner). `00_START_HERE.md:L32`, `CEO_QUESTIONS.md:L19`
- D1.4 Every answer lists its sources, cited to the exact file and line or Slack message. `00_START_HERE.md:L29`
- D1.5 Every answer carries a calibrated confidence level with the reason for that level. `00_START_HERE.md:L29-L30`, `00_START_HERE.md:L56-L57`
- D1.6 The Q1 answer is built from the P&L line items and itemises what is being paid for. `CEO_QUESTIONS.md:L13`
- D1.7 Where sources disagree, the answer says they do not reconcile and why. `CEO_CONTEXT.md:L9`
- D1.8 Where there is no clean answer, the output says so and names what would be needed. `00_START_HERE.md:L57-L58`
- D1.9 Reproducible live, including on a fresh file of the same shape: no hardcoded line numbers, amounts or names. Citations are computed at run time. `00_START_HERE.md:L54-L55`

### D2. One value number, CFO-grade (`repo:value/`)
- D2.1 Exactly one headline number. `00_START_HERE.md:L33`
- D2.2 Derived from the bundle data, and something a CFO can act on (a cost to cut, time to save, or a leak to close). `00_START_HERE.md:L33-L34`
- D2.3 Baseline stated. `00_START_HERE.md:L34-L35`
- D2.4 Arithmetic shown step by step, and a script reproduces it from `data/`. `00_START_HERE.md:L35`
- D2.5 Exact source rows cited for every input. `00_START_HERE.md:L35`
- D2.6 Explicit list of what could NOT be verified. `00_START_HERE.md:L35`
- D2.7 Every input is labelled either sourced or assumption, so a finance reviewer can attack each one. `00_START_HERE.md:L35-L36`
- D2.8 Delivered as a named value-number worksheet. `00_START_HERE.md:L53`

### D3. One automation, shipped and running (`repo:automation/`)
- D3.1 The bundle is mined for where the most time is wasted, with cited evidence, across ops, finance, content, support. This is the answer to Q3. `00_START_HERE.md:L37`, `CEO_QUESTIONS.md:L23-L25`
- D3.2 Exactly one workflow is picked, with the reason it beats the alternatives. `00_START_HERE.md:L38`, `CEO_QUESTIONS.md:L25`
- D3.3 A working version runs end to end on this data. A design or stub does not count. `00_START_HERE.md:L38-L39`, `00_START_HERE.md:L41-L42`
- D3.4 It produces a real before and after number. `00_START_HERE.md:L39`
- D3.5 A builder spec exists, one page, written for a remote builder. `00_START_HERE.md:L39-L40`
- D3.6 Spec states scope. `00_START_HERE.md:L40`
- D3.7 Spec has a data contract naming the actual files and columns. `00_START_HERE.md:L40`
- D3.8 Spec has an "answer-complete" acceptance test. `00_START_HERE.md:L41`
- D3.9 Spec states what is in and what is out. `00_START_HERE.md:L41`

### D4. Build log (`repo:BUILD_LOG.md`)
- D4.1 Running log, written as the work happens, every entry timestamped. `00_START_HERE.md:L43`
- D4.2 Records the prompts run. `00_START_HERE.md:L43`
- D4.3 Records the files created. `00_START_HERE.md:L43-L44`
- D4.4 Records dead ends. `00_START_HERE.md:L44`
- D4.5 Records every judgment call on dirty data (inconsistent, ambiguous, untrustworthy), each with a one-line reason. `00_START_HERE.md:L44-L46`

### P. Submission and packaging
- P1 One folder holding artifact, build log, value-number worksheet, builder spec. `00_START_HERE.md:L26`, `00_START_HERE.md:L53-L54`
- P2 GitHub repo shared with Valis from day one, history readable commit by commit. `email:(a)`
- P3 LLM chat logs included (`repo:chat_logs/`). `email:(b)`
- P4 Total time at most 8 hours, evidenced by build log timestamps. `00_START_HERE.md:L50`, `email:(c)`
- P5 Solo, with heavy and visible use of AI tooling. The candidate can drive, debug and explain every part. `00_START_HERE.md:L50-L52`
- P6 Walkthrough ready: each deliverable reproduces from one documented command in a 30 minute screen share. `00_START_HERE.md:L54-L55`
- P7 Shipped code is Python 3 standard library only. No LLM or API calls, no installs, no network. Runs on macOS, Linux, Windows. `repo:README.md:L21-L22`
- P8 Reports are Markdown or a single self-contained HTML file. `repo:README.md:L23`
- P9 `data/` is byte identical to `data/CHECKSUMS.txt`. `repo:README.md:L9`, `repo:README.md:L24`
- P10 The CEO report answers Q1, Q2, Q3, answer first then support, MECE. `repo:pipeline/README.md:L20`, `repo:pipeline/README.md:L23`
- P11 Bundle is marked confidential and under NDA. Repo visibility must respect that. `00_START_HERE.md:L61`

## 3. Gold standard

**D1.** A reviewer runs one command and reads the answer in under a minute: answer first, then sources, then confidence. Every citation can be opened and the cited line says what the answer claims. Confidence differs between questions and the stated reason explains the difference. Conflicting or superseded sources are shown side by side, not silently dropped. When the reviewer swaps in a fresh file of the same shape, the tool either answers with new citations or states plainly what it could not parse. It never crashes and never repeats the old answer.

**D2.** A finance person can rebuild the number with a calculator from the cited rows and land on the same figure. Baseline, period and unit are unambiguous (per quarter or per year, gross or net). Each assumption is listed separately with its effect on the number if wrong. The claim is conservative: anything unverifiable is excluded from the headline or shown as a range. The "could not verify" list is specific, and names the document or person that would close each gap.

**D3.** The choice of workflow is defended with evidence of volume and effort from the bundle, and the runners-up are named with why they lost. The automation runs from one command and prints the before and after number with the rows behind it. The before figure is measured from data, not asserted. The spec fits one page, and a builder who has never seen Northwind could implement it and know when to stop. The acceptance test is binary and runnable.

**D4.** A reader can replay the day from the log alone: what was asked, what was built, what failed, what was decided. Every data-quality flag in `repo:pipeline/01_inventory.md` that touches an answer has a logged decision and reason. Dead ends and corrections are kept, not tidied away. Human decisions are distinguishable from agent actions.

**P.** Commit history shows steady progress, not one final dump. A fresh clone on macOS runs with `python3` and nothing else.

## 4. Rules that apply to everything

- R1 Every number traces to a row. `00_START_HERE.md:L56`
- R2 Confidence is honest: high where the data is clean, "I couldn't verify this" where it is not. `00_START_HERE.md:L56-L57`
- R3 Never manufacture an answer. If the data has no clean answer, say so and say what would be needed. `00_START_HERE.md:L57-L58`
- R4 True and traceable beats looking right. `00_START_HERE.md:L58-L59`
- R5 If two sources disagree, report "these do not reconcile and here is why". Never a clean number that is wrong. `CEO_CONTEXT.md:L9`
- R6 Work from raw sources and cross-check them against each other. `CEO_CONTEXT.md:L7`, `CEO_CONTEXT.md:L9`
- R7 Separate fact from assumption or opinion in every output. `CEO_CONTEXT.md:L7`
- R8 Cite the exact file and line, or Slack message, for every claim (section 5). `00_START_HERE.md:L29`
- R9 Every number is either in a cited source or produced by shown arithmetic on cited sources. `repo:pipeline/README.md:L22`
- R10 `data/` is never edited. All cleaning happens in code and is logged. `repo:README.md:L24`
- R11 Every handling decision on dirty data is logged with a one-line reason. `00_START_HERE.md:L44-L46`
- R12 Correct and well supported beats fast. `CEO_QUESTIONS.md:L29`
- R13 If a work stream fails the tester twice, the report states that the data does not support an answer. `repo:pipeline/README.md:L18`

## 5. Citation format

A citation is a backticked token. Three forms, all checked against `repo:pipeline/index.json` (a list of units with `file`, `line`, `kind`, and for messages `end_line`, `channel`, `author`, `when`).

1. Line: `` `<file>:L<n>` ``. Regex: `^(?P<file>[A-Za-z0-9_./-]+\.(md|csv)):L(?P<a>[1-9][0-9]*)(-L(?P<b>[1-9][0-9]*))?$`
   - `<file>` equals a unit's `file` value exactly (relative to `data/`, forward slashes, for example `meeting_notes/finance_review_2026-05-28.md`).
   - Resolves if a unit exists with that `file` and `line == n`, or a message unit with `line <= n <= end_line`.
2. Range: `` `<file>:L<a>-L<b>` `` with `a < b`. Resolves if both end lines resolve. Use only for contiguous lines that jointly support one claim. Cite individual rows when summing.
3. Slack message: `` `slack_export.md:L<n> [<channel> | <author> | <when>]` ``. `n` is the message header line (the unit's `line`). `<channel>`, `<author>`, `<when>` equal the unit's fields character for character, for example `` `slack_export.md:L10 [#leadership | Dana Whitfield | Mon Apr 21, 9:02 AM]` ``. Slack is always cited in this form, never as a bare line.

Further rules:
- CSV rows are cited by physical line number in the file (header of `pnl_q1_2026.csv` is L1). Where a row has a natural key, append it for the reader: `` `pnl_q1_2026.csv:L2` (Line Item: ...) ``. The key text must match the unit's `fields`.
- Slack timestamps have no year (`repo:pipeline/01_inventory.md:L94`). Quote `when` as written. Any inferred year is a logged judgment call (R11).
- Code that emits citations computes them at run time from the parsed file (D1.9).
- Non-data references use the `repo:` prefix and are not checked against the index. Blank lines and CSV header lines are not units and cannot be cited. Refer to columns by name.

## 6. Out of scope, not asked for

- Dashboards. The CEO explicitly does not want more. `CEO_CONTEXT.md:L7`
- More than one value number, or more than one automation. `00_START_HERE.md:L33`, `00_START_HERE.md:L38`
- A general chatbot or free-text question answering beyond Q1 and Q2. `00_START_HERE.md:L28-L32`
- LLM or API calls, third-party packages, hosted services, or a UI in the shipped code. `repo:README.md:L21-L23`
- Production integrations with Slack, the finance system or the ticketing tool. The bundle is static files. `00_START_HERE.md:L15-L24`
- Fixing or editing the source data. `repo:README.md:L24`
- Answering questions the CEO did not ask (for example open items raised inside the meeting notes), unless needed as evidence for Q1 to Q3 or D2.
- Organisational or strategy recommendations beyond which workflow to automate first. `CEO_QUESTIONS.md:L25`
- External benchmarks or outside data. Any figure not in the bundle is an assumption and must be labelled as one (D2.7, R7).
- Polish and extensibility ahead of a running artifact. `00_START_HERE.md:L41-L42`
