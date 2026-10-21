"""Tests for src/jackpot_sim.py strategies on a small synthetic card."""
import numpy as np
import pandas as pd

from src.jackpot_sim import DRAW, favourites_1, tweaks_3, draw_heavy_3, close_draws_3, run


def _card(n=13, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):  # balanced games where the draw is never the favourite, like real jackpot cards
        draw = rng.uniform(0.24, 0.30)
        home = rng.uniform(0.32, 0.45)
        p = [home, draw, 1 - home - draw]
        rows.append({"pH": p[0], "pD": p[1], "pA": p[2], "pU": 0.5, "res": "HDA"[i % 3],
                     "week": "2025-01", "season": 2025})
    return pd.DataFrame(rows)


def test_favourites_slip_picks_the_likeliest_outcome():
    card = _card()
    assert (favourites_1(card, None)[0] == card[["pH", "pD", "pA"]].values.argmax(1)).all()


def test_draw_heavy_has_three_draws_per_slip_and_keeps_clearest_favourites():
    card = _card()
    p = card[["pH", "pD", "pA"]].values
    fav = p.argmax(1)
    clearest = np.argsort(-(np.sort(p, 1)[:, 2] - np.sort(p, 1)[:, 1]))[:3]
    for s in draw_heavy_3(card, None):
        assert ((s == DRAW) & (fav != DRAW)).sum() == 3
        assert (s[clearest] == fav[clearest]).all()


def test_tweaks_change_at_most_two_games_per_slip():
    card = _card()
    fav = favourites_1(card, None)[0]
    slips = tweaks_3(card, None)
    assert [int((s != fav).sum()) for s in slips] == [0, 1, 2]
    assert len(close_draws_3(card, None)) == 3


def test_run_scores_every_strategy():
    res, changes = run([_card(), _card(seed=1)], [8, 10])
    assert set(res.columns) >= {"best", "slip_mean", "8+", "10+"}
    assert res.groupby("strategy").size().min() == 2
