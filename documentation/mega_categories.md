# Mega Jackpot Pro: play 15 of the 17 games (study, 19 Oct 2026)

**What we found.**
- SportPesa's Mega Jackpot Pro widget lets a slip cover **any 13 to 17** of the 17 games. The page code validates `selectedEvents` with at least 13 and offers only open (not yet started) games.
- Each count is its own category, with its own jackpot and bonus ladder. The archive feed confirms separate prizes and winner counts for 13/13, 14/14, 15/15, 16/16 and 17/17.
- The stake is the same KSh 99. The user's 18 Oct slip was a 15-game slip placed after two games had finished.

| Category | Bonus from | Median pot (last 60 cards) | Median payout of the lowest bonus tier |
|---|---|---|---|
| 17/17 | 12/17 | KSh 120M | KSh 9,700 |
| 16/16 | 11/16 | KSh 126M | KSh 4,800 |
| **15/15** | **10/15** | KSh 95M | KSh 2,100 (11/15 ≈ 9,200; 12/15 ≈ 33,400) |
| 14/14 | 10/14 | KSh 28M | KSh 5,700 |
| 13/13 | 10/13 | KSh 15M | KSh 13,500 |

**Chance of a bonus for one favourites slip, picking the k clearest games:**

| Category | Card 204 (17-18 Oct) | 46 fully priced archive cards (average) |
|---|---|---|
| 17/17 | 0.74% | 1.20% |
| 16/16 | 1.44% | 2.29% |
| **15/15** | **2.69%** | **4.19%** |
| 14/14 | 1.40% | 2.34% |
| 13/13 | 0.63% | 1.14% |

**Replay with what SportPesa actually paid** (46 real cards, one favourites slip per card, KSh 4,554 staked in each category):

| Category | Bonus wins | Total won |
|---|---|---|
| 17/17 | 1 | KSh 1,218 |
| 16/16 | 2 | KSh 2,423 |
| **15/15** | **3** | **KSh 8,077** |
| 14/14 | 1 | KSh 2,196 |
| 13/13 | 0 | KSh 0 |

**Why 15 wins.** Dropping the two closest coin flips removes the hardest games, and the bonus starts at 10 of 15 (67%) instead of 12 of 17 (71%). 13 and 14 games drop more games but their bonus bar is relatively higher (10 of 13 is 77%).

**Limits.**
- Three wins is a small sample. One of them, KSh 5,635 for 11/15, is most of the 15-game total, so this is no proof of profit.
- The lowest 15/15 tier pays less than 12/17 when it pays, because more tickets win it.
- The direction matches the probability maths on every card checked. That is why we use it, not as a promise of returns.

**How to use it** (`mega_categories(probs)` in src/slip_optimizer.py):
1. On the latest consensus, list each category's bonus chance and the games to drop.
2. Normally choose 15/15: drop the two closest games (smallest favourite chance).
3. Build multiple slips on the 15 kept games with `optimise(probs_15, n_slips, target=10)`.
4. When placing on the weekend, a slip can be placed after early games have finished, as long as 15 open games remain. Later placement means more line-up news.
