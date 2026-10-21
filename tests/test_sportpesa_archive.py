import json

import numpy as np
import pandas as pd

from src.archive_study import estimate_tilt
from src.slip_optimizer import sportpesa_tilt
from src.sportpesa_archive import load_archive, match_odds, merge_dumps, similarity


def _card(tmp_path):
    raw = [{"h": 7, "id": "x", "f": "2024-01-07T21:00:00Z",
            "e": [[1, "2024-01-06T15:00:00Z", "Everton FC", "Wolverhampton Wanderers", "Away", "0:2"],
                  [2, "2024-01-06T15:00:00Z", "Stade Rennais FC", "OGC Nice", "Draw", "PD:X"]],
            "p": [["17/17", 1e8]],
            "w": {"17/17": [["Jackpot", 1e8, 0, 0], ["Category5", 2e6, 300, 9000.5]]}}]
    path = tmp_path / "a.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    return load_archive(path)


def test_load_archive_flags_postponed_and_tiers(tmp_path):
    games, cards = _card(tmp_path)
    assert list(games["result"]) == ["A", "D"]
    assert not games.loc[0, "postponed"] and games.loc[1, "postponed"]
    assert np.isnan(games.loc[1, "hg"])
    assert cards.loc[0, "winners_12"] == 300 and cards.loc[0, "paid_12"] == 9000.5
    assert cards.loc[0, "winners_17"] == 0


def test_similarity_handles_club_suffixes():
    assert similarity("Everton FC", "Everton") == 1.0
    assert similarity("Stade Rennais FC", "Rennes") >= 0.6
    assert similarity("Everton FC", "Burnley") < 0.5


def test_match_needs_same_score_and_day(tmp_path):
    games, _ = _card(tmp_path)
    odds = pd.DataFrame({
        "league": ["E0", "E0"], "date": pd.to_datetime(["2024-01-06", "2024-01-06"]),
        "fd_home": ["Everton", "Rennes"], "fd_away": ["Wolves", "Nice"], "fhg": [0, 1], "fag": [2, 1],
        "oh": [2.5, 2.4], "od": [3.2, 3.3], "oa": [2.9, 3.0], "ch": [2.6, 2.4], "cd": [3.2, 3.3],
        "ca": [2.8, 3.0], "over": [2.0, 2.0], "under": [1.8, 1.8]})
    m = match_odds(games, odds)
    # Everton-Wolves: same score, same day, one name exact -> matched despite "Wolves"
    assert m.loc[0, "league"] == "E0" and m.loc[0, "has_odds"]
    assert abs(m.loc[0, ["pH", "pD", "pA"]].sum() - 1) < 1e-9
    # the postponed game is never matched
    assert not m.loc[1, "has_odds"]
    wrong = odds.assign(fag=[3, 1])
    assert not match_odds(games, wrong).loc[0, "has_odds"]


def test_merge_dumps_adds_and_replaces_cards(tmp_path):
    archive = tmp_path / "arch.json"
    archive.write_text(json.dumps([{"h": 1, "e": []}, {"h": 2, "e": []}]), encoding="utf-8")
    payload = json.dumps([{"h": 2, "e": [1]}, {"h": 3, "e": []}])
    dump = tmp_path / "dump.txt"
    dump.write_text(json.dumps([{"type": "text", "text": json.dumps(f"SPCHUNK0|{len(payload)}|{payload}")}]),
                    encoding="utf-8")
    assert merge_dumps([dump], archive) == 3
    cards = json.loads(archive.read_text(encoding="utf-8"))
    assert [c["h"] for c in cards] == [1, 2, 3] and cards[1]["e"] == [1]


def test_estimate_tilt_shrinks_towards_one():
    n = 400
    g = pd.DataFrame({"has_odds": True, "played": True, "fav": "H", "card": np.arange(n) // 17,
                      "pH": 0.40, "pD": 0.30, "pA": 0.30, "fav_p": 0.40,
                      "result": ["H"] * 160 + ["D"] * 140 + ["A"] * 100})
    g["fav_won"] = (g["result"] == "H").astype(float)
    g["isD"] = (g["result"] == "D").astype(float)
    t = estimate_tilt(g, prior_games=400, save=False)
    assert t["raw"]["fav"] == 1.0 and abs(t["raw"]["draw"] - 140 / 120) < 1e-3
    assert t["weight"] == 0.5
    assert abs(t["draw"] - (1 + (140 / 120 - 1) / 2)) < 1e-3 and t["dog"] < 1


def test_sportpesa_tilt_moves_underdog_to_draw():
    p = np.array([[0.42, 0.28, 0.30], [0.30, 0.28, 0.42], [0.33, 0.35, 0.32]])
    t = sportpesa_tilt(p, 1.0125, 1.03, 0.955)
    assert np.allclose(t.sum(axis=1), 1)
    assert t[0, 1] > p[0, 1] and t[0, 2] < p[0, 2] and t[0, 0] > p[0, 0]
    assert t[1, 1] > p[1, 1] and t[1, 0] < p[1, 0]
    assert np.allclose(t[2], p[2])  # draw favourite left alone
    assert np.allclose(sportpesa_tilt(p, 1, 1, 1), p)
