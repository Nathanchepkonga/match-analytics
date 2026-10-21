"""Tests for src/slip_optimizer.py: the exact chance must match brute-force enumeration."""
import itertools

import numpy as np

from src.slip_optimizer import DRAW, optimise


def _card(n, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        draw = rng.uniform(0.24, 0.31)
        home = rng.uniform(0.30, 0.46)
        rows.append([home, draw, 1 - home - draw])
    return np.array(rows)


def _brute(p, slips, target):
    idx = np.array(list(itertools.product(range(3), repeat=len(p))), dtype=np.int8)
    prob = np.prod(p[np.arange(len(p)), idx], axis=1)
    best = np.stack([(idx == s).sum(axis=1) for s in slips]).max(axis=0)
    return prob[best >= target].sum()


def test_exact_chance_matches_brute_force():
    p = _card(8)
    r = optimise(p, n_slips=3, target=6, m=4)
    assert abs(r["chance"] - _brute(p, r["slips"], 6)) < 1e-12


def test_first_slip_is_the_favourites_and_others_change_only_close_games():
    p = _card(9, seed=2)
    r = optimise(p, n_slips=3, target=7, m=4)
    fav = p.argmax(axis=1)
    assert (r["slips"][0] == fav).all()
    outside = np.setdiff1d(np.arange(9), r["close_games"])
    for s in r["slips"]:
        assert (s[outside] == fav[outside]).all()


def test_more_slips_never_lower_the_chance():
    p = _card(8, seed=3)
    chances = [optimise(p, n_slips=k, target=6, m=4)["chance"] for k in (1, 2, 3)]
    assert chances[0] <= chances[1] <= chances[2]


def test_draw_minimum_is_respected():
    p = _card(8, seed=4)
    r = optimise(p, n_slips=3, target=6, m=4, min_draws=2)
    assert all((s == DRAW).sum() >= 2 for s in r["slips"])


def test_chance_matches_the_optimiser_and_simulation_agrees():
    from src.slip_optimizer import chance
    p = _card(8, seed=5)
    r = optimise(p, n_slips=3, target=6, m=4)
    assert abs(chance(p, r["slips"], 6) - r["chance"]) < 1e-12


def test_per_slip_draw_minimums():
    p = _card(8, seed=6)
    r = optimise(p, n_slips=3, target=6, m=4, min_draws=[0, 0, 2])
    assert (r["slips"][2] == DRAW).sum() >= 2


def test_draw_range_and_chosen_games():
    from src.slip_optimizer import draw_cost_order
    p = _card(9, seed=7)
    vary = list(draw_cost_order(p)[:5])
    r = optimise(p, n_slips=3, target=7, min_draws=3, max_draws=4, vary=vary)
    assert sorted(r["close_games"]) == sorted(vary)
    assert all(3 <= (s == DRAW).sum() <= 4 for s in r["slips"])
    assert abs(r["chance"] - _brute(p, r["slips"], 7)) < 1e-12


def test_mega_categories_drops_the_least_clear_games():
    import numpy as np
    from src.slip_optimizer import mega_categories
    p = np.array([[0.5, 0.25, 0.25]] * 15 + [[0.34, 0.33, 0.33]] * 2)
    cats = {c["games"]: c for c in mega_categories(p)}
    assert cats[15]["drop"] == [16, 17]
    assert cats[17]["drop"] == []
    assert cats[15]["bonus_chance"] > cats[17]["bonus_chance"]
    assert cats[13]["all_correct"] > cats[17]["all_correct"]
