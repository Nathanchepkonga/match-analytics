"""What makes a draw more likely than the bookmakers' price says?

For every league match in data/football_data (main leagues, 2019-2027) this builds pre-match team
numbers from that team's earlier games in the same season only: goals scored and conceded per
game, bookings (yellow + red cards) per game in their matches, shots on target, and how often
they drew. Each factor is then tested against the margin-removed draw price (and the chance of
under 2.5 goals) with a logistic model that uses the price as its starting point, fitted on
2019-2023 and scored on 2023-2027. A factor only matters if it adds something the price misses.

Run: python -m src.draw_factors
"""
import glob
import os
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

DATA_DIR = Path(__file__).parent.parent / "data" / "football_data"
MIN_GAMES = 5


def load_matches(directory: Path = DATA_DIR) -> pd.DataFrame:
    frames = []
    for p in glob.glob(str(directory / "*_*.csv")):
        name = os.path.basename(p)[:-4]
        if name.startswith("new_"):
            continue
        df = pd.read_csv(p, encoding="utf-8-sig", encoding_errors="replace", on_bad_lines="skip", low_memory=False)
        need = {"HomeTeam", "AwayTeam", "FTHG", "FTAG", "HY", "AY", "HR", "AR"}
        if not need <= set(df.columns):
            continue
        g = df.get
        div, season = name.split("_")
        frames.append(pd.DataFrame({
            "league": div, "season": season, "date": df["Date"], "home": df["HomeTeam"], "away": df["AwayTeam"],
            "hg": df["FTHG"], "ag": df["FTAG"], "hy": df["HY"], "ay": df["AY"], "hr": df["HR"], "ar": df["AR"],
            "hst": g("HST"), "ast": g("AST"),
            "oh": g("AvgCH", g("AvgH")), "od": g("AvgCD", g("AvgD")), "oa": g("AvgCA", g("AvgA")),
            "over": g("AvgC>2.5", g("Avg>2.5")), "under": g("AvgC<2.5", g("Avg<2.5"))}))
    d = pd.concat(frames, ignore_index=True)
    d["date"] = pd.to_datetime(d["date"], dayfirst=True, errors="coerce")
    num = ["hg", "ag", "hy", "ay", "hr", "ar", "hst", "ast", "oh", "od", "oa", "over", "under"]
    d[num] = d[num].apply(pd.to_numeric, errors="coerce")
    d = d.dropna(subset=["date", "hg", "ag", "oh", "od", "oa"]).sort_values("date", kind="stable").reset_index(drop=True)
    inv = 1 / d[["oh", "od", "oa"]].values
    p = inv / inv.sum(1, keepdims=True)
    d["pH"], d["pD"], d["pA"] = p.T
    d["pU"] = (1 / d["under"]) / (1 / d["under"] + 1 / d["over"])
    d["draw"] = (d["hg"] == d["ag"]).astype(int)
    d["cards"] = d["hy"] + d["ay"] + 2 * (d["hr"] + d["ar"])
    return d


def add_team_form(d: pd.DataFrame) -> pd.DataFrame:
    """Per team, per season: averages over that team's earlier games only (no peeking)."""
    long = pd.concat([
        pd.DataFrame({"i": d.index, "key": d["league"] + d["season"] + d["home"], "gf": d["hg"], "ga": d["ag"],
                      "cards_game": d["cards"], "sot_f": d["hst"], "sot_a": d["ast"], "dr": d["draw"]}),
        pd.DataFrame({"i": d.index, "key": d["league"] + d["season"] + d["away"], "gf": d["ag"], "ga": d["hg"],
                      "cards_game": d["cards"], "sot_f": d["ast"], "sot_a": d["hst"], "dr": d["draw"]}),
    ]).sort_values("i", kind="stable")
    grp = long.groupby("key")
    for c in ["gf", "ga", "cards_game", "sot_f", "sot_a", "dr"]:
        long[c + "_pre"] = grp[c].transform(lambda s: s.shift().expanding().mean())
    long["n_pre"] = grp.cumcount()
    # each match appears twice, home row first (stable sort), so split back by position
    h = long.groupby("i").nth(0).set_index("i")
    a = long.groupby("i").nth(1).set_index("i")
    for pre, src in (("h_", h), ("a_", a)):
        for c in ["gf_pre", "ga_pre", "cards_game_pre", "sot_f_pre", "sot_a_pre", "dr_pre", "n_pre"]:
            d[pre + c] = src[c]
    return d


def build_features(d: pd.DataFrame) -> pd.DataFrame:
    d = d[(d["h_n_pre"] >= MIN_GAMES) & (d["a_n_pre"] >= MIN_GAMES)].copy()
    d["goals_rate"] = (d["h_gf_pre"] + d["h_ga_pre"] + d["a_gf_pre"] + d["a_ga_pre"]) / 2   # goals in their games
    d["weak_attack"] = d[["h_gf_pre", "a_gf_pre"]].min(axis=1)                            # the poorer scorer
    d["attack_gap"] = (d["h_gf_pre"] - d["h_ga_pre"]) - (d["a_gf_pre"] - d["a_ga_pre"])   # goal-difference gap
    d["cards_rate"] = (d["h_cards_game_pre"] + d["a_cards_game_pre"]) / 2                 # bookings in their games
    d["sot_rate"] = (d["h_sot_f_pre"] + d["a_sot_f_pre"]).where(d["h_sot_f_pre"].notna())
    d["team_draw_rate"] = (d["h_dr_pre"] + d["a_dr_pre"]) / 2
    d["closeness"] = (d["pH"] - d["pA"]).abs()
    d["fav_p"] = d[["pH", "pD", "pA"]].max(axis=1)
    d["train"] = d["date"] < "2023-07-01"
    return d


FACTORS = ["goals_rate", "weak_attack", "cards_rate", "sot_rate", "team_draw_rate", "closeness", "pU"]


def _fit(df, cols):
    X = sm.add_constant(df[cols]) if cols else np.ones((len(df), 1))
    off = np.log(df["pD"] / (1 - df["pD"]))
    return sm.GLM(df["draw"], X, family=sm.families.Binomial(), offset=off).fit()


def test_factors(d: pd.DataFrame, balanced_only: bool = True) -> pd.DataFrame:
    """One factor at a time, on top of the draw price (and pU when given). Held-out log-loss gain."""
    s = d[d["fav_p"] <= 0.47] if balanced_only else d
    rows = []
    for f in FACTORS:
        cols = [f] if f == "pU" else [f, "pU"]
        t = s.dropna(subset=cols + ["pD"])
        tr, te = t[t["train"]], t[~t["train"]]
        if len(tr) < 1000 or len(te) < 500:
            continue
        base_cols = [] if f == "pU" else ["pU"]
        z = lambda df, c: (df[c] - tr[c].mean()) / tr[c].std()
        trz, tez = tr.copy(), te.copy()
        for c in set(cols):
            trz[c], tez[c] = z(tr, c), z(te, c)
        m0, m1 = _fit(trz, base_cols), _fit(trz, cols)
        def ll(m, df, c):
            X = sm.add_constant(df[c], has_constant="add") if c else np.ones((len(df), 1))
            p = m.predict(X, offset=np.log(df["pD"] / (1 - df["pD"])))
            return -np.mean(df["draw"] * np.log(p) + (1 - df["draw"]) * np.log(1 - p))
        gain = ll(m0, tez, base_cols) - ll(m1, tez, cols)
        # paired bootstrap over held-out matches for the gain
        rng = np.random.default_rng(0)
        X0 = sm.add_constant(tez[base_cols], has_constant="add") if base_cols else np.ones((len(tez), 1))
        X1 = sm.add_constant(tez[cols], has_constant="add")
        off = np.log(tez["pD"] / (1 - tez["pD"]))
        p0, p1 = m0.predict(X0, offset=off), m1.predict(X1, offset=off)
        y = tez["draw"].values
        l0 = -(y * np.log(p0) + (1 - y) * np.log(1 - p0)); l1 = -(y * np.log(p1) + (1 - y) * np.log(1 - p1))
        diff = (l0 - l1).values
        boots = [diff[rng.integers(0, len(diff), len(diff))].mean() for _ in range(500)]
        q = pd.qcut(te[f], 5, duplicates="drop")
        bins = te.groupby(q, observed=True).apply(lambda x: 100 * (x["draw"].mean() - x["pD"].mean()))
        rows.append({"factor": f, "train_n": len(tr), "test_n": len(te), "coef_per_sd": m1.params[f],
                     "train_p": m1.pvalues[f], "test_gain_x1000": 1000 * gain, "p_no_gain": float(np.mean(np.array(boots) <= 0)),
                     "draw_minus_price_by_quintile_pts": " ".join(f"{v:+.1f}" for v in bins.values)})
    return pd.DataFrame(rows)


def raw_tables(d: pd.DataFrame) -> dict:
    """Plain draw rates by factor fifths in balanced games (no model), with the price alongside."""
    s = d[d["fav_p"] <= 0.47]
    out = {}
    for f in ["goals_rate", "weak_attack", "cards_rate", "team_draw_rate", "pU"]:
        t = s.dropna(subset=[f])
        q = pd.qcut(t[f], 5, duplicates="drop")
        out[f] = t.groupby(q, observed=True).agg(n=("draw", "size"), draws=("draw", "mean"), price=("pD", "mean")).round(3)
    return out


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    d = build_features(add_team_form(load_matches()))
    print(f"{len(d)} matches with >= {MIN_GAMES} earlier games per team; balanced (fav <= 47%): {(d['fav_p'] <= 0.47).sum()}")
    print(test_factors(d).round(4).to_string(index=False))
    for k, v in raw_tables(d).items():
        print(f"\n{k}\n{v.to_string()}")
