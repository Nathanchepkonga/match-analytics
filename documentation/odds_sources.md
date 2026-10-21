# Where to get jackpot odds fast (recipes that worked, Oct 2026)

These are the price checks used for the 16 Oct 2026 jackpot. All of them need the built-in browser: Akamai blocks curl on the SportPesa hosts, and the bookmakers' feeds only answer from their own pages. Fetch from the page with `javascript_tool`, using your **own tab** (`tabs_create`), because research agents share the browser pane and will navigate a shared tab away mid-script.

**User rule (16 Oct 2026): don't use Betika odds.** Betika and Odibets copy SportPesa's supplier (Sportradar) almost exactly, so they add little anyway. The independent prices are Paripesa (1xBet's engine, the same as 1xBet, 22Bet and Megapari) and Stake.

## Odibets (Sportradar prices, Kenyan)
Open https://odibets.com/, then fetch from the page:
`https://apis.odibets.com/sportsbook/v1?sport_id=soccer&country_id=<CC>&sort_by=&sub_type_id=&competition_id=&hour=&filter=&cs=&hs=&sportsbook=sportsbook&resource=sport&day=<YYYY-MM-DD>`

- **Paging:** `page=` doesn't page; loop `country_id` over '', DNK, TUR, SWE, FRA, POL, ITA, IRL, NIR, ENG, ... instead.
- **Matching:** match games by `parent_match_id`, which is the Sportradar match id; SportPesa uses the same ids.
- **1X2 market:** `sub_type_id == '1'`.
- **Coverage:** Swedish third-tier games are often missing.

## Paripesa (1xBet engine, independent)
Open https://paripesa.co.ke/en/line/football, then fetch:
`/service-api/LineFeed/Web_SearchZip?text=<team>&limit=50&lng=en&mode=4`

- **Filtering:** keep events by kickoff (`S`, unix seconds) and skip leagues containing "Alternative".
- **1X2 prices:** in `E` where `G == 1`, with `T` 1 = home, 2 = draw, 3 = away.
- **Over/under 2.5:** `G == 17`, `P == 2.5`, `T` 9 = over, 10 = under.
- **Timeouts:** run the searches in parallel with an AbortController timeout (about 30 s). Sequential loops can pass the 45 s tool limit.

## Stake (via BetExplorer, independent)
- **Finding the pages:** BetExplorer's daily list (`https://www.betexplorer.com/next/soccer/?year=&month=&day=`) holds hidden match links. Collect them with `[...document.querySelectorAll('a')]`.
- **Reading prices:** open each match page, wait about 6 s, and read the table rows that start with "Stake.com". The 1xBet, 22Bet and Megapari rows repeat Paripesa.
- **Reliability:** pages sometimes redirect to the home page; retry once. Pinnacle is blocked in the browser pane.

## SportPesa
- **Mega Jackpot Pro (17):** the open card with SportPesa's prices is `https://jackpot-offer-api.ke.sportpesa.com/api/jackpots/active`, fetched from https://jackpot-widget.ke.sportpesa.com/. The archive of past cards is in `src/sportpesa_archive.py`.
- **Midweek 13-game jackpot:** not in that feed. The user pastes the card and its updated prices.

## Turning prices into chances
1. **Remove each site's margin:** `devig` in src/jackpot_ledger.py.
2. **Average the sites:** treat the Kenyan Sportradar group as one source.
3. **Save to the slate:** write the result as `market_probs_<when>` and `market_odds_final`.
4. **Compare snapshots:** look for favourite flips and moves of 3+ points.
