"""Tests for src/jackpot_ledger.py, including regression checks against hand-verified scores."""
from src.jackpot_ledger import (
    load_slates, score_slip, favourite, departures, style_report, slate_summary,
    devig, chance_at_least, tipster_scores, tipster_report, expected_best, money_summary,
    draw_role, draw_plan,
)


def _slate(sid):
    return next(s for s in load_slates() if s["slate_id"] == sid)


def _slip(slate, name):
    return next(x for x in slate["slips"] if x["name"] == name)["picks"].split()


def test_favourite_is_shortest_price():
    assert favourite([2.70, 3.40, 2.23]) == "A"
    assert favourite([2.07, 3.40, 3.30]) == "H"


def test_real_ledgers_reproduce_verified_scores():
    s4 = _slate("2026-10-03")
    assert score_slip(s4, _slip(s4, "S1")) == 6
    assert score_slip(s4, _slip(s4, "S6")) == 8
    s3 = _slate("2026-10-02")
    assert score_slip(s3, _slip(s3, "A3")) == 2
    assert score_slip(s3, _slip(s3, "D6")) == 7
    assert score_slip(s3, [favourite(g["odds"]) for g in s3["games"]]) == 6


def test_tweak_style_counts_match_hand_count():
    deps = departures([_slate("2026-10-03")])
    tweaks = deps[deps["style"] == "near-even-tweaks"]
    assert len(tweaks) == 15
    assert int(tweaks["pick_right"].sum()) == 7
    assert int(tweaks["fav_right"].sum()) == 4


def test_unplayed_slate_is_ignored():
    slate = {"slate_id": "x", "games": [{"n": 1, "odds": [2.0, 3.0, 4.0]}],
             "slips": [{"name": "S1", "style": "favourites", "picks": "H"}]}
    assert style_report([slate]).empty
    assert slate_summary([slate]).empty


def test_devig_removes_the_margin():
    probs = devig([2.0, 3.4, 3.6])
    assert abs(sum(probs) - 1) < 1e-9
    assert probs[0] > probs[1] > probs[2]


def test_chance_at_least_matches_hand_calculation():
    assert abs(chance_at_least([0.5, 0.5], 1) - 0.75) < 1e-9
    assert abs(chance_at_least([0.5, 0.5], 2) - 0.25) < 1e-9
    assert chance_at_least([0.4] * 3, 0) == 1.0


def test_double_chance_and_missing_picks_score_correctly():
    slate = {"games": [{"result": "H"}, {"result": "D"}, {"result": "A"}]}
    assert score_slip(slate, ["HD", "HD", "-"]) == 2


def test_tipsters_scored_from_picks_or_recorded_totals():
    slate = {"slate_id": "x", "games": [{"n": 1, "odds": [2.0, 3.4, 3.6], "result": "H"},
                                        {"n": 2, "odds": [2.0, 3.4, 3.6], "result": "A"}],
             "slips": [{"name": "S1", "style": "favourites", "picks": "H H"}],
             "tipsters": [{"name": "picks", "picks": "H -"},
                          {"name": "total", "correct": 1, "games": 2, "doubles": 0}]}
    scores = {t["tipster"]: t for t in tipster_scores(slate)}
    assert (scores["picks"]["correct"], scores["picks"]["games"]) == (1, 1)
    assert scores["total"]["correct"] == 1
    assert len(tipster_report([slate])) == 2


def test_slate_summary_benchmarks_for_3_oct():
    row = slate_summary([_slate("2026-10-03")]).iloc[0]
    assert row["random_expected"] == 5.7
    assert row["favourites_expected"] == 6.6
    assert row["favourites_correct"] == 6
    assert row["tipsters_avg"] == 6.0


def test_expected_best_matches_hand_cases():
    certain = {"games": [{"odds": [1.0001, 1e6, 1e6], "result": "H"}] * 3,
               "slips": [{"picks": "H H H"}, {"picks": "A A A"}]}
    assert abs(expected_best(certain, sims=2000) - 3) < 1e-6
    # 6 slips on the 3 Oct card: the odds expected a best slip of ~8.2; it scored 8.
    assert 8.0 <= expected_best(_slate("2026-10-03")) <= 8.4


def test_money_summary_totals():
    slates = [{"slate_id": "a", "staked_ksh": 990, "won_ksh": 0},
              {"slate_id": "b", "staked_ksh": 594, "won_ksh": 4280},
              {"slate_id": "c"}]
    df = money_summary(slates)
    assert list(df["slate"]) == ["a", "b", "total"]
    assert df.iloc[-1]["net_ksh"] == 4280 - 1584
    assert money_summary([{"slate_id": "x"}]).empty


def test_tipster_with_no_picks_is_skipped():
    slate = {"slate_id": "x", "games": [{"n": 1, "odds": [2.0, 3.4, 3.6], "result": "H"}],
             "slips": [{"name": "S1", "style": "favourites", "picks": "H"}],
             "tipsters": [{"name": "not posted", "picks": "-"}]}
    assert tipster_scores(slate) == []
    assert tipster_report([slate]).empty
    assert slate_summary([slate]).iloc[0]["tipsters_avg"] is None


def test_draw_role_follows_the_study_thresholds():
    assert draw_role([2.39, 2.90, 2.90]) == "draw-backup"        # draw level with the other side
    assert draw_role([2.80, 2.85, 2.80]) == "draw-main"          # three-way tie
    assert draw_role([2.75, 3.25, 2.70]) == "side-backup"        # home and away level
    assert draw_role([2.41, 3.10, 2.70]) == "either-backup"      # draw >= 29%, favourite <= 40%
    assert draw_role([2.07, 3.35, 2.95]) == "side-backup"        # draw 3rd and under 29%
    assert draw_role([2.07, 3.35, 2.95], p_under=0.58) == "either-backup"
    assert draw_role([2.41, 3.10, 2.70], p_under=0.45) == "side-backup"


def test_draw_plan_covers_every_game():
    plan = draw_plan(_slate("2026-10-09"))
    assert list(plan["game"]) == list(range(1, 14))
    assert plan.loc[plan["game"] == 6, "draw_role"].item() == "draw-backup"


def test_change_types_splits_draws_and_sides_and_dedupes():
    from src.jackpot_ledger import change_types
    slate = {"slate_id": "t", "games": [
        {"n": 1, "odds": [2.0, 3.4, 3.8], "result": "D"},   # favourite H
        {"n": 2, "odds": [2.0, 3.4, 3.8], "result": "A"}],
        "slips": [{"name": "S1", "style": "x", "picks": "D A"},
                  {"name": "S2", "style": "x", "picks": "D H"}]}
    t = change_types([slate]).set_index("change")
    assert t.loc["draw", "picks_on_slips"] == 2 and t.loc["draw", "distinct_calls"] == 1
    assert t.loc["draw", "calls_right"] == 1
    assert t.loc["side", "distinct_calls"] == 1 and t.loc["side", "calls_right"] == 1


def test_reason_report_groups_by_recorded_reason():
    from src.jackpot_ledger import reason_report
    slate = {"slate_id": "t", "games": [
        {"n": 1, "odds": [2.0, 3.4, 3.8], "result": "A"},
        {"n": 2, "odds": [2.0, 3.4, 3.8], "result": "H"}],
        "slips": [{"name": "S1", "style": "x", "picks": "A D", "reasons": {"1": "news", "2": "draw-rule"}},
                  {"name": "S2", "style": "x", "picks": "A H", "reasons": {"1": "news"}}]}
    t = reason_report([slate]).set_index("reason")
    assert t.loc["news", "calls"] == 1 and t.loc["news", "right"] == 1
    assert t.loc["draw-rule", "calls"] == 1 and t.loc["draw-rule", "favourite_would_have"] == 1
