# automation/ : Q3 time-waste analysis and the one running automation

## Run

    python3 automation/run.py            # from the repo root
    python3 automation/run.py --check    # same, plus the acceptance test (exit 1 on any FAIL)

Options: `--data <dir>` (default `data/`), `--out <dir>` (default `automation/out/`),
`--category "<name>"` (override the target category from `rules.json`).

Python 3.8 or later (stock macOS `python3` is 3.9), standard library only. No network, no installs.
`data/` is only read. The scripts switch bytecode off, so no `__pycache__` is left behind.
Every generated file is UTF-8 with LF line endings on every OS, Windows included.

Pilot acceptance: `--check --max-target-minutes N` (optionally `--pilot-days D`, default `pilot_days`
in `rules.json`, 14, ASSUMPTION). It FAILs, with the reason, unless all three hold: (1) coverage, the
export has at least one target-category row ("not evaluable: no target tickets in this export"
otherwise); (2) window, its dates span at least D days; (3) outcome, the export has the column
`Self_Serve_Outcome` (name and accepted values under `pilot` in `rules.json`) readable on every target
row, and the logged minutes on target tickets that came back to a person, printed as "After (MEASURED
on the pilot export)" with the counts resolved and returned, are at or below N. The Q1 bundle file has
no outcome column, so on it the headline still says the after in minutes is not measured, and adds
one line pointing to this path and the demo below.

## Demo of the pilot measurement (synthetic fixture, not case data)

`demo_pilot/` holds a made-up pilot export (24 rows, `DEMO-` IDs, July dates, outcome column). Its
README says in line 1 that it is a synthetic test fixture. The run recognises that line
(`pilot.fixture_marker` in `rules.json`), puts a banner on both reports and skips the README as evidence.

    python3 automation/run.py --data automation/demo_pilot --out /tmp/pilot_demo --check --max-target-minutes 105

Expected, abridged (figures from the fixture, not a Northwind result):

    **SYNTHETIC TEST FIXTURE. ... They are not a Northwind result.**
    - **Before (MEASURED): all 15 tickets, 370 logged minutes, reach a person today.** 9 more were resolved by self-serve ...
    - **After (MEASURED on the pilot export): 100 logged minutes on the 5 Thumbnail re-upload tickets that came back to a person.** 9 ... resolved by self-serve and 5 came back to a person ...
    PASS  pilot coverage: the export has tickets of the target category (14 Thumbnail re-upload rows)
    PASS  pilot window: dates span at least 14 days (2026-07-06 to 2026-07-19, 14 days)
    PASS  pilot outcome: After (MEASURED on the pilot export) is at or below 105 minutes (100 logged minutes on 5 tickets that came back to a person (re-summed 100), 9 resolved by self-serve)
    ACCEPTANCE: PASS

With `--max-target-minutes 90` the outcome line FAILs and the exit code is 1. The Q3 report on the
fixture (`time_waste.md`) still uses the 13 week quarter from `rules.json`; read `before_after.md`.

## What it does

1. `analyze_time.py` reads the ticket log plus the Slack export and meeting notes, and writes
   `out/time_waste.md`: every candidate workflow, ranked in hours a quarter, tagged MEASURED
   (summed from logged rows) or ASSERTED (someone said it), with citations.
2. `run.py` gives every ticket row one action and writes `out/routed_queue.csv`:
   `SELF_SERVE` (target category), `HUMAN` (other known category), `EXCEPTION` (unknown
   category, blank or unreadable field).
3. `run.py` writes `out/before_after.md`. Headline, in this order: before (all tickets reach a
   person, measured), after (tickets and logged minutes routed to each path, executed), the
   measured ceiling and the floor of 0, and what is not measured. An illustration with assumed
   shares sits lower down, labelled as a scenario and not a result.

## Files

| File | Purpose |
|---|---|
| `run.py` | The automation, the before and after report, the acceptance test |
| `analyze_time.py` | Loading, validation and the Q3 evidence report |
| `rules.json` | The only place for file and column names, categories, keywords, assumptions |
| `BUILDER_SPEC.md` | One-page spec for a remote builder |
| `JUDGMENTS.md` | Timestamped judgment calls and dead ends |
| `out/` | Generated outputs, committed so a reader can see them without running anything |
| `demo_pilot/` | Synthetic pilot export for the demo above. Test fixture, not case data |

Parsing goes through `pipeline/importer.py`, so a citable line means the same thing here as in
the other deliverables.

## How the two labels are decided

- MEASURED: the figure is a sum of `Handle_Minutes` over rows that are each cited.
- ASSERTED: the figure is a number found in a Slack message or meeting note by a keyword and
  a pattern from `rules.json`. The message is cited. No time log behind the figure is in the bundle.
  Where the sources give the figure as approximate ("~3 days", "basically three full days"), the
  report says "about" (pattern `approx` per candidate in `rules.json`).

## Limits, stated plainly

- The run routes tickets. It does not swap thumbnails: the CMS is not in the bundle and the
  self-serve replacement does not exist yet. The run alone saves 0 minutes. The most it can
  save is the logged minutes on the self-serve path. The bundle does not support a measured
  after figure in minutes: a two week pilot export run through the same command produces it.
- The ticket file is found by the pattern `file_pattern` in `rules.json`. If several files
  match, the last by name is used and the others are named in the output.
- Minutes above `max_plausible_minutes` in `rules.json` (ASSUMPTION) and repeats of a ticket ID
  go to the exception queue and are not counted.
- The finance reconciliation is the larger claimed time sink. It was not built because the
  claim is self-reported and its three input files are not in the bundle.
- A file that is not UTF-8, has no header or lacks a required column stops the run with a
  plain `CANNOT RUN` message naming what is needed. `Assigned_To` and `Status` are optional
  (`optional_columns` in `rules.json`): without them the run goes ahead, skips the flags that need
  them, and both reports and stdout say which column was absent and which flag was skipped. Bad rows never stop the run: they go to
  the exception queue.
- Evidence is found by keywords in `rules.json`. A new topic in a fresh Slack export is only
  picked up after a keyword is added there.
