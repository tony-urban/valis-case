# Builder spec: self-serve routing for creator support tickets

For a remote builder who has never seen the company. A working reference implementation is in
this folder (`run.py`, `rules.json`). Take it from a batch run on an export to a live step in
the ticketing tool.

## 1. Scope

A media company runs a support queue for the video creators it manages. The largest ticket
category by count is a creator asking to swap a thumbnail after publishing, handled by hand today.
Figures and the rows behind them are in `out/before_after.md` (regenerate, do not copy numbers).
Build: when a ticket arrives, read its category and do exactly one of three things.

| Action | When | What happens |
|---|---|---|
| `SELF_SERVE` | category equals `target_category` in `rules.json` | auto-reply with the self-serve replacement link |
| `HUMAN` | any other category in `known_categories` | stays in the human queue, untouched |
| `EXCEPTION` | anything else, or an unreadable required field | review queue, with the reason |

## 2. Data contract

Input: `data/support_tickets_q1_2026.csv`, UTF-8, comma separated, header on line 1, one ticket
per line. Extra columns are ignored. Column names are configured in `rules.json`.

| Column | Type | Rule |
|---|---|---|
| `Ticket_ID` | text | required, unique. Blank or repeated: `EXCEPTION` |
| `Date` | `YYYY-MM-DD` | required, real calendar date. Otherwise `EXCEPTION` |
| `Category` | text | required, exact match against `rules.json`. Unknown: `EXCEPTION` |
| `Handle_Minutes` | number above 0 | required. Blank or not a number: `EXCEPTION` |
| `Assigned_To` | text | optional. Blank is flagged, not an exception |
| `Status` | text | optional. Anything other than `Closed` is flagged |
| `Submitted_By` | text | not read |

Output: `out/routed_queue.csv`, one row per input row in input order, columns `ticket_id,
source, category, handle_minutes, action, reason, flags`. `source` is `<file>:L<line>`.
Reports: `out/before_after.md` and `out/time_waste.md`.

## 3. Acceptance test ("answer-complete")

From the repo root: `python3 automation/run.py --check`
Pass: the last line is `ACCEPTANCE: PASS` and the exit code is 0. Any `FAIL` gives exit code 1.
Answer-complete means all seven checks pass:

1. One output row per input row. Nothing dropped, nothing added.
2. Every row has one action and a reason.
3. The before number equals a re-sum of `Handle_Minutes` by separate code on the raw file.
4. Every `SELF_SERVE` row is the target category with readable minutes.
5. No unknown category reaches `SELF_SERVE` or `HUMAN`.
6. The report separates MEASURED, EXECUTED and MODELLED, labels each modelled input
   ASSUMPTION with a low and a high case, and has a "Not verified" list.
7. Every citation in the reports resolves to a real line or Slack message in `data/`.

Then run `--data <copy> --out <tmp> --check` on a copy with three added rows: a new category,
blank minutes, text in the minutes cell. It must pass, list all three as exceptions, and
change the totals, with no traceback.

## 4. In and out

In: rule-based routing on `Category` with rules only in `rules.json`. The exception queue and
its reasons. The before and after report on every run. Changing the target with `--category`.

Out: the self-serve replacement tool itself (needs CMS access, not available here). Reading
ticket free text or guessing a category. Machine learning or LLM calls. Automating any category
other than the target. Dashboards, a UI, dollar values for time saved. The finance month-end
reconciliation: it is the larger claimed time sink, but its three input files were not
provided (`out/time_waste.md` lists what is needed).

Constraints: Python 3 standard library only, no network, never edit `data/`, no category
names, amounts or line numbers in code. Unknown input goes to `EXCEPTION`, never to a guess.
