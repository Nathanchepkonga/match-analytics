# Improvement scope and research agenda (started 19 Oct 2026, after Betika jackpot 2544)

Purpose: one place for what to improve and what to research next, with a test and a success measure for each item. Nothing here changes a live rule until it passes an out-of-sample test (see the guardrails at the end).

## 1. What jackpot 2544 taught us (Betika Must Be Won, 17-18 Oct 2026)

- Results H A A A D H D A A H A H H A A. Five slips scored 9, 8, 7, 7, 8 of 15; the non-Betika market favourites also scored 9; par was 6.4. Nothing reached 13, so nothing paid.
- Favourites failed on games 3, 4, 5, 7, 11, 12. Only 2 draws came (games 5, 7), while each slip held 3 draws and 15 draw picks in total returned 2.
- Both user-requested upset picks missed (Augsburg away, Man Utd away).
- The ledger now flags `tail-optimizer` as "worse than the favourite" (24 slips, changes right 23% against 53% for the favourite on the same games). That is a flag to investigate, not a final verdict.
- Process failures worth fixing: the Betika slate file was overwritten by another chat's SportPesa slate (same date id); two research agents ended without delivering a report; the odds sources that matter (Pinnacle, Betfair, Oddschecker, per-bookmaker tables) were unreadable, so favourites rested on a thin set of prices; Betika's results page needs a login.

## 2. Improvement scope

### A. Data and process (do first, cheap, no betting risk)
1. **Unique slate ids per product.** Use `<date>-betika` and `<date>-sportpesa`; add a `product` field to every slate; add a test that refuses to overwrite an existing slate with a different `product`. (Betika slate was rebuilt as `2026-10-17-betika.json` on 19 Oct.)
2. **Results fetcher.** Add `src/results_fetch.py` using ESPN public scoreboards (`site.api.espn.com/apis/site/v2/sports/soccer/<league>/scoreboard?dates=YYYYMMDD`) to fill `score` and `result`, because Betika's results page needs a login. The user still confirms against Betika.
3. **Price snapshots.** Save a timestamped price snapshot per game at each check (build, 10 am, 1 pm, close) with per-source prices, so line movement and late favourite flips (R22) can be measured instead of assumed.
4. **Save the slate as soon as it is built**, not at the end, and record which scheduled checks actually ran.
5. **Agent reliability.** Research agents hit rate limits and ended without a report. Split work into smaller blocks, require a file written within the first few steps, and have the main session read the file instead of trusting the hand-back.
6. **Tipster and crowd capture.** The free tipster sites rarely had the Betika card. Decide whether to keep collecting them or drop it; they were never used as inputs.

### B. Method (needs evidence before any rule changes)
7. **Why did tail-optimizer fall behind?** On near-even games a change is close to a coin flip, so a lower hit rate than the favourite is expected. Check with a proper test on the 75 changes, split by game gap and by draw versus side change, and compare with the historical backtest (12,580 cards) which found it better at the tail. Possible conclusion: the optimiser is right for tail probability but costs score on average, which only matters when the target is 13+.
8. **Draw placement.** Draws came 2 of 15 here, and draw picks have been right 14% of the time on our slips. Re-test the draw study (documentation/draw_study.md) on the 2026-27 season so far, and measure whether "cheapest draw price" ordering picked draws better than random near-even games.
9. **Market calibration.** Score the non-Betika consensus (and the Betika card) with Brier and log-loss on all ledger slates; check whether favourites win as often as priced in jackpot-selected games.
10. **News-fact ledger.** Every Tier 1 fact (injury, suspension, rest, referee) is logged per game with a date, a direction (for or against the favourite) and a label priced / possibly unpriced, then scored after the match. This is the only way to learn whether late news carries any value the odds miss. Hindsight is excluded by writing facts before kickoff only.
11. **Free xG.** The 2026-27 football-data files carry `HxG` and `AxG` columns for some leagues (the E0 file does). Check which leagues have them and use these instead of Understat, which was unreadable.
12. **Double Chance.** A double on one game costs the same as two singles that differ only in that game, so it is not a free extra. Verify that the optimiser's slips already cover the same combinations, so no separate method is needed. Only Game Pass tokens are free coverage.

### C. Week 8 and winner-takes-it weeks
13. **Different objective.** In the final week the jackpot goes to the highest score (terms, 16 Oct). The goal is the best score among all players, not 13+. Model it as: win probability = chance that our best score is at least the best of the other players.
14. **Crowd model.** Most players pick favourites or tipster picks, so many tickets share a score. Estimate the distribution of the top score from player counts (unknown), a favourites-heavy crowd assumption, and a sensitivity range; then compare a favourites-led set with a set that disagrees on a few near-even games.
15. **Missing evidence.** The search found no published week-8 winning scores or winner counts. Ask the user to note the score and number of winners for the next one, and record them.

### D. Tools and tests
16. Add tests for the ledger collision guard, the results fetcher and the price-snapshot writer.
17. Keep the scheduled-check prompts in the repo (documentation or a `docs/checks` file) so a rebuild does not depend on conversation memory.

## 3. Research agenda (question, data, test, success measure)

| # | Question | Data we have | Test | Counts as a result when |
|---|---|---|---|---|
| R-A | Does the optimiser hurt average score? | ledger, jackpot_sim history | paired comparison of slip scores vs favourites slip, per slate | n of 30+ slips and a confidence interval that excludes zero |
| R-B | Are draws priced right in jackpot-like games this season? | football_data 2026-27, ledger | actual vs priced draw rate in balanced games | 500+ games, both halves of season agree |
| R-C | Do late news facts predict surprises? | news-fact ledger (new) | hit rate of "possibly unpriced against favourite" facts | 100+ logged facts |
| R-D | Is the consensus better than Betika's card prices? | ledger odds vs market_odds_final | log-loss and Brier over all slates | 5+ slates |
| R-E | What score wins a week 8? | not found yet | user-recorded results | 2+ week-8 results |
| R-F | Does free xG add anything over the odds? | football_data HxG/AxG | model with xG vs odds-only, held out | out-of-sample log-loss gain |

## 4. Guardrails

- No rule is changed, added or retired from one slate's result. Hits and misses in one week are variance until a test says otherwise.
- Test changes out of sample, one change at a time, with the target decided first.
- Every jackpot is still built from scratch (no patterns carried over); the research above is about method, never about expected results.
- Facts are dated and written before kickoff; "not found" is stated, never filled with a guess.
- Honest chances are stated with every slip set. This is a long-shot product; 6-8 of 15 is a normal week.
- Betting and payments stay the user's decision.

## 5. Open questions for the user
- Did you place all five slips, and what did you win? (The ledger assumes 245 staked, 0 won.)
- Please record the winning score and number of winners for week 8 when it happens.
- Which items above should go first? Suggested order: A1-A3, then 7-9, then 13-14 for week 8.
