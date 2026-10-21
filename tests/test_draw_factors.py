import pandas as pd

from src.draw_factors import add_team_form


def test_team_form_uses_only_earlier_games():
    d = pd.DataFrame({
        "league": "X", "season": "2627", "date": pd.to_datetime(["2026-08-01", "2026-08-08", "2026-08-15"]),
        "home": ["A", "B", "A"], "away": ["B", "A", "B"], "hg": [3, 0, 1], "ag": [0, 0, 1],
        "hst": [5, 2, 3], "ast": [1, 2, 3], "cards": [2, 6, 4], "draw": [0, 1, 1]})
    f = add_team_form(d)
    # first game: nothing known yet
    assert pd.isna(f.loc[0, "h_gf_pre"]) and f.loc[0, "h_n_pre"] == 0
    # game 3 (A at home): A scored 3 then 0 in its two earlier games, B conceded 3 and 0
    assert f.loc[2, "h_gf_pre"] == 1.5 and f.loc[2, "h_n_pre"] == 2
    assert f.loc[2, "a_ga_pre"] == 1.5
    assert f.loc[2, "h_cards_game_pre"] == 4.0          # bookings in A's games: 2 and 6
    assert f.loc[2, "h_dr_pre"] == 0.5 and f.loc[2, "a_dr_pre"] == 0.5
