"""
Author: Tiago Monteiro
Date: 21-12-2025
Combinatorial slip construction for jackpot-style multi-leg bets. Given per-leg
outcome probability estimates, splits fixtures into bankers (fixed across every
slip) and live/uncertain legs, then wheels the live legs across a slip budget
instead of producing independent narrative guesses per slip.
"""

import random
from itertools import product
from typing import List, Tuple

import pandas as pd

from .schema import FixtureIntel

OUTCOMES = ["Home", "Draw", "Away"]


def classify_legs(
    fixtures: List[FixtureIntel], banker_threshold: float = 0.45
) -> Tuple[List[Tuple[FixtureIntel, str]], List[FixtureIntel]]:
    """
    Split fixtures into bankers (a single outcome clearly favoured) and live legs
    (genuinely uncertain, no outcome estimate clears the threshold).

    :param fixtures: Fixtures with analysis.outcome_estimate populated.
    :param banker_threshold: Minimum top-outcome probability to treat a leg as a banker.
    :return: (bankers as (fixture, pick) pairs, live fixtures list).
    """
    bankers, live = [], []
    for f in fixtures:
        est = f.analysis.outcome_estimate if f.analysis else []
        if len(est) != 3:
            live.append(f)
            continue
        top_p = max(est)
        if top_p >= banker_threshold:
            bankers.append((f, OUTCOMES[est.index(top_p)]))
        else:
            live.append(f)
    return bankers, live


def build_wheel(
    fixtures: List[FixtureIntel], num_slips: int, banker_threshold: float = 0.45, seed: int = 42
) -> pd.DataFrame:
    """
    Build num_slips full-slate slip combinations. Bankers get the same pick in every
    slip. Live legs are wheeled: if the full combination space (3^num_live_legs) fits
    within the slip budget, every combination is covered exactly once (a genuine full
    guarantee on the live legs). Otherwise, slips are sampled without replacement,
    weighted by each leg's own estimated probability, so the portfolio spreads
    coverage across the most plausible combinations rather than repeating the single
    most likely one num_slips times.

    :param fixtures: Fixtures with analysis.outcome_estimate populated.
    :param num_slips: Slip budget.
    :param banker_threshold: Passed through to classify_legs.
    :param seed: RNG seed, for reproducibility.
    :return: DataFrame, one row per slip, one column per match_id plus a 'slip' index.
    """
    bankers, live = classify_legs(fixtures, banker_threshold)
    rng = random.Random(seed)

    # 3**len(live) can be astronomically large (e.g. 3**15 ~= 14M) - never materialize
    # the full space. Only enumerate exhaustively when it's small enough to be cheap.
    MAX_ENUMERATE = 5000
    total_combos = 3 ** len(live) if live else 1

    if total_combos <= MAX_ENUMERATE and total_combos <= num_slips:
        live_space = list(product(OUTCOMES, repeat=len(live))) if live else [()]
        chosen = live_space * (num_slips // total_combos) + live_space[: num_slips % total_combos]
    elif total_combos <= MAX_ENUMERATE:
        live_space = list(product(OUTCOMES, repeat=len(live))) if live else [()]

        def combo_weight(combo):
            w = 1.0
            for f, outcome in zip(live, combo):
                est = f.analysis.outcome_estimate if f.analysis else [1 / 3, 1 / 3, 1 / 3]
                w *= est[OUTCOMES.index(outcome)]
            return w

        pool = [(c, combo_weight(c)) for c in live_space]
        chosen = []
        while len(chosen) < num_slips and pool:
            combos, weights = zip(*pool)
            pick = rng.choices(combos, weights=weights, k=1)[0]
            chosen.append(pick)
            pool = [(c, w) for c, w in pool if c != pick]
    else:
        # Space too large to enumerate: sample each leg independently (weighted by its
        # own estimated probability) per slip, rejecting exact duplicate slips.
        chosen = []
        seen = set()
        attempts = 0
        max_attempts = num_slips * 200
        while len(chosen) < num_slips and attempts < max_attempts:
            attempts += 1
            combo = tuple(
                rng.choices(OUTCOMES, weights=(f.analysis.outcome_estimate if f.analysis else [1 / 3, 1 / 3, 1 / 3]), k=1)[0]
                for f in live
            )
            if combo not in seen:
                seen.add(combo)
                chosen.append(combo)
        # Top up with random (possibly duplicate) combos if uniqueness sampling stalled.
        while len(chosen) < num_slips:
            combo = tuple(
                rng.choices(OUTCOMES, weights=(f.analysis.outcome_estimate if f.analysis else [1 / 3, 1 / 3, 1 / 3]), k=1)[0]
                for f in live
            )
            chosen.append(combo)

    banker_dict = {f.match_id: pick for f, pick in bankers}
    rows = []
    for slip_idx, combo in enumerate(chosen, start=1):
        live_dict = {f.match_id: pick for f, pick in zip(live, combo)}
        row = {"slip": slip_idx}
        for f in fixtures:
            row[f.match_id] = banker_dict.get(f.match_id) or live_dict.get(f.match_id)
        rows.append(row)

    return pd.DataFrame(rows)


def score_wheel(wheel: pd.DataFrame, fixtures: List[FixtureIntel]) -> pd.DataFrame:
    """
    Score every slip in a wheel against fixtures' actual_result, for backtesting.

    :param wheel: Output of build_wheel.
    :param fixtures: Fixtures with actual_result populated.
    :return: wheel with an added 'correct' column (count of legs matching actual_result).
    """
    actuals = {f.match_id: f.actual_result for f in fixtures if f.actual_result}
    match_cols = [c for c in wheel.columns if c in actuals]
    scored = wheel.copy()
    scored["correct"] = scored[match_cols].apply(
        lambda row: sum(1 for col in match_cols if row[col] == actuals[col]), axis=1
    )
    return scored
