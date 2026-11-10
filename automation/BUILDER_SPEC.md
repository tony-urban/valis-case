# Builder spec: self-serve thumbnail replacement behind the ticket router

For a remote builder who has never seen the company. The router in this folder (`run.py`,
`rules.json`) already runs. **Your job is the missing piece behind it: the self-serve replacement
that the `SELF_SERVE` reply points to. It does not exist yet, so today the router saves 0 minutes.
The measured ceiling is the logged minutes on the self-serve path. No measured after figure exists yet.**

## 1. Scope

A media company runs a support queue for the video creators it manages. The largest ticket
category by count is a creator asking to swap a thumbnail after publishing. A person does each
swap by hand in the CMS. Figures and rows: `out/before_after.md` (regenerate, do not copy numbers).
Build: (a) a page or form where a creator replaces the thumbnail on their own published item,
(b) the router as a live step in the ticketing tool, doing exactly one of three things per ticket.

| Action | When | What happens |
|---|---|---|
| `SELF_SERVE` | category equals `target_category` in `rules.json` | auto-reply with the link to (a) |
| `HUMAN` | any other category in `known_categories` | stays in the human queue, untouched |
| `EXCEPTION` | anything else, or an unreadable required field | review queue, with the reason |

## 2. Data contract

Input: `data/support_tickets_q1_2026.csv` (found by the pattern `support_tickets_*.csv` in `rules.json`),
UTF-8, comma separated, header on line 1, one ticket per line. Extra columns are ignored.

| Column | Type | Rule |
|---|---|---|
| `Ticket_ID` | text | required. Blank or repeated: `EXCEPTION`, a repeat's minutes are not counted |
| `Date` | `YYYY-MM-DD` | required, real calendar date. Otherwise `EXCEPTION` |
| `Category` | text | required, exact match against `rules.json`. Unknown: `EXCEPTION` |
| `Handle_Minutes` | number, above 0, at most `max_plausible_minutes` | otherwise `EXCEPTION`, not counted |
| `Assigned_To`, `Status` | text | optional. Blank assignee or a status other than `Closed` is flagged. `Submitted_By` is not read |

Output: `out/routed_queue.csv`, one row per input row, columns `ticket_id, source, category, handle_minutes, action, reason, flags`.

## 3. Acceptance test ("answer-complete")

Each step is a command run from the repo root. Pass means the stated output and exit code 0.

| # | Command | Pass | Proves |
|---|---|---|---|
| 1 | `python3 automation/run.py --check` | `ACCEPTANCE: PASS` | Router is intact: one output row per input row, before number re-summed by separate code, every citation resolves, headline gives ceiling and floor of 0 and no assumed share |
| 2 | `python3 tests/check.py` | no `FAIL` line | Same on a changed copy: a new category and a blank minutes cell become exceptions, totals change, no traceback |
| 3 | `python3 automation/run.py --data <pilot export dir> --out <tmp> --check --max-target-minutes <N>` | `ACCEPTANCE: PASS` | Your piece works: on a ticket export from a two week pilot, logged minutes on the target category are at or below N |

For step 3, N is agreed with the client before the pilot, from the weekly figure in
`out/before_after.md` times the pilot weeks, less the saving they expect. "Answer-complete" means
all three pass. Step 3 produces the measured after figure in minutes that the bundle cannot give.

## 4. In and out

In: the self-serve replacement (a). The router as a live step, rules only in `rules.json`. The
exception queue with reasons. The before and after report on every run. The two week pilot export.

Out: reading ticket free text or guessing a category. Machine learning or LLM calls. Automating
any category other than the target. Dashboards, dollar values for time saved. The finance
month-end reconciliation: larger claimed time sink, inputs not provided (`out/time_waste.md`).
Constraints: Python 3.8 or later, standard library only, no network, never edit `data/`, no
category names or amounts in code. Unknown input goes to `EXCEPTION`, never to a guess.
