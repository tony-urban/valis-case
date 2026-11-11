# ask/ : ask-with-sources slice (deliverable 1)

Answers the CEO's two questions from the raw bundle, each with sources cited to the exact line or Slack message, a rule-based confidence level, and a list of what could not be verified.

- Q1: "What did we actually spend on SaaS tools last quarter?"
- Q2: "Did we decide to hire in Sales or freeze hiring, what's the current state, and who owns it?"

## Run

```
python3 ask/ask.py                      # both answers: printed, and written to ask/out/q1.md and ask/out/q2.md
python3 ask/ask.py --q q1               # one question
python3 ask/ask.py --data path/to/dir   # a fresh folder of the same shape: prints only, ask/out/ is not touched
python3 ask/ask.py --data path/to/dir --out some/dir   # same, and also writes q1.md and q2.md there
```

Python 3.8 or later, standard library only (run on Python 3.8.20: same bytes as on the default python3). No network, no LLM or API call, nothing to install. Same command on macOS, Linux and Windows. `data/` is read, never written.

## Files

| File | What it is |
|---|---|
| `ask.py` | The tool. One file. |
| `config.json` | All matching vocabulary: file patterns, column names, category terms, status words, role patterns, one threshold. No amounts, people, vendors or line numbers. |
| `../pipeline/shared.py`, `../pipeline/shared.json` | Not in this folder: the SaaS category rule, the subtotal rule and the repeat rule. `value/` imports the same module, so Q1 and the worksheet cannot drift apart. |
| `out/q1.md`, `out/q2.md` | Generated answers. Rewritten on every run. |
| `JUDGMENTS.md` | Every judgment call on the dirty data, timestamped, with reason and source. Dead ends included. |

## How it works

1. **Parse.** `Bundle` runs every `.csv` and `.md` in the data folder through the shared parser `pipeline/importer.py`. The result is a list of units, each with a file and a line. A citation can only be built from a unit (`cite()`), so every citation resolves by construction.
2. **Retrieve.** Deterministic filters only: the shared SaaS rule for the P&L rows, requisition IDs and team plus hiring words for chat and notes, then the rest of the same thread (same channel and day) or notes section.
3. **Cross-check.** Row sum against the stated subtotal. Suspected repeats by the shared rule in `pipeline/shared.py`: a row whose label is near-identical to an earlier row's, with an equal amount, counted once. Annual contract figures divided by four against the posted quarter. Roster status against later dated statements. Decision dates across sources. The chat list of open requisitions against the roster table.
4. **Order by date.** Slack timestamps have no year, so the year comes from the export header. The weekday is ignored. "Current" always means the Slack export date, never today.
5. **Confidence.** One rule, in `confidence()`: LOW if a core check fails, MEDIUM if only flag checks fail, HIGH if nothing fails. Each check is computed and printed as PASS or FAIL. Confidence is given per claim, so "what the P&L lists" and "what was actually paid" get different levels.
6. **Print.** Answer first, then evidence, then confidence, then could not verify with what would close each gap. Conflicting or stale sources are printed side by side with the rule that decides which governs.

## Walkthrough map for `ask.py`

| Section | Read it for |
|---|---|
| small helpers | `has` (term match), `quote` (verbatim sentences), `cite` (citation format), `money` |
| `Bundle` | parsing, the export date, dating a unit, threads |
| `confidence` | the one confidence rule |
| `q1` | rows and sum, duplicates, "final" statements, contract check, boundary and currency |
| `team_names`, `names_team` | other teams, read from the roster and org chart, for tying a decision to Sales |
| `classify` | status label of one unit: question, negation and hedge guards |
| `q2` | evidence timeline, who may change the state, owners, later unclassified messages, stale against superseding, dates, triggers, open actions |
| `main` | options, output files, the last-resort guard |

## Fresh file behaviour

Checked on temp copies of `data/` (details in the hand-off report and `JUDGMENTS.md`):

- Change a SaaS amount: the total changes and the output says the rows no longer reconcile with the stated subtotal.
- Add a SaaS row or shift lines: new row listed, all citations move with the file.
- Remove the duplicate pair: "No candidate found".
- Put a non-USD amount inside the SaaS category: the row is shown, excluded from the sum, and the as-listed claim drops to LOW.
- Add a later chat message from the decision maker that lifts the freeze, in any wording: the state reads "NOT CERTAIN. Last state set by a decision record: frozen", the message is quoted in the state line, current state LOW. Chat never reverses a decision record.
- Add a later meeting note with a decision record that lifts the freeze: the state follows it.
- The same note lifting the Engineering freeze (or naming an Engineering requisition, or under an Engineering heading): Sales stays frozen, the record is listed under "Decisions about other teams, not applied to Sales".
- The same note with no team in the line or its heading: NOT CERTAIN, the line is quoted, current state LOW. "Sales and Engineering freezes are lifted" is tied to Sales and applied.
- A P&L row in "Software implementation services": not counted, listed as outside the boundary. A third Amplitude lookalike: two repeats, each row deducted once.
- Add a later lift worded without any status word, from the decision maker: state reads NOT CERTAIN, the message is printed verbatim, current state LOW.
- Add "we are NOT lifting the freeze", a conditional ("if July holds we will be lifting") or a lift of some other freeze, from the decision maker: NOT CERTAIN, quoted, LOW. Never "lifted".
- Add "I think the freeze should be lifted" from someone who does not own the decision: state unchanged, the message is listed as not applied.
- Change the roster status or date: the roster never changes the state. A newer roster with any different status, known word or not, is reported as a conflict, current state LOW.
- A P&L row with the wrong number of fields (for example an unquoted `9,000`): named, excluded, headline starts with PARTIAL.
- Add a later message about the duplicate pair: status becomes "suspected, later message found, read it", in the headline too.
- Remove the P&L, the roster, the Slack export or the notes: a plain "Cannot answer, needed: ..." or a degraded answer that says what is missing. Exit code 0, no traceback.

## Limits (read before trusting it on a new bundle)

- It answers these two questions only. It is not a general question answerer.
- Status and role detection is keyword and pattern matching from `config.json`, with four guards for Q2:
  - A decision record in the meeting notes sets the state. A chat message from the named decision maker or enforcer may confirm that state. It may never reverse it: if it reads as a different state it is quoted, not applied, the state line says NOT CERTAIN and confidence is LOW. With no decision record at all, the state is reported as "stated in chat by a decision owner, not confirmed by a decision record", MEDIUM at best. Everyone else is listed and never applied. The roster is the baseline only.
  - A status word in a question, after a negation (within three words, same clause) or in a hedged sentence is UNCLEAR, never a state. These two heuristics now only stop a message from counting as a confirmation. They are no longer what protects against a false reversal.
  - Any later message on the topic that the tool cannot classify is printed verbatim, the state line reads NOT CERTAIN, and current-state confidence drops to LOW.
  - A later statement from a non-owner that points the other way is shown in the answer and costs a flag.
- These guards make the tool cautious, not clever. Sarcasm, a decision owner changing, or a reversal worded without any status word will land in "could not classify" at best. A new way of saying "frozen" or "I own this" needs a new term in the config.
- Q1 duplicate status has three values only: "suspected, unconfirmed" (the latest message says it is not confirmed), "suspected, later message found, read it" (any later message mentions the pair: quoted, never interpreted), "suspected, detected by rule only" (no message at all).
- Amounts written as `$11,000` or `11,000` are read as plain USD and the answer says so. Any other format is excluded, and the headline starts with PARTIAL.
- A "thread" is same channel and same day. A reply on a later day is not linked.
- If the Slack export header with the export date is missing, messages cannot be dated and are listed as undated.
- It cannot see payments. No invoice, contract or FX rate is in the bundle, so "actually spent" stays LOW until one is added.

- A decision record or a decision-owner chat message changes the Sales state only if it is tied to Sales: the line names the team term or a Sales requisition ID (mapped through the roster's requisition table), or the line names no team and its notes heading (for chat: an earlier message in the same thread) names Sales. A line naming only another team is listed and never applied. One naming no team anywhere is quoted, NOT CERTAIN, LOW.
  - Other team names are matched case-sensitively, as written in the roster summary and the org chart (spaces around `/` ignored). An abbreviation they do not contain ("Eng") is not recognised, so such a line counts as naming no team: NOT CERTAIN, never applied.
  - A Sales-headed decision line that also names another team as a word, for example "per Finance", is read as about that team and not applied. Cautious, and visible in the output.
- Q1 uses `pipeline/shared.py` for which rows are SaaS (a SaaS term as a whole word in the category: "Software implementation services" is out), for subtotal rows, and for repeats. If more than one category label matches, each is named. With several repeats, each later row is deducted once and the status is given per row.
- Cost of the confirm-only rule: a real lift announced only in chat is reported as NOT CERTAIN until a decision record exists. That is deliberate: the tool asks a person to read the message.
