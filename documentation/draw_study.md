# Draw study (2026-10-08)

**Question.** SportPesa builds its jackpots from balanced games, so draws are always likely: on the 9 Oct card the odds expect 3.55 draws in 13 games, and the chance of no draws at all is 1.6%. Yet the draw is the least likely result in 12 of those 13 games. So where should draws go on a slip?

**Data.** 86,868 matches from 41 leagues, 2019-2026 (football-data.co.uk). The leagues include the English, Scottish, German, Italian, Spanish, French and Dutch top and second tiers, Turkey, Finland, Norway, Russia, Argentina and Ireland. Each match uses the average bookmaker odds before kickoff, with the margin removed. The extra leagues only have closing averages, so those are used for them. 38,281 matches are "balanced": the favourite's chance is 45% or less, like every jackpot game. Every rule below was checked separately on 2019-22 and 2023-26. Rerun it with `python -m src.draw_study`.

## Findings

**1. Draws are slightly underpriced in balanced games; favourites are priced correctly.**

| Period | Draws actual | Draws in the odds | Favourites actual | Favourites in the odds |
|---|---|---|---|---|
| All balanced games | 29.6% | 28.9% | 40.0% | 40.0% |
| 2019-22 | 29.6% | 29.1% | | |
| 2023-26 | 29.7% | 28.7% | | |

**2. A draw is only as good as the favourite in near three-way ties.** That means the favourite's chance is at most 36% and the draw's at least 31%. The draw then won 35.5% against the favourite's 33.2% (n=1,695). It was ahead in both periods, but the gap isn't proven (p=0.25). Everywhere else the favourite is the better single pick.

**3. Choosing the backup pick (the alternative to the favourite in slips 2+):**

| Situation (from the game's own odds) | Draw right | Other side right | Verdict |
|---|---|---|---|
| Draw ranked 2nd by the odds (n=10,567) | 31.6% | 26.4% | **Draw is the better backup.** Held in both periods, p < 0.000001 |
| Home and away within 2 pts (n=4,327) | 31.0% | 33.8% | Other side is better (p=0.02) |
| Draw ranked 3rd, under 2.5 goals 55%+ likely (n=4,674) | 31.9% | 31.5% | About equal: choose on the game's facts |
| Draw ranked 3rd, under 2.5 goals less than 50% likely (n=7,369) | 27.8% | 31.3% | Other side is better (p=0.0001) |
| Draw ranked 3rd and under 29% (n=19,444) | 27.7% | 31.7% | Other side is better. Held in both periods, p < 0.000001 |

## The rule (`draw_role` in src/jackpot_ledger.py)

Every input comes from that game's own odds, so nothing is carried over from earlier jackpots (R17).

- **draw-main:** the favourite is at most 36% and the draw at least 31%, or the draw is the favourite. A draw may be the pick in slip 1 if a dated fact supports it.
- **draw-backup:** the draw is ranked 2nd. When a slip changes this game, it changes to the draw. Across the slips, the draw must appear in at least one.
- **either-backup:** the draw is ranked 3rd and the game is low-scoring (under 2.5 goals at least 55% likely), or, when that isn't known, the draw is at least 29% and the favourite at most 40%. The draw and the other side are about equal, so the game's facts decide.
- **side-backup:** every other case. A change on this game goes to the other side, not the draw.

**What this does and doesn't do.** Draws go where the evidence puts them. That includes every slip set that has a draw-backup game, so draws appear wherever the data supports them. The favourites slip still has no draws unless a game is a near three-way tie. Picking the most likely result in every game is still what gives one slip its best chance of 13/13. Draws also matter for payout: the public under-picks draws (pool research; on 9 Oct the tipsters picked 2 draws across 39 single picks), so a correct draw is shared with fewer winners.

**Limits.** These are average bookmaker odds, not SportPesa's own prices. Under/over prices exist only for the main European leagues. Rule 2's edge for the draw is not statistically proven.
