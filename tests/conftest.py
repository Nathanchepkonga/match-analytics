"""Shared fixtures for the test suite."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import pytest

from src.schema import FixtureIntel, FixtureAnalysis, FixtureForm


def make_fixture(
    match_id="test_home_away",
    home_team="Home FC",
    away_team="Away FC",
    outcome_estimate=(0.4, 0.3, 0.3),
    outcome_pick="Home",
    actual_result=None,
    confidence="medium",
):
    return FixtureIntel(
        match_id=match_id,
        kickoff_date="2026-01-01",
        kickoff_time="15:00",
        country="Testland",
        competition="Test League",
        home_team=home_team,
        away_team=away_team,
        home_form=FixtureForm(),
        away_form=FixtureForm(),
        confidence=confidence,
        analysis=FixtureAnalysis(
            tactical_read="test",
            prediction_lean="test",
            outcome_estimate=list(outcome_estimate),
            outcome_pick=outcome_pick,
        ),
        actual_result=actual_result,
    )


@pytest.fixture
def make_fixture_factory():
    return make_fixture
