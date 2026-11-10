# 06 Test (Tester), round 1 of 2

Written by an agent that built none of the work. Checks: `python3 tests/check.py` (standard library, one PASS or FAIL line per check, exit 0 only if all pass). Manual review: every cited line in the three default outputs was read against the raw files in `data/`.

**check.py result: 35 of 37 pass, exit 1.** Failing: 6m (ask overwrites `ask/out/` when run with `--data`) and 7d (`ask/ask.py` uses a call that needs Python 3.10). Passing: checksums, three commands rerun to identical bytes, 426 citations resolved (q1 47, q2 93, worksheet 35, time_waste 182, before_after 69) plus 140 queue rows, independent arithmetic (81,000 / 7,500 / 73,500 USD, 140 tickets 4,230 min, target 63 tickets 1,365 min), cross-stream figures and status wording, fresh-file run (changed amount, added SaaS row, unknown category, blank minutes, later message lifting the freeze, removed files, removed duplicate row), hygiene (em dash, imports, no names or amounts in code). Committed outputs are left as the default commands produce them.

## 1. Requirement table

| ID | Result | Evidence |
|---|---|---|
| D1.1 | PASS | Reads `data/` at run time. Perturbed copy gives a new sum (82,734) and new citations (checks 6a to 6d). |
| D1.2 | PASS | `ask/out/q1.md`: 81,000 as listed, 73,500 without the suspected duplicate, both shown. |
| D1.3 | PASS | `ask/out/q2.md`: decision, current state with as-of date, owner roles listed separately. |
| D1.4 | PASS | 140 citations in the two answers resolve. Read by hand: each cited line says what is claimed. |
| D1.5 | PASS | Levels per claim from printed checks. Q1 listed HIGH, Q1 actually spent LOW, Q2 current state MEDIUM. See m2. |
| D1.6 | PASS | 15 rows itemised with P&L notes, each amount equals the raw row (check 4b). |
| D1.7 | PASS | Salesforce direction, decision date, requisition list all reported as not reconciling. One conflict missed: m1. |
| D1.8 | PASS | "Could not verify" lists what closes each gap. P&L removed gives "Cannot answer", exit 0 (6k). |
| D1.9 | FAIL | Mechanics pass, but a fresh Slack file can produce a wrong current state or the old answer (M1, M2). |
| D2.1 | PASS | One headline: 7,500 USD at risk, Q1 2026, unconfirmed (check 5c). Annual figure kept out as A3. |
| D2.2 | PASS | From P&L rows. Framed as at risk, not a saving. Small and already known to Finance: see note N1. |
| D2.3 | PASS | Baseline table of 15 cited rows, computed sum equals stated subtotal. |
| D2.4 | PASS | Steps 1 to 5 reproduce with a calculator. Script regenerates the worksheet byte for byte (check 2). |
| D2.5 | PASS | Every input row cited. 35 citations resolve. |
| D2.6 | PASS | Seven items, each with the document or person that closes it. |
| D2.7 | PASS | I1 to I6 SOURCED, A1 to A3 ASSUMPTION with effect if wrong. |
| D2.8 | PASS | `value/VALUE_WORKSHEET.md`. |
| D3.1 | PASS | `time_waste.md` covers finance, support, ops, content. MEASURED and ASSERTED kept apart. Stats re-derived by hand. |
| D3.2 | PASS | One pick, with the fact that it is second by minutes and that the largest claim was not built, stated plainly. |
| D3.3 | PASS | Router runs end to end on 140 rows. It is a rule on an existing `Category` column: thin, see M4. |
| D3.4 | PASS | Before 1,365 min measured and re-added (4e). After is a model on an unsourced share, labelled so. Qualified: M4. |
| D3.5 | PASS | `BUILDER_SPEC.md` exists, 70 lines against a target of about 60 (m8). |
| D3.6 | PASS | Section 1, three actions. |
| D3.7 | PASS | Real file and all seven columns named with a rule each. |
| D3.8 | PASS | `python3 automation/run.py --check`, binary, seven checks. Second step is prose (m8). |
| D3.9 | PASS | Section 4. |
| D4.1 | PASS | Every row stamped. Two stamps out of order, one explained by a Correction row (m7). |
| D4.2 | PASS | Prompts recorded as one-line summaries. Verbatim text depends on P3. |
| D4.3 | PASS | Output rows name the files created. |
| D4.4 | PASS | Two dead ends in the log, more in each `JUDGMENTS.md`. |
| D4.5 | PASS | Main calls logged with reasons. Gap: m1. No tester entry yet (tester may not edit the log). |
| P1 | PASS | One repo folder holds artifact, log, worksheet, spec. |
| P2 | NOT TESTABLE YET | No git metadata in this sandbox and the tester does not run git. |
| P3 | NOT TESTABLE YET | `chat_logs/` is empty. |
| P4 | PASS | Clock started 15:39, tester round 1 finished 16:48 by the sandbox clock. |
| P5 | NOT TESTABLE YET | Depends on the live walkthrough. |
| P6 | NOT TESTABLE YET | Each folder README has its command. Root `README.md` has none and still says "case work not started" (m7). |
| P7 | FAIL | `ask/ask.py` needs Python 3.10 or later. Stock macOS `python3` is 3.9 (B1). No network or third-party import found (7b). |
| P8 | PASS | All reports are Markdown or CSV. |
| P9 | PASS | Checksums match before and after all runs. |
| P10 | NOT TESTABLE YET | `answers/` is empty. |
| P11 | NOT TESTABLE YET | Open decision: log at 16:10 says the repo can be public, the bundle footer says NDA (O1). |
| R1, R9 | PASS | Every printed figure re-derived from cited rows (checks 4a to 4f, 5e). |
| R2 | PASS | LOW where no invoice exists, HIGH only for "what the file lists". |
| R3, R4 | PASS | No figure without a source or an ASSUMPTION label found in the default outputs. |
| R5 | PASS | See D1.7. |
| R6, R7 | PASS | Raw files only. Fact, assertion and assumption tagged. |
| R8 | PASS | Check 3a and 3b. |
| R10 | PASS | See P9. |
| R11 | PASS | See D4.5. |
| R12 | PASS | Nothing found that trades correctness for speed. |
| R13 | NOT TESTABLE YET | Applies only after round 2. |

## 2. Defects

### BLOCKER

**B1. `ask/ask.py:648` crashes on Python 3.9.** `Path.write_text(..., newline="\n")` exists only from Python 3.10. The call is outside the `try`, so the result is a traceback before anything is printed or written. Reviewers run macOS, where the stock `python3` is 3.9. `value/JUDGMENTS.md` records the same trap and avoids it. Reproduced by: static check 7d. Not run on 3.9 (this sandbox has 3.11 to 3.13 only). Fixed when: the file is written with `open(path, "w", encoding="utf-8", newline="\n")`, check 7d passes, and the README states the minimum Python version.

### MAJOR

**M1. `ask` Q2 gives a wrong current state on a plausible fresh Slack file.** Reproduced by adding one `#leadership` message dated Jun 17 to a copy of `data/` and running `python3 ask/ask.py --q q2 --data <copy>`:
- "The hold on Sales hiring is over, Tomás go ahead and make the offer on REQ-114" (CEO): answer stays "frozen" and says "Nothing in the bundle is later than" Jun 15. Old answer repeated, false statement.
- "we are NOT lifting the freeze on Sales hiring" (CEO): answer says "the Sales freeze is lifted".
- "I think the freeze should be lifted" (VP Sales, not the decision maker): answer says "the Sales freeze is lifted".

The README lists negation as a limit, but the output states the wrong state in bold with MEDIUM confidence. Fixed when: (1) only a decision record or a message from the named decision maker or enforcer can change the state, (2) a negation word close to a status term blocks the label, (3) any later message that names the team or requisition and is not classified is printed as "later message, not classified, read it" and drops current state to LOW, (4) "Nothing in the bundle is later" is printed only when true.

**M2. `ask` Q1 and `value` ignore a later message that resolves the duplicate.** Reproduced by adding a `#finance` message dated Jun 16: "Amplitude and Amplitude Analytics are two separate contracts, not a duplicate." `ask` quotes it and then prints "The latest word on it is" the Jun 2 message "which says it has not been confirmed": false. `value` keeps the headline "7,500 USD at risk, unconfirmed". Fixed when: the "latest word" is the last message in the evidence list, and when any message postdates the unconfirmed one both tools say so at the top ("a later message exists, status must be read by a person") and stop asserting "unconfirmed".

**M3. `ask` overwrites committed outputs when run on other data.** `ask/out/q1.md` and `q2.md` are rewritten whatever `--data` is (check 6m; the README admits it). In the walkthrough a fresh-file run silently replaces the committed answers. Fixed when: a non-default `--data` prints only, or `--out` exists, as in `value` and `automation`.

**M4. Automation "after" is thinner than the headline reads.** (a) `before_after.md` says "Tickets that still need a person to pick them up: 140 before, 77 after routing". The same file assumes 10% to 50% of the 63 routed tickets come back, so 77 is intake only. (b) The file itself says routing alone removes no handling minutes, and the `SELF_SERVE` reply points to a tool that does not exist. (c) The 50% to 90% share has no source. All three are disclosed, none is hidden, but a reviewer pushing on "real before and after" will land here. Fixed when: the 77 line reads as queue at intake with the returning share shown next to it, and Tony confirms the framing (open decision 1 in `03_scope.md`).

**O1. Repo visibility (open decision, not a code defect).** `BUILD_LOG.md` 16:10 allows a public repo. `00_START_HERE.md:L61` marks the bundle confidential under NDA. Fixed when: Tony decides and the log records it. A private repo shared with Valis satisfies both.

### MINOR

- **m1. Q2 approval date conflict not flagged.** Slack on Apr 21 says REQ-114 is already approved (`slack_export.md` L16), the leadership note says "approved back in early May" (`leadership_sync` L15). Both are in the timeline, neither is reported as not reconciling, nor logged.
- **m2. Q2 calibration reads oddly.** "MEDIUM (1 of 6 checks pass)". Action 2 (notify People) is listed as unverified although the Jun 11 `#people` message shows People already know. What is unverified is the Greenhouse change.
- **m3. Q2 noise.** The scope list includes the May 1 roster message, a question is labelled FROZEN, and the revisit list counts the decision sentence twice.
- **m4. `time_waste.md` "6 statements".** It is 6 number matches in 5 lines (one message is counted twice), all tracing to one person's self-report plus the CFO repeating it.
- **m5. Q1 number parsing.** A SaaS amount written as `"$11,000"` is dropped from the sum and the bold headline becomes 70,000. It is flagged LOW below, but the headline should say partial. With a Q2 P&L file the Slack "$81k for Q1" still counts as a second source.
- **m6. Automation edge rows.** A 9,999 minute ticket is accepted without a flag. A repeated ticket ID goes to EXCEPTION but its minutes still count in "before".
- **m7. Log and README.** Stamps out of order at 16:16 and 16:35. Root README status is stale and lists no run commands. `tests/README.md` and `tests/JUDGMENTS.md` from the scope were not written (tester was limited to two files).
- **m8. Builder spec.** 70 lines. The second acceptance step (three added rows) is prose, not a command. `tests/check.py` 6h and 6i now cover it.
- **m9. Stray `__pycache__`** in `automation/` and `pipeline/` (ignored by git). `automation/run.py` does not switch bytecode off.

Note N1 (not a defect). The value number is 7,500 USD against 5.25M revenue, and Finance already flagged it. The worksheet says both in section 8. Expect the walkthrough to push here.

## 3. Readability and fresh-file judgment

A 30 minute walkthrough is feasible: one command per deliverable, answer first, READMEs map code to sections. `ask.py` at 650 lines and `q2.md` at 120 lines are the heavy parts. The tools behave well on changed rows, added rows, moved lines, CRLF and BOM files, reordered ticket columns and missing files. They behave badly when a new Slack message changes the meaning of an answer (M1, M2).

## 4. Verdict per work stream

| WS | Verdict | Why |
|---|---|---|
| WS1 `ask/` | Back to scope | B1, M1, M2, M3. Default answers are correct and well cited. |
| WS2 `automation/` | Back to scope (narrow) | M4 wording and framing. Everything else passes. |
| WS3 `value/` | PASS | Only its share of M2 (stale status after a later message). Fix alongside WS1 if time allows. |
