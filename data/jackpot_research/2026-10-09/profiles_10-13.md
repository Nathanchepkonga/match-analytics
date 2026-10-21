# Match profiles, games 10-13 (match-profiler, captured 2026-10-07 16:30 EAT)

Sources: FotMob, ESPN standings/scoreboard JSON, Sky Sports, Irish Examiner, BetExplorer, Wikipedia (season pages), Open-Meteo plus multi-model check. Facts only. All four kickoffs confirmed for Fri 9 Oct at the card's Kenya times.

| # | Match, competition | H2H (home view) | Weather at kickoff | Positions | Form last 5, newest first (home / away) |
|---|---|---|---|---|---|
| 10 | Avellino v Sampdoria, Serie B rd 6 | Only 2 meetings (2025-26): L W. At this ground: W 2-1 (Jan 2026) | 17.5C, dry, wind 7 km/h. Normal | 7th/20 (8th on ESPN; 7 pts, play-off band; home-only 6th) v 17th (4 pts, play-out slot, 1 above drop; away-only 19th, 1 pt from 3). Early season, 5 played: table unreliable (R2) | L D W W L / W L L L D |
| 11 | Lens v Lyon, Ligue 1 rd 6 | W D L W D (incl. a Coupe de France 2-2, Lens won on pens). At Bollaert: L D W W D. Since 2010: Lens W7 D4 L8 | 14.3C, wind 20 (models 22-31), gusts 38-53. Gust flag | 15th/18 (4 pts, level with 16th, 1 above direct drop; home-only 11th) v 2nd (11 pts, GD +8; away-only 5th). Early season, 5 played (R2) | L D W L L / W W D W D |
| 12 | Cobh Ramblers v Kerry FC, LOI First Division rd 35 of 36 | L W W D L (incl. one FAI Cup). At St Colman's since 2023: W5 D2 L1. Since 2023 overall: Cobh W9 D5 L3 | 12.2C, dry, wind 21, gusts 36-46 (all models). Gust flag. Artificial pitch | 4th/10 (49 pts) v 6th (48 pts). Places 2-5 = promotion play-offs. 5th Longford, 6th Kerry and 7th Athlone all on 48. Cork already champions. 2 games left each (Kerry's last: home to Cork) | W D L W D / W W L L W |
| 13 | Malaga v Espanyol, La Liga MD 8 | L L L L L, but all 5 are 5-10 years old and 2 were in Segunda: counts for little (R4) | 21.7C, dry, calm. Normal | 20th/20 (3 pts, 0 wins, GD -9, 2 behind safety; home-only 18th) v 15th (7 pts, 2 above drop; away-only 10th). 7 played | L L D D L / L L W D L |

Notes:
- Rest: games 10, 11, 13 both sides 19-21 days since last match (international break; no fixture in between). Game 12 both played 2 Oct.
- Game 11: Lens beat Slavia Prague away in the Champions League on 10 Sep; Lyon beat Anderlecht away in the Europa League on 16 Sep.
- Game 12 stakes: Cobh 4th with 49 pts, then three teams on 48 for the last two play-off places. Kerry's 3-0 win on 3 Aug was described as their first ever win over Cobh. Cobh home table 8th of 10 (W6 D7 L4); last 5 home league D D D W W.
- Game 13: Malaga promoted via play-offs (beat Almeria). Bottom, winless after 7.
- Data warnings: a search summary invented "2-1 Avellino" for the unplayed game 10 (recycled from Jan); ontourfootball and futboltotal list wrong dates for games 10 and 13.

Ledger JSON (weather flag strings rewritten as plain text):
```
{"n": 10, "profile": {"h2h_home_view": "L W", "h2h_meetings": 2, "home_pos": 7, "away_pos": 17, "teams": 20, "home_form": "L D W W L", "away_form": "W L L L D", "weather": {"temp_c": 17.5, "rain_mm": 0.2, "rain_pct": 13, "wind_kmh": 7.1, "gust_kmh": 15.1, "flag": "normal"}, "captured": "2026-10-07 16:30 EAT"}}
{"n": 11, "profile": {"h2h_home_view": "W D L W D", "h2h_meetings": 5, "home_pos": 15, "away_pos": 2, "teams": 18, "home_form": "L D W L L", "away_form": "W W D W D", "weather": {"temp_c": 14.3, "rain_mm": 0.0, "rain_pct": 57, "wind_kmh": 20.5, "gust_kmh": 37.8, "flag": "gusts 30+, sustained under 30"}, "captured": "2026-10-07 16:30 EAT"}}
{"n": 12, "profile": {"h2h_home_view": "L W W D L", "h2h_meetings": 5, "home_pos": 4, "away_pos": 6, "teams": 10, "home_form": "W D L W D", "away_form": "W W L L W", "weather": {"temp_c": 12.2, "rain_mm": 0.0, "rain_pct": 0, "wind_kmh": 20.9, "gust_kmh": 36.4, "flag": "gusts 30+, sustained under 30"}, "captured": "2026-10-07 16:30 EAT"}}
{"n": 13, "profile": {"h2h_home_view": "L L L L L", "h2h_meetings": 5, "home_pos": 20, "away_pos": 15, "teams": 20, "home_form": "L L D D L", "away_form": "L L W D L", "weather": {"temp_c": 21.7, "rain_mm": 0.0, "rain_pct": 1, "wind_kmh": 1.8, "gust_kmh": 11.9, "flag": "normal"}, "captured": "2026-10-07 16:30 EAT"}}
```
