"""Leakage-safe baseline prediction models for the local football-data archive.

The models are intentionally transparent baselines. They are useful for diagnostics,
backtesting, and UI integration, not a substitute for a fully trained production model.
"""

from math import factorial
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

import numpy as np
import pandas as pd


OUTCOMES = ("H", "D", "A")


def load_match_results(data_dir: Optional[Path] = None) -> pd.DataFrame:
    """Load football-data CSVs with a common schema and discard unusable rows."""
    data_dir = data_dir or Path(__file__).parent.parent / "data" / "football_data"
    frames = []
    for path in sorted(data_dir.glob("*.csv")):
        raw = pd.read_csv(
            path,
            encoding="utf-8-sig",
            encoding_errors="replace",
            on_bad_lines="skip",
            low_memory=False,
        )
        columns = set(raw.columns)
        if {"HomeTeam", "AwayTeam", "FTHG", "FTAG"} <= columns:
            frame = pd.DataFrame(
                {
                    "league": path.stem.split("_")[0],
                    "date": raw.get("Date"),
                    "home": raw["HomeTeam"],
                    "away": raw["AwayTeam"],
                    "home_goals": raw["FTHG"],
                    "away_goals": raw["FTAG"],
                    "home_odds": raw.get("AvgH"),
                    "draw_odds": raw.get("AvgD"),
                    "away_odds": raw.get("AvgA"),
                }
            )
        elif {"Home", "Away", "HG", "AG"} <= columns:
            frame = pd.DataFrame(
                {
                    "league": raw.get("Country", "").astype(str) + " " + raw.get("League", "").astype(str),
                    "date": raw.get("Date"),
                    "home": raw["Home"],
                    "away": raw["Away"],
                    "home_goals": raw["HG"],
                    "away_goals": raw["AG"],
                    "home_odds": raw.get("AvgCH"),
                    "draw_odds": raw.get("AvgCD"),
                    "away_odds": raw.get("AvgCA"),
                }
            )
        else:
            continue
        frames.append(frame)

    if not frames:
        return pd.DataFrame(
            columns=[
                "league", "date", "home", "away", "home_goals", "away_goals",
                "home_odds", "draw_odds", "away_odds", "result",
            ]
        )

    matches = pd.concat(frames, ignore_index=True)
    matches["date"] = pd.to_datetime(matches["date"], dayfirst=True, errors="coerce")
    for column in ("home_goals", "away_goals", "home_odds", "draw_odds", "away_odds"):
        matches[column] = pd.to_numeric(matches[column], errors="coerce")
    matches = matches.dropna(subset=["date", "home", "away", "home_goals", "away_goals"])
    matches["result"] = np.select(
        [matches["home_goals"] > matches["away_goals"], matches["home_goals"] == matches["away_goals"]],
        ["H", "D"],
        default="A",
    )
    return matches.sort_values("date", kind="stable").reset_index(drop=True)


def _team_rates(history: pd.DataFrame, team: str, prior_matches: int = 20) -> Tuple[float, float]:
    """Estimate goals scored and conceded using only historical matches."""
    home = history[history["home"] == team][["home_goals", "away_goals"]].rename(
        columns={"home_goals": "for", "away_goals": "against"}
    )
    away = history[history["away"] == team][["away_goals", "home_goals"]].rename(
        columns={"away_goals": "for", "home_goals": "against"}
    )
    games = pd.concat([home, away]).tail(prior_matches)
    if games.empty:
        return 1.2, 1.2
    return float(games["for"].mean()), float(games["against"].mean())


def poisson_probabilities(home_rate: float, away_rate: float, max_goals: int = 8) -> Dict[str, object]:
    """Turn expected goals into scoreline and H/D/A probabilities."""
    goals = np.arange(max_goals + 1)
    home_pmf = np.exp(-home_rate) * np.power(home_rate, goals) / np.array([factorial(int(g)) for g in goals])
    away_pmf = np.exp(-away_rate) * np.power(away_rate, goals) / np.array([factorial(int(g)) for g in goals])
    matrix = np.outer(home_pmf, away_pmf)
    matrix = matrix / matrix.sum()
    outcome = {
        "H": float(np.tril(matrix, -1).sum()),
        "D": float(np.trace(matrix)),
        "A": float(np.triu(matrix, 1).sum()),
    }
    over_25 = float(sum(matrix[i, j] for i in goals for j in goals if i + j > 2))
    btts = float(sum(matrix[i, j] for i in goals for j in goals if i > 0 and j > 0))
    best = np.unravel_index(np.argmax(matrix), matrix.shape)
    return {
        "outcome": outcome,
        "over_2_5": over_25,
        "under_2_5": 1.0 - over_25,
        "btts_yes": btts,
        "btts_no": 1.0 - btts,
        "expected_home_goals": home_rate,
        "expected_away_goals": away_rate,
        "most_likely_score": f"{best[0]}-{best[1]}",
        "score_matrix": matrix,
    }


def predict_match(history: pd.DataFrame, home: str, away: str, prior_matches: int = 20) -> Dict[str, object]:
    """Predict a fixture from prior results only."""
    home_for, home_against = _team_rates(history, home, prior_matches)
    away_for, away_against = _team_rates(history, away, prior_matches)
    league_home = float(history["home_goals"].mean()) if not history.empty else 1.4
    league_away = float(history["away_goals"].mean()) if not history.empty else 1.1
    home_rate = max(0.05, league_home * (home_for / max(0.1, league_home)) * (away_against / max(0.1, league_home)))
    away_rate = max(0.05, league_away * (away_for / max(0.1, league_away)) * (home_against / max(0.1, league_away)))
    return poisson_probabilities(home_rate, away_rate)


def _log_loss(probabilities: Iterable[float], actual: str) -> float:
    value = max(1e-9, float(dict(zip(OUTCOMES, probabilities))[actual]))
    return -float(np.log(value))


def rolling_backtest(matches: pd.DataFrame, min_history: int = 100) -> pd.DataFrame:
    """Run a chronological backtest with no future matches visible to the model."""
    rows = []
    if matches.empty:
        return pd.DataFrame(columns=["date", "home", "away", "actual", "pick", "log_loss", "brier", "roi"])

    team_history = {}
    total_home_goals = 0.0
    total_away_goals = 0.0
    total_matches = 0

    def rates(team):
        games = team_history.get(team, [])[-20:]
        if not games:
            return 1.2, 1.2
        goals_for = [item[0] for item in games]
        goals_against = [item[1] for item in games]
        return float(np.mean(goals_for)), float(np.mean(goals_against))

    warmup = matches.iloc[:min_history]
    for row in warmup.itertuples(index=False):
        home_goals = float(row.home_goals)
        away_goals = float(row.away_goals)
        team_history.setdefault(row.home, []).append((home_goals, away_goals))
        team_history.setdefault(row.away, []).append((away_goals, home_goals))
        total_home_goals += home_goals
        total_away_goals += away_goals
        total_matches += 1

    for index in range(min_history, len(matches)):
        current = matches.iloc[index]
        home_for, home_against = rates(current["home"])
        away_for, away_against = rates(current["away"])
        league_home = total_home_goals / max(1, total_matches)
        league_away = total_away_goals / max(1, total_matches)
        home_rate = max(0.05, league_home * (home_for / max(0.1, league_home)) * (away_against / max(0.1, league_home)))
        away_rate = max(0.05, league_away * (away_for / max(0.1, league_away)) * (home_against / max(0.1, league_away)))
        prediction = poisson_probabilities(home_rate, away_rate)
        probs = prediction["outcome"]
        pick = max(OUTCOMES, key=lambda outcome: probs[outcome])
        actual = current["result"]
        brier = sum((probs[outcome] - float(outcome == actual)) ** 2 for outcome in OUTCOMES)
        odds_column = {"H": "home_odds", "D": "draw_odds", "A": "away_odds"}[pick]
        odds = current.get(odds_column)
        roi = np.nan if pd.isna(odds) or float(odds) <= 1 else (float(odds) - 1 if pick == actual else -1.0)
        rows.append(
            {
                "date": current["date"],
                "home": current["home"],
                "away": current["away"],
                "actual": actual,
                "pick": pick,
                "log_loss": _log_loss([probs[o] for o in OUTCOMES], actual),
                "brier": brier,
                "correct": pick == actual,
                "odds": odds,
                "roi": roi,
            }
        )
        home_goals = float(current["home_goals"])
        away_goals = float(current["away_goals"])
        team_history.setdefault(current["home"], []).append((home_goals, away_goals))
        team_history.setdefault(current["away"], []).append((away_goals, home_goals))
        total_home_goals += home_goals
        total_away_goals += away_goals
        total_matches += 1
    return pd.DataFrame(rows)


def summarize_backtest(results: pd.DataFrame) -> Dict[str, float]:
    """Return stable headline metrics for the prediction dashboard."""
    if results.empty:
        return {"matches": 0, "accuracy": 0.0, "log_loss": 0.0, "brier": 0.0, "roi": 0.0}
    return {
        "matches": int(len(results)),
        "accuracy": float(results["correct"].mean()),
        "log_loss": float(results["log_loss"].mean()),
        "brier": float(results["brier"].mean()),
        "roi": float(results["roi"].dropna().mean()) if results["roi"].notna().any() else 0.0,
    }
