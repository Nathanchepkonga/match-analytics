"""What 199 real SportPesa Mega Jackpot Pro cards (Dec 2022 - Oct 2026, 3,383 games) say.

Uses data/sportpesa_archive/mega_games.csv from src.sportpesa_archive (results for every game,
closing average odds for the ~73% of games in leagues football-data.co.uk covers).

Run: python -m src.archive_study
"""
import json
import math

import numpy as np
import pandas as pd

from src.sportpesa_archive import OUT_CSV, load_archive, load_odds, _devig
from src.slip_optimizer import TILT_JSON, optimise

RES = list("HDA")


def _z(actual, expected, var):
    z = (actual - expected) / math.sqrt(var) if var > 0 else 0.0
    p = math.erfc(abs(z) / math.sqrt(2))
    return z, p


def load() -> pd.DataFrame:
    g = pd.read_csv(OUT_CSV)
    g["kickoff_eat"] = pd.to_datetime(g["kickoff_eat"], utc=True).dt.tz_convert("Africa/Nairobi")
    g["year"] = g["kickoff_eat"].dt.year
    g["played"] = ~g["postponed"]
    g["goals"] = g["hg"] + g["ag"]
    for r in RES:
        g[f"is{r}"] = (g["result"] == r).astype(float)
    pr = g[["pH", "pD", "pA"]].values
    g["p_res"] = np.where(g["has_odds"], pr[np.arange(len(g)), g["result"].map({"H": 0, "D": 1, "A": 2}).values], np.nan)
    g["fav_won"] = np.where(g["has_odds"], (g["fav"] == g["result"]).astype(float), np.nan)
    g["rank"] = np.where(~g["has_odds"], np.nan,
                         np.where(g["fav"] == g["result"], 1, np.where(g["second"] == g["result"], 2, 3)))
    return g


def results_overview(g: pd.DataFrame) -> dict:
    p = g[g["played"]]
    per_card = g.groupby("card")["isD"].sum()
    return {
        "games": len(g), "cards": g["card"].nunique(), "postponed": int(g["postponed"].sum()),
        "H": p["isH"].mean(), "D": p["isD"].mean(), "A": p["isA"].mean(),
        "by_year": p.groupby("year")[["isH", "isD", "isA"]].mean().round(3).to_dict("index"),
        "goals_per_game": p["goals"].mean(), "nil_nil": (p["goals"] == 0).mean(),
        "under_2_5": (p["goals"] <= 2).mean(),
        "draws_per_card": per_card.describe().round(2).to_dict(),
        "draws_per_card_counts": per_card.value_counts().sort_index().to_dict(),
        "top_scores": (p["hg"].astype(int).astype(str) + "-" + p["ag"].astype(int).astype(str)).value_counts().head(8).to_dict(),
    }


def position_test(g: pd.DataFrame) -> dict:
    """Does a game's slot on the card (1-17) relate to its result? Chi-square on 17x3."""
    p = g[g["played"]]
    tab = pd.crosstab(p["n"], p["result"])[RES]
    exp = np.outer(tab.sum(1), tab.sum(0)) / tab.values.sum()
    chi = ((tab.values - exp) ** 2 / exp).sum()
    dof = (tab.shape[0] - 1) * (tab.shape[1] - 1)
    return {"chi2": chi, "dof": dof, "p": _chi2_sf(chi, dof), "table": tab}


def _chi2_sf(x, k):
    """Upper tail of chi-square (Wilson-Hilferty approximation, fine for k >= 10)."""
    z = ((x / k) ** (1 / 3) - (1 - 2 / (9 * k))) / math.sqrt(2 / (9 * k))
    return 0.5 * math.erfc(z / math.sqrt(2))


def selection_profile(g: pd.DataFrame) -> dict:
    """How balanced the chosen games are, against every other match in the same leagues and
    the same kickoff windows (the pool SportPesa chose from)."""
    o = load_odds()
    ok = o[["ch", "cd", "ca"]].notna().all(axis=1) & (o[["ch", "cd", "ca"]] > 1.01).all(axis=1)
    o = o[ok].copy()
    o[["pH", "pD", "pA"]] = _devig(o["ch"], o["cd"], o["ca"])
    o["fav_p"] = o[["pH", "pD", "pA"]].max(axis=1)
    o["day"] = o["date"].dt.normalize()
    s = g[g["has_odds"]]
    leagues = set(s["league"])
    days = set(pd.to_datetime(s["kickoff_eat"]).dt.tz_localize(None).dt.normalize())
    pool = o[o["league"].isin(leagues) & o["day"].isin(days)]
    pool_keys = set(zip(pool["fd_home"], pool["fd_away"], pool["day"]))
    chosen_keys = set(zip(s["fd_home"], s["fd_away"], pd.to_datetime(s["kickoff_eat"]).dt.tz_localize(None).dt.normalize()))
    rest = pool[[k not in chosen_keys for k in zip(pool["fd_home"], pool["fd_away"], pool["day"])]]
    bins = [0, 0.40, 0.45, 0.50, 0.60, 1.0]
    lab = ["<=40%", "40-45%", "45-50%", "50-60%", ">60%"]
    out = {"chosen_n": len(s), "pool_n": len(rest), "pool_matched_keys": len(pool_keys),
           "chosen_fav_mean": s["fav_p"].mean(), "pool_fav_mean": rest["fav_p"].mean(),
           "chosen_bins": pd.cut(s["fav_p"], bins, labels=lab).value_counts(normalize=True).reindex(lab).round(3).to_dict(),
           "pool_bins": pd.cut(rest["fav_p"], bins, labels=lab).value_counts(normalize=True).reindex(lab).round(3).to_dict(),
           "chosen_home_fav": (s["fav"] == "H").mean(), "pool_home_fav": (rest["pH"] >= rest[["pD", "pA"]].max(axis=1)).mean(),
           "chosen_draw_p": s["pD"].mean(), "pool_draw_p": rest["pD"].mean(),
           "chosen_fav_max": s["fav_p"].max(), "chosen_fav_q": s["fav_p"].quantile([0.05, 0.5, 0.95]).round(3).to_dict()}
    return out


def calibration(g: pd.DataFrame) -> pd.DataFrame:
    """Actual v implied rates on the priced games, with a z-score per row."""
    s = g[g["has_odds"] & g["played"]].copy()
    rows = []

    def add(name, mask, outcome, prob):
        m = s[mask]
        act, exp = outcome[mask].sum(), prob[mask].sum()
        var = (prob[mask] * (1 - prob[mask])).sum()
        z, p = _z(act, exp, var)
        rows.append({"test": name, "n": int(mask.sum()), "actual": act / max(mask.sum(), 1),
                     "implied": exp / max(mask.sum(), 1), "diff_pts": 100 * (act - exp) / max(mask.sum(), 1),
                     "z": z, "p": p})

    every = pd.Series(True, index=s.index)
    fav_prob = s["fav_p"]
    second_prob = s[["pH", "pD", "pA"]].apply(lambda r: sorted(r)[1], axis=1)
    third_prob = s[["pH", "pD", "pA"]].min(axis=1)
    add("favourite wins", every, s["fav_won"], fav_prob)
    add("second choice wins", every, (s["rank"] == 2).astype(float), second_prob)
    add("third choice wins", every, (s["rank"] == 3).astype(float), third_prob)
    add("home wins", every, s["isH"], s["pH"])
    add("draws", every, s["isD"], s["pD"])
    add("away wins", every, s["isA"], s["pA"])
    add("home favourite wins", s["fav"] == "H", s["fav_won"], fav_prob)
    add("away favourite wins", s["fav"] == "A", s["fav_won"], fav_prob)
    for lo, hi in [(0, 0.38), (0.38, 0.42), (0.42, 0.46), (0.46, 0.52), (0.52, 1.01)]:
        add(f"favourite {int(lo*100)}-{int(min(hi,1)*100)}%", (fav_prob > lo) & (fav_prob <= hi), s["fav_won"], fav_prob)
    for lo, hi in [(0, 0.27), (0.27, 0.29), (0.29, 0.31), (0.31, 1)]:
        add(f"draw priced {int(lo*100)}-{int(min(hi,1)*100)}%", (s["pD"] > lo) & (s["pD"] <= hi), s["isD"], s["pD"])
    return pd.DataFrame(rows)


def dispersion(g: pd.DataFrame) -> dict:
    """Do upsets or draws cluster on some cards beyond what each game's own odds imply?
    Pearson dispersion across cards (about 1.0 if not; well above 1 if they cluster)."""
    s = g[g["has_odds"] & g["played"]]
    out = {}
    for name, x, p in [("favourites correct", s["fav_won"], s["fav_p"]), ("draws", s["isD"], s["pD"])]:
        d = pd.DataFrame({"card": s["card"], "x": x, "p": p, "v": p * (1 - p)}).groupby("card").sum()
        d = d[d["v"] > 0]
        stat = (((d["x"] - d["p"]) ** 2) / d["v"]).sum()
        k = len(d)
        out[name] = {"cards": k, "ratio": stat / k, "p_over": _chi2_sf(stat, k)}
    return out


def late_moves(g: pd.DataFrame) -> dict:
    """Games where the opening (pre-match average) favourite differs from the closing one."""
    s = g[g["has_odds"] & g["played"] & g[["oH", "oD", "oA"]].notna().all(axis=1)].copy()
    s["open_fav"] = np.array(RES)[s[["oH", "oD", "oA"]].values.argmax(axis=1)]
    f = s[s["open_fav"] != s["fav"]]
    return {"priced_with_open": len(s), "flips": len(f),
            "closing_fav_won": (f["result"] == f["fav"]).mean() if len(f) else np.nan,
            "opening_fav_won": (f["result"] == f["open_fav"]).mean() if len(f) else np.nan}


def draw_rule(g: pd.DataFrame) -> dict:
    """R19 on SportPesa's own games: when the favourite loses, which backup comes in?"""
    s = g[g["has_odds"] & g["played"]].copy()
    draw_second = s["second"] == "D"
    out = {}
    for name, m in [("draw ranked 2nd", draw_second), ("draw ranked 3rd", ~draw_second & (s["fav"] != "D"))]:
        t = s[m]
        other = np.where(t["fav"] == "H", "A", "H")
        out[name] = {"n": len(t), "draw_rate": t["isD"].mean(), "draw_implied": t["pD"].mean(),
                     "other_side_rate": (t["result"].values == other).mean()}
    low = s[s["pU"] >= 0.55]
    out["low-scoring (under 2.5 >= 55%)"] = {"n": len(low), "draw_rate": low["isD"].mean(), "draw_implied": low["pD"].mean()}
    return out


def crowd(g: pd.DataFrame, cards: pd.DataFrame) -> dict:
    """Winning tickets per tier on the 17-game product, and how they track the favourites."""
    c = cards.set_index("card")
    tiers = [12, 13, 14, 15, 16, 17]
    won_any = {t: int((c[f"winners_{t}"] > 0).sum()) for t in tiers}
    s = g[g["played"]]
    full = g.groupby("card").filter(lambda d: d["has_odds"].all())
    fav_ok = full.groupby("card")["fav_won"].sum()
    joined = c.join(fav_ok.rename("fav_correct"), how="inner")
    corr = joined[["fav_correct", "winners_12"]].corr(method="spearman").iloc[0, 1] if len(joined) > 5 else np.nan
    by_fav = joined.groupby("fav_correct")["winners_12"].median().to_dict()
    return {"cards_with_winners": won_any, "median_winners": {t: float(c[f"winners_{t}"].median()) for t in tiers},
            "median_paid_12": float(c.loc[c["winners_12"] > 0, "paid_12"].median()),
            "median_paid_13": float(c.loc[c["winners_13"] > 0, "paid_13"].median()),
            "median_paid_14": float(c.loc[c["winners_14"] > 0, "paid_14"].median()),
            "jackpot_17_won_cards": c.index[c["winners_17"] > 0].tolist(),
            "spearman_favs_v_12winners": corr, "median_12winners_by_favs_correct": by_fav}


def backtest(g: pd.DataFrame) -> pd.DataFrame:
    """Slip methods on every fully priced real card (closing odds as the pricing)."""
    full = g.groupby("card").filter(lambda d: d["has_odds"].all() and len(d) == 17)
    rows = []
    for card, d in full.groupby("card"):
        d = d.sort_values("n")
        probs = d[["pH", "pD", "pA"]].values
        res = d["result"].map({"H": 0, "D": 1, "A": 2}).values
        fav = probs.argmax(1)
        free = optimise(probs, n_slips=3, target=12)
        mix = optimise(probs, n_slips=3, target=12, min_draws=[0, 0, 3])
        four = optimise(probs, n_slips=3, target=12, min_draws=4, max_draws=6)
        rows.append({
            "card": card, "favourites": int((fav == res).sum()),
            "fav_expected": probs.max(1).sum(),
            "opt_best": max(int((np.array(s) == res).sum()) for s in free["slips"]),
            "opt_p12": free["chance"],
            "mix_best": max(int((np.array(s) == res).sum()) for s in mix["slips"]),
            "four_draw_best": max(int((np.array(s) == res).sum()) for s in four["slips"]),
            "four_p12": four["chance"],
            "draws_on_card": int((res == 1).sum()),
        })
    return pd.DataFrame(rows)


def estimate_tilt(g: pd.DataFrame, prior_games: int = 2500, save: bool = True) -> dict:
    """Favourite / draw / underdog-side factors (actual over implied) from every priced archive
    game, shrunk towards 1 by n / (n + prior_games). With ~2,500 games that is half strength;
    each new card moves it a little, and if the effect fades the factors drift back to 1."""
    s = g[g["has_odds"] & g["played"] & (g["fav"] != "D")]
    dog_won = (s["result"] == np.where(s["fav"] == "H", "A", "H")).astype(float)
    p_dog = np.where(s["fav"] == "H", s["pA"], s["pH"])
    raw = {"fav": s["fav_won"].mean() / s["fav_p"].mean(), "draw": s["isD"].mean() / s["pD"].mean(),
           "dog": dog_won.mean() / p_dog.mean()}
    w = len(s) / (len(s) + prior_games)
    out = {k: round(1 + (v - 1) * w, 4) for k, v in raw.items()}
    out.update({"games": len(s), "cards": int(s["card"].nunique()), "weight": round(w, 3),
                "raw": {k: round(v, 4) for k, v in raw.items()}})
    if save:
        TILT_JSON.write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


def report() -> dict:
    g = load()
    _, cards = load_archive()
    out = {"overview": results_overview(g), "position": position_test(g), "selection": selection_profile(g),
           "calibration": calibration(g), "dispersion": dispersion(g), "late": late_moves(g),
           "draw_rule": draw_rule(g), "crowd": crowd(g, cards), "backtest": backtest(g),
           "tilt": estimate_tilt(g)}
    return out


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    r = report()
    for k, v in r.items():
        print(f"\n=== {k} ===")
        if isinstance(v, pd.DataFrame):
            print(v.round(3).to_string())
        elif isinstance(v, dict):
            for kk, vv in v.items():
                print(f"  {kk}: {vv if not isinstance(vv, pd.DataFrame) else chr(10) + vv.to_string()}")
