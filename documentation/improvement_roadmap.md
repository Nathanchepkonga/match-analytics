# Improvement and research roadmap

A working document: what we know, what we're still testing, and how each open question gets decided. Update it after every jackpot (scores) and every month (re-run the studies). Rules for picking games are in [prediction_factor_matrix.md](prediction_factor_matrix.md); this file is about what to learn next.

Last updated: 19 Oct 2026, after the 16 Oct 13-game jackpot and the 17-18 Oct Mega (card 204).

## 1. Established (keep doing)

| Finding | Evidence | Where |
|---|---|---|
| Bookmaker odds, averaged across independent books, are the best single predictor | 86k matches; 3,383 SportPesa archive games; 43.5k-match factor test; Reading 51-bookmaker study | draw_study.md, sportpesa_archive_study.md, factor_checklist_200.md |
| No measurable statistical factor (shots, goals, form, H2H, rest, referee, bookings) beats the closing odds | 30 held-out tests, none past correction | src/factor_tests.py |
| Several slips built by the optimiser beat several hand-made slips for big scores | 12,580 simulated cards; 46 real SportPesa cards | jackpot_simulation.md, src/slip_optimizer.py |
| The SportPesa crowd backs favourites and avoids draws, so draw-heavy winning tickets are rarely shared | crowd model fitted on archive winner counts, held-out rank correlation 0.65-0.72 | src/crowd_model.py |
| Draws come in at about their price (roughly 1 game in 4 on jackpot cards); forcing them costs as priced | ledger: draw calls 25% v favourite 39% (36 calls) | `python -m src.jackpot_ledger` |

## 2. Open research questions

Each has a test, a sample size to wait for, and a status. Decide only when the sample is reached; until then, report the running number without acting on it.

| # | Question | How we test it | Decide at | Status (19 Oct) |
|---|---|---|---|---|
| Q1 | Do **news-backed changes** (dated, possibly-unpriced facts from the 200-factor checklist) beat the favourite? | `reason_report()`, reason `news` | 20 decided calls | 1 call, 1 right |
| Q2 | What does the **user's draw rule** cost, and does it ever pay? | `reason_report()`, reason `draw-rule`; `change_types()` | 30 calls | 8 calls, 2 right (favourite 2) |
| Q3 | Do **late favourite flips** (R22) pay in our live jackpots? | reason `late-move` plus the archive's opening-v-closing test once more cards are priced | 20 calls | 2 calls, 0 right; archive 316 flips: closing 35.1% v opening 32.9% |
| Q4 | Is the **underdog shortfall** on SportPesa cards (R23) real? | `python -m src.archive_study` (tilt.json re-estimates itself) | 230 cards (about 30 more) | 200 cards; tilt at half strength |
| Q5 | Does **SportPesa's own Monday card favourite** do as well as the Friday multi-book consensus? | score both favourite columns per slate | 10 slates | 16 Oct: card 8/13 v consensus 6/13 (one slate) |
| Q6 | Does the **13-game midweek** product behave like the Mega (draw rate, underdog shortfall)? | build its own archive from the cards the user pastes (no public feed) | 20 cards | 3 cards in the ledger |
| Q7 | Do **double-chance or combination tickets** give better coverage per shilling than 5 single slips? | price combination lines with `chance()` against the same budget | next time the budget allows | not started |
| Q8 | Do **xG** factors (1, 2, 26 on the checklist) add anything over the odds? | add xG to src/factor_tests.py | one full season of xG data (end of 2026-27) | data too short |
| Q9 | Which tie-breaks raise **expected winnings** (bonus and jackpot sharing) without lowering the hit chance? | crowd model plus archive payouts per tier | 30 more cards | method built, not yet used for tie-breaks |
| Q10 | Do **weather and referee** facts (checklist Tier 1) predict anything? | collect them in each game's profile; test against results | 100 games | collected since 7 Oct |

| Q11 | Which **jackpot product and category** gives the best bonus chance per shilling? | `mega_categories()`; replay archive payouts; compare the midweek 13 (no category choice) | 30 more Mega cards for payouts | **Answered for now: Mega 15/15** (4.2% v 1.2% bonus chance per slip; real-payout replay 3 wins v 1). Re-check payouts as cards arrive |

## 3. What every slate must record (so the questions above can be answered)

- **Odds snapshots** from each site, with the time: Monday, the day before, match morning. No Betika (user rule).
- **A reason tag for every change from the favourite** on every slip: `"reasons": {"<game>": "news" | "late-move" | "draw-rule" | "optimiser" | "coverage" | "research-model" | "psychology" | "tipster"}`. Untagged changes can't be evaluated.
- **Research facts** with date, source and a priced / possibly-unpriced label (checklist files).
- **Match profiles** (H2H, weather, table, form) as JSON in the slate.
- **Tipster strings**, results, scores, and money staked and won.

## 4. Process improvements (backlog)

| Item | Why | Status |
|---|---|---|
| Archive update after each Mega card | keeps Q3, Q4 and Q9 growing; football-data posts weekend odds a day or two later | manual: see project memory and documentation/odds_sources.md; could become a Monday scheduled task |
| One script for the multi-site odds pull | the browser steps take time on match day | recipe written (odds_sources.md); not yet scripted |
| Agents in their own browser tab | collisions on 15-16 Oct | done (agent files) |
| Ledger reports for change types and reasons | separates what pays from what costs | done (`change_types`, `reason_report`) |
| Save the jackpot work in git | about 30 files of work are untracked, and the remote belongs to the original app's author | waiting for the user's decision (own repository or branch) |
| A jackpot page in the Streamlit app (ledger, archive, slips) | easier review than the command line | optional |

## 5. Review cadence

- **After each jackpot:** score every slip, tag any missing reasons, and run `python -m src.jackpot_ledger`. Update the status column above.
- **Monthly:** re-run `src.archive_study`, `src.crowd_model` and `src.factor_tests` on the new data, then update sections 1 and 2.
- **Retire or promote a rule** only when its decision sample is reached, and write the decision in the ruleset's calibration log.
