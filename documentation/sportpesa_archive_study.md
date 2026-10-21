# SportPesa Mega Jackpot Pro archive study (199 real cards, 3,383 games)

Run 12 Oct 2026. Data: every card in SportPesa's public jackpot archive (jackpot-widget.ke.sportpesa.com,
history feed), IDs 1-203, 18 Dec 2022 to 11 Oct 2026. IDs 24, 102, 162 and 183 were cancelled, leaving
199 cards. The archive holds only the 17-game Mega Jackpot Pro; the 13-game midweek jackpot isn't in it.

- `data/sportpesa_archive/mega_archive.json`: the raw archive (teams, kickoff, score, prize tiers, winner counts).
- `data/sportpesa_archive/mega_games.csv`: one row per game, joined to closing average odds where football-data.co.uk covers the league.
- `data/sportpesa_archive/backtest_full_cards.csv`: slip methods scored on every fully priced card.
- Code: `python -m src.sportpesa_archive` (build and match), `python -m src.archive_study` (all tables below).
- Tests: tests/test_sportpesa_archive.py.

**Matching.** Each game was matched by kickoff date (±1 day), an identical score and team-name
similarity. Every borderline match was checked by eye (Wolves, Espanol, M'gladbach, FC Koln, Hearts and
so on) and all were correct.
- 2,480 games (73%) got odds; 46 cards are fully priced.
- The rest are leagues football-data doesn't cover: Serie C, Primera RFEF, Israel, Cyprus, Hungary, Uruguay, Kazakhstan, internationals, and others.
- 33 games (1%) were postponed and settled by SportPesa's rule ("PD"); they are left out of the football tables.

## 1. What the cards look like (all 3,350 played games)

- Results: Home 35.7%, Draw 31.1%, Away 33.1%. Goals 2.55 per game; 0-0 9.3%; under 2.5 goals 52.5%. The most common score is 1-1 (14%).
- Draws per card: mean 5.3 of 17, sd 1.8, range 1-9.

  | Draws on the card | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
  |---|---|---|---|---|---|---|---|---|---|
  | Number of cards | 4 | 9 | 19 | 29 | 39 | 51 | 29 | 13 | 6 |

- Kickoffs: Sunday 75%, Saturday 25%.
- Most-used leagues among the priced games: La Liga 258, Ligue 1 257, Serie A 244, Premier League 217, Segunda 216, Eredivisie 121, Bundesliga 120.

## 2. How SportPesa picks its games

The 2,480 priced games are compared with 28,108 other games in the same leagues on the same days, the pool SportPesa chose from.

| | Chosen | Not chosen |
|---|---|---|
| Favourite's chance, average | 40.2% | 50.6% |
| Favourite ≤ 40% | 54% | 18% |
| 40-45% | 35% | 20% |
| 45-50% | 10% | 18% |
| 50-60% | 1% | 25% |
| over 60% | 0% | 19% |
| Home side is favourite | 56% | 70% |
| Draw's price-implied chance | 28.8% | 25.6% |

- The strongest favourite ever chosen had 58%. 90% of chosen favourites were between 35% and 47%.
- SportPesa picks games where nobody is likely to win, and prefers away favourites.
- This is why a favourites slip averages about 7/17, and why tipsters get 6-7.

## 3. Do these games behave as the odds say?

| Test (closing odds, margin removed) | Games | Actual | Odds said | Gap | z |
|---|---|---|---|---|---|
| Favourite wins | 2,480 | 41.2% | 40.2% | +1.0 | +1.0 |
| Draw | 2,480 | 30.5% | 28.8% | +1.7 | +1.9 |
| Underdog side wins | 2,462 | 28.2% | 31.0% | **-2.8** | **-3.0** |
| Home favourite wins | 1,399 | 41.2% | 40.4% | +0.8 | +0.6 |
| Away favourite wins | 1,063 | 41.3% | 40.0% | +1.3 | +0.8 |
| Favourite 0-38% | 752 | 35.8% | 36.5% | -0.7 | -0.4 |
| Favourite 38-42% | 1,028 | 42.2% | 39.8% | +2.4 | +1.6 |
| Favourite 42-46% | 513 | 45.0% | 43.7% | +1.4 | +0.6 |
| Favourite 46-52% | 176 | 45.5% | 47.9% | -2.4 | -0.7 |

**The favourites are honest.** SportPesa does not pick games where the favourite is a trap: favourites won slightly more than priced, though not significantly.

**One candidate effect: the underdog side wins less than priced and the draw more.** It shows up in every year and in both halves of the archive.

| Period | Favourite | Draw | Underdog side |
|---|---|---|---|
| Cards 1-100 (Dec 2022 - Nov 2024) | +0.3 | +1.7 | -2.0 |
| Cards 101-203 (Nov 2024 - Oct 2026) | +1.8 | +1.8 | -3.6 |
| 2023 / 2024 / 2025 / 2026 (underdog only) | | | -1.2 / -2.8 / -4.3 / -3.0 |

- **It isn't just closeness.** Balanced games SportPesa did not pick, reweighted to the same closeness between the two sides, show draw +0.55 and second choice +0.43. SportPesa's picks show draw +1.75 and second choice -2.74.
- **Out of sample.** The adjustment was learned on one half and tested on the other.
  - Learned on cards 1-100 (factors favourite ×1.007, draw ×1.059, underdog ×0.936), it improved the log loss on cards 101-203 from 1.0810 to 1.0786 (bootstrap by card, P(no gain) = 0.03).
  - Learned on cards 101-203, it improved cards 1-100 only slightly, from 1.0869 to 1.0865 (P = 0.39).
- **Status: probable but not proven.** z = -3.0 misses a strict multiple-testing bar (about 25 tests, so it needs z ≈ 3.1). It's small, about 0.5 picks per 17-game card, at most.
- **Use: R23 tilt** (`sportpesa_tilt` in src/slip_optimizer.py, `--tilt` on the CLI). It applies half the measured size (favourite ×1.0125, draw ×1.03, underdog ×0.955). If the effect is real, backups lean to the draw instead of the underdog side. If it isn't, it costs almost nothing.

**The draw as the backup pick, on SportPesa's own games.**

| | Games | Draw came in | Draw priced | Other side came in |
|---|---|---|---|---|
| Draw ranked 2nd by the odds | 731 | 29.3% | 30.4% | 26.1% |
| Draw ranked 3rd by the odds | 1,731 | 31.0% | 28.0% | 29.1% |
| Under 2.5 goals ≥ 55% | 843 | 32.0% | 31.1% | |

- R19's "draw ranked 2nd → the draw is the backup" holds here too.
- R19's "draw ranked 3rd → the other side is the backup" does **not** hold on SportPesa cards: the draw came in at least as often (31.0% v 29.1%). By half: 30.4 v 31.1 in cards 1-100 and 31.7 v 26.9 in cards 101-203.
- On SportPesa cards, side-backup games are therefore treated as either-backup: facts decide, with a lean to the draw.

## 4. Patterns people look for: none survive

- **Card position (slot 1-17) v result:** chi-square 39.0 on 32 df, p = 0.18. No slot effect. Slot 4's 45% away wins is chance.
- **Upsets clustering on some cards:** the dispersion of favourites correct per card is 0.90 (1.0 = pure chance, p = 0.84). Draws per card 0.87. "Crazy weeks" are ordinary luck, not a hidden rule.
- **Home v away favourites:** both are priced correctly.
- **Late price moves:** on 316 games where the opening and closing favourites differed, the closing favourite won 35.1% and the opening favourite 32.9%. R22's direction holds; the sample is small.

## 5. The crowd and the prizes (17-game tier)

| Tier | Cards with any winner | Median winners | Median paid per ticket |
|---|---|---|---|
| 17/17 | **1 of 199** (card 140, 3 Aug 2025: KSh 424.7m, one ticket) | 0 | |
| 16/17 | 28 (14%) | 0 | |
| 15/17 | 134 (67%) | 1 | |
| 14/17 | 197 | 13 | KSh 247,165 |
| 13/17 | 199 | 113 | KSh 41,739 |
| 12/17 | 199 | 619 | KSh 9,418 |

- The crowd's success tracks the favourites. The Spearman correlation between favourites correct on a card and the number of 12/17 winners is 0.63.
- When favourites come in, the bonus is split among more people. On card 140, 2,808 tickets got 12/17 and each was paid KSh 2,200.

Median bonus per ticket, by how many favourites won (136 cards with ≥ 12 priced games):

| Favourites correct | ≤ 5 | 6-7 | 8-9 | 10+ |
|---|---|---|---|---|
| Cards | 31 | 60 | 29 | 16 |
| 12/17 winners | 425 | 536 | 789 | 2,772 |
| 12/17 paid | KSh 11,330 | 11,261 | 7,085 | 2,845 |
| 13/17 paid | KSh 51,765 | 49,991 | 28,224 | 11,580 |

A correct non-favourite pick is worth about 4 times as much as one on a favourites week, because fewer tickets share the bonus. It is still less likely to come in, so this only breaks ties between equally likely changes.

**Self-updating tilt.** `python -m src.archive_study` re-estimates the R23 factors from every priced game and writes `data/sportpesa_archive/tilt.json`. The factors are shrunk by n / (n + 2,500), which is half strength today. If new cards don't show the effect, the factors drift back towards 1 on their own.

## 6. Our slip methods on the 46 fully priced real cards

Closing odds are used as the pricing. That is slightly better information than we have at the jackpot's close.

| Method | Average best score | Cards with 10+ | 11+ | 12+ (expected) |
|---|---|---|---|---|
| Favourites, 1 slip | 6.83 (odds expected 6.88) | 4 | 2 | 1 |
| Optimiser, 3 free slips | 7.70 | 9 | 4 | 3 (1.27) |
| Optimiser 0/0/3 draws | 7.76 | 8 | 4 | 3 |
| Optimiser, 4-6 draws per slip | 7.74 | 7 | 1 | 1 (0.93) |

Favourites correct per full card: 2 (1 card), 4 (3), 5 (7), 6 (11), 7 (9), 8 (6), 9 (5), 10 (2), 11 (1), 12 (1).

This matches the 12,580-card simulator: three optimised slips roughly double or triple one slip's chance of a big score. On 46 cards, nothing separates the free and draw variants.

## What this changes

1. Confirmed on real SportPesa cards: the odds are the best single guide, and the favourite is right about 41% of the time on these games.
2. New R23 (candidate): on SportPesa cards, the draw has been the better backup than the underdog side. Use `--tilt` and lean side-backup choices to the draw. Track it on new cards; drop it if the next 30+ cards show no underdog shortfall.
3. A card averages 5.3 draws. Draws belong in slips 2-3 as backups, not instead of the favourite: a draw pick is right about 30.5% of the time against 41% for the favourite.
4. No hidden patterns in slot, clustering, home/away or year.

## 7. How the crowd picks (crowd model, 15 Oct 2026; `python -m src.crowd_model`)

**The model.** Each crowd line picks an outcome with share ∝ price^alpha × exp(delta if draw). Alpha, delta and the number of lines N were fitted by Poisson likelihood to the 12/17-16/17 winner counts on the 46 fully priced cards.

| Crowd hypothesis | Fit (lower = better) |
|---|---|
| Random picks | -287,485 |
| Picks in line with the odds | -302,469 |
| Favourite-heavy, alpha 1.72 | -306,412 |
| **Favourite-heavy and draw-shy, alpha 1.72, delta -0.18** | **-307,050** |

**What it says.**
- About **393,000 lines** are played per Mega card.
- The crowd **piles onto favourites far beyond the odds** and **under-picks draws** by about 16% more on top of that.

**How well it fits.**
- Median winners, predicted v actual: 553 v 610 (12/17), 97 v 104 (13/17), 12.4 v 13 (14/17), 1.1 v 1 (15/17).
- **Held out** (fit on half the cards, test on the other half): rank correlation 0.65-0.72 for 12/17 and 13/17.
- Across the halves alpha was 1.39-1.98, delta -0.06 to -0.25 and N 376k-402k. The direction is stable.

**Use (Clair & Letscher, *Operations Research* 2007: maximise expected return, not expected correct picks).**
- A winning slip shares the pot with about N × popularity other lines, where popularity is the product of the crowd shares of its picks.
- On the 16 Oct 13-game card, the all-favourites ticket would share a 13/13 with about 4-17 others (for 100k-400k lines). The F1-F5 slips (3 draws each) would share with about 0.4-3.
- Jackpot-only expected winnings per KSh 495 (assuming 100k / 250k / 400k lines):
  - F1-F5: KSh 168 / 113 / 82
  - Best possible with 3-4 draws: KSh 175 / 118 / 96
  - Five favourites-style tickets: much lower
- The F set is within 4-15% of the best possible, with about 34% more chance of hitting.
