# Jackpot simulator findings (2026-10-09)

**What it does.** `python -m src.jackpot_sim` rebuilds SportPesa-style jackpots from real past weekends, 2019-2026, using the 86,868 matches from the draw study. Each card is built like this:
- Take the most balanced Friday-to-Sunday games of the week (favourite at most 45%), with at most 2 from one league.
- Draw 13 or 17 games at random from the 40 most balanced.
- Use the average bookmaker odds before kickoff, with the margin removed.

Each slip-building strategy is then scored against the real results. The cards are realistic, if slightly harder than SportPesa's: the favourite averages 38% (SportPesa 39-45%), the balance score is 0.993 (SportPesa 0.97-0.99), and there are 4.0 draws per 13 games.

## Results

**13-game cards** (6,600 cards, 330 weekends):

| Strategy | Typical best | 9+ | 10+ | 11+ | 12+ |
|---|---|---|---|---|---|
| Favourites, 1 slip | 4.94 | 2.2% | 0.48% | 0.08% | 0.00% |
| Random, 3 slips | 5.77 | 2.8% | 0.70% | 0.12% | 0.02% |
| Evidence tweaks (R19), 3 slips | 5.61 | 4.6% | **1.03%** | 0.15% | 0.03% |
| Draw-heavy, 3 per slip (9 Oct method), 3 slips | 5.80 | 4.8% | **1.00%** | 0.26% | 0.03% |
| 3 draws per slip on the 5 closest games, 3 slips | 5.57 | 3.9% | 0.88% | 0.12% | 0.02% |

**17-game cards** (5,980 cards, 299 weekends):

| Strategy | Typical best | 11+ | 12+ | 13+ |
|---|---|---|---|---|
| Favourites, 1 slip | 6.39 | 2.4% | 0.52% | 0.10% |
| Random, 3 slips | 7.32 | 2.5% | 0.62% | 0.12% |
| Evidence tweaks (R19), 3 slips | 7.06 | **4.8%** | **1.35%** | 0.28% |
| Draw-heavy, 3 per slip, 3 slips | 7.26 | 4.5% | **1.47%** | 0.37% |
| 3 draws on the 5 closest games, 3 slips | 7.07 | 4.2% | 1.22% | 0.20% |

**Picks that differ from the favourite** (each distinct pick counted once; both periods agree):

| Strategy | Changed pick right | Favourite right on the same games | p |
|---|---|---|---|
| Evidence tweaks, 13-game | 34.3% | 34.8% | 0.78 (no cost) |
| Evidence tweaks, draws only, 13-game | 38.1% | 31.0% | 0.046 |
| Draw-heavy, all changes, 13-game | 33.3% | 36.5% | 0.003 |
| Draw-heavy, draws where the draw is the least likely result | 29.7% | 37.4% | 0.00002 |
| Draw-heavy, all changes, 17-game | 32.0% | 36.4% | 0.0002 |

## Findings

1. **The odds are honest.** Slips score what the odds expect: 4.98 actual against 4.94 expected on 13 games, and 6.50 against 6.43 on 17. A favourites slip averages 6.4-6.5 of 17 on these cards, which is exactly the 6-7 that prediction sites manage. That is the ceiling the card design allows, not tipster incompetence.
2. **No way of making picks beats the favourite pick by pick.** The best changes (evidence tweaks on the closest games) break even, and forced changes lose.
3. **How the 3 slips are combined is the real lever.** Three well-built slips give about 2 to 2.5 times the big-score chance of one favourites slip: 13-game 10+ goes from 0.48% to about 1.0%, and 17-game 12+ from 0.52% to about 1.4%. Three random slips give much less (0.70%, 0.62%). Variety alone isn't enough; the changes must go on close games.
4. **A draw quota of 3 per slip does no better and no worse than the evidence method at the jackpot tail,** with differences inside the noise. Pick by pick, though, it is worse: forced draws are right 33% of the time against the favourite's 36% (p < 0.01 in both periods). Draws where the draw is the least likely result (side-backup games) are clearly bad: 30% against 37%.
5. **The typical best score is a misleading measure.** Random slips score high on it but poorly where it matters. Slip sets should be judged on the chance of 10+/12+ (13-game) or 12+/13+ (17-game).
6. **Big wins stay rare whatever we do.** With 3 good slips, 10+/13 comes about once in 100 weeks and 12+/13 about once in 3,300. On 17 games, 12+ is about once in 70 weeks.

**Limits.** These are average bookmaker odds, not SportPesa's early-week card prices. Late team news, the one place a real edge could come from, can't be tested on history; the live ledger tracks that. Cards within a weekend share games, so tail rates are less certain than the card counts suggest.

## Tail optimiser and combinations (2026-10-09)

`src/slip_optimizer.py` picks the 3 slips that maximise the exact chance that at least one reaches the target (10/13 or 12/17). Every slip keeps the favourite on the clearer games and varies only the 6 closest. Its chance calculation matches brute-force enumeration exactly. It was tested on two fresh sets of historical cards (seeds 7 and 11, 10 random cards per weekend, 6,600 thirteen-game and 5,980 seventeen-game cards in all), together with combinations that require draws on some slips.

**13-game cards** (set A / set B):

| Strategy | 9+ | 10+ | 11+ |
|---|---|---|---|
| Favourites, 1 slip | 2.6 / 2.3% | 0.61 / 0.48% | 0.06 / 0.18% |
| Evidence tweaks (R19) | 5.2 / 4.5% | 1.42 / 1.00% | 0.24 / 0.27% |
| Draw-heavy, 3 per slip (9 Oct method) | 4.8 / 4.4% | 0.64 / 0.85% | 0.15 / 0.06% |
| **Tail optimiser** | **5.9 / 5.4%** | **1.48 / 1.09%** | 0.30 / 0.30% |
| **Optimiser combination, draws 0/0/3** | **5.9 / 5.4%** | **1.48 / 1.06%** | 0.12 / 0.24% |
| Optimiser combination, draws 0/3/3 | 5.6 / 5.1% | 1.30 / 1.15% | 0.12 / 0.24% |
| Optimiser, 3 draws on every slip | 4.8 / 4.4% | 1.42 / 0.82% | 0.27 / 0.15% |

Paired by weekend on 10+ (660 weekend-sets):
- The optimiser beats the 9 Oct draw-heavy method: 1.29% against 0.74%, +73%, better in 59 weekends and worse in 32, p=0.006.
- The 0/0/3 combination also beats it: 1.27%, p=0.01.
- Against the evidence tweaks the optimiser is +6% (not significant at 10+). At 9+, where there are more hits to count, it is ahead in both sets (+15-20%).

**17-game cards (12+):** every good 3-slip method ties at about 1.4-1.6%:
- optimiser 1.57%
- evidence tweaks 1.59%
- draw-heavy 1.57%
- combination 0/0/3: 1.51%

The optimiser leads at 11+ in both sets but shows no proven gain at 12+. A wider set of varying games (7-8) for 17-game cards is the next thing to test.

**Conclusions (R21):**
- For 13-game jackpots, build slips with the optimiser.
- If draws are wanted, use the 0/0/3 combination: two free slips and one slip with 3 draws, chosen together. It keeps almost all of the optimiser's chance.
- Requiring 3 draws on every slip costs about a quarter of the 10+ chance, even when optimised.
- For 17-game jackpots, the optimiser, the evidence tweaks and the draw-heavy method are equivalent at 12+ on the evidence so far.

## How many draws per slip? (2026-10-09, 299 independent 17-game and 330 13-game cards, one per weekend)

The figures are the optimiser's exact chance, averaged over real historical cards. The odds were shown to be calibrated, so these averages are low-noise. Real hits at 12+ (2-3 of 299) are too few to separate the variants, but they are consistent.

| Draws per slip (forced) | 13 games: chance of 10+ | 17 games: chance of 12+ |
|---|---|---|
| None forced (the optimiser's own choice) | 1.33% (0.35 draws per slip chosen) | 1.61% with 7 varying games, 1.58% with 6 (about 0.5 draws per slip chosen) |
| 0/0/3 (one 3-draw slip) | 1.29% (-3%) | 1.58% (-2%) |
| 0/3/3 | - | 1.49% (-7%) |
| 3/3/3 | 1.03% (-22%) | 1.35% (-16%) |

On balanced cards the draw is usually the least likely result, so the best slips carry only about half a draw each. Draws still happen (5.1 per 17-game card), but they are spread unpredictably across games. Each forced draw costs a little. One 3-draw slip costs only 2-3%, so the 0/0/3 combination stays the recommended way to include draws. The optimiser now varies 7 games by default on 17-game cards (+2%).
