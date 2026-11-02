import numpy as np
import pandas as pd

from src.prediction import poisson_probabilities, rolling_backtest, summarize_backtest


def test_poisson_probabilities_are_valid():
    result = poisson_probabilities(1.4, 1.1)

    assert np.isclose(sum(result["outcome"].values()), 1.0)
    assert 0.0 <= result["over_2_5"] <= 1.0
    assert 0.0 <= result["btts_yes"] <= 1.0
    assert result["most_likely_score"].count("-") == 1


def test_rolling_backtest_only_scores_future_matches():
    matches = pd.DataFrame(
        [
            {"date": "2024-01-01", "home": "A", "away": "B", "home_goals": 1, "away_goals": 0, "result": "H"},
            {"date": "2024-01-02", "home": "B", "away": "A", "home_goals": 0, "away_goals": 0, "result": "D"},
            {"date": "2024-01-03", "home": "A", "away": "B", "home_goals": 2, "away_goals": 1, "result": "H"},
        ]
    )
    results = rolling_backtest(matches, min_history=2)

    assert len(results) == 1
    assert results.iloc[0]["date"] == "2024-01-03"


def test_empty_backtest_summary_is_stable():
    summary = summarize_backtest(pd.DataFrame())

    assert summary == {"matches": 0, "accuracy": 0.0, "log_loss": 0.0, "brier": 0.0, "roi": 0.0}
