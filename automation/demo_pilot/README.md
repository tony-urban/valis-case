This folder is a synthetic TEST FIXTURE invented for the demo: it is not Northwind data and it is not in data/.

# demo_pilot: a made-up pilot export to show the pilot measurement working

Nothing here came from the case bundle. Every row was typed in by hand to exercise the method.
Ticket IDs start with `DEMO-`, creators are `demo_creator_NN`, and the dates (2026-07-06 to
2026-07-19, 14 days) sit after the bundle's Q1 period. Do not quote any figure from it as a result.

What it contains: `support_tickets_demo_pilot.csv`, 24 rows, the same columns as the Q1 ticket log
plus `Self_Serve_Outcome`, the column a real pilot export must carry (see `../BUILDER_SPEC.md`).

- 14 `Thumbnail re-upload` rows: 9 resolved by self-serve (0 minutes logged, no assignee) and
  5 returned to a person (100 minutes logged in total).
- 10 rows in other known categories, which the router leaves with a person.

Run it from the repo root (writes to a scratch folder, never to `automation/out/`):

    python3 automation/run.py --data automation/demo_pilot --out /tmp/pilot_demo --check --max-target-minutes 105

105 is the ceiling the spec's rule would give: the Q1 weekly figure for the target category
(1,365 minutes / 13 weeks = 105 a week) times 2 pilot weeks, less an expected 50% saving.
That 50% is an illustration, not an agreed number. The run prints a banner saying the input is
a synthetic test fixture. It is recognised by the first line of this file (`fixture_marker` in
`../rules.json`), so this README must keep that first line.

Every row also carries `Data_Source = SYNTHETIC TEST FIXTURE, not Northwind data`, and every ticket ID starts with `DEMO-`, so the file stays labelled if it is copied without this README.
