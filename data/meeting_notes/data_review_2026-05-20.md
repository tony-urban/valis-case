# Data Review — 2026-05-20

**Attendees:** Ben Okoro (Head of Data), Dana Whitfield (CEO), Hannah Cole (VP Growth / Marketing)
**Note-taker:** Ben Okoro
**Cadence:** Bi-weekly metrics review

---

## 1. Active creators — working definition

Ben walked through how the Data team currently counts "active" creators, since the number keeps coming up differently in different rooms.

> **Data team definition of "active":** a creator who **posted ≥1 time in the last 30 days**.
> On this definition, **active creators = 1,210** (as of 2026-05-19 dashboard snapshot).

Ben flagged that this is *not* the same as the headcount Finance and Talent quote. Finance/Talent talk about "creators under contract" (the signed roster), which is a larger number and counts everyone with an active agreement regardless of whether they posted. The Data dashboard intentionally measures **engagement**, not the contract book.

- Dana: wants the two reconciled before the board update — "I don't want to say 1,210 in one slide and a different number in another."
- Ben: will publish a short definitions note so we stop comparing apples to oranges. **Action: Ben to write up "active (posted ≥1/30d)" vs "under contract" so each number is labeled with its definition.**
- Until then: when a single "creator count" is requested, **ask which definition is meant** — engagement (Data, 1,210) or contracted roster (Finance/Talent).

## 2. Posting funnel (last 30 days)

| Metric | Value | Notes |
|---|---|---|
| Creators under management (dashboard universe) | — | pulled from roster sync; see definitions note |
| Active (posted ≥1, last 30d) | 1,210 | working definition above |
| Posted ≥4 (weekly cadence) | 690 | ~57% of active |
| Zero posts in last 30d | (see definitions note) | the gap vs the contracted roster |

Hannah: the weekly-cadence cohort (690) is the one that correlates with brand-deal eligibility — wants that broken out as a standing tile.

## 3. Dashboard / pipeline items

- **Looker refresh latency** — creator engagement model now refreshes nightly (was 2x/week). Stable for 3 weeks. Ben considers it done.
- **Amplitude event hygiene** — duplicate `post_published` events from the mobile client were inflating the cadence number by ~2–3% in April; fix shipped, numbers above are post-fix.
- **Attribution for subscriptions** — Hannah asked for a first-touch vs last-touch split on creator-subscription signups. Ben: doable, ~1 week, low priority vs the definitions cleanup.

## 4. Open items

- [ ] Ben — publish "active vs under contract" definitions note (owner: Data) — **before board update**
- [ ] Ben — add weekly-cadence (690) standing tile for Hannah
- [ ] Hannah — confirm which creator number Growth reports externally so it matches the labeled definition

---

*Next data review: 2026-06-03.*
