# 200-factor research checklist (the starting scope for every slate)

Source: the user's PDF "200 Factors That Determine the Outcome of a Single Football Match" (added 15 Oct 2026). All 200 factors, with a tier, a source and an evidence rating, are in [data/factors/factors_200.csv](../data/factors/factors_200.csv). The older 67-factor guide is [prediction_factor_matrix.md](prediction_factor_matrix.md); this checklist is the working scope, and that file stays the record of how the slip rules were found.

**Rule from the user (15 Oct 2026):** when asked to look for favourites in the news and on other sites, always start with these factors. Other factors outside the list may be added, but the list comes first.

## How to use it

1. **Tier 1 (23 factors): check every game, every slate.** They can be found before kickoff, have some evidence behind them, and news on them can arrive after the odds were set.
2. **Tier 2 (39): check when a game is near-even** (top two outcomes within about 5 points) or when a stats site is readily available.
3. **Tier 3 (109): only when the news flags it.** Team and player statistics the odds already contain, or that are hard to find for most leagues.
4. **Tier 4 (29): not knowable before kickoff** (in-match events, rituals, luck). Use them only to review a result afterwards, never to pick.
5. For every fact found, record the date, the source and one label: **priced** (public before the odds closed, so the market has it) or **possibly unpriced** (news that came out after the prices were set). Only possibly-unpriced, concrete, one-sided facts can justify a change on a slip (see R9 and the slip-builder rules). Write "not found" when a factor can't be found; never fill a gap with a guess.
6. Report each factor as a fact, not an adjective. "Rest: 3 days after a Thursday Europa League game" counts; "tired legs" doesn't.

## What the evidence says (honest summary)

| Group | Factors | What research and our own data show |
|---|---|---|
| A-C Team attacking, defensive, possession (1-62) | xG, shots, PPDA, possession | xG predicts results better than raw goals, and small studies report betting profits from xG models ([thesis, top-5 leagues](https://dspace.cuni.cz/bitstream/handle/20.500.11956/190556/130386534.pdf), [student study](https://jsr.org/index.php/path/article/download/1116/906)). Those are small samples, and many bookmakers already use xG ([PMC review](https://pmc.ncbi.nlm.nih.gov/articles/PMC10075453/)). Our Dixon-Coles check (15 Oct 2026) did worse than the odds on 237 matches. Treat as **priced**. |
| D-F Goalkeepers, players (63-120) | Keeper form, finishing, discipline | Finishing form regresses to the mean. The useful part is availability and suspension risk (109), which is news, not statistics. |
| G Tactics and coaching (121-140) | Formation, press, set pieces | Hard to measure before the match; use only when a preview names a concrete matchup problem. |
| H Physical (141-155) | Rest, congestion, travel, injuries, weather | Congestion raises muscle-injury rates, but league results show little effect except Europa League games with 3 days or less of rest ([UEFA injury study summary](https://www.kitmanlabs.com/?p=28400), [University of Huddersfield study](https://www.hud.ac.uk/news/2020/november/football-fixture-congestion-new-study/)). Wind above roughly 20 km/h affects passing and shooting; effects are small ([Biology of Sport 2024](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11474995/)). Late injuries are the clearest source of unpriced news. |
| I Psychology and context (156-170) | Home advantage, stakes, new manager, morale | Home advantage and stakes are real and priced. The "new-manager bounce" is mostly regression to the mean ([Erasmus study](https://www.eur.nl/en/news/irrational-managerial-changes-remain-norm-europes-top-football-leagues)). Morale, "due a win" and unbeaten-run pressure are unproven, and the slip-builder rules list them as brain traps. |
| J In-match events (171-185) | Red cards, VAR, added time | Red cards matter once they happen, but only in-match. Referee home bias exists and is small, and it grows with crowd size ([EPL study](https://lida.sport-iat.de/dfb/Record/4013091), [Bundesliga ghost games](https://www.research-collection.ethz.ch/handle/20.500.11850/445575)). Check the appointed referee; don't use in-match items to pick. |
| K Tiny details (186-200) | Sun in eyes, kit colours, luck | Noise. Not researched. |

**Our own results so far** (from this repo): form, head-to-head, weather and news did not beat the favourite on past slates; no pick method beat the favourite pick by pick (jackpot_simulation.md); draws are slightly underpriced in balanced games (draw_study.md); a Dixon-Coles model was worse than the bookmakers on 237 matches in 2026-27. So the checklist is for finding **unpriced late news and vetoes**, not for fading the market.

## Our own test of the measurable factors (15 Oct 2026, `python -m src.factor_tests`)

The list was checked against the PDF line by line: all 200 factors, same numbers, same order.

**What was tested.** Every factor that football-data.co.uk lets us measure before kickoff:
- 43,542 main-league matches, 2019-2027, both teams with 5+ games played that season.
- Team numbers come only from earlier games.
- Each factor is added to the bookmakers' closing price, learned on 24,344 matches (to mid-2023) and scored on 19,198 later ones.
- 30 tests in all, so only z > 3.1 survives a multiple-testing correction.
- Results are in `data/factors/factor_tests.csv` and in the `our_test_2026_10_15` column of the CSV.

| # (PDF) | Factor | All matches, held out (home / away win z) | Jackpot-like games (favourite ≤ 47%) | Verdict |
|---|---|---|---|---|
| 4, 27 | Shots for minus against | +2.5 / +2.3 | nothing | Hint only: shot-dominant teams are very slightly underpriced, not in balanced games |
| 5, 28 | Shots on target for minus against | +1.9 / +2.2 | nothing | Hint only |
| 8 | Goals scored per game | +1.4 / +2.2 | nothing | Priced |
| 45 | Clean sheet rate | +1.1 / +0.3 | nothing | Priced |
| 12 | Corners won minus conceded | +1.6 / +1.4 | nothing | Priced |
| 43 | Fouls conceded | +0.8 / +1.1 | nothing | Priced |
| 109 | Cards per game | +2.5 / +2.2 (gain ~0) | nothing | Priced |
| 141 | Rest days | +2.9 / -1.1 (gain ~0) | nothing | Priced. Cup games are missing from the data, so check midweek European/cup games (144) in the news |
| 142 | Games in the last 14 days | +0.1 / -0.6 | nothing | Priced |
| 161 | Points per game, last 5 ("morale") | +0.2 / -1.0 | nothing | Priced: recent form adds nothing |
| 167 | Lost the previous game ("bounce-back") | -0.9 / -1.9 | nothing | No effect |
| 168 | Unbeaten-run length | +1.8 / +2.7 | nothing | Hint only |
| (extra) | Head-to-head, last meeting | +2.2 / +1.0 | nothing | Priced |
| 177 | Referee strictness | -2.1 / +1.6 | nothing | No effect |
| 178 | Referee home-win tendency | +0.6 / +0.3 | nothing | No effect |
| 156 | Home advantage | home wins 43.5% v 43.3% implied | | Priced |

**Conclusion.**
- No measurable statistical factor on the list beats the closing odds after correction. In jackpot-like balanced games, none even reaches a hint.
- The statistics (groups A-C, F, form, head-to-head, referee) are already in the price.
- The checklist earns its keep on the **news factors** that can't be backtested and can arrive after the prices are set:
  - injuries, suspensions and late fitness tests (148-150)
  - midweek European or cup games (144)
  - motivation gaps and dead rubbers (159, 160)
  - new or sacked managers (162, 163)
  - contract or wage trouble (170)
  - the appointed referee (177-178, small)
- Research time goes there first. The xG factors (1, 2, 26) can't be tested yet, because football-data has xG only for 2026-27; the outside studies above suggest they are priced too.

## Tier 1 factors (check for every game)

| # | Factor | Where to find it | Evidence |
|---|---|---|---|
| 1, 2, 26 | xG, non-penalty xG, xGA | Understat, FBref, FotMob (big-5 leagues only) | documented, priced |
| 109 | Yellow-card accumulation risk | Transfermarkt, league card tables | documented |
| 139 | Coaching tenure | Transfermarkt manager history | weak |
| 141, 142 | Rest days, games in last 14 days | FBref/Transfermarkt schedule | mixed |
| 143 | Travel and time zones | club news, fixture list | weak |
| 144 | Midweek European/cup game | UEFA/league fixture lists | mixed (Europa League 3 days or less: more losses) |
| 148, 149, 150 | Injuries, suspensions, late fitness tests | Press conferences, Transfermarkt, Physioroom | documented, often unpriced early |
| 152, 153 | Temperature, wind | Open-Meteo or Met Office forecast (recheck on the day) | mixed |
| 156 | Home advantage | n/a | documented, priced |
| 158 | Derby or rivalry | fixture context | weak |
| 159, 160 | Stakes, motivation gap | league tables | documented, partly priced |
| 161 | Morale after recent results | recent scores | unproven; facts only |
| 162, 163 | Manager under pressure, new manager | club news | weak (regression to mean) |
| 177, 178 | Referee strictness, home bias | referee appointment (about 2 days before) | documented, small |

The Tier 2 factors (xG per shot, shots, big chances, set pieces, keeper form, striker finishing, formation matchup, altitude, pitch, crowd, bounce-back and unbeaten runs, contract situations and others) are listed in the CSV with their sources. Tier 3 and Tier 4 are listed there too.

## Limits

- Most free sources cover the big-5 leagues only; for other leagues many factors will be "not found".
- Tipster picks and prediction sites are opinions, not factors (record them only as a note).
- No factor on this list has been proven to beat the closing odds on its own. Their use is to catch what the odds can't yet contain: news after the prices were set.
