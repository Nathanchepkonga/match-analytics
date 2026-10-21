"""How does the SportPesa crowd pick? Fitted from the Mega Jackpot Pro archive's winner counts.

Model: each crowd line picks game i's outcome o with share q_i(o) ∝ p_i(o)^alpha · exp(delta·[o = draw]),
where p is the margin-removed closing price. alpha > 1 means the crowd piles onto favourites more
than the odds justify; delta < 0 means it avoids draws. With N lines per card, the expected number
of lines with exactly k correct is N · PoissonBinomial(k; q_i(actual result)). alpha, delta and N
are fitted by Poisson likelihood to the archive's 12/17-16/17 winner counts on fully priced cards.

Use: popularity(probs, picks, alpha, delta) = the share of crowd lines identical to a slip, so a
winning slip expects about N_card · popularity co-winners.

Run: python -m src.crowd_model
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src.sportpesa_archive import load_archive

TIERS = [12, 13, 14, 15, 16]


def crowd_shares(probs, alpha: float, delta: float) -> np.ndarray:
    p = np.asarray(probs, float)
    w = p ** alpha * np.exp(delta * np.array([0.0, 1.0, 0.0]))
    return w / w.sum(axis=1, keepdims=True)


def poisson_binomial(q) -> np.ndarray:
    dist = np.zeros(len(q) + 1)
    dist[0] = 1.0
    for x in q:
        dist[1:] = dist[1:] * (1 - x) + dist[:-1] * x
        dist[0] *= (1 - x)
    return dist


def popularity(probs, picks, alpha: float, delta: float) -> float:
    q = crowd_shares(probs, alpha, delta)
    return float(np.prod(q[np.arange(len(picks)), picks]))


def full_cards():
    from src.archive_study import load
    g = load()
    _, cards = load_archive()
    full = g.groupby("card").filter(lambda d: d["has_odds"].all() and len(d) == 17)
    out = []
    c = cards.set_index("card")
    for card, d in full.groupby("card"):
        d = d.sort_values("n")
        probs = d[["pH", "pD", "pA"]].values
        res = d["result"].map({"H": 0, "D": 1, "A": 2}).values
        winners = np.array([c.loc[card, f"winners_{k}"] for k in TIERS], float)
        out.append((card, probs, res, winners, float(c.loc[card, "pool_17"])))
    return out


def fit(cards, per_card_n: bool = False):
    """Fit alpha, delta and log N (one N for all cards) by Poisson likelihood."""
    def nll(theta):
        a, dl, logn = theta
        tot = 0.0
        for _, probs, res, w, _ in cards:
            q = crowd_shares(probs, a, dl)[np.arange(17), res]
            pk = poisson_binomial(q)[TIERS]
            lam = np.exp(logn) * pk + 1e-12
            tot -= np.sum(w * np.log(lam) - lam)
        return tot
    r = minimize(nll, x0=[1.5, 0.0, np.log(2e6)], method="Nelder-Mead", options={"maxiter": 4000, "xatol": 1e-4, "fatol": 1e-4})
    return {"alpha": r.x[0], "delta": r.x[1], "N": float(np.exp(r.x[2])), "nll": r.fun}


def fit_fixed(cards, alpha, delta):
    """Best N (closed form) and fit for given alpha, delta - for comparing crowd hypotheses."""
    pks, ws = [], []
    for _, probs, res, w, _ in cards:
        q = crowd_shares(probs, alpha, delta)[np.arange(17), res]
        pks.append(poisson_binomial(q)[TIERS]); ws.append(w)
    pks, ws = np.array(pks), np.array(ws)
    n = ws.sum() / pks.sum()
    lam = n * pks + 1e-12
    return {"alpha": alpha, "delta": delta, "N": n, "nll": float(-(ws * np.log(lam) - lam).sum())}


if __name__ == "__main__":
    cards = full_cards()
    print(f"{len(cards)} fully priced cards")
    best = fit(cards)
    print("fitted:", {k: round(v, 3) if k != "N" else round(v) for k, v in best.items()})
    for a, dl in [(0.0, 0.0), (1.0, 0.0), (best["alpha"], 0.0), (1.0, best["delta"])]:
        f = fit_fixed(cards, a, dl)
        print(f"alpha {a:.2f} delta {dl:+.2f}: N {f['N']:,.0f}  nll {f['nll']:.1f}")
    # predicted v observed winners per tier
    a, dl, n = best["alpha"], best["delta"], best["N"]
    rows = []
    for card, probs, res, w, pool in cards:
        q = crowd_shares(probs, a, dl)[np.arange(17), res]
        rows.append([card, *w, *(n * poisson_binomial(q)[TIERS])])
    t = pd.DataFrame(rows, columns=["card"] + [f"obs{k}" for k in TIERS] + [f"pred{k}" for k in TIERS])
    print(t[[c for c in t.columns if c != "card"]].median().round(1).to_string())
    print("spearman obs v pred 12/17:", round(t[["obs12", "pred12"]].corr("spearman").iloc[0, 1], 3))
