import numpy as np

from src.crowd_model import crowd_shares, poisson_binomial, popularity


def test_crowd_shares_normalise_and_tilt():
    p = np.array([[0.45, 0.27, 0.28]])
    q = crowd_shares(p, 1.0, 0.0)
    assert np.allclose(q, p)
    q2 = crowd_shares(p, 2.0, -0.2)
    assert np.isclose(q2.sum(), 1) and q2[0, 0] > p[0, 0] and q2[0, 1] < p[0, 1]


def test_poisson_binomial_matches_binomial():
    from math import comb
    d = poisson_binomial([0.3] * 5)
    assert np.allclose(d, [comb(5, k) * 0.3 ** k * 0.7 ** (5 - k) for k in range(6)])


def test_popularity_is_product_of_shares():
    p = np.array([[0.5, 0.25, 0.25], [0.4, 0.3, 0.3]])
    assert np.isclose(popularity(p, [0, 1], 1.0, 0.0), 0.5 * 0.3)
