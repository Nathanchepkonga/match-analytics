"""
Draw study: are draws priced correctly in balanced games, and when is a draw the right pick?
Downloads results and average bookmaker odds from football-data.co.uk (2019-2026, 41 leagues),
then runs the checks behind `draw_role` in src/jackpot_ledger.py. Results and method are written
up in documentation/draw_study.md. Run with `python -m src.draw_study` from the repo root.
"""

import glob
import os
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

DATA_DIR = Path(__file__).parent.parent / "data" / "football_data"
SEASONS = ["1920", "2021", "2122", "2223", "2324", "2425", "2526"]
DIVISIONS = ["E0", "E1", "E2", "E3", "EC", "SC0", "SC1", "SC2", "SC3", "D1", "D2", "I1", "I2",
             "SP1", "SP2", "F1", "F2", "N1", "B1", "P1", "T1", "G1"]
EXTRA = ["ARG", "AUT", "BRA", "CHN", "DNK", "FIN", "IRL", "JPN", "MEX", "NOR", "POL", "ROU",
         "RUS", "SWE", "SWZ", "USA"]
BALANCED = 0.45  # favourite's margin-removed chance at or below this = a jackpot-like game


def download(directory: Path = DATA_DIR) -> None:
    """Fetch the CSVs that aren't already on disk (about 33 MB in all)."""
    directory.mkdir(parents=True, exist_ok=True)
    jobs = [(f"https://www.football-data.co.uk/mmz4281/{s}/{d}.csv", f"{d}_{s}.csv")
            for s in SEASONS for d in DIVISIONS]
    jobs += [(f"https://www.football-data.co.uk/new/{c}.csv", f"new_{c}.csv") for c in EXTRA]
    for url, name in jobs:
        path = directory / name
        if path.exists() and path.stat().st_size > 1000:
            continue
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research)"})
        path.write_bytes(urllib.request.urlopen(req, timeout=30).read())
        time.sleep(0.2)


def load(directory: Path = DATA_DIR) -> pd.DataFrame:
    """One row per match: league, season, result and margin-removed H/D/A chances from the
    pre-match average odds (closing averages for the extra leagues, which have no pre-match
    columns), plus the chance of under 2.5 goals where available."""
    frames = []
    for p in glob.glob(str(directory / "*.csv")):
        name = os.path.basename(p)[:-4]
        df = pd.read_csv(p, encoding="utf-8-sig", encoding_errors="replace", on_bad_lines="skip",
                         low_memory=False)
        if name.startswith("new_"):
            df = df[pd.to_numeric(df["Season"].astype(str).str[:4], errors="coerce") >= 2019]
            frames.append(pd.DataFrame({
                "league": df["Country"].astype(str) + " " + df["League"].astype(str),
                "season": df["Season"].astype(str).str[:4].astype(int), "date": df["Date"], "res": df["Res"],
                "h": df["AvgCH"], "d": df["AvgCD"], "a": df["AvgCA"], "over": np.nan, "under": np.nan}))
        elif {"FTR", "AvgH", "AvgD", "AvgA"} <= set(df.columns):
            div, season = name.split("_")
            frames.append(pd.DataFrame({
                "league": div, "season": 2000 + int(season[:2]), "date": df["Date"], "res": df["FTR"],
                "h": df["AvgH"], "d": df["AvgD"], "a": df["AvgA"],
                "over": df.get("Avg>2.5"), "under": df.get("Avg<2.5")}))
    data = pd.concat(frames, ignore_index=True)
    for c in ["h", "d", "a", "over", "under"]:
        data[c] = pd.to_numeric(data[c], errors="coerce")
    data = data[data["res"].isin(["H", "D", "A"])].dropna(subset=["h", "d", "a"])
    data = data[(data[["h", "d", "a"]] > 1.01).all(axis=1)].copy()
    data["date"] = pd.to_datetime(data["date"], dayfirst=True, errors="coerce")
    inv = 1 / data[["h", "d", "a"]].values
    probs = inv / inv.sum(axis=1, keepdims=True)
    data["pH"], data["pD"], data["pA"] = probs.T
    data["pU"] = (1 / data["under"]) / (1 / data["under"] + 1 / data["over"])
    data["fav_p"] = probs.max(axis=1)
    data["fav"] = np.array(list("HDA"))[probs.argmax(axis=1)]
    data["second"] = np.array(list("HDA"))[np.argsort(-probs, axis=1)[:, 1]]
    data["other"] = np.where(data["fav"] == "H", "A", np.where(data["fav"] == "A", "H",
                             np.where(data["pH"] >= data["pA"], "H", "A")))
    data["half"] = np.where(data["season"] <= 2022, "2019-22", "2023-26")
    return data


def duel(games: pd.DataFrame, rival: str) -> dict:
    """Draw against the favourite ("fav") or the other side ("other") on the same games."""
    draw_right = int((games["res"] == "D").sum())
    rival_right = int((games["res"] == games[rival]).sum())
    decided = draw_right + rival_right
    return {"n": len(games), "draw": draw_right / len(games), rival: rival_right / len(games),
            "p": binomtest(draw_right, decided, 0.5).pvalue if decided else np.nan}


def report(data: pd.DataFrame) -> None:
    bal = data[data["fav_p"] <= BALANCED]
    third = (bal["second"] != "D") & (bal["fav"] != "D")
    print(f"{len(data)} matches, {data['league'].nunique()} leagues; {len(bal)} balanced (favourite <= 45%)")
    for half, g in bal.groupby("half"):
        print(f"  {half}: draws {g['res'].eq('D').mean():.4f} actual v {g['pD'].mean():.4f} in the odds")
    rules = {
        "draw as main pick: favourite <= 36%, draw >= 31%": ((bal.fav_p <= .36) & (bal.pD >= .31), "fav"),
        "draw as backup: draw ranked 2nd": (bal["second"] == "D", "other"),
        "draw as backup: home and away within 2%": ((bal.pH - bal.pA).abs() <= .02, "other"),
        "draw as backup: ranked 3rd, P(under 2.5) >= 55%": (third & (bal.pU >= .55), "other"),
        "draw as backup: ranked 3rd, P(under 2.5) < 50%": (third & (bal.pU < .50), "other"),
        "draw as backup: ranked 3rd, draw < 29%": (third & (bal.pD < .29), "other"),
    }
    for name, (cond, rival) in rules.items():
        print(name)
        for half in ["2019-22", "2023-26", "all"]:
            g = bal[cond.fillna(False) & ((bal["half"] == half) | (half == "all"))]
            r = duel(g, rival)
            print(f"  {half:<8} n={r['n']:>6}  draw {r['draw']:.3f}  {rival} {r[rival]:.3f}  p={r['p']:.3g}")


if __name__ == "__main__":
    download()
    report(load())
