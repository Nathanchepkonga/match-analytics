"""
Independent team-strength model built from results only (no odds as inputs). Elo ratings run
through every league match in data/football_data/ in date order, with home advantage, a
goal-margin multiplier, a pull back towards the league average after the summer break, and new
teams entering at the league's 25th percentile. An ordinal logistic model, with its own
home/draw cut-points per league and one shared slope, turns the rating gap into H/D/A chances.
It is fitted on 2020-2024 and tested on 2025-26 and 2026-27 against the bookmakers' margin-removed
odds. Run with `python -m src.team_ratings` from the repo root.
"""

import glob
import os
from collections import defaultdict
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "football_data")
HOME_ADV = 55.0
K = 20.0


def load_results(directory: str = DATA_DIR) -> pd.DataFrame:
    frames = []
    for p in glob.glob(os.path.join(directory, "*.csv")):
        name = os.path.basename(p)[:-4]
        df = pd.read_csv(p, encoding="utf-8-sig", encoding_errors="replace", on_bad_lines="skip", low_memory=False)
        if name.startswith("new_"):
            if not {"Home", "Away", "HG", "AG"} <= set(df.columns):
                continue
            df = df[pd.to_numeric(df["Season"].astype(str).str[:4], errors="coerce") >= 2018]
            odds = [df.get(c) for c in ("AvgCH", "AvgCD", "AvgCA")]
            frames.append(pd.DataFrame({"league": df["Country"].astype(str) + " " + df["League"].astype(str),
                                        "date": df["Date"], "home": df["Home"], "away": df["Away"],
                                        "hg": df["HG"], "ag": df["AG"], "oh": odds[0], "od": odds[1], "oa": odds[2]}))
        elif {"HomeTeam", "AwayTeam", "FTHG", "FTAG"} <= set(df.columns):
            frames.append(pd.DataFrame({"league": name.split("_")[0], "date": df["Date"], "home": df["HomeTeam"],
                                        "away": df["AwayTeam"], "hg": df["FTHG"], "ag": df["FTAG"],
                                        "oh": df.get("AvgH"), "od": df.get("AvgD"), "oa": df.get("AvgA")}))
    d = pd.concat(frames, ignore_index=True)
    d["date"] = pd.to_datetime(d["date"], dayfirst=True, errors="coerce")
    for c in ("hg", "ag", "oh", "od", "oa"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=["date", "home", "away", "hg", "ag"]).sort_values("date", kind="stable").reset_index(drop=True)
    d["res"] = np.where(d["hg"] > d["ag"], 0, np.where(d["hg"] == d["ag"], 1, 2))
    return d


def run_elo(d: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, float], Dict[str, str]]:
    """Ratings before every match (columns rh, ra), plus final ratings and each team's latest league."""
    rating: Dict[str, float] = {}
    last_seen: Dict[str, pd.Timestamp] = {}
    league_of: Dict[str, str] = {}
    members = defaultdict(dict)  # league -> team -> last date
    rh, ra = np.empty(len(d)), np.empty(len(d))
    for i, (lg, dt, h, a, hg, ag) in enumerate(zip(d["league"], d["date"], d["home"], d["away"], d["hg"], d["ag"])):
        cur = [rating[t] for t, seen in members[lg].items() if (dt - seen).days < 400 and t in rating]
        lg_mean = np.mean(cur) if cur else 1500.0
        for t in (h, a):
            if t not in rating:
                rating[t] = np.percentile(cur, 25) if len(cur) >= 6 else 1500.0
            elif (dt - last_seen[t]).days > 60:  # new season: pull 20% back to the league average
                rating[t] = 0.8 * rating[t] + 0.2 * lg_mean
            last_seen[t] = dt
            league_of[t] = lg
            members[lg][t] = dt
        rh[i], ra[i] = rating[h], rating[a]
        exp_home = 1 / (1 + 10 ** (-(rating[h] + HOME_ADV - rating[a]) / 400))
        score = 1.0 if hg > ag else 0.5 if hg == ag else 0.0
        gd = abs(hg - ag)
        mult = 1.0 if gd <= 1 else 1.5 if gd == 2 else (11 + gd) / 8
        delta = K * mult * (score - exp_home)
        rating[h] += delta
        rating[a] -= delta
    return d.assign(rh=rh, ra=ra), rating, league_of


def _ordinal_probs(z, c1, c2, b):
    """P(away), P(draw), P(home) from the rating gap z via two cut-points (c1 < c2)."""
    pa = 1 / (1 + np.exp(-(c1 - b * z)))
    pad = 1 / (1 + np.exp(-(c2 - b * z)))
    return np.column_stack([1 - pad, pad - pa, pa])  # H, D, A


def fit_model(d: pd.DataFrame, min_games: int = 400) -> Dict:
    """Shared slope, per-league cut-points (leagues with fewer games use the pooled ones)."""
    z = (d["rh"] - d["ra"]).values / 100
    res = d["res"].values
    leagues = d["league"].values
    big = [lg for lg, n in pd.Series(leagues).value_counts().items() if n >= min_games]
    idx = {lg: i for i, lg in enumerate(big)}
    li = np.array([idx.get(lg, len(big)) for lg in leagues])
    n_l = len(big) + 1

    def nll(theta):
        b = theta[0]
        c1 = theta[1:1 + n_l][li]
        c2 = c1 + np.exp(theta[1 + n_l:][li])
        p = _ordinal_probs(z, c1, c2, b)
        return -np.log(np.clip(p[np.arange(len(res)), res], 1e-9, 1)).sum()

    theta0 = np.concatenate([[0.3], np.full(n_l, -0.6), np.full(n_l, np.log(1.1))])
    sol = minimize(nll, theta0, method="L-BFGS-B")
    b = sol.x[0]
    c1 = dict(zip(big + ["_other"], sol.x[1:1 + n_l]))
    gap = dict(zip(big + ["_other"], np.exp(sol.x[1 + n_l:])))
    return {"b": b, "c1": c1, "gap": gap}


def predict(model: Dict, league: str, z_points: float) -> np.ndarray:
    """H/D/A chances for a rating gap of `z_points` Elo (home minus away, before home advantage)."""
    key = league if league in model["c1"] else "_other"
    c1 = model["c1"][key]
    return _ordinal_probs(np.array([z_points / 100]), c1, c1 + model["gap"][key], model["b"])[0]


def evaluate(d: pd.DataFrame, model: Dict, mask) -> Dict:
    t = d[mask].dropna(subset=["oh", "od", "oa"])
    t = t[(t[["oh", "od", "oa"]] > 1.01).all(axis=1)]
    pm = np.array([predict(model, lg, z) for lg, z in zip(t["league"], t["rh"] - t["ra"])])
    inv = 1 / t[["oh", "od", "oa"]].values
    pb = inv / inv.sum(axis=1, keepdims=True)
    r = t["res"].values
    out = {"n": len(t)}
    for name, p in (("model", pm), ("bookmakers", pb)):
        out[f"{name}_logloss"] = float(-np.log(p[np.arange(len(r)), r]).mean())
        out[f"{name}_accuracy"] = float((p.argmax(axis=1) == r).mean())
    bal = pb.max(axis=1) <= 0.45
    out["balanced_n"] = int(bal.sum())
    out["model_acc_balanced"] = float((pm[bal].argmax(axis=1) == r[bal]).mean())
    out["book_acc_balanced"] = float((pb[bal].argmax(axis=1) == r[bal]).mean())
    out["agree_on_favourite"] = float((pm.argmax(axis=1) == pb.argmax(axis=1)).mean())
    return out


if __name__ == "__main__":
    d, rating, league_of = run_elo(load_results())
    year = d["date"].dt.year + (d["date"].dt.month >= 7)  # season label by its end year
    train = (year >= 2021) & (year <= 2025)
    model = fit_model(d[train])
    for label, mask in (("2025-26 (held out)", year == 2026), ("2026-27 so far (held out)", year == 2027)):
        e = evaluate(d, model, mask)
        print(f"{label}: {e['n']} matches | log loss model {e['model_logloss']:.4f} v bookmakers {e['bookmakers_logloss']:.4f} | "
              f"accuracy {e['model_accuracy']:.3f} v {e['bookmakers_accuracy']:.3f} | balanced games ({e['balanced_n']}): "
              f"{e['model_acc_balanced']:.3f} v {e['book_acc_balanced']:.3f} | same favourite {e['agree_on_favourite']:.2f}")
