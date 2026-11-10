# automation/ : Q3 time-waste analysis and the one running automation

## Run

    python3 automation/run.py            # from the repo root
    python3 automation/run.py --check    # same, plus the acceptance test (exit 1 on any FAIL)

Options: `--data <dir>` (default `data/`), `--out <dir>` (default `automation/out/`),
`--category "<name>"` (override the target category from `rules.json`).

Python 3.8 or later (stock macOS `python3` is 3.9), standard library only. No network, no installs.
`data/` is only read. The scripts switch bytecode off, so no `__pycache__` is left behind.
With `--check`, `--max-target-minutes N` adds a ceiling on the target category's logged minutes (for a pilot export).

## What it does

1. `analyze_time.py` reads the ticket log plus the Slack export and meeting notes, and writes
   `out/time_waste.md`: every candidate workflow, ranked in hours a quarter, tagged MEASURED
   (summed from logged rows) or ASSERTED (someone said it), with citations.
2. `run.py` gives every ticket row one action and writes `out/routed_queue.csv`:
   `SELF_SERVE` (target category), `HUMAN` (other known category), `EXCEPTION` (unknown
   category, blank or unreadable field).
3. `run.py` writes `out/before_after.md`: the before number (measured), what the run executed,
   the statement that the run alone saves 0 minutes, and a scenario (not a result) with a 0%,
   a low and a high case.

## Files

| File | Purpose |
|---|---|
| `run.py` | The automation, the before and after report, the acceptance test |
| `analyze_time.py` | Loading, validation and the Q3 evidence report |
| `rules.json` | The only place for file and column names, categories, keywords, assumptions |
| `BUILDER_SPEC.md` | One-page spec for a remote builder |
| `JUDGMENTS.md` | Timestamped judgment calls and dead ends |
| `out/` | Generated outputs, committed so a reader can see them without running anything |

Parsing goes through `pipeline/importer.py`, so a citable line means the same thing here as in
the other deliverables.

## How the two labels are decided

- MEASURED: the figure is a sum of `Handle_Minutes` over rows that are each cited.
- ASSERTED: the figure is a number found in a Slack message or meeting note by a keyword and
  a pattern from `rules.json`. The message is cited. Nobody logged the time.

## Limits, stated plainly

- The run routes tickets. It does not swap thumbnails: the CMS is not in the bundle and the
  self-serve replacement does not exist yet. The run alone saves 0 minutes. The scenario is
  routed minutes times a deflection share that has no source in the bundle.
- Minutes above `max_plausible_minutes` in `rules.json` (ASSUMPTION) and repeats of a ticket ID
  go to the exception queue and are not counted.
- The finance reconciliation is the larger claimed time sink. It was not built because the
  claim is self-reported and its three input files are not in the bundle.
- A file that is not UTF-8, has no header or lacks a configured column stops the run with a
  plain `CANNOT RUN` message naming what is needed. Bad rows never stop the run: they go to
  the exception queue.
- Evidence is found by keywords in `rules.json`. A new topic in a fresh Slack export is only
  picked up after a keyword is added there.
