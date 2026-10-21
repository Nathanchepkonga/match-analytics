"""
Author: Tiago Monteiro
Date: 21-12-2025
Loader for pre-match fixture intelligence (external stats sources + tactical analysis).
Distinct from data_loader.py: this covers fixtures with no public tracking data,
sourced instead from stats/event sites (FBref, Understat, Sofascore, FotMob, Transfermarkt).
"""

import json
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

from .schema import FixtureIntel

FIXTURE_DATA_DIR = Path(__file__).parent.parent / "data" / "fixture_intelligence"


def load_fixtures(path: Path = None) -> List[FixtureIntel]:
    """
    Load fixture intelligence records from a JSON file.

    :param path: Optional explicit path. Defaults to the newest file in FIXTURE_DATA_DIR.
    :return: List of validated FixtureIntel records.
    """
    if path is None:
        if not FIXTURE_DATA_DIR.exists():
            return []
        files = sorted(FIXTURE_DATA_DIR.glob("*.json"))
        if not files:
            return []
        path = files[-1]

    if not path.exists():
        return []

    raw = json.loads(path.read_text(encoding="utf-8"))
    return [FixtureIntel(**item) for item in raw]


def load_all_fixtures() -> List[FixtureIntel]:
    """
    Load fixture intelligence records from every slate on disk (all JSON files in
    FIXTURE_DATA_DIR), for cross-slate scoring/backtesting rather than just the latest round.

    :return: Combined list of validated FixtureIntel records across all slates.
    """
    if not FIXTURE_DATA_DIR.exists():
        return []
    fixtures = []
    for path in sorted(FIXTURE_DATA_DIR.glob("*.json")):
        fixtures.extend(load_fixtures(path))
    return fixtures


def _result_for(home_score: int, away_score: int) -> str:
    if home_score > away_score:
        return "Home"
    if home_score < away_score:
        return "Away"
    return "Draw"


def score_predictions(fixtures: List[FixtureIntel] = None) -> pd.DataFrame:
    """
    Score every predictor (this app's own outcome_pick plus any recorded external_predictions,
    e.g. Sofascore/FotMob/FootyStats/Opta Analyst) against actual results, for fixtures where
    actual_result has been filled in. Fixtures with no actual_result are skipped (match not yet
    played, or result not yet recorded).

    :param fixtures: Fixtures to score. Defaults to every slate on disk (load_all_fixtures()).
    :return: DataFrame with one row per predictor and its hit rate, plus a naive "Always Home"
        baseline row for comparison.
    """
    if fixtures is None:
        fixtures = load_all_fixtures()

    completed = [f for f in fixtures if f.actual_result]
    if not completed:
        return pd.DataFrame(columns=["Predictor", "Correct", "Total", "Hit Rate"])

    tallies: Dict[str, Dict[str, int]] = {}

    def _tally(name: str, pick: str, actual: str):
        if name not in tallies:
            tallies[name] = {"correct": 0, "total": 0}
        tallies[name]["total"] += 1
        if pick == actual:
            tallies[name]["correct"] += 1

    for f in completed:
        actual = f.actual_result
        if f.analysis and f.analysis.outcome_pick:
            _tally("Claude (this app)", f.analysis.outcome_pick, actual)
        for site, pick in f.external_predictions.items():
            _tally(site, pick, actual)
        _tally("Baseline: always Home", "Home", actual)

    rows = []
    for name, t in tallies.items():
        rows.append({
            "Predictor": name,
            "Correct": t["correct"],
            "Total": t["total"],
            "Hit Rate": round(100 * t["correct"] / t["total"], 1) if t["total"] else 0.0,
        })

    df = pd.DataFrame(rows).sort_values("Hit Rate", ascending=False).reset_index(drop=True)
    return df


def match_results_table(fixtures: List[FixtureIntel] = None) -> pd.DataFrame:
    """
    Per-match breakdown of every predictor's pick vs the actual result, for completed fixtures.

    :param fixtures: Fixtures to include. Defaults to every slate on disk.
    :return: DataFrame with one row per completed fixture, one column per predictor.
    """
    if fixtures is None:
        fixtures = load_all_fixtures()

    completed = [f for f in fixtures if f.actual_result]
    rows = []
    for f in completed:
        row: Dict[str, Any] = {
            "Match": f"{f.home_team} vs {f.away_team}",
            "Score": f.actual_score or "",
            "Actual": f.actual_result,
        }
        if f.analysis and f.analysis.outcome_pick:
            row["Claude"] = f.analysis.outcome_pick
        for site, pick in f.external_predictions.items():
            row[site] = pick
        rows.append(row)
    return pd.DataFrame(rows)
