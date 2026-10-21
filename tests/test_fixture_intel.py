"""Tests for src/fixture_intel.py - the loader and scoring functions."""
import json

from src.fixture_intel import load_fixtures, load_all_fixtures, score_predictions, match_results_table


def _write_slate(tmp_path, filename, fixtures_data):
    path = tmp_path / filename
    path.write_text(json.dumps(fixtures_data), encoding="utf-8")
    return path


def _fixture_dict(match_id, outcome_pick, actual_result, external_predictions=None):
    return {
        "match_id": match_id,
        "kickoff_date": "2026-01-01",
        "kickoff_time": "15:00",
        "country": "Testland",
        "competition": "Test League",
        "home_team": "Home FC",
        "away_team": "Away FC",
        "analysis": {
            "tactical_read": "test",
            "prediction_lean": "test",
            "outcome_estimate": [0.4, 0.3, 0.3],
            "outcome_pick": outcome_pick,
        },
        "actual_result": actual_result,
        "external_predictions": external_predictions or {},
    }


def test_load_fixtures_validates_via_schema(tmp_path):
    data = [_fixture_dict("m1", "Home", "Home")]
    path = _write_slate(tmp_path, "slate.json", data)
    fixtures = load_fixtures(path)
    assert len(fixtures) == 1
    assert fixtures[0].match_id == "m1"
    assert fixtures[0].analysis.outcome_pick == "Home"


def test_load_fixtures_missing_file_returns_empty(tmp_path):
    assert load_fixtures(tmp_path / "does_not_exist.json") == []


def test_load_all_fixtures_combines_multiple_slates(tmp_path, monkeypatch):
    import src.fixture_intel as fi
    monkeypatch.setattr(fi, "FIXTURE_DATA_DIR", tmp_path)

    _write_slate(tmp_path, "2026-01-01.json", [_fixture_dict("m1", "Home", "Home")])
    _write_slate(tmp_path, "2026-01-08.json", [_fixture_dict("m2", "Away", "Away")])

    fixtures = fi.load_all_fixtures()
    assert len(fixtures) == 2
    assert {f.match_id for f in fixtures} == {"m1", "m2"}


def test_score_predictions_computes_hit_rate_and_baseline(tmp_path):
    data = [
        _fixture_dict("m1", "Home", "Home"),   # correct
        _fixture_dict("m2", "Away", "Draw"),   # wrong
        _fixture_dict("m3", "Draw", "Draw"),   # correct
    ]
    path = _write_slate(tmp_path, "slate.json", data)
    fixtures = load_fixtures(path)

    scores = score_predictions(fixtures)
    claude_row = scores[scores["Predictor"] == "Claude (this app)"].iloc[0]
    baseline_row = scores[scores["Predictor"] == "Baseline: always Home"].iloc[0]

    assert claude_row["Correct"] == 2
    assert claude_row["Total"] == 3
    assert baseline_row["Correct"] == 1  # only m1's actual_result is Home
    assert baseline_row["Total"] == 3


def test_score_predictions_includes_external_predictions(tmp_path):
    data = [_fixture_dict("m1", "Home", "Home", external_predictions={"Sofascore": "Away"})]
    path = _write_slate(tmp_path, "slate.json", data)
    fixtures = load_fixtures(path)

    scores = score_predictions(fixtures)
    sofascore_row = scores[scores["Predictor"] == "Sofascore"].iloc[0]
    assert sofascore_row["Correct"] == 0
    assert sofascore_row["Total"] == 1


def test_score_predictions_skips_unplayed_fixtures(tmp_path):
    data = [_fixture_dict("m1", "Home", None)]  # not yet played
    path = _write_slate(tmp_path, "slate.json", data)
    fixtures = load_fixtures(path)

    scores = score_predictions(fixtures)
    assert scores.empty


def test_match_results_table_only_includes_completed(tmp_path):
    data = [
        _fixture_dict("m1", "Home", "Home"),
        _fixture_dict("m2", "Away", None),
    ]
    path = _write_slate(tmp_path, "slate.json", data)
    fixtures = load_fixtures(path)

    table = match_results_table(fixtures)
    assert len(table) == 1
    assert table.iloc[0]["Match"] == "Home FC vs Away FC"
