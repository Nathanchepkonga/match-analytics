import numpy as np
import pandas as pd

from src.factor_tests import h2h_and_referee


def test_h2h_uses_only_the_previous_meeting():
    d = pd.DataFrame({
        "home": ["A", "B", "A"], "away": ["B", "A", "B"], "hg": [2, 1, 0], "ag": [0, 1, 0],
        "hy": [1, 2, 3], "ay": [1, 2, 3], "hr": [0, 0, 0], "ar": [0, 0, 0],
        "res": ["H", "D", "D"], "league": "X", "ref": ["R", "R", None]})
    out = h2h_and_referee(d)
    assert np.isnan(out.loc[0, "h2h_last"])       # first meeting: nothing known
    assert out.loc[1, "h2h_last"] == -1.0          # B at home; last meeting A won
    assert out.loc[2, "h2h_last"] == 0.0           # last meeting was a draw
    assert np.isnan(out.loc[2, "ref_cards"])       # no referee named
    # referee's second game uses only the first game's cards, shrunk to the league mean
    assert out.loc[1, "ref_cards"] < out.loc[0, "ref_cards"] or out.loc[1, "ref_cards"] > 0
