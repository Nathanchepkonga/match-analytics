# The Complete Football Match Determination Factor Matrix (67 Factors)

Scientific data analysis guide for football predictions, supplied by the user (June 2026, v1.0). Kept here as the reference methodology behind the qualitative "tactical read" and outcome-lean estimates on the [Fixture Intelligence](../pages/6_Fixture_Intelligence.py) page.

## Current ruleset at a glance (read this first, not the full history below)

This doc grows every slate. This section is the *only* part that should need reading before predicting a new slate - it's the current state, not the derivation. The full narrative below (how each rule was found, what broke) is justification/audit trail, kept for when a rule needs re-examining, not something to re-read each time.

**The single executable procedure is the numbered checklist under "Consolidated decision procedure" further down** - follow that step by step. Summary of what it encodes:

1. **Every jackpot is predicted from scratch (user rule, 2026-10-07; R17).** Each game is judged only on its own evidence: its current odds, team news, stakes, form, head-to-head, league position and weather. No patterns are carried over from earlier jackpots: no draw prior or draw target, no quota of homes/draws/aways, no "last week had lots of draws/upsets", no "this league always...". The result mix changed every time (draws 29%, 41%, 23%, 24%; the most common result was Home, Draw, Away, Home). R7, R8, R9's draw default, R13 and R15's draw default are retired.
2. **Draws follow the draw study (R19, from 2026-10-08; documentation/draw_study.md, 38,281 balanced matches).** Each game gets a `draw_role` from its own odds (and its chance of under 2.5 goals). **draw-main:** a near three-way tie; the draw may be slip 1's pick if a dated fact supports it. **draw-backup:** the draw is ranked 2nd; it's the change used on that game and must appear in at least one slip. **either-backup:** the draw and the other side are about equal, so facts decide. **side-backup:** changes go to the other side, never the draw. **SportPesa cards (from 2026-10-12, archive study):** on 1,731 real SportPesa games where the draw was ranked 3rd, the draw came in 31.0% against 29.1% for the other side. So on SportPesa cards side-backup is treated as either-backup: facts decide, leaning to the draw (R23).
3. Never fade market odds on research alone - measured net value of disagreeing with the market so far is zero (R9/market-efficiency finding).
4. Don't trust subjective confidence labels or even the raw probability-estimate gap as a validated accuracy signal yet - both are unreliable/non-monotonic (R14, R15). Don't use them for high-stakes judgment calls (e.g. wheel-system banker classification) until re-validated.
5. What carries over between jackpots is only *method*, never expected results: anchor on that game's favourite (rule 8), facts must be dated and checked, and the ledger's scoreboard says which slip-building methods have failed. None of these say what results to expect.
6. Track any new variable (weather, player ratings/style, stadium) as a separately-tagged input, so its value can be isolated in the next backtest rather than lumped into the already-tested form/H2H/news bucket. From 2026-10-07 the match-profiler agent collects H2H, weather, league position and last-5 form, and they're saved per game as `"profile"` in the ledger slate files.
7. **Statistical status as of the last check (n=34, 2 slates)**: cannot yet prove a real edge over even a flat 1/3 baseline - 95% CI on the Brier-score difference includes zero. Would need ~95-125 total matches (5-7 more slates) for a properly powered test. Treat every slate's result as one more data point toward that, not a verdict on its own.
8. **Slip construction (from 2026-10-03):** slip 1 is the market favourites; every other slip changes at most 2-3 legs from it, each change backed by a written news reason. Run the "what am I missing?" checklist on every game first: motivation asymmetry, emotional events (farewell, derby, new manager, takeover), late absences after the odds were set, H2H at that ground, and what would have to be true for the favourite to lose. Prediction sites are cross-checks only. Log each tweak and score it against the favourite.
9. **Par score (R16, from 2026-10-07):** on these cards the odds themselves expect only ~6.6/17 from the favourites slip (random picks: 5.7). Free tipsters average ~6/17. Judge slips against par from the odds, never fade tipsters, and use tipster consensus only as a tie-breaker between two equally justified near-even tweaks (it affects payout size, not the chance of winning).
13. **Latest prices win (R22, from 2026-10-10).** On 47,762 historical matches, closing odds beat early-week odds. When the favourite changes before kickoff (5.7% of matches), the new favourite wins 38.1% against 32.2% for the old one. So re-check prices as close to the jackpot's close as possible, and follow a late favourite change unless a dated fact says otherwise.
12. **Slip optimiser (R21, from 2026-10-09).** For 13-game jackpots, build the slips with `python -m src.slip_optimizer <slate> --min-draws 0,0,3` (two free slips plus one 3-draw slip). On historical cards it beats the 9 Oct draw-heavy method at 10+ (1.27-1.29% v 0.74%, p ≤ 0.01) and matches or beats the evidence tweaks. For 17-game jackpots the good methods tie at 12+ so far. Price any hand-made change with `chance()` before accepting it.
11. **Simulator findings (R20, from 2026-10-09; documentation/jackpot_simulation.md, 12,580 historical jackpot cards).**
    - Judge slip sets on their chance of 10+/12+ (13 games) or 12+/13+ (17 games), never on the typical best score.
    - Three slips built from favourites plus changes on close games give about 2-2.5 times one slip's big-score chance; random variety doesn't.
    - Draws where the draw is the least likely result lose to the favourite (30% vs 37%).
    - A 3-draws-per-slip quota is no better and no worse at the tail than the evidence method, but worse pick by pick.
    - No way of making picks beats the favourite pick by pick.
14. **SportPesa archive tilt (R23, candidate, from 2026-10-12; documentation/sportpesa_archive_study.md).** The study covers 199 real Mega Jackpot Pro cards, 3,383 games, 2,480 with closing odds.
    - SportPesa picks games with favourites at 35-47% (average 40% v 51% in the pool it chose from), and favourites win as priced (41.2% v 40.2%).
    - The underdog side won 2.8 pts less than priced (z -3.0, every year) and the draw 1.8 pts more. It improved predictions out of sample in one direction (p = 0.03), but not in the other.
    - Build SportPesa slips with `--tilt`, which applies half the measured size.
    - No slot, clustering or home/away pattern exists.
    - Re-test after 30 more cards.
15. **2-5 draws in every slip (R24, user rule from 2026-10-14; documentation/draw_factors.md).**
    - Every slip carries 2-5 draws, placed by the optimiser (`min_draws=2, max_draws=5`) only on the games with the cheapest draw price. Ties are broken by low goals, bookings and league draw rate.
    - The draw-factor study (46,758 matches) found nothing that beats the bookmakers' draw price: bookings were a hint only, and team draw rate, goals, shots and closeness added nothing. So the price decides where draws go.
    - State the cost each time. On the 16 Oct card it was 10+ 2.97% → 2.38%.
10. **Psychology (R18, from 2026-10-07):** on the pitch, only concrete one-sided facts count (motivation gap, dated emotional event, morale shock, crowd); never "momentum" or "due". In our heads, every slip passes a brain-trap check, the expected best score across the slips is stated so a normal week isn't read as a near miss, and money staked and won is tracked in the ledger.

## How this repo actually uses it

Fixture Intelligence is built from public stats-site data (form, H2H, standings, injury/suspension news) rather than GPS tracking, referee databases, or weather feeds. Of the 67 factors below, only a subset is realistically backed by that data:

**Used, with real sourced data:**
- #9 Key Player Absence Impact / #11 Cumulative Injury Burden / #12 Suspension Cascades — from injury/suspension notes gathered per fixture
- #18 Win/Loss Streak Psychology / #24 Variance in Recent Results — from last-5 form strings
- #20 Points-Per-Game Trajectory / #21 Goals Conceded Trend — from current standings and goals for/against
- #33 Psychological Bogey Teams (H2H curse) — from head-to-head history
- #34 New Manager Bounce / #35 Club Stability vs Unrest — flagged where sourced (e.g. a mid-season managerial sacking)
- #54 Expected Goals (xG) Differential — only where a source publishes xG (Understat/FBref; mainly "big 5" leagues)
- #38 Relegation Zone Desperation / #39 Promotion Clinch Scenarios — from league position context

**Explicitly NOT used (no reliable data source for these matches):**
- Set piece conversion (#2), pressing intensity/GPS (#3, #5), defensive line height (#4) — needs tracking/event data this app doesn't have for these fixtures
- Weather (#43, #44, #46), pitch condition (#45, #47), referee tendencies (#51, #52, #53) — not part of the sourced research
- Travel/fatigue/altitude (#26, #28, #29, #30, #31) — not tracked for domestic league fixtures at this level
- Anything below "Medium" impact in the original guide (crowd noise, ball familiarity, superstition, meal timing, sleep) — noise relative to what's actually available

Each fixture's `analysis.confidence_note` in `data/fixture_intelligence/*.json` should be read with this in mind: the `outcome_estimate` is a qualitative lean informed by the factors above that had real data, not a calibrated statistical model, and should not be read as having the same reliability as the framework's own "75%+ accuracy" claim (which assumes access to the full factor set, including tracking/weather/referee data this app does not have for these matches).

## Calibration log

Real-world scoring keeps this honest. Each entry below is a dated backtest against actual results, followed by the ruleset it produced. Rules accumulate — a later entry supersedes an earlier one only where they conflict.

### 2026-09-19/20 slate — 17 fixtures, first backtest

Predicted a single Home/Draw/Away "Overall Read" for all 17 fixtures plus BTTS/Over-2.5/Over-1.5 markets. Results:

| Method | Hit rate |
|---|---|
| Overall Read (H/D/A) | 7/17 = 41% |
| Form Trend (H/D/A) | 7/17 = 41% |
| Head-to-Head (H/D/A) | 5/17 = 29% |
| Attack/Defense (H/D/A) | 5/17 = 29% |
| BTTS | 8/16 = 50% |
| Over/Under 2.5 | 8/16 = 50% |
| Over/Under 1.5 | 12/16 = 75% |

**Baseline comparison:** a trivial "always pick Home" strategy also scores 7/17 (actual split was 7 home wins, 5 away wins, 5 draws). The Overall Read and Form Trend columns did not beat this naive baseline. The H2H and Attack/Defense columns scored *worse* than it — on this slate they were net-negative signals, not net-positive ones.

**Root causes identified:**
1. The Overall Read column predicted zero draws across all 17 fixtures, despite draws making up 29% of actual outcomes (5 of 17) — including matches where the fixture's own `outcome_estimate` had Draw within a few points of the top pick (e.g. Roma-Inter: 33/29/38).
2. Two fixtures picked as confident BTTS-Yes/Over-2.5 legs (Stuttgart-Dortmund, Schalke-Elversberg) finished 0-1 and 0-0 — both had an elite recent defensive number (GA ~0.7/game or better) that was noted in the sourced data but not allowed to override the attacking-optimism lean.
3. A contrarian Under-2.5 pick for Parma-Genoa (based on last season's two 0-0 meetings) missed (actual 2-1) — misapplied Factor #38 (Relegation Zone Desperation), which predicts *volatility*, not caution.
4. H2H and early-season GF/GA (3-4 game samples) underperformed a coin flip, consistent with those being high-noise, low-signal inputs at this sample size and this far removed from the squads/managers involved.

**Ruleset adopted from this backtest (applies to all future predictions on this repo):**
- **R1 — Draw trigger:** if the top two outcome probabilities are within ~8 points of each other AND both teams have similar recent points-per-game (within ~0.3 pts/game), the primary Home/Draw/Away pick becomes **Draw**, not a forced decisive pick.
- **R2 — Small-sample discount:** any GF/GA or form line built from fewer than 5 games is a weak, noisy prior. Blend it with the team's longer-run form (last full season's finishing position/form) rather than trusting the early-season number at face value.
- **R3 — Defensive-solidity override:** if either side is conceding under ~0.7-1.0 goals/game, pull BTTS and Over-2.5 toward No/Under regardless of the opponent's attacking output. This signal outranks generic "both teams have scored recently" reasoning.
- **R4 — H2H decay:** downweight head-to-head history further the more seasons old it is and the more a league has heavy year-to-year squad turnover (true of most leagues below the top divisions covered here). Treat it as a tiebreaker, not a primary signal.
- **R5 — Desperation/volatility fixtures get lower confidence, not contrarian confidence:** relegation six-pointers, promoted-team "surprise story" fixtures, and new-manager-bounce games should be flagged as high-variance and given a wider/lower-conviction estimate — never a confident pick in either direction off a small sample or an old H2H trend.
- **R6 — Always backtest:** every future slate gets scored against actual results using this same table format before the next slate is predicted. If a method (H2H, Attack/Defense, etc.) is net-negative against the naive "always Home" baseline over two consecutive slates, retire it or re-weight it down rather than carrying it forward unchanged.

### 2026-09-26/27 slate — 17 fixtures, jackpot-curated slate, second backtest

This slate was explicitly curated by a jackpot compiler for volatility (odds bunched within a few points across almost every game). Three strategies were scored against actual results:

| Strategy | Score |
|---|---|
| Pure market-favourite pick, every leg | 8/17 (47%) |
| Persisted "official" outcome_pick (mix of news + light disruption) | 8/17 (47%) |
| Unused "Heavy Disruption" variant (leaned hardest into Draw) | **9/17 (53%)** |

**Confirmed finding: draws occurred at 41.2% (7/17) on this slate** — following 29.4% (5/17) on the first slate. Two slates, both well above the generic ~25-27% baseline. This is now a repeating pattern, not a one-off: **jackpot-curated fixtures draw more often than ordinary football**, plausibly because compilers select evenly-matched games specifically, and an evenly matched game is mechanically more likely to finish level.

**Cross-method divergence:** the pure-odds slip and the news-researched slip only agreed on 3 of their combined correct picks (#3, #6, #11) — everywhere else they diverged, each catching different rights. Between the two, at least one was correct on 13 of 17 legs. Market odds and independent news research are not redundant signals; they catch different things and are worth running as parallel, genuinely separate lines rather than blending into one narrative.

**Both methods failed identically on 4 legs (#1, #7, #8, #14):**
- Two were draws neither method picked (#1 Tranmere 1-1 Walsall, #14 Lithuania 1-1 Azerbaijan) — #14 is notable because Azerbaijan's data had been explicitly flagged as "not found," and the pick still went to the *known* side (Lithuania) to win outright rather than defaulting to Draw under real uncertainty.
- One was a strong favourite (Cannes, unbeaten and in-form by both odds and news) held to a 0-0 by a defensive performance neither signal source anticipated (#7).
- One was a genuine upset neither signal source saw (#8 Paris13 beat the odds/news favourite Bastia 1-0).

**Rules adopted from this backtest (supersedes/extends the previous ruleset where noted):**
- **R7 — Draw floor for jackpot-curated slates:** default Draw prior rises to ~35-40% for fixtures on a slate that is itself curated for volatility (tight odds spread across nearly every game), not the generic ~25-27%. Confirmed by two slates now.
- **R8 — Data-gap defaults to Draw:** when one side's current form/data is an explicit gap ("not found," thin sample), the pick defaults to Draw rather than backing the side with more available information by default. R1's draw-trigger condition is satisfied by a data gap, not just a close numeric probability.
- **R9 — Cross-method disagreement is a Draw signal:** when independently-derived signals (market odds vs. researched news) disagree on the winner, treat the disagreement itself as evidence of a toss-up and default to Draw, rather than picking whichever narrative is more persuasive.
- **R10 — Run odds-based and news-based lines as parallel, separate predictions, not one blended narrative:** the two methods caught different correct results on this slate (only 3 of their combined correct picks overlapped). A single blended "tactical read" per fixture discards this diversification value. Where they agree, confidence is higher; where they disagree, apply R9.
- **R11 — Even the best strategy this round (9/17, 53%) is barely better than a coin flip.** For a genuine jackpot product requiring a high correct-count threshold, no single-point-prediction method tested so far is anywhere close to sufficient — slip construction must lean on combinatorial coverage (a reduced/wheel system across the highest-uncertainty legs) rather than trying to out-predict a deliberately hard product leg-by-leg.

### Correction to R7 — same slate, actual placed-slip result (real money, SportPesa Mega Jackpot Pro 17)

The persisted "official" pick for this slate predicted Draw on 9 of 17 legs (53%) — against an actual draw rate of 41% (7/17). Breaking down the 9 misses by type:

| Failure type | Count | Legs |
|---|---|---|
| Picked a winner, actual was Draw | 3 | #1, #7, #14 |
| **Picked Draw, actual was a clear winner** | **5** | **#8, #9, #13, #16, #17** |
| Picked wrong side (no draw involved) | 1 | #5 |

**The dominant failure mode was over-applying Draw, not under-applying it.** Every one of the 5 "picked Draw, missed a real winner" legs had a genuinely reasonable directional signal available (Bastia's better away form, La Roche's unbeaten run, Córdoba's better points tally, Ireland's ranking edge, Portugal's ranking edge) that got overridden by the draw-floor instinct instead of just tempered. #13 (Valladolid 3-1 Córdoba) is the clearest case: correctly identifying that the market's odds overstated Valladolid was right — but the fix should have been *reduce confidence in Valladolid*, not *flip to Draw*, and they won by two.

**R7 is revised**: the draw-floor is a **surgical override for specific legs with a confirmed conflict or data gap (R8, R9)**, not a blanket increase in draw frequency across an entire slate. Raising the aggregate draw-rate prior for volatility-curated slates is still empirically supported (confirmed twice now) — but it must not be spent by converting otherwise-good single-direction signal into a hedge. If a leg has one clean, uncontradicted signal (one side clearly stronger by both position and something else concrete), keep the direction and only reduce the confidence estimate; reserve the actual Draw pick for legs where R8 or R9 specifically triggers.

### Root-cause diagnostic — six hypotheses tested against all 34 fixtures (both slates)

Ran a quantitative test of six candidate explanations for the prediction errors, rather than assuming which one applied. Script: `scratchpad` (not committed; rerunnable against `load_all_fixtures()` + the slate-2 odds table). Results:

| Hypothesis | Verdict | Evidence |
|---|---|---|
| Model bias | Confirmed, but see below - it's instability, not a fixed bias | Pooled picks: Home 29.4% (actual 35.3%), Draw 26.5% (actual 35.3%), Away 44.1% (actual 29.4%) |
| Poor/missing data | Confirmed, localized to specific competition tiers | Already established via R12 (French Ligue 3 0/3, weak-nation internationals 1/4) |
| Calibration problems | Confirmed | Brier score 0.6316 vs. 0.6667 for a flat 1/3 prior - only a ~5% relative improvement over knowing nothing. Confidence-bucket hit rates are not monotonic (see below) |
| Market efficiency | Confirmed | On slate 2, market-favourite-only scored 8/17 (47.1%), my picks also scored 8/17. Where market and I *disagreed* (12 of 17 legs), my pick was correct 5/12 and the market pick was correct 5/12 - an exact tie |
| Bookmaker margin | Confirmed, quantified | Average overround across slate-2 odds: 9.47% per match (range 6.2%-12.1%) - a real, compounding structural tax across a 17-leg product |
| Selection bias | Confirmed across both slates | Draw rate 29.4% then 41.2%, pooled 35.3%, vs. a commonly-cited ~24-27% general baseline (that baseline is a standard football-analytics heuristic, not independently re-verified against a live database this session) |

**Two findings beyond the original hypothesis list:**

1. **Instability, not a fixed bias.** The pooled "+14.7pp Away" figure is misleading in isolation: slate 1 predicted zero draws across 17 games; slate 2 predicted draws in 9 of 17. This is an overcorrection swing between backtests (reacting to the immediately preceding lesson) rather than convergence toward a stable, calibrated draw rate. **R13**: commit to a fixed draw-rate policy per slate in advance rather than adjusting reactively leg-count-wise after each backtest.

2. **Stated confidence does not track actual accuracy - sometimes inversely.** Hit rate by confidence bucket: high 1/1 (100%, n too small to matter), medium-high 2/4 (50%), medium 8/21 (38.1%), low-medium 0/2 (0%), **low 4/6 (66.7%)**. Low-confidence fixtures outperformed medium-confidence ones. **R14**: do not use the subjective confidence label as the classifier for "banker" vs. "live" legs (e.g. in `src/jackpot_wheel.py`'s `classify_legs`) until it has been independently recalibrated - it is not currently validated to discriminate accuracy.

**Practical implication for R9 (cross-method disagreement -> Draw)**: this rule is still directionally reasonable (disagreement is a real uncertainty signal), but the market-efficiency finding above shows that *disagreeing in order to back my own research over the market* adds no measured value. R9's Draw override remains sound; a rule to "trust my research over the market when they diverge" would not be, and should not be adopted.

**R15 - objective probability-gap check (supersedes using the subjective confidence label for banker/live classification, per R14):** bucketed the actual gap between top and second outcome_estimate (not the subjective label) against accuracy, n=34: smallest-gap tercile (avg gap 0.009, i.e. near-flat) scored 2/11 = 18.2% - *worse than random* - middle tercile (avg gap 0.045) scored 7/11 = 63.6%, largest tercile (avg gap 0.195) scored only 6/12 = 50%. Correlation is weak and non-monotonic (r=0.298). Conclusion: when the top-two estimates are within roughly 0.02 of each other, do not take the nominal top pick - default to Draw explicitly, since a near-tied internal estimate carries no real information and picking "whichever is a hair higher" measured worse than chance. Do not treat a wide gap as license for high stated confidence either - the widest-gap tercile still only hit 50%.

### Consolidated decision procedure (synthesizes R1-R15 into one executable checklist)

For each fixture, in order:

1. **Gather data**: form (discount if <5 games, R2), H2H (decay by age/league turnover, R4), league position/points, injury/suspension news, market odds if available. New for the next slate, tracked as separate untested variables: player ratings/style-matchup, weather forecast, stadium/pitch context.
2. **Flag data completeness.** If either side's data is a genuine gap ("not found" on core signals), say so. A data gap means less certainty, not a draw.
3. **Build outcome_estimate from this game's own margin-removed odds**, then adjust only for this game's own dated facts. No prior carried from earlier jackpots (R17; the old 35.3% draw prior is retired).
4. **Determine outcome_pick:** the favourite from this game's odds, unless this game's own facts give a concrete reason to change it (slip rules in the ruleset above). No automatic draw triggers; a draw needs its own short price and its own reason.
5. **Do not fade the market by default.** Where odds exist, treat market-implied probability as a co-equal input, not something to override on research alone (R9/market-efficiency finding: disagreeing added zero net value last round).
6. **Confidence labeling**: until independently revalidated, do not assign a subjective high/medium/low spread that isn't shown to track accuracy (R14). Use the R15 gap bucket only as a provisional, still-unproven signal for banker/live wheel classification - not as a claim of real confidence.
7. **Log new variables (weather, player-style, stadium) as distinct, separately-tagged inputs** this round, so the next backtest can isolate whether *they* specifically add value, rather than lumping them into the same bucket as form/H2H/news that has already been tested twice with weak results.
8. **No slate-wide targets.** Don't set a number of draws, homes or aways for the slate. Each pick comes from its own game (R17; R13 retired).
9. **Always backtest (R6)** the completed slate the same way, updating this procedure only where the new evidence actually supports a change - not by reacting to a single slate's specific misses.

**R12 — Competition-tier coverage gates confidence, independent of direction.** Clustering the 17 results by competition: English lower league went 3/4, MLS went 2/2, but French Ligue 3 (a newly-professionalized, thinly-covered third tier) went **0/3**, and the bottom-tier Nations League internationals (weakest-ranked nations) went **1/4**. The failure in those two clusters wasn't a directional bias (wrong side vs. wrong draw-call) — it was that the underlying news signal was too thin to support *any* confident pick, in either direction. When a competition tier has this little public coverage, treat every leg from it as high-uncertainty by default, regardless of what the sparse available data seems to suggest.

### 2026-10-07 — Par score and the outside-tipster benchmark

On 2026-10-06, 14 Kenyan jackpot tipster sites were checked against the 2 Oct (13-game) and 3–4 Oct (17-game) results. The ones that could be scored are now in the ledger (`"tipsters"` in each slate file; `python -m src.jackpot_ledger` prints them).

| 3–4 Oct, 17 games | Correct |
|---|---|
| Random picks, expected | 5.7 |
| Favourites slip, expected from the margin-removed odds | 6.6 |
| Favourites slip, actual | 6 |
| Free tipsters, single picks only (4 sources), actual average | 6.0 |
| Our 6 slips, actual average / best | 6.5 / 8 |

**R16 — 6–7 correct is par, not failure.** SportPesa's 17-game card had an average favourite chance of 39% (13-game card on 2 Oct: 45%). Even perfect knowledge of the true odds expects only ~6.6/17. Tipsters, the favourites and our slips all scored around par. Uses:
- Judge every slip and style against `favourites_expected`, not against "it should have got 12".
- State the chance of a big score from the odds. The 3 Oct favourites slip: 10+ about 1 in 13, 12+ about 1 in 124, 13+ about 1 in 545, 17/17 about 1 in 9.8 million (games treated as independent).
- **Never fade the tipsters.** If they're wrong 60% of the time, that 60% is split between two outcomes, each less likely than their pick. Our own picks against the favourite were right 18–22% of the time against 41% for the favourite on the same games.
- **Crowd tie-breaker (unproven).** Bonus tiers appear to be shared among winners: 12/17 paid KSh 4,280 on 28 Sep but KSh 10,904 on 4 Oct. So when two near-even tweaks are equally justified, prefer the one that differs from the tipster consensus. This can only change the payout if you win, not the chance of winning, and it is never a reason to change a favourite by itself. Whether tipster picks reflect what most players pick is unverified.
- Record free tipster picks the day before kickoff with the time posted, so they get a dated record the sites don't keep themselves.

### 2026-10-07 — Every jackpot from scratch (user rule)

| Jackpot | Home | Draw | Away |
|---|---|---|---|
| 19–20 Sep (17) | 7 | 5 (29%) | 5 |
| 26–27 Sep (17) | 5 | 7 (41%) | 5 |
| 2 Oct (13) | 4 | 3 (23%) | 6 |
| 3–4 Oct (17) | 9 | 4 (24%) | 4 |

**R17 — No patterns carried between jackpots.** The "jackpot slates draw far more" rule (R7) was built after the 41% slate and failed on the next two (23%, 24%). The most common result was different almost every week. So every game is predicted from its own odds and its own dated facts, with no draw prior, no slate-wide draw target, no outcome quotas, and no reasoning from earlier jackpots' results or league stereotypes. Retired: R7, R8 (data gap → draw), the draw default in R9 and R15, and R13 (draw-rate target). Kept, because they are about method rather than expected results: anchor on each game's own favourite, ≤3 reasoned changes per slip, dated and verified facts, the par score computed from each slate's own odds (R16), and the ledger's check of which slip-building methods have failed.

### 2026-10-07 — How SportPesa picks its games, checked against our data

| Claim (industry practice; SportPesa doesn't publish its criteria) | Our data | Verdict |
|---|---|---|
| Games are chosen for balanced 1X2 odds | Balance score (1 = perfect three-way coin flip): 3 Oct 0.989, 2 Oct 0.968. Favourite averaged 39% on 3 Oct; the draw was never the favourite on any of 30 games | Confirmed |
| Draw-prone fixtures | Draw priced at 28% on average on 3 Oct; actual draws 29%, 41%, 23%, 24% | Already in the odds; not a reason to add draws (R17) |
| Mostly 2nd-tier European leagues | Mostly 2nd-4th tiers across many countries (3 Oct: 11 countries, at most 4 from England) | Confirmed, and lower than claimed |
| Friendlies and headline games avoided | 26–27 Sep card had Mexico v Colombia (friendly), England v Spain, Norway v Portugal | Not true for SportPesa |
| KSh 99 stake, bonuses 12-16 correct | News coverage | Confirmed |
| Postponed game | SportPesa holds a live public draw to set the result | Confirmed (news); random, nothing to research |

**What it changes:** the difficulty is built in: SportPesa makes every game a near coin flip on early-week odds. The only things that can make a game less balanced afterwards are specific to that game: late team news, lineups, motivation, weather, and the market moving away from the SportPesa card price. That's where research effort goes. The researcher now reports, per game, how far the current market has moved from the card price and whether the favourite has changed.

### 2026-10-07 — Human psychology as a factor (R18)

**On the pitch (per game, dated facts only).**
- Motivation gaps (one side has much more at stake), emotional events (farewell, derby, new manager's first games, unpaid wages, takeover), morale shocks (a heavy defeat in the last week) and crowd (hostile, empty or neutral ground; it works mainly through referees, and home advantage shrank in the empty-stadium seasons of 2020-21).
- Streaks, "momentum" and new-manager bounces are mostly regression to the mean: clubs sack managers after unusually bad runs, which tend to end anyway. The odds already include form.
- The psychology percentages in factors #18 and #33-#42 below ("+20%", "-35%") come from the supplied guide and are untested. Don't apply them as numbers.

**In our heads (the bettor's brain).**

| Brain trap | How it showed up here | Guard |
|---|---|---|
| Near-miss effect: near misses fire the brain's reward system almost like wins (Clark et al., *Neuron*, 2009) | 8/17 felt close. The odds expected a best of 8.2 from our 6 slips on 3 Oct (7.6 from 21 slips on 2 Oct; best was 7) | `best_expected` in the ledger |
| Gambler's fallacy | "We've lost 4 jackpots, we're due" | Each jackpot is independent (R17) |
| Recency / overreaction | Method changed after every loss: draw-heavy → simulation → contrarian | Ledger needs 20 decided games before a verdict |
| Hindsight bias | "The signs were there" after results | Only facts dated before kickoff count |
| Narrative fallacy | Revenge, farewell or "bogey team" stories feel like evidence | Every change needs a dated fact |
| Illusion of control | More agents and research feel like more control; par barely moves | Par and expected best stated every week |
| Loss aversion and chasing: losses hurt about twice as much as equal gains (Kahneman & Tversky) | Pressure to win back losses with more slips or bigger stakes | Fixed budget set before seeing slips; money table in the ledger |
| Availability | News shows the jackpot winners, not the many who lost | The ledger's money table: our own totals |
| Multiple-slip illusion | 6 slips feel like 6 chances; they share most picks | 3 Oct: any of 6 slips 12+ = 1 in 31, vs 1 in 124 for one slip and 1 in 21 if they were independent |

**The crowd's brain (2026-10-07):** most players back favourites, home teams and famous names. That affects only how many people share a prize (R16 tie-breaker), not the chance of winning.

### 2026-10-08 — Draw study (R19)

The user pointed out that a slip can't simply leave out draws, because these games are built to be close. The 9 Oct card expects 3.55 draws in 13, with only a 1.6% chance of none. The full study is in documentation/draw_study.md (86,868 matches, 38,281 balanced, checked on 2019-22 and 2023-26 separately). In short:
- **Draws are slightly underpriced** in balanced games: 29.6% actual against 28.9% in the odds. Favourites are exact at 40.0% against 40.0%.
- **When the odds rank the draw 2nd**, it is the better backup pick than the other side: 31.6% against 26.4%, p < 0.000001 in both periods.
- **When the draw is ranked 3rd and under 29%**, or the game is higher-scoring, the other side is the better backup.
- **A draw is only level with the favourite as a main pick in near three-way ties** (favourite ≤36%, draw ≥31%), and that edge isn't proven.

This replaces the old "short draw price + reason" rule with `draw_role` per game (ruleset item 2).

**Tipster factor, refined (R16, 2026-10-08).** On the 9 Oct card the tipster consensus matched the bookmaker favourite on 11 of 13 games. Picking "the other alternative" everywhere expected 4.37/13 (random picks: 4.33) and 13/13 at 1 in 1.5 million, against 1 in 159,000 for the favourites, so blanket fading is out. The valid version is one **targeted tipster-fade slip** (style `tipster-fade`):
- Where the tipsters oppose the market, back the favourite (or the draw they ignore).
- On near-even games where the tipsters agree with the favourite, take the alternative they don't pick.

Swapping that slip in for the weakest slip raised every set-level number (any 10+ 1.94% → 2.18%). The tipsters picked 3.5 draws in 39 picks, so draws are the main alternative the crowd leaves alone.

---

### 2026-10-09 jackpot (13 games): scored 2026-10-10

Results: H H H A D A A H A H H A D. Two draws, against 3.55 expected.

**Scores:**
- **Played slips:** S2 9/13, S1 6/13, S6 5/13.
- **Unplayed slips:** S4 8, S5 (tipster-fade) 8, S3 5; tail optimiser O1-O3 6/7/6.
- **Favourites:** 6/13, against par 5.2. The best slip's expected score was about 6.6.
- **Tipsters:** Jackpot Kenya 8/13 (4 double chances), Sokapedia 6/13, AdiBet 3/13.

**What went right:**
- G10 Avellino 4-1 v Sampdoria. This change was based on dated news (Abildgaard's ban, eight Sampdoria players unavailable).
- The draws on G5 (either-backup, low-scoring) and G13.
- S5's G2 Braunschweig.

**What went wrong:**
- G6: draw on all three played slips. The Friday market moved towards Sarmiento, and Sarmiento won 3-1.
- G7: Annecy won at Dunkerque. Annecy had won the last three there without conceding, and Mayela was suspended; this was noted but not acted on.
- G12: Kerry won.

**Late price moves.** Between Wednesday and Friday, 5 of 7 price moves pointed to the right result: G1, G4, G6, G11, G12 right; G2 and G13 wrong. Tested on history, the effect is real (R22).

**Style verdicts:** all still "not enough evidence". draw-heavy changes were right 42% of the time against 26% for the favourite (13/20 decided games). One week can't overturn the simulator's 12,580 cards.

### 2026-10-10/11 Mega Jackpot (17 games): scored 2026-10-12

Results: A H D H H H D A A H H A A A H A D. Three draws.

**Scores:**
- **Played slips:** P1 8/17; P2 6; R1, R2, R3, P3 5. No bonus (12+ needed).
- **Unplayed:** tail optimiser with one 3-draw slip (D1) **9/17, the best of every set**. Optimiser M3 8, odds-based 4-draw W2 8.
- **Favourites:** 7/17 against par 6.6. Research model picks 6/17.
- **Tipsters:** Jackpot Kenya 9 (8 double chances), Sokapedia 8 (single picks), AdiBet 7, Chambuabet 7.
- **Sunday slips for games 5-17:** 2-7/13. Favourites got 5/13 on Sunday, an upset-heavy day.

**What worked and what didn't:**
- **Research disagreements went 1 for 6:** Ipswich right; Forest, Strasbourg, Teplice, Gaziantep and Excelsior wrong.
- **Late favourite changes went 0 for 4:** G3 Brentford (draw), G5 Forest, G8 Gaziantep, G13 Aalesund. Late money was also wrong on G4 Paris FC and G16 Cadiz.
  - The historical edge (38% v 32%) allows a weekend like this: about 15% chance of 0 from 4.
  - Live record so far: 9 Oct 5 of 7 moves right, this weekend about 2 of 8.
  - R22 stays, but it is a small edge.
- **Tipster picks against the bookmakers won twice** (Mantova, Sporting), after losing twice on 9 Oct. That's 2 of 4, so no edge either way.
- **Psychology:** Vaduz and Corum right (P2), Aalesund wrong; the draw on Racing-Valencia (a new manager's debut) right in all three P slips.

**Lesson:** the validated baseline, the market-odds optimiser with one 3-draw slip, beat every overridden set this weekend. One weekend proves nothing, but the ledger now leans that way: research-model changes were right 15% of the time against the favourite's 37% on the same games (14/20 decided).

### 2026-10-12 — SportPesa archive study (R23)

The user pointed to SportPesa's public archive. All 199 Mega Jackpot Pro cards since Dec 2022 (3,383 games) were read from the widget's history feed and matched to closing odds for 2,480 games. Full tables: documentation/sportpesa_archive_study.md.
- **Results:** Home 35.7%, Draw 31.1%, Away 33.1%, about 5.3 draws per card.
- **Selection:** favourites at 35-47% only.
- **Prices:** favourites are honestly priced. The underdog side wins 2.8 pts less than priced and the draw 1.8 pts more. This is a candidate effect, now in the optimiser as R23 `--tilt` at half strength.
- **Backups:** on these cards the draw was at least as good a backup as the other side even when ranked 3rd, which amends R19.
- **Patterns:** no slot or clustering patterns.
- **Crowd:** 17/17 has been won once in 199 cards; the median 12/17 bonus is KSh 9.4k.
- **Backtest:** on 46 fully priced cards, the 3-slip optimiser reached 12+ on 3 cards and the favourites slip on 1.


### 2026-10-16 jackpot (13 games): scored 2026-10-18

Results: A D H A A A D A H H A A A (2 draws).
- **Played:** the birthday slips B1-B5 (3 draws each) scored 4, 5, 6, 5, 5. No bonus; KSh 495 lost.
- **Favourites:** SportPesa's Monday card favourites got 8/13; the Friday-morning bookmaker consensus 6/13; par 5.3.
- **Unplayed:** the Monday optimiser slips M1 and M5 got 8; Sokapedia 8 (10 with double chances).

**What worked and what didn't:**
- **Draws:** 2 of 77 draw picks were right. They sat on games 5, 6, 11 and 12, which all ended in away wins; the real draws (games 2, 7) were priced at 26-27%.
- **News-backed side switches:** 3 for 3 (UCD after Wexford's bans, Trelleborg with Ruuska back, Nancy on late money).
- **Late favourite flips:** G1 to Koge lost, G4 to Lunds lost, G5 to Nancy won. R22 stays: it rests on 47,762 matches, and on 316 SportPesa archive flips the closing favourite won 35.1% against 32.9%. One week doesn't overturn it.

**New ledger table** (`change_types`): side switches were right 37% against 41% for the favourite on the same games (46 calls); draw picks 25% against 39% (36 calls). The odds were roughly right about both.

**Lesson:**
- Forced draws are the main cost of the user's draw rules.
- News-backed side switches on near-even games are nearly free.
- Within the user's rules: the minimum number of draws, on the cheapest-draw games, and changes made through dated news facts.

## Full factor list (as supplied)

### Quick reference summary

CRITICAL (40-50% impact): #1 Tactical Shape Matchup, #9 Key Player Absence Impact, #18 Win/Loss Streak Psychology, #26 The 48-Hour Recovery Rule, #54 Expected Goals (xG) Differential

HIGH (30-40% impact): #2 Set Piece Conversion Rate, #3 Pressing Intensity, #4 Defensive Line Height, #10 Replacement Quality, #11 Cumulative Injury Burden, #12 Suspension Cascades, #19 xG Over/Underperformance, #20 Points Per Game Trajectory, #21 Goals Conceded Trend, #27 Fixture Congestion, #28 Travel Distance & Jet Lag, #33 Psychological Bogey Teams, #34 New Manager Bounce, #35 Club Unrest, #43 Wind Conditions, #44 Rain Conditions, #51 Referee Bias

MEDIUM-HIGH (15-25%): 15+ factors (#5, #13, #14, #15, #22, #23, #29, #30, #31, #36, #37, #38, #45, #46, #67)

MEDIUM (5-15%): 20+ factors (#6, #7, #8, #16, #17, #24, #25, #32, #39, #40, #41, #42, #48, #49, #52, #53, #56, #57, #58, #59, #60, #61)

LOW / LOW-MEDIUM (<5%): #50, #62, #63, #64, #65, #66

### Full descriptions

**#1 Tactical Shape Matchup** — CRITICAL. E.g. 4-2-3-1 vs 3-5-2 creates different vulnerabilities. Map formation against opponent's strengths/weaknesses.

**#2 Set Piece Conversion Rate** — HIGH. 30-40% of goals from corners/free kicks. Compare team conversion rates.

**#3 Pressing Intensity (by minute)** — HIGH. Loss of 15-20% pressing effectiveness after 60 minutes; late-game pressing breakdowns create chances.

**#4 Defensive Line Height** — HIGH. High line vulnerable to pace (+25% clear chances); low line vulnerable to through balls (+30%).

**#5 Transition Speed** — MEDIUM-HIGH. Possession-to-shot in <15s = 3x higher accuracy.

**#6 Wide Play vs Central Play** — MEDIUM. Wide pitch (110m+) favors wing-backs (+20%); narrow pitch (105m) favors central play.

**#7 Counter-Attack Trigger Points** — MEDIUM. Pressing teams concede 5-8 counter chances/match when losing possession; defensive teams concede 1-2.

**#8 Dead Ball Organization** — MEDIUM. Well-organized: 20% corner conversion vs 8% disorganized — 10+ extra goals/season.

**#9 Key Player Absence Impact** — CRITICAL. Holding midfielder missing -40%; striker -25%; wing-back -15%; squad player -5%.

**#10 Replacement Quality** — CRITICAL. Experienced backup -5%; decent backup -10%; academy/young player -25%. Can swing outcome 10-15%.

**#11 Cumulative Injury Burden** — HIGH. 1 injury -5%; 2 -10%; 3+ -20%; 4+ key injuries -35%.

**#12 Suspension Cascades** — HIGH. 1 suspension -5%; 2 same-position -15%; multiple -20%.

**#13 Return From Injury (First Match)** — MEDIUM-HIGH. Match 1: 70% fitness, +20% error rate; match 2: 80%/+10%; match 3+: 90%+/normal.

**#14 Fatigue Accumulation (Individual)** — MEDIUM-HIGH. 2 matches/4 days -5%; 3/7 days -10%; 4/10 days -15%; 5+/14 days -20%.

**#15 Age Factor in Fatigue** — MEDIUM-HIGH. <25yo with 4 matches/14 days -10%; 25-30 -15%; 30+ -25%.

**#16 Position-Specific Injury Impact** — MEDIUM. Missing CB -20% defensive structure; missing LB -15% flank/+5% opposite flank; missing holding mid -30%; missing striker -25%.

**#17 Long-Term Injury Psychology** — MEDIUM. Returning after 8+ weeks: +20% motivation for 3 matches, 1-2 extra chances.

**#18 Win/Loss Streak Psychology** — CRITICAL. 3+ wins +20%; 3+ losses -25%; 5+ win streak +30% psychological edge; 5+ loss streak -35%. Up to a 50-60 point swing.

**#19 xG Over/Underperformance** — HIGH. Scoring 30% above xG → expect -15% regression next 2-3 matches; 30% below → +15% improvement expected.

**#20 Points-Per-Game Trajectory** — HIGH. Trending up +15% win probability; trending down -15%. More predictive than raw current form.

**#21 Goals Conceded Trend** — HIGH. Conceding 50%+ above average signals defensive disintegration (-20%); 50% below average signals due-for-regression.

**#22 Clean Sheet Streaks** — MEDIUM-HIGH. 3+ clean sheets: +20% confidence but -10% concentration; one goal conceded breaks it (-30% next match confidence, 1-2 match recovery).

**#23 Scoring Drought Duration** — MEDIUM-HIGH. 3+ matches without a goal: -20% striker confidence, shot accuracy drops 5-10%.

**#24 Variance in Recent Results** — MEDIUM. Consistent (W-W-W-W-W) +20% next-match win probability; chaotic (W-L-W-D-L) ~50% prediction accuracy.

**#25 Recent Performance vs Similar Teams** — MEDIUM. More predictive than overall form; vs-top-4 and vs-bottom-6 records diverge.

**#26 The 48-Hour Recovery Rule** — CRITICAL. <48h turnaround: -20% sprint distance, -15% intensity, +20% errors; 48-72h: -10% sprint distance; 72h+: normal.

**#27 Fixture Congestion** — HIGH. 4+ matches/14 days: -20% pressing after 60min, -15% pass completion; 5+ matches: -25% overall.

**#28 Travel Distance & Jet Lag** — HIGH. <2h no impact; 8h+ long-haul: -15% first match, -8% second match.

**#29 Sleep Disruption From Travel** — MEDIUM-HIGH. 4am arrival -20% cognitive function; 6pm arrival minimal disruption.

**#30 Altitude Adaptation** — MEDIUM-HIGH. 1500m+: -25% first-match sprint performance; day 4 -50% penalty; normalized by week 2.

**#31 Midweek European Fatigue** — MEDIUM-HIGH. Thursday European + Sunday league: -12%; Tuesday European + Saturday league: -8%.

**#32 Turnaround Time** — MEDIUM. <24h -25%; 24-48h -15%; 48-72h -8%; 72h+ normal.

**#33 Psychological Bogey Teams (H2H Curse)** — HIGH. 0 wins in 15 meetings: conceding first goal triggers surrender mentality (-40%).

**#34 New Manager Bounce** — HIGH. Matches 1-3: +25% effort, shock results likely; match 4+: regression to normal.

**#35 Club Stability vs Unrest** — HIGH. Ownership drama + financial trouble + manager criticism combined: -25% team performance.

**#36 Revenge Motivation** — MEDIUM-HIGH. Lost previous meeting: +15% intensity, -5% discipline, +20% fouls, elevated red-card risk.

**#37 Title Pressure vs Nothing to Play For** — MEDIUM-HIGH. Title race: +20% intensity, -10% creativity (risk-averse); dead rubber: -15% intensity.

**#38 Relegation Zone Desperation** — MEDIUM-HIGH. Bottom 3, <5 matches left: +30% effort, -25% discipline — wild swings.

**#39 Promotion Clinch Scenarios** — MEDIUM. Already clinched: -15% intensity, +25% recklessness; still chasing: +25% intensity.

**#40 Team Spirit/Cohesion Level** — MEDIUM. High cohesion +10%; low cohesion -15%. Proxied via social sentiment, interviews, training reports.

**#41 Confidence in Individual Skill** — MEDIUM. Striker on a 5-game goal streak +20% shot accuracy; 5-game drought -30%.

**#42 Group Mentality After Embarrassing Loss** — MEDIUM. Loss by 4+: -20% confidence, +25% aggression; 2-3 week recovery.

**#43 Weather — Wind** — HIGH. <10km/h no impact; 30km/h+: -30% long-ball accuracy, +15% goalkeeper errors, favors possession teams.

**#44 Weather — Rain** — HIGH. Light rain: +5% technical-team advantage; heavy rain: -15% passing accuracy, +25% defensive advantage; waterlogged: -30% passing, near-random.

**#45 Pitch Dimensions & Surface** — MEDIUM-HIGH. Wide pitch (112m) +15% possession-team advantage; narrow (103m) +15% defensive-team advantage; bumpy +20% physical-team advantage.

**#46 Temperature Extremes** — MEDIUM-HIGH. <5°C: -15% agility, +20% injury risk; >30°C: -25% intensity after 60min, +30% cramping.

**#47 Pitch Condition (Quality)** — MEDIUM. Poor pitch: -15% passing accuracy, +20% errors; waterlogged: -30% passing, high chaos.

**#48 Crowd Noise & Communication** — MEDIUM. >100dB impairs visiting captain's communication; +5-10% favorable ref decisions for home team (subconscious bias).

**#49 Time of Kick-Off** — MEDIUM. 11am: -10% performance; 8pm: optimal (+2%); 10pm+: -15% visibility.

**#50 Atmospheric Pressure Changes** — LOW-MEDIUM. Falling pressure (storm): -5%, affects 10-15% of squad.

**#51 Referee Bias (Documented Tendencies)** — MEDIUM-HIGH. Strict referee: +15% technical-team advantage; lenient: +15% physical-team advantage.

**#52 VAR Decision Patterns** — MEDIUM. Refs who frequently overturn: 1-2 extra reversals/season, ±30% penalty frequency swing.

**#53 Home Referee Bias** — MEDIUM. First 45min: +5% favorable home decisions; last 15min: +10%.

**#54 Expected Goals (xG) Differential** — CRITICAL. +0.5 xG advantage: 65% win probability; -0.5 xG deficit: 25% win probability. Most reliable single predictor.

**#55 Shot Accuracy (%) vs Opponent** — HIGH. 35% vs 20% accuracy: 70% win probability. More predictive than shot volume.

**#56 Possession % Efficiency** — MEDIUM-HIGH. 60% possession + 85% pass accuracy = dominant; 60% possession + 50% accuracy = ineffective. Accuracy matters more than raw possession share.

**#57 Draw Clustering in League** — MEDIUM. After 2-3 consecutive draws: +15% draw probability (clustering effect); e.g. Argentine league ~35% draw rate with clustering.

**#58 Home/Away Win Rate Differential** — MEDIUM. 60% home / 30% away win rate signals psychological home dependency; a 20-point gap suggests true away strength differs from perception.

**#59 Media Pressure/Hype** — MEDIUM. Massive hype: -15% performance, +20% errors; under-the-radar: +10% performance.

**#60 Transfer Rumors/Drama** — MEDIUM. Star player rumors: -20% focus, +15% errors; confirmed transfer: -30% motivation for 1 week.

**#61 Contract Negotiation Timing** — MEDIUM. Final contract year and negotiating: +25% performance; no offers on the table: -15% motivation.

**#62 Managerial Criticism/Support Cycles** — LOW-MEDIUM. Manager criticized: +20% team effort (rally effect) for 2-3 matches; strong support: -5% motivation.

**#63 Ball Familiarity** — LOW-MEDIUM. Official ball changed mid-season: +8% misplaced passes first match, adjusted by match 2-3.

**#64 Ground Familiarity** — LOW-MEDIUM. Temporary stadium: -15% first 2 matches, normalized by match 3.

**#65 Superstition Compliance** — LOW. Disrupted pre-match ritual: -10% confidence in first 20 minutes; teams with consistent rituals perform more consistently.

**#66 Pre-Match Meal Timing** — LOW. Meal <2h before kickoff: -10% agility, +20% cramping; 3h+ before: optimal.

**#67 Sleep Quality (Previous Night)** — LOW-MEDIUM. Poor sleep: -25% sprint speed, -20% decision-making; highly individual response.

### Suggested workflow (as supplied)

1. Select 5-10 most relevant factors for the specific match.
2. Weight them: Critical 40%, High 35%, Medium-High 20%, Medium 5%.
3. Account for factor interactions, not isolated factors (e.g. wind + rain + poor pitch = high randomness; new-manager bounce + unrest + revenge motivation = elevated upset risk; injured holding mid + high defensive line = collapse risk).
4. Build a probability distribution rather than a single scoreline prediction.
5. Compare to market odds — a significant mismatch may indicate an edge.

This app applies steps 1-3 qualitatively wherever the underlying data was actually available (see "How this repo actually uses it" above); it does not compute steps 4-5 as a calibrated numeric model.
