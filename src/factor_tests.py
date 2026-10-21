"""Which of the user's 200 factors (data/factors/factors_200.csv) predict results beyond the odds?

Tests every factor that football-data.co.uk lets us measure before kickoff, for every main-league
match 2019-2027 where both teams had played 5+ games that season. Team numbers use only that team's
earlier games (no peeking). For home wins and away wins separately, a logistic model starts from
the margin-removed closing price (as an offset) and adds one standardised factor; it is fitted on
games before July 2023 and scored on later games. "Held-out gain" is the drop in log loss on those
later games; z is that gain divided by its standard error. With about 30 tests, only |z| > 3.1
survives a Bonferroni correction.

Run: python -m src.factor_tests
"""
import glob
import os
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

DATA_DIR = Path(__file__).parent.parent / "data" / "football_data"
OUT = Path(__file__).parent.parent / "data" / "factors" / "factor_tests.csv"
SPLIT = "2023-07-01"

# factor column -> (PDF id, name in the user's list)
FACTORS = {
    "shots_dom": ("4/27", "Total shots for minus against"),
    "sot_dom": ("5/28", "Shots on target for minus against"),
    "goals_for": ("8", "Goals scored per game"),
    "clean_sheets": ("45", "Clean sheet rate"),
    "corners_dom": ("12", "Corner kicks won minus conceded"),
    "fouls": ("43", "Fouls conceded per game"),
    "cards": ("109", "Disciplinary record (cards per game)"),
    "rest": ("141", "Rest days before the match"),
    "congestion": ("142", "Games in the last 14 days"),
    "form5": ("161", "Morale: points per game, last 5"),
    "lost_last": ("167", "Bounce-back: lost the previous game"),
    "unbeaten": ("168", "Length of the unbeaten run"),
    "h2h_last": ("extra", "Head-to-head: last meeting (home view)"),
    "ref_cards": ("177", "Referee strictness (cards per game)"),
    "ref_home": ("178", "Referee home-win tendency"),
}


def load() -> pd.DataFrame:
    frames = []
    for p in glob.glob(str(DATA_DIR / "*_*.csv")):
        name = os.path.basename(p)[:-4]
        if name.startswith("new_"):
            continue
        df = pd.read_csv(p, encoding="utf-8-sig", encoding_errors="replace", on_bad_lines="skip", low_memory=False)
        if not {"HomeTeam", "AwayTeam", "FTHG", "FTAG", "HS", "AS", "HST", "AST"} <= set(df.columns):
            continue
        g = df.get
        div, season = name.split("_")
        frames.append(pd.DataFrame({
            "league": div, "season": season, "date": df["Date"], "home": df["HomeTeam"], "away": df["AwayTeam"],
            "hg": df["FTHG"], "ag": df["FTAG"], "hs": df["HS"], "as_": df["AS"], "hst": df["HST"], "ast": df["AST"],
            "hc": g("HC"), "ac": g("AC"), "hf": g("HF"), "af": g("AF"), "hy": g("HY"), "ay": g("AY"),
            "hr": g("HR"), "ar": g("AR"), "ref": g("Referee"),
            "oh": g("AvgCH", g("AvgH")), "od": g("AvgCD", g("AvgD")), "oa": g("AvgCA", g("AvgA"))}))
    d = pd.concat(frames, ignore_index=True)
    d["date"] = pd.to_datetime(d["date"], dayfirst=True, errors="coerce")
    num = ["hg", "ag", "hs", "as_", "hst", "ast", "hc", "ac", "hf", "af", "hy", "ay", "hr", "ar", "oh", "od", "oa"]
    d[num] = d[num].apply(pd.to_numeric, errors="coerce")
    d = d.dropna(subset=["date", "hg", "ag", "oh", "od", "oa"]).sort_values("date", kind="stable").reset_index(drop=True)
    inv = 1 / d[["oh", "od", "oa"]].values
    p = inv / inv.sum(1, keepdims=True)
    d["pH"], d["pD"], d["pA"] = p.T
    d["res"] = np.where(d["hg"] > d["ag"], "H", np.where(d["hg"] == d["ag"], "D", "A"))
    return d


def team_features(d: pd.DataFrame) -> pd.DataFrame:
    """Pre-match numbers for the home ('h_') and away ('a_') side, earlier games only."""
    side = lambda home: pd.DataFrame({
        "i": d.index, "date": d["date"], "season_key": d["league"] + d["season"] + (d["home"] if home else d["away"]),
        "team": d["home"] if home else d["away"],
        "gf": d["hg"] if home else d["ag"], "ga": d["ag"] if home else d["hg"],
        "sf": d["hs"] if home else d["as_"], "sa": d["as_"] if home else d["hs"],
        "stf": d["hst"] if home else d["ast"], "sta": d["ast"] if home else d["hst"],
        "cf": d["hc"] if home else d["ac"], "ca": d["ac"] if home else d["hc"],
        "fl": d["hf"] if home else d["af"],
        "cd": (d["hy"] + 2 * d["hr"]) if home else (d["ay"] + 2 * d["ar"]),
        "is_home": home})
    long = pd.concat([side(True), side(False)]).sort_values(["date", "i"], kind="stable").reset_index(drop=True)
    long["pts"] = np.where(long["gf"] > long["ga"], 3, np.where(long["gf"] == long["ga"], 1, 0))
    long["cs"] = (long["ga"] == 0).astype(float)
    long["lost"] = (long["gf"] < long["ga"]).astype(float)
    s = long.groupby("season_key")
    prior = lambda col: s[col].transform(lambda x: x.shift().expanding().mean())
    long["n_pre"] = s.cumcount()
    long["goals_for"] = prior("gf")
    long["clean_sheets"] = prior("cs")
    long["shots_dom"] = prior("sf") - prior("sa")
    long["sot_dom"] = prior("stf") - prior("sta")
    long["corners_dom"] = prior("cf") - prior("ca")
    long["fouls"] = prior("fl")
    long["cards"] = prior("cd")
    long["form5"] = s["pts"].transform(lambda x: x.shift().rolling(5, min_periods=3).mean())
    long["lost_last"] = s["lost"].transform(lambda x: x.shift())
    # unbeaten run length before this game
    def run(x):
        out, c = [], 0
        for v in x:
            out.append(c)
            c = 0 if v == 1.0 else c + 1
        return pd.Series(out, index=x.index)
    long["unbeaten"] = s["lost"].transform(run).clip(upper=15)
    # rest and congestion across all league games of the team (cup games are not in the data)
    t = long.groupby("team")
    long["rest"] = (long["date"] - t["date"].shift()).dt.days.clip(upper=21)
    long["congestion"] = t["date"].transform(
        lambda x: pd.Series([((x.iloc[:k] >= x.iloc[k] - pd.Timedelta(days=14))).sum() for k in range(len(x))], index=x.index))
    cols = ["n_pre", "goals_for", "clean_sheets", "shots_dom", "sot_dom", "corners_dom", "fouls", "cards",
            "form5", "lost_last", "unbeaten", "rest", "congestion"]
    h = long[long["is_home"]].set_index("i")[cols].add_prefix("h_")
    a = long[~long["is_home"]].set_index("i")[cols].add_prefix("a_")
    return d.join(h).join(a)


def h2h_and_referee(d: pd.DataFrame) -> pd.DataFrame:
    """Last meeting (home team's view: +1 won, 0 drew, -1 lost; any venue, earlier seasons included) and
    the referee's earlier cards-per-game and home-win rate (shrunk towards the league)."""
    last = {}
    h2h = []
    for r in d[["home", "away", "hg", "ag"]].itertuples():
        key = tuple(sorted((r.home, r.away)))
        prev = last.get(key)
        if prev is None:
            h2h.append(np.nan)
        else:
            winner, = (prev,)
            h2h.append(1.0 if winner == r.home else (0.0 if winner == "draw" else -1.0))
        last[key] = r.home if r.hg > r.ag else (r.away if r.ag > r.hg else "draw")
    d["h2h_last"] = h2h
    cards_total = d["hy"] + d["ay"] + 2 * (d["hr"] + d["ar"])
    g = d.assign(_c=cards_total, _h=(d["res"] == "H").astype(float)).groupby("ref")
    n_prev = g.cumcount()
    k = 20.0
    league_c = cards_total.groupby(d["league"]).transform("mean")
    league_h = (d["res"] == "H").astype(float).groupby(d["league"]).transform("mean")
    prev_c = g["_c"].transform(lambda x: x.shift().expanding().sum()).fillna(0)
    prev_h = g["_h"].transform(lambda x: x.shift().expanding().sum()).fillna(0)
    d["ref_cards"] = np.where(d["ref"].notna(), (prev_c + k * league_c) / (n_prev + k), np.nan)
    d["ref_home"] = np.where(d["ref"].notna(), (prev_h + k * league_h) / (n_prev + k) - league_h, np.nan)
    return d


def build() -> pd.DataFrame:
    d = h2h_and_referee(team_features(load()))
    d = d[(d["h_n_pre"] >= 5) & (d["a_n_pre"] >= 5)].copy()
    for f in ["goals_for", "clean_sheets", "shots_dom", "sot_dom", "corners_dom", "fouls", "cards", "form5",
              "lost_last", "unbeaten", "rest", "congestion"]:
        d[f] = d["h_" + f] - d["a_" + f]          # home minus away
    d["fav_p"] = d[["pH", "pD", "pA"]].max(axis=1)
    d["train"] = d["date"] < SPLIT
    return d


def test(d: pd.DataFrame, balanced_only: bool = False) -> pd.DataFrame:
    s = d[d["fav_p"] <= 0.47] if balanced_only else d
    rows = []
    for outcome, pcol in (("home win", "pH"), ("away win", "pA")):
        y_all = (s["res"] == ("H" if outcome == "home win" else "A")).astype(float)
        for f, (pid, name) in FACTORS.items():
            t = s[[f, pcol, "train"]].assign(y=y_all).dropna()
            tr, te = t[t["train"]], t[~t["train"]]
            if len(tr) < 2000 or len(te) < 1000:
                continue
            mu, sd = tr[f].mean(), tr[f].std()
            if not sd > 0:
                continue
            off = lambda df: np.log(df[pcol] / (1 - df[pcol]))
            X = lambda df: sm.add_constant(((df[f] - mu) / sd).rename("x"), has_constant="add")
            m1 = sm.GLM(tr["y"], X(tr), family=sm.families.Binomial(), offset=off(tr)).fit()
            m0 = sm.GLM(tr["y"], np.ones((len(tr), 1)), family=sm.families.Binomial(), offset=off(tr)).fit()
            p1 = m1.predict(X(te), offset=off(te))
            p0 = m0.predict(np.ones((len(te), 1)), offset=off(te))
            y = te["y"].values
            l0 = -(y * np.log(p0) + (1 - y) * np.log(1 - p0))
            l1 = -(y * np.log(p1) + (1 - y) * np.log(1 - p1))
            diff = np.asarray(l0 - l1)
            rows.append({"outcome": outcome, "pdf_id": pid, "factor": name, "train_n": len(tr), "test_n": len(te),
                         "coef_per_sd": m1.params["x"], "train_p": m1.pvalues["x"],
                         "heldout_gain_x1000": 1000 * diff.mean(), "z": diff.mean() / (diff.std(ddof=1) / np.sqrt(len(diff)))})
    out = pd.DataFrame(rows)
    out["verdict"] = np.where(out["z"] > 3.1, "beats the odds (survives correction)",
                     np.where(out["z"] > 2.0, "hint (not after correction)", "no edge over the odds"))
    return out


def home_advantage(d: pd.DataFrame) -> dict:
    """Factor 156: is home advantage priced? Actual v implied home-win rate, recent seasons."""
    t = d[~d["train"]]
    return {"games": len(t), "home_win_actual": (t["res"] == "H").mean(), "home_win_implied": t["pH"].mean()}


if __name__ == "__main__":
    pd.set_option("display.width", 230)
    d = build()
    print(f"{len(d)} matches (both teams 5+ games); train {d['train'].sum()}, test {(~d['train']).sum()}")
    allg = test(d)
    bal = test(d, balanced_only=True).add_prefix("bal_")
    print(allg.round(4).to_string(index=False))
    print("\nBalanced games only (favourite <= 47%):")
    print(bal[["bal_outcome", "bal_factor", "bal_coef_per_sd", "bal_heldout_gain_x1000", "bal_z", "bal_verdict"]].round(4).to_string(index=False))
    print("\nHome advantage (156):", {k: round(v, 4) for k, v in home_advantage(d).items()})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.concat([allg.assign(sample="all"), test(d, True).assign(sample="balanced")]).to_csv(OUT, index=False)
