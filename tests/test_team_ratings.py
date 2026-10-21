"""Tests for src/team_ratings.py: the probability model behaves sensibly."""
import numpy as np

from src.team_ratings import _ordinal_probs


def test_probabilities_sum_to_one_and_follow_the_rating_gap():
    z = np.array([-2.0, 0.0, 2.0])
    p = _ordinal_probs(z, -0.6, 0.5, 0.3)
    assert np.allclose(p.sum(axis=1), 1)
    assert p[0, 0] < p[1, 0] < p[2, 0]   # home chance rises with the home side's rating
    assert p[0, 2] > p[1, 2] > p[2, 2]   # away chance falls
