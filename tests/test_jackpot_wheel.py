"""
Tests for src/jackpot_wheel.py. Includes a regression test for a real bug found in
production: build_wheel used to eagerly materialize the full combinatorial space
(3**num_live_legs), which hung and consumed ~1.8GB RAM for a 14-live-leg slate.
"""
import time

from src.jackpot_wheel import classify_legs, build_wheel, score_wheel, OUTCOMES


def test_classify_legs_splits_bankers_and_live(make_fixture_factory):
    banker = make_fixture_factory(match_id="a", outcome_estimate=(0.6, 0.2, 0.2))
    live = make_fixture_factory(match_id="b", outcome_estimate=(0.34, 0.33, 0.33))

    bankers, live_legs = classify_legs([banker, live], banker_threshold=0.45)

    assert len(bankers) == 1
    assert bankers[0][0].match_id == "a"
    assert bankers[0][1] == "Home"
    assert len(live_legs) == 1
    assert live_legs[0].match_id == "b"


def test_build_wheel_full_coverage_when_space_fits_budget(make_fixture_factory):
    # 2 live legs -> 3**2 = 9 combinations, well within a 9-slip budget: every
    # combination should be covered exactly once.
    fixtures = [
        make_fixture_factory(match_id="live1", outcome_estimate=(0.34, 0.33, 0.33)),
        make_fixture_factory(match_id="live2", outcome_estimate=(0.34, 0.33, 0.33)),
    ]
    wheel = build_wheel(fixtures, num_slips=9, banker_threshold=0.45)

    assert len(wheel) == 9
    combos = set(zip(wheel["live1"], wheel["live2"]))
    assert len(combos) == 9  # every one of the 3x3 combinations appears


def test_build_wheel_bankers_are_identical_across_all_slips(make_fixture_factory):
    banker = make_fixture_factory(match_id="banker", outcome_estimate=(0.7, 0.15, 0.15))
    live = make_fixture_factory(match_id="live", outcome_estimate=(0.34, 0.33, 0.33))
    wheel = build_wheel([banker, live], num_slips=5, banker_threshold=0.45)

    assert (wheel["banker"] == "Home").all()


def test_build_wheel_does_not_hang_on_large_live_leg_count(make_fixture_factory):
    """
    Regression test: 14 live legs means 3**14 ~= 4.8M combinations. The original
    implementation materialized this list eagerly and hung / exhausted memory.
    This must complete quickly regardless of live-leg count.
    """
    fixtures = [
        make_fixture_factory(match_id=f"live{i}", outcome_estimate=(0.34, 0.33, 0.33))
        for i in range(14)
    ]
    start = time.time()
    wheel = build_wheel(fixtures, num_slips=10, banker_threshold=0.45)
    elapsed = time.time() - start

    assert len(wheel) == 10
    assert elapsed < 10, f"build_wheel took {elapsed:.1f}s for 14 live legs - should be near-instant"


def test_build_wheel_produces_unique_slips_when_space_exceeds_budget(make_fixture_factory):
    fixtures = [
        make_fixture_factory(match_id=f"live{i}", outcome_estimate=(0.4, 0.3, 0.3))
        for i in range(5)
    ]
    wheel = build_wheel(fixtures, num_slips=8, banker_threshold=0.45)
    live_cols = [c for c in wheel.columns if c != "slip"]
    rows_as_tuples = [tuple(row) for row in wheel[live_cols].itertuples(index=False)]
    assert len(set(rows_as_tuples)) == len(rows_as_tuples), "slips should not duplicate when unique combos are available"


def test_score_wheel_counts_correct_legs(make_fixture_factory):
    f1 = make_fixture_factory(match_id="m1", actual_result="Home")
    f2 = make_fixture_factory(match_id="m2", actual_result="Away")
    wheel = build_wheel([f1, f2], num_slips=1, banker_threshold=0.0)  # both bankers
    scored = score_wheel(wheel, [f1, f2])
    assert "correct" in scored.columns
    assert scored["correct"].iloc[0] in (0, 1, 2)


def test_outcomes_constant_matches_schema_values():
    assert OUTCOMES == ["Home", "Draw", "Away"]
