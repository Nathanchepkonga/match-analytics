import pandas as pd

from src import live_feeds


def test_betika_feed_filters_to_nairobi_day(monkeypatch):
    monkeypatch.setattr(
        live_feeds,
        "_get_json",
        lambda url, headers=None: {
            "data": [
                {
                    "match_id": "today",
                    "start_time": "2026-11-02 18:00:00",
                    "competition_name": "Test League",
                    "category": "Kenya",
                    "home_team": "Home",
                    "away_team": "Away",
                    "home_odd": "2.10",
                    "neutral_odd": "3.20",
                    "away_odd": "3.40",
                },
                {
                    "match_id": "tomorrow",
                    "start_time": "2026-11-03 00:01:00",
                    "competition_name": "Test League",
                    "category": "Kenya",
                    "home_team": "Later",
                    "away_team": "Match",
                },
            ]
        },
    )

    matches = live_feeds.fetch_betika_daily_matches(
        now=pd.Timestamp("2026-11-02 10:00:00", tz="Africa/Nairobi").to_pydatetime()
    )

    assert len(matches) == 1
    assert matches.iloc[0]["match_id"] == "today"
    assert matches.iloc[0]["home_odds"] == 2.10


def test_sportpesa_feed_normalizes_events(monkeypatch):
    monkeypatch.setattr(
        live_feeds,
        "_get_json",
        lambda url, headers=None: {
            "id": "jackpot-id",
            "humanId": 10,
            "bettingStatus": "Open",
            "settings": {"numberOfEvents": 17},
            "events": [
                {
                    "id": "match-id",
                    "utcKickOffTime": "2026-11-02T18:00:00Z",
                    "tournamentName": "Test Cup",
                    "countryName": "Testland",
                    "competitors": [
                        {"competitorName": "Home", "isHome": True},
                        {"competitorName": "Away", "isHome": False},
                    ],
                    "home": 2.0,
                    "draw": 3.0,
                    "away": 4.0,
                    "score": None,
                    "order": 1,
                }
            ],
        },
    )

    jackpot = live_feeds.fetch_sportpesa_jackpot()

    assert jackpot["human_id"] == 10
    assert jackpot["number_of_events"] == 17
    assert jackpot["events"][0]["home_team"] == "Home"
    assert jackpot["events"][0]["draw_odds"] == 3.0
