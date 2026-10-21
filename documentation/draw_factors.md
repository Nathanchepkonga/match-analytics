# What makes a draw? (draw-factor study, 14 Oct 2026)

The user asked: research the factors that cause draws (bookings, the goals each team scores), and
add a standing rule that every slip carries 2-5 draws. Code: `python -m src.draw_factors`.

**Data.**
- 46,758 league matches from 20 main leagues, 2019-2027, where both teams had played 5+ games that season.
- 24,004 of them are balanced like jackpot games (favourite ≤ 47%).
- Every team number uses only that team's earlier games in the same season, so nothing peeks at the result.
- Each factor is tested on top of the bookmakers' margin-removed draw price and their under-2.5 price.
- Factors were fitted on 2019-23 and scored on 2023-26.

## Results (balanced games)

| Factor | What it measures | Held-out gain over the price | Verdict |
|---|---|---|---|
| Chance of under 2.5 goals | Market's goal expectation | none (already inside the draw price) | Low-scoring games do draw more, 27% → 33%, but the price already says so |
| Goals in the teams' games | Both teams' scored + conceded per game | tiny, p = 0.08 | Not proven. If anything the price over-reacts: high-scoring pairings draw 2 pts more than priced |
| Bookings in the teams' games | Yellow + red cards per game in their matches | none, p = 0.43 | A hint only: the top fifth drew 32.0% v 30.1% priced, but it didn't hold on the later seasons |
| Team draw rate | How often each team has drawn | none | No: drawing teams don't keep drawing beyond the price |
| Weaker attack | The poorer scorer's goals per game | none | No |
| Shots on target | Attacking volume | none | No |
| Closeness of the two sides | Home v away price gap | none | No: already in the price |

**Conclusion.**
- The bookmakers' draw price already contains goals, closeness and team styles. No single factor predicts draws better than the price.
- Bookings are the only factor with any sign, and it isn't proven.
- So the best way to decide *where* to put draws is the draw price itself: highest draw chance first, or cheapest draw relative to the favourite.
- Use bookings and the teams' goal records only to break ties between games with the same draw price.

## The rule (R24, user, from 14 Oct 2026)

**Every slip carries 2-5 draws.** Build with `optimise(probs, n, target, min_draws=2, max_draws=5, vary=...)`:
- `vary` holds the close games plus the draw candidates.
- Draws go only on the draw candidates: the games with the cheapest draw price, tie-broken by low goals, bookings and league draw rate. Mask the other games' draw chance to near zero during the search, then score on the true prices.
- State the cost each time.

**The cost on the 16 Oct 13-game card (5 slips):**

| Set | Draws | 10+ | 9+ |
|---|---|---|---|
| Free optimiser W1-W5 | 1 in total | 2.97% | 10.9% |
| 2 per slip, anywhere | 10 | 2.39% | 9.4% |
| 2 per slip, only on games 5, 6, 12, 13 | 10 | 2.38% | 9.5% |

The optimiser always settles on 2 per slip, because each extra draw costs more.

**From our own ledger (4 jackpots, 60 games, 12 draws):**
- Of our 142 draw picks, 27 were right (19%). The favourite on the same games was right 45 times (32%).
- On the 28 games where we picked a draw, 8 ended drawn (29%, as priced). So we chose the right games, but those weeks were short of draws: 20% against 31% in SportPesa's 4-year archive.

## Update (user, 21 Oct 2026): draws per slip by card size

- **13-game slips carry 3-4 draws; 15-game slips (Mega 15/15) carry 4-5.** This narrows R24's 2-5 range.
- Build the same way: `optimise(probs, n, target, min_draws=4, max_draws=5, vary=...)` with draws masked to the draw pool, then score on the true prices.
- Card 205 (24-25 Oct), two slips: joint chance of 10+/15 is 4.05% with 4 draws each, against 5.72% for the free optimiser pair. Five draws each drops it to 3.2%, so the optimiser settles on 4.
