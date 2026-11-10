# Valis — build exercise (Principal, GTM)

**The setup.** You've been dropped in next to **Dana Whitfield, CEO of Northwind Media** — a
~300-person creator-economy company. Her data is scattered across Slack, spreadsheets, meeting notes,
and an org chart, and — her words — she's *"drowning in dashboards and doesn't fully trust her own
numbers."* You have **one focused day** to show what a Valis-style first slice looks like — **built by
hand, on her real (synthetic) mess.**

Everything in this folder is **100% synthetic** — a fabricated company. Use it freely; nothing here is
real client data.

**Start with `CEO_CONTEXT.md`** (Dana's framing), then **`CEO_QUESTIONS.md`** (what she's asking). The
rest is the raw material to work from.

## What's attached — the "Northwind-in-a-box" bundle

- `CEO_CONTEXT.md` — Dana's orientation note · **read first**
- `CEO_QUESTIONS.md` — the questions to answer
- `org_chart.md` — leadership and team structure
- `pnl_q1_2026.csv` — quarterly P&L extract
- `headcount_roster.csv` — headcount roster + open requisitions (snapshot 2026-05-01)
- `support_tickets_q1_2026.csv` — support-ticket log
- `slack_export.md` — `#leadership` / `#finance` / `#ops` / `#people`, ~8 weeks
- `meeting_notes/` — leadership sync, finance review, data review

## Deliverables — four things, in one folder you send back

1. **A working ask-with-sources slice.** Build something that *runs on this data* and answers the CEO's
   two questions, each **with its sources cited to the exact file/line/message and a calibrated
   confidence level**:
   - *"What did we actually spend on SaaS tools last quarter?"*
   - *"Did we decide to hire in Sales or freeze hiring — what's the current state, and who owns it?"*
2. **One value number, CFO-grade.** From the data, produce **one number you'd put in front of the CFO**
   to prove value (a cost you'd cut, time you'd save, a leak you'd close). Show its **baseline, the
   arithmetic, the exact source rows, and an explicit list of what you could NOT verify.** Assume a
   finance person will try to break it.
3. **One automation, shipped and running.** Mine the bundle for where Northwind wastes the most time.
   Pick the single best workflow to automate and **build a working version that actually runs on this
   data** end-to-end and produces a real before→after number — plus the **one-page builder spec** you'd
   hand a remote builder (scope, a data contract referencing the actual columns/files, an
   "answer-complete" acceptance test, what's in/out). The thing must run; "a builder could extend this"
   is for polish, not a substitute for it running.
4. **A build log.** As you work, keep a running, **timestamped** log — the prompts you ran, files you
   created, dead-ends, and **every judgment call you made on the dirty data** — wherever something
   looked inconsistent, ambiguous, or untrustworthy and you had to decide how to handle it — each with a
   one-line reason. We read this as carefully as the artifact.

## How to work it

- **Time-box.** One focused day (~8h). Solo. **Use your own AI tooling — Claude, MCP, skills — heavily;
  we want to see you AI-native.** The test is whether *you* drive, debug, and own the output, not
  whether your agent can.
- **How to submit.** Send back one folder (your artifact + build log + value-number worksheet + builder
  spec). Then we'll do a **30-minute live walkthrough** where you screen-share, reproduce a step or two
  we pick on the spot — possibly on a fresh file you haven't seen — and we'll push on the value number.
- **What "show your work" means here.** Every number traces to a row. Confidence is honest — high where
  the data is clean, *"I couldn't verify this"* where it isn't. If a question has no clean answer in the
  data, say so and tell us what you'd need — **don't manufacture one.** The right answer matters less
  than that it's true and traceable.

*Valis — confidential. Shared under NDA.*
