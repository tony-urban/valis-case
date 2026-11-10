# Report to Dana Whitfield, CEO: three answers and one number

Built from the raw files in `data/` only. Every figure below is copied from a generated output that you can regenerate (last section). Citations are relative to `data/`. As of date: the Slack export date, 2026-06-18 `slack_export.md:L3`. Nothing here is checked against an invoice, because the bundle holds none.

## The answers

- **Q1, SaaS spend.** The Q1 2026 P&L lists 81,000 USD of Software & SaaS across 15 line items `pnl_q1_2026.csv:L24`. One 7,500 USD line looks like a duplicate `pnl_q1_2026.csv:L13`. Finance has flagged it and not confirmed it. If it is a duplicate the figure is 73,500 USD. What was actually paid cannot be checked. Confidence: HIGH that the P&L says 81,000 USD, LOW that 81,000 USD is what was spent.
- **Q2, Sales hiring.** You froze it. All new Sales headcount is frozen, REQ-114 included `slack_export.md:L66 [#leadership | Dana Whitfield | Wed Jun 10, 8:47 AM]`, and the leadership sync recorded it `meeting_notes/leadership_sync_2026-06-11.md:L16`. You own the decision, Priya Raman enforces it on requisitions `meeting_notes/leadership_sync_2026-06-11.md:L18`. The roster still shows REQ-114 as APPROVED and is stale `headcount_roster.csv:L22`. Confidence: HIGH on the decision and the owner, MEDIUM on the current state.
- **Q3, wasted time.** The largest measured time sink is the creator support queue: 4,230 logged minutes on 140 tickets in the quarter. The largest claimed one is the month-end brand-deal revenue reconciliation in Finance, at 3 days a month, self-reported and never timed `meeting_notes/leadership_sync_2026-06-11.md:L35`. I automated thumbnail re-upload tickets first: 63 tickets, 1,365 logged minutes. The router runs today and saves 0 minutes today. The most it can save is 1,365 minutes a quarter. The bundle does not support a measured after figure in minutes.
- **The value number.** 7,500 USD at risk in Q1 2026 `pnl_q1_2026.csv:L13`. Status: suspected duplicate, unconfirmed, closed by one invoice. It is an amount at risk, not a saving.

## Q1. What did we spend on SaaS tools last quarter?

**As listed, 81,000 USD. 73,500 USD if the suspected duplicate is confirmed (81,000 - 7,500). Neither figure is checked against an invoice.**

| Line item | USD | What it is | Source row |
|---|---:|---|---|
| Salesforce | 12,000 | CRM | `pnl_q1_2026.csv:L9` (Line Item: Salesforce) |
| HubSpot | 9,000 | Marketing automation | `pnl_q1_2026.csv:L10` (Line Item: HubSpot) |
| Looker | 11,000 | BI / dashboards | `pnl_q1_2026.csv:L11` (Line Item: Looker) |
| Amplitude | 7,500 | Product analytics | `pnl_q1_2026.csv:L12` (Line Item: Amplitude) |
| Amplitude Analytics | 7,500 | Product analytics | `pnl_q1_2026.csv:L13` (Line Item: Amplitude Analytics) |
| Figma | 3,600 | Design | `pnl_q1_2026.csv:L14` (Line Item: Figma) |
| Adobe Creative Cloud | 5,400 | Editing / creative suite | `pnl_q1_2026.csv:L15` (Line Item: Adobe Creative Cloud) |
| Notion | 2,400 | Docs / wiki | `pnl_q1_2026.csv:L16` (Line Item: Notion) |
| Slack | 4,200 | Internal comms | `pnl_q1_2026.csv:L17` (Line Item: Slack) |
| Google Workspace | 6,000 | Email / docs / storage | `pnl_q1_2026.csv:L18` (Line Item: Google Workspace) |
| Zoom | 1,800 | Video calls | `pnl_q1_2026.csv:L19` (Line Item: Zoom) |
| GitHub | 3,000 | Source control | `pnl_q1_2026.csv:L20` (Line Item: GitHub) |
| Sentry | 1,500 | Error monitoring | `pnl_q1_2026.csv:L21` (Line Item: Sentry) |
| Greenhouse | 4,000 | ATS / recruiting | `pnl_q1_2026.csv:L22` (Line Item: Greenhouse) |
| Airtable | 2,100 | Ops trackers | `pnl_q1_2026.csv:L23` (Line Item: Airtable) |

- Arithmetic: 12,000 + 9,000 + 11,000 + 7,500 + 7,500 + 3,600 + 5,400 + 2,400 + 4,200 + 6,000 + 1,800 + 3,000 + 1,500 + 4,000 + 2,100 = 81,000 USD. It equals the stated subtotal `pnl_q1_2026.csv:L24` (Line Item: Software & SaaS subtotal).
- A second source states the same subtotal: "Software & SaaS line is finalized for Q1, subtotal as listed is $81k for the quarter." `slack_export.md:L143 [#finance | Priya Raman | Mon Jun 2, 10:30 AM]`
- Boundary: rows whose `Category` is Software & SaaS. AWS, 38,000 USD, sits under Infrastructure and is left out `pnl_q1_2026.csv:L25` (Line Item: AWS), as the CFO instructs in the same message. Folding it in would give 81,000 + 38,000 = 119,000 USD. Cloudflare is posted as '€1900', also under Infrastructure, and is not converted or added `pnl_q1_2026.csv:L26` (Line Item: Cloudflare).
- **Confidence, as the tool computed it.** The P&L as listed says 81,000 USD: HIGH. All 15 rows are numeric, the row sum equals the subtotal row, and a second source states the same subtotal. 81,000 USD is what was actually spent: LOW, read as could not verify. No invoice or contract file is in the bundle, a suspected duplicate is open, one source questions a posted amount `meeting_notes/finance_review_2026-05-28.md:L23`, and a finance note marks its own figures "Figures illustrative / pre-close." `meeting_notes/finance_review_2026-05-28.md:L42`

## Q2. Did we decide to hire in Sales or freeze, what is the current state, and who owns it?

**Decision: frozen. Current state as of 2026-06-18: frozen, no new Sales hiring. Owner: you. Enforcer: Priya Raman.**

- **Decision.** First recorded 2026-06-10: "After the Q1 sales miss we're FREEZING all new Sales headcount until pipeline recovers." `slack_export.md:L66 [#leadership | Dana Whitfield | Wed Jun 10, 8:47 AM]`. Recorded as a DECISION in the leadership sync notes dated 2026-06-11 `meeting_notes/leadership_sync_2026-06-11.md:L16`. Sequence of positions: APPROVED (roster, 2026-05-01), then FROZEN (2026-06-10, chat), then FROZEN (2026-06-11, decision record).
- **Current state.** The latest statement consistent with the freeze is dated 2026-06-15: "Note Sales is on freeze so don't bother submitting Sales reqs until that lifts." `slack_export.md:L243 [#people | Elena Novak | Mon Jun 15, 2:00 PM]`. Nothing in the bundle on this topic is later, so the 3 days up to the export date are not evidenced.
- **Owner.** "To be clear so there's no ambiguity downstream: current state is frozen on Sales hiring, I'm making the call, Priya enforces it on the req side." `slack_export.md:L78 [#leadership | Dana Whitfield | Wed Jun 10, 9:14 AM]`. The notes say the same `meeting_notes/leadership_sync_2026-06-11.md:L18`. Roles per the org chart: Dana Whitfield, CEO `org_chart.md:L14`, and Priya Raman, CFO `org_chart.md:L16`. Hiring manager for REQ-114 is Tomás Reyes `headcount_roster.csv:L22` (Req_ID: REQ-114).
- **Scope.** Net-new Sales requisitions only. Backfills for regretted attrition are reviewed case by case by Priya Raman and Tomás Reyes `meeting_notes/leadership_sync_2026-06-11.md:L17`. Other teams are unaffected `slack_export.md:L235 [#people | Elena Novak | Thu Jun 11, 9:41 AM]`. REQ-114 is paused, not cancelled: "Tomás, that means REQ-114 is paused, not killed — we revisit when Q2 pipeline shows recovery." `slack_export.md:L69 [#leadership | Priya Raman | Wed Jun 10, 8:52 AM]`
- **Open follow-ups.** Two actions from the sync are past their due dates with no completion mark in the notes: candidate handling for REQ-114, due 2026-06-13 `meeting_notes/leadership_sync_2026-06-11.md:L42`, and notifying People to pause the requisition in Greenhouse, due 2026-06-12 `meeting_notes/leadership_sync_2026-06-11.md:L43`. Elena Novak already posts about the freeze, so she knows of it `slack_export.md:L229 [#people | Elena Novak | Thu Jun 11, 9:30 AM]`. The change in Greenhouse itself is not evidenced. A candidate was in late-stage interviews for REQ-114 and the handling is unresolved in the sources `meeting_notes/leadership_sync_2026-06-11.md:L20`.
- **Confidence, as the tool computed it.** What was decided: HIGH (an explicit decision statement exists, no later message from a decision owner reads differently, recorded in more than one place). Who owns it: HIGH (exactly one decision maker is named, in more than one source). Current state as of 2026-06-18: MEDIUM. No core check fails. 5 of 7 flag checks fail: the roster shows a different status, the sources give different decision dates, 2 follow-up actions are past due without a completion mark, 1 loose end is open, and the evidence stops before the export date.

## Q3. Where is the most time wasted, and what did I automate first?

**Largest claim: the Finance month-end reconciliation, self-reported. Largest measured: the support queue. Built and running: a router for thumbnail re-upload tickets.**

The tool tags every figure MEASURED (summed from logged rows), ASSERTED (someone said it, no log behind it) or ASSUMPTION (my input). It computes no HIGH, MEDIUM or LOW level for this question, so the tags are the confidence statement.

| Rank | Workflow | Tag | Hours a quarter | Basis |
|---|---|---|---|---|
| 1 | Month-end brand-deal revenue reconciliation (Finance) | ASSERTED | 72 | claim of 3 days a month, 1 day = 8 hours (ASSUMPTION) |
| 2 | Creator support queue, all categories together | MEASURED | 70.5 | 4,230 logged minutes on 140 tickets |
| 3 | Tax form (W-9/W-8) chasing | MEASURED | 25.9 | 1,555 logged minutes on 36 tickets |
| 4 | Thumbnail re-upload requests (the pick) | MEASURED | 22.8 | 1,365 logged minutes on 63 tickets |

Ranks 3 and 4 are parts of rank 2 and do not add to it. Every ticket row behind these sums is cited one by one in `repo:automation/out/time_waste.md` (its last section), for example `support_tickets_q1_2026.csv:L2` = 25 minutes. The log covers 2026-01-02 to 2026-03-31. Post-production is called the bottleneck with no volume or effort figure anywhere in the bundle, so it cannot be ranked `slack_export.md:L33 [#leadership | Yuki Tanaka | Wed Apr 30, 2:05 PM]`.

**The finance reconciliation is the larger claimed time sink, and I did not build it.**
- The claim is 3 days a month, in 5 source lines that all trace to one person's self-report: `slack_export.md:L107 [#finance | Maya Fortin | Fri May 2, 5:10 PM]`, `slack_export.md:L113 [#finance | Maya Fortin | Fri May 2, 5:22 PM]`, `slack_export.md:L157 [#finance | Maya Fortin | Fri Jun 13, 4:55 PM]`, `meeting_notes/finance_review_2026-05-28.md:L11`, `meeting_notes/leadership_sync_2026-06-11.md:L35`. Nobody timed it. Converted: 3 days x 3 months x 8 hours a day (ASSUMPTION) = 72 hours a quarter. That is 3.2 times the measured 22.8 hours of the workflow I built.
- Why it was not built: there is no time log, and the three files it reconciles (the CRM export, the invoicing sheet, the payout tracker, named in `slack_export.md:L99 [#finance | Maya Fortin | Tue Apr 22, 9:43 AM]`) are not in the bundle. Building it would mean inventing the data it reconciles.
- Files needed to build and measure it: the CRM deal export, the invoicing sheet, the payout tracker, a time log of the close (date, task, hours), and the written list of manual steps that the finance review already assigns as an action `meeting_notes/finance_review_2026-05-28.md:L36`.

**Why thumbnail re-uploads first.** It is one of the few workflows with both a measured before figure and its input file in the bundle. It is rank 1 of 6 categories by ticket count (63) and rank 2 of 6 by logged minutes (1,365). Handle time sits in a narrow band, 15 to 25 minutes per ticket. The ops lead asks for this automation by name `slack_export.md:L192 [#ops | Liam Doyle | Thu May 21, 3:05 PM]`. Stated plainly: tax form chasing has more logged minutes (1,555 against 1,365). It lost because the log carries no form status or creator contact data to drive a chaser, the work needs a compliance check per form, and the reply in its own thread points to cheap off-the-shelf services and defers it to Q3 planning `slack_export.md:L203 [#ops | Elena Novak | Wed Jun 4, 10:25 AM]`. That a thumbnail swap needs no money or compliance decision is my judgment, not a sourced fact.

**Before and after, as the run computes it** (rows in `repo:automation/out/before_after.md`):
- Before (MEASURED): all 140 tickets, 4,230 logged minutes, reach a person today.
- After (EXECUTED by the run): 77 tickets (2,865 logged minutes) routed to a person, 63 tickets (1,365 logged minutes) routed to the self-serve path, 0 exceptions. Routed to the self-serve path does not mean resolved without a person.
- Measured ceiling: at most 1,365 minutes in the period (22.8 hours, 32.3% of logged support time, 105 minutes a week over 13 weeks, the weeks being an ASSUMPTION). Floor today: 0. Minutes saved by the run alone: 0, because the self-serve thumbnail replacement that the router points to does not exist yet. That piece is the builder's job, specified in `repo:automation/BUILDER_SPEC.md`.
- **The bundle does not support a measured after figure in minutes, for this or any other workflow in it.** Where between 0 and 1,365 the result lands is not measured. A two week pilot export run through the same command produces it. No dollar value is put on these hours: the bundle has no support wage.

## The value number: 7,500 USD at risk in Q1 2026

**Suspected duplicate Software & SaaS line item, unconfirmed, closed by one invoice. Worth between 0 and 7,500 USD for the quarter depending on what the invoice shows.**

- The pair: `pnl_q1_2026.csv:L12` (Line Item: Amplitude) is 7,500 USD and `pnl_q1_2026.csv:L13` (Line Item: Amplitude Analytics) is 7,500 USD. Equal amounts, near-identical labels, identical Notes text.
- Baseline: Software & SaaS as listed, 81,000 USD `pnl_q1_2026.csv:L24`. Without the suspected duplicate: 81,000 - 7,500 = 73,500 USD. Share of the category: 7,500 / 81,000 = 9.3%.
- Finance already knows: "I'm 90% sure that's the same product entered twice but I haven't confirmed against the invoice." `slack_export.md:L146 [#finance | Maya Fortin | Mon Jun 2, 10:38 AM]`. The value is not the discovery. It is that the item is still open at the last message in the thread: "Haven't gotten the invoice back yet so I'm leaving the CSV as-is until I can confirm." `slack_export.md:L152 [#finance | Maya Fortin | Mon Jun 2, 10:47 AM]`. The 90% is one person's estimate and is not used in any arithmetic. The number is small, and it was chosen because every input is a cited row and one document settles it.
- Three readings the bundle cannot tell apart. Entered twice, paid once: the category is overstated by 7,500 USD, no cash effect, a reporting correction. Billed or paid twice: up to 7,500 USD left the business, recovery depends on the vendor. Two real contracts: the value is 0.
- Labelled assumption, not part of the number: if, and only if, the same repeat sits in every quarter of a year, the figure is 7,500 x 4 = 30,000 USD a year. The bundle holds one quarter only.
- Confidence: the worksheet computes no level. Its status is fixed at suspected, unconfirmed, and the script never upgrades it. Full worksheet: `repo:value/VALUE_WORKSHEET.md`.

## What does not reconcile

Sources that contradict each other. Each appears once, with what settles it.

1. **Amplitude and Amplitude Analytics, 7,500 USD each**, so 81,000 or 73,500 USD (`pnl_q1_2026.csv:L12`, `pnl_q1_2026.csv:L13`). Why: one product may have been entered twice. Settled by: the Amplitude invoice or invoices and order form for Q1 2026, then the accounts payable ledger and bank or card statement to tell entered twice from paid twice. Ask Priya Raman, Maya Fortin.
2. **Called final, with a check still open.** The SaaS line is called finalized at 81,000 `slack_export.md:L143 [#finance | Priya Raman | Mon Jun 2, 10:30 AM]`, and the same thread then leaves the duplicate check open `slack_export.md:L152 [#finance | Maya Fortin | Mon Jun 2, 10:47 AM]`. Finalized describes the state of the file, not a verified number. Settled by: the closed, published P&L.
3. **Salesforce: the note says higher, the numbers say lower.** The finance review says the posted quarterly figure "looks higher than a $60k annual would imply" `meeting_notes/finance_review_2026-05-28.md:L23`. The arithmetic says 60,000 / 4 = 15,000 per quarter, and the posted 12,000 is lower by 3,000 `pnl_q1_2026.csv:L9`. The renewal is first mentioned 2026-05-14, after the quarter ended, so the posted amount is left as posted `slack_export.md:L118 [#finance | Priya Raman | Wed May 14, 11:02 AM]`. Settled by: the signed contract and the invoices for the quarter.
4. **Roster against the decision.** The roster snapshot dated 2026-05-01 shows REQ-114 APPROVED `headcount_roster.csv:L22`. The decision record governs because it is later and says so: "The 2026-05-01 roster showing it APPROVED is superseded by this decision." `meeting_notes/leadership_sync_2026-06-11.md:L16`. Settled by: a current roster export or the ATS status.
5. **Decision date: 2026-06-10 or 2026-06-11.** Your message is dated 2026-06-10 `slack_export.md:L66 [#leadership | Dana Whitfield | Wed Jun 10, 8:47 AM]`, the notes are dated 2026-06-11 `meeting_notes/leadership_sync_2026-06-11.md:L16`, and a 2026-06-11 message says "yesterday's leadership call" `slack_export.md:L229 [#people | Elena Novak | Thu Jun 11, 9:30 AM]`. The outcome is the same in each. The earliest date is used. The bundle holds no meeting note dated 2026-06-10. Settled by: notes or a calendar entry for the earlier call.
6. **When REQ-114 was approved.** The notes say "approved back in early May" `meeting_notes/leadership_sync_2026-06-11.md:L15`. A message dated 2026-04-21 already calls it approved `slack_export.md:L16 [#leadership | Tomás Reyes | Mon Apr 21, 9:31 AM]`. Settled by: the approval record in the requisition tracker.
7. **Open requisitions outside Sales.** The roster table has 4 open requisitions: Sales, Engineering, Content/Production, Data (`headcount_roster.csv:L22`, `headcount_roster.csv:L23`, `headcount_roster.csv:L24`, `headcount_roster.csv:L25`). The chat summary of the same snapshot names a Sales AE, a Creator Management backfill and an Eng role `slack_export.md:L221 [#people | Elena Novak | Fri May 1, 4:30 PM]`. So the statement that other teams are unaffected cannot be tied to one agreed list. Settled by: a current requisition list from People.
8. **Three revisit triggers, worded differently**: `slack_export.md:L69 [#leadership | Priya Raman | Wed Jun 10, 8:52 AM]`, `slack_export.md:L75 [#leadership | Marcus Lindqvist | Wed Jun 10, 9:11 AM]`, `meeting_notes/leadership_sync_2026-06-11.md:L19`. Settled by: you.
9. **Support effort, claimed against logged.** Claimed 40 hours a week `slack_export.md:L175 [#ops | Liam Doyle | Tue May 6, 11:40 AM]`. Measured 5.4 hours a week (4,230 minutes / 60 / 13 weeks), 14% of the claim. Claimed 47 thumbnail requests in one week `slack_export.md:L192 [#ops | Liam Doyle | Thu May 21, 3:05 PM]`. Busiest week in the log: 6. A swap is described as "only a few minutes" `slack_export.md:L167 [#ops | Yuki Tanaka | Mon Apr 28, 9:22 AM]`. Logged: 15 to 25 minutes, mean 21.7. One claim holds up: "half my tickets" against 63 of 140 = 45.0% by count. Why this is not a clean contradiction: the log ends 2026-03-31 and the claims were made from 2026-04-21 on `slack_export.md:L4`, so it is claim period against log period. The claim is challenged in its own thread: "40 hrs/week is a lot — is that measured or a vibe?" `slack_export.md:L178 [#ops | Elena Novak | Tue May 6, 11:52 AM]`. Settled by: the ticket export for the following quarter.

## What I could not verify and what would close it

Gaps where the bundle has no source at all. Each appears once.

1. Cash actually paid for any of the 15 SaaS rows. Closes with: invoices or the AP ledger.
2. Whether the P&L extract is final `meeting_notes/finance_review_2026-05-28.md:L42`. Closes with: the published final P&L for Q1 2026 from Finance.
3. The USD value of Cloudflare ('€1900') `pnl_q1_2026.csv:L26`, which leaves the Infrastructure subtotal blank `pnl_q1_2026.csv:L27`. Closes with: the month-end FX rate Finance uses, or the invoice.
4. Whether any Software & SaaS row was billed in another currency and converted before posting `meeting_notes/finance_review_2026-05-28.md:L25`. Closes with: Finance's FX working for the quarter.
5. Whether the duplicate recurs in other quarters, and whether anything is recoverable. Closes with: the P&L extracts or general ledger vendor detail for the other quarters, the contract terms, the vendor account manager.
6. Anything on Sales hiring after 2026-06-15. Closes with: the channels after the export date, or a word from you.
7. Whether REQ-114 was actually paused in Greenhouse, and whether the two due actions were done. Closes with: the ATS status, Priya Raman and Tomás Reyes for the candidate, Marcus Lindqvist for the notification.
8. What `Handle_Minutes` measures (hands-on or elapsed, timed or estimated), and whether all support work is ticketed. 140 of 140 values are multiples of five, which suggests estimates. Closes with: the ticketing tool's field definition and a one week time sample from the support team.
9. The measured after figure for the automation, and whether the self-serve replacement can be built in the CMS. Closes with: a two week pilot export counting routed tickets that come back to a person, and CMS access or its API documentation.
10. The real time spent on the finance reconciliation, and any effort figure for post-production. Closes with: the files listed under Q3, and for post-production jobs per week, hours per job, queue length.

## How to check this yourself

From the repo root. Python 3.8 or later, standard library only, nothing to install, no network.

```
python3 tests/check.py               # every check prints PASS or FAIL, including that every citation resolves
python3 ask/ask.py                   # Q1 and Q2, rewrites ask/out/q1.md and ask/out/q2.md
python3 value/value.py               # the value number, rewrites value/VALUE_WORKSHEET.md
python3 automation/run.py --check    # Q3 ranking, the router, before and after, acceptance test
```

Each citation is a file and a line under `data/`. Open the line and it says what the report claims. To try a fresh file of the same shape, copy `data/` to another folder, change it, and add `--data <folder>` to any of the last three commands. The committed outputs are not touched.
