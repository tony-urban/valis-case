# 06 Test (Tester), round 2 of 2 (final)

Written by an agent that built none of the work. Checks: `python3 tests/check.py` (standard library, one PASS or FAIL line per check, exit 0 only if all pass). Manual review: the regenerated default outputs were read again against the raw files in `data/`.

**check.py result: 50 of 54 pass, exit 1.** The four failures are real and listed below (M1r three cases, N1). Everything from round 1 still passes: checksums, three commands rerun to identical bytes, 426 citations plus 140 queue rows resolved, independent arithmetic (81,000 / 7,500 / 73,500 USD, 140 tickets 4,230 min, target 63 tickets 1,365 min), cross-stream figures, fresh-file run, hygiene. New in round 2: 17 regression and adversarial checks (section 8 of the script). Python 3.8 and 3.9 are not installed here: check 7d is static only (3.8 grammar plus a scan for newer calls). No real run on those versions happened. Committed outputs are as the default commands produce them, `data/` matches its checksums.

## 1. Round 1 defects, re-verified

| ID | Status | How reproduced |
|---|---|---|
| B1 Python 3.10 call in `ask.py` | FIXED (static) | `ask/ask.py:735` now uses `open(..., newline="\n")`. Check 7d passes on 6 files. Not run on 3.8 or 3.9. |
| M1 Q2 wrong state on a fresh Slack message | PARTLY | Reworded lift: now NOT CERTAIN, LOW, message printed (8b). Negated lift: stays frozen (8c). Non-owner opinion: stays frozen, shown (8d). New cases still fail: see M1r. |
| M2 later message on the duplicate ignored | FIXED | Added a Jun 16 "two separate contracts" message. Both tools now say "later message found, read it" at the top (8k). |
| M3 `ask --data` overwrites `ask/out/` | FIXED | `--out` added, `--data` alone prints only (6m). |
| M4 automation headline overstated | FIXED | Headline now says the run alone saves 0 minutes and the after figure is a scenario. The "140 before, 77 after" line is gone (8a). See section 3 for D3.4. |
| m1 approval date conflict | FIXED | `q2.md` evidence 4 reports Apr 21 against "early May" and lists it under could not verify. |
| m2 Q2 calibration wording | FIXED | Core and flag failures counted separately. Action 2 now says the person knows, the system change is not evidenced. |
| m3 Q2 noise | FIXED | Question labelled QUESTION, scope list trimmed. Side effect: the CEO's own "until pipeline recovers" is no longer in the revisit list (it is still quoted in answer line 1). |
| m4 "6 statements" | FIXED | Now "5 source lines", one self-report plus the CFO repeating it. Checked against the lines. |
| m5 currency-formatted amount | PARTLY | `ask` reads `"$11,000"` and says so (8l). `value` still drops it: see N1. |
| m6 implausible minutes, repeated ID | FIXED | 9,999 minutes and a repeated ID go to EXCEPTION and are not counted (8n). Side effect: N3. |
| m8 builder spec length and test | FIXED | 60 lines, three command-based steps. Step 3 needs a pilot export, so it cannot be run today, and the spec says so. |

Not in the fix list and unchanged: m7 (root `README.md` still says "case work not started" and lists no commands), m9 (stray `__pycache__`), O1 (repo visibility against the NDA footer).

## 2. Remaining defects

### MAJOR

**M1r. `ask` Q2 still flips to "the Sales freeze is lifted" on three kinds of message from a decision owner.** Each is one `#leadership` message from the CEO dated Jun 17, added to a copy of `data/`, run with `python3 ask/ask.py --q q2 --data <copy>`. Current state prints as lifted with MEDIUM confidence in all three:
- 8f, negation more than three words away: "We are not, despite what Tomás has been telling people in the hallway all week, lifting the freeze on Sales hiring." Same with "I never said the freeze on Sales hiring was lifted."
- 8g, conditional: "If July conversion holds we will be lifting the freeze on Sales hiring."
- 8h, another topic: "We are lifting the freeze on Engineering contractor spend as of today." Sales is not mentioned.

The README states the three-word negation window as a limit, and the quoted sentence is printed next to the claim, so a reader can catch it. It is still a wrong answer in bold. Smallest robust fix: a chat message may confirm the current state, but may never reverse it on a keyword. A reversal from chat prints NOT CERTAIN with the message quoted, unless a decision record in the notes says the same (8e shows that path works). Related, minor: a hypothetical from the CEO dated before the decision adds "LIFTED (2026-06-09)" to the sequence line, and a newer roster showing the requisition as OPEN (a word outside the vocabulary) is not reported as a conflict.

### MINOR

- **N1. `ask` and `value` disagree on the same file (8m).** With `"$11,000"` in one SaaS row, `ask` reports 81,000 as listed and `value` reports a baseline of 70,000 with "DOES NOT match". The headline 7,500 is unaffected. Fixed when `value` parses amounts the way `ask` does.
- **N2. A row with an unquoted thousands separator is misread silently.** `HubSpot,9,000,...` shifts the columns. Both tools read 9, the sum becomes 72,009, and the headline is not marked PARTIAL. The subtotal mismatch is reported and confidence is LOW, but the broken row is not named. Fixed when a row with the wrong field count is listed as unreadable.
- **N3. `before_after.md` ticket count includes rows whose minutes are excluded.** With every ticket repeated once, the headline reads "1,365 minutes on 126 tickets". Fixed when the count is the counted rows.
- **N4. `automation` needs the exact file name in `rules.json`.** A fresh file named `support_tickets_q2_2026.csv` gives a plain CANNOT RUN. `ask` and `value` use patterns. In the walkthrough: rename the file or edit one line.
- **m7, m9, O1** as in round 1.

No BLOCKER. Nothing manufactured was found in the default outputs.

## 3. D3.4 judgment: "produces a real before and after number"

As now worded, deliverable 3 produces a real before (1,365 minutes, measured, re-added by `tests/check.py` 4e) and states that the run alone saves 0 minutes. The after in minutes is a scenario on a share with no source. So D3.4 is met in tickets and not met in minutes, and no code change can fix that: no workflow in the bundle has both a measured effort figure and the system needed to change it.

**R13 applies here and only here: the data does not support a measured after number in minutes for any workflow in the bundle.** The report should say exactly that.

Strongest honest framing, using only figures the run computes:
- Executed, real: all 140 tickets (4,230 logged minutes) reach a person today. After the router, 77 tickets (2,865 minutes) are routed to a person and 63 tickets (1,365 minutes) to the self-serve path.
- Measured ceiling: the most this workflow can save is 1,365 minutes a quarter (22.8 hours, 32.3% of logged support time, 105 minutes a week). The floor, today, is 0.
- Not measured: where between 0 and 1,365 the result lands. A two week pilot export run through the same command (spec step 3) turns it into a measured after.
- Do not lead with 136.5 to 682.5 minutes. It rests on 50% and 90%, which are inputs, not findings.

## 4. Default answers, second review

- `ask/out/q2.md`: state now derives from decision owners and the decision record. Decision, current state, owner, dates and the stale roster all check against the cited lines. No overstatement found.
- `ask/out/q1.md`: unchanged in substance, "latest message" wording is now true.
- `automation/out/before_after.md`: headline is accurate. `time_waste.md` source count is accurate.
- `value/VALUE_WORKSHEET.md`: unchanged on default data.

## 5. Requirement table

| ID | Result | Evidence |
|---|---|---|
| D1.1 to D1.8 | PASS | As round 1. 140 citations in the two answers resolve and were read by hand. |
| D1.9 | PARTLY | No hardcoding, citations computed, `--out` works, removed files handled. Limit: M1r. |
| D2.1 to D2.8 | PASS | As round 1. One headline, baseline, steps, cited rows, assumptions, could not verify. N1 is on a changed file only. |
| D3.1, D3.2, D3.3 | PASS | Evidence table, one pick with runners-up, router runs on 140 rows. |
| D3.4 | PARTLY (R13) | Real before. After is real in tickets, a scenario in minutes. See section 3. |
| D3.5 to D3.9 | PASS | 60 lines, scope, real file and columns, three command-based acceptance steps, in and out. |
| D4.1 to D4.5 | PASS | Round 1 defects, fixes and the open D3 limit are logged with times. Stamps at 16:16 and 16:35 remain out of order. |
| P1, P4, P8, P9 | PASS | One folder. 15:39 to 17:01 so far. Markdown and CSV only. Checksums match. |
| P7 | PASS (static) | No third-party or network import. Compatible with 3.8 by static check only. |
| P2, P3, P5, P6, P10, P11 | NOT TESTABLE YET | No git here, `chat_logs/` and `answers/` empty, root README stale, visibility decision open. |
| R1 to R12 | PASS | Every printed figure re-derived. Assertions, measurements and assumptions are tagged. Nothing in `data/` changed. |
| R13 | APPLIED | To the after number in minutes for deliverable 3 only. Not to Q1, Q2, the value number or the Q3 ranking. |

## 6. Verdict per work stream

| WS | Verdict | Why |
|---|---|---|
| WS1 `ask/` | PASS on the answers, one open MAJOR on fresh files | Q1 and Q2 on the bundle are correct, cited and honestly graded. M1r must be fixed with the one-rule change above or said out loud in the walkthrough. R13 does not apply: the data supports both answers. |
| WS2 `automation/` | PASS, with the R13 statement | Runs, routes, measures the before, and no longer overstates. The after in minutes is not supported by the data and must be reported that way. |
| WS3 `value/` | PASS | Only N1, on a changed file. |

## Round 1 summary (16:48)

35 of 37 checks passed. One BLOCKER (B1), four MAJOR (M1 to M4), nine MINOR (m1 to m9), one open decision (O1). Verdict then: `ask/` and `automation/` back for fixes, `value/` PASS. All default answers already held against the raw sources.
