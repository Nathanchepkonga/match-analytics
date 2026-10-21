"""
Author: Tiago Monteiro
Date: 21-12-2025
Jackpot ledger: records every slate's odds, slips and results, and reports which
prediction styles have actually beaten the bookmaker favourite. Run with
`python -m src.jackpot_ledger` from the repo root.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy.stats import binomtest

LEDGER_DIR = Path(__file__).parent.parent / "data" / "jackpot_ledger"
OUTCOMES = "HDA"
# A style needs at least this many games where exactly one of (its pick, the favourite)
# was right before it can be called better or worse than the favourite.
MIN_DECIDED = 20


def load_slates(directory: Path = LEDGER_DIR) -> List[Dict]:
    """Load every slate file in the ledger directory, oldest first."""
    if not directory.exists():
        return []
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(directory.glob("*.json"))]


def favourite(odds: List[float]) -> str:
    """The bookmaker favourite: the outcome with the shortest price."""
    return OUTCOMES[min(range(3), key=lambda i: odds[i])]


def devig(odds: List[float]) -> List[float]:
    """Margin-removed chances for H, D, A from decimal odds."""
    inv = [1 / o for o in odds]
    return [x / sum(inv) for x in inv]


def hit_chances(slate: Dict, picks: List[str]) -> List[float]:
    """The bookmaker's margin-removed chance that each pick is right."""
    return [sum(devig(g["odds"])[OUTCOMES.index(o)] for o in p if o in OUTCOMES)
            for p, g in zip(picks, slate["games"])]


def draw_role(odds: List[float], p_under: Optional[float] = None) -> str:
    """Where a draw belongs for one game, from that game's own odds (plus the chance of under
    2.5 goals if known). Thresholds come from 38,281 balanced matches, 2019-2026, checked on
    2019-22 and 2023-26 separately (documentation/draw_study.md):
      "draw-main"     draw at least level with the favourite (favourite <= 36%, draw >= 31%)
      "draw-backup"   draw is the better alternative to the favourite (+5 pts, proven)
      "either-backup" draw and the other side are about equal; choose on the game's facts
      "side-backup"   the other side is the better alternative (+3-4 pts, proven)"""
    p_home, p_draw, p_away = devig(odds)
    fav = max(p_home, p_draw, p_away)
    if p_draw == fav or (fav <= 0.36 and p_draw >= 0.31):
        return "draw-main"
    if p_draw >= min(p_home, p_away):
        return "draw-backup"
    if abs(p_home - p_away) <= 0.02:
        return "side-backup"
    if p_under is not None:
        return "either-backup" if p_under >= 0.55 else "side-backup"
    return "either-backup" if p_draw >= 0.29 and fav <= 0.40 else "side-backup"


def draw_plan(slate: Dict) -> pd.DataFrame:
    """The draw role of every game on a slate. A game's `"p_under"` (margin-removed chance of
    under 2.5 goals) is used when the researcher recorded it."""
    rows = []
    for g in slate["games"]:
        p = devig(g["odds"])
        rows.append({"game": g["n"], "match": f"{g['home']} v {g['away']}",
                     "home": round(p[0], 3), "draw": round(p[1], 3), "away": round(p[2], 3),
                     "p_under": g.get("p_under"), "draw_role": draw_role(g["odds"], g.get("p_under"))})
    return pd.DataFrame(rows)


def chance_at_least(chances: List[float], k: int) -> float:
    """Chance of k or more picks right, treating games as independent."""
    dist = [1.0]
    for p in chances:
        dist = [a * (1 - p) + b * p for a, b in zip(dist + [0.0], [0.0] + dist)]
    return sum(dist[k:])


def expected_best(slate: Dict, sims: int = 20000, seed: int = 0) -> float:
    """Average score of the best slip if results followed the margin-removed odds. A best
    slip near this number was a normal week, not a near miss."""
    idx = [i for i, g in enumerate(slate["games"]) if g.get("result")]
    probs = np.array([devig(slate["games"][i]["odds"]) for i in idx])
    u = np.random.default_rng(seed).random((sims, len(idx), 1))
    results = np.minimum((u > probs.cumsum(axis=1)).sum(axis=2), 2)
    slips = [slip["picks"].split() for slip in slate["slips"]]
    covered = np.array([[[o in picks[i] for o in OUTCOMES] for i in idx] for picks in slips])
    hits = covered[:, np.arange(len(idx))[None, :], results].sum(axis=2)
    return float(hits.max(axis=0).mean())


def score_slip(slate: Dict, picks: List[str]) -> int:
    """Number of correct picks on the games that have a result. A double chance such as
    "HD" counts if either outcome happened; "-" means no pick."""
    return sum(g["result"] in p for p, g in zip(picks, slate["games"]) if g.get("result"))


def departures(slates: List[Dict]) -> pd.DataFrame:
    """Every pick that differed from the favourite, with whether each side was right."""
    rows = []
    for s in slates:
        for slip in s["slips"]:
            for g, p in zip(s["games"], slip["picks"].split()):
                fav = favourite(g["odds"])
                if p != fav and g.get("result"):
                    rows.append({
                        "slate": s["slate_id"], "slip": slip["name"], "style": slip["style"],
                        "game": g["n"], "pick": p, "pick_right": p == g["result"], "fav_right": fav == g["result"],
                    })
    return pd.DataFrame(rows, columns=["slate", "slip", "style", "game", "pick", "pick_right", "fav_right"])


REASONS = ["news", "late-move", "draw-rule", "optimiser", "coverage", "research-model", "psychology", "tipster"]


def reason_report(slates: Optional[List[Dict]] = None) -> pd.DataFrame:
    """Changes from the favourite grouped by the reason recorded for them. A slip may carry
    "reasons": {"<game n>": "<reason>"} (see REASONS); changes without one count as 'untagged'.
    Each slate/game/pick/reason counts once, however many slips copied it."""
    slates = load_slates() if slates is None else slates
    rows = []
    for s in slates:
        for slip in s["slips"]:
            tags = slip.get("reasons", {})
            for g, p in zip(s["games"], slip["picks"].split()):
                fav = favourite(g["odds"])
                if p in ("H", "D", "A") and p != fav and g.get("result"):
                    rows.append({"slate": s["slate_id"], "game": g["n"], "pick": p,
                                 "reason": tags.get(str(g["n"]), "untagged"),
                                 "pick_right": p == g["result"], "fav_right": fav == g["result"]})
    if not rows:
        return pd.DataFrame()
    calls = pd.DataFrame(rows).drop_duplicates(["slate", "game", "pick", "reason"])
    out = calls.groupby("reason").agg(calls=("pick", "size"), right=("pick_right", "sum"),
                                      favourite_would_have=("fav_right", "sum")).reset_index()
    out["right_pct"] = (100 * out["right"] / out["calls"]).round(0).astype(int).astype(str) + "%"
    out["favourite_pct"] = (100 * out["favourite_would_have"] / out["calls"]).round(0).astype(int).astype(str) + "%"
    return out.sort_values("calls", ascending=False)


def change_types(slates: Optional[List[Dict]] = None) -> pd.DataFrame:
    """Changes from the favourite split into draw picks and side switches. 'calls' counts each
    slate/game/pick once, so a change copied onto many slips is not counted many times."""
    slates = load_slates() if slates is None else slates
    deps = departures(slates)
    if deps.empty:
        return pd.DataFrame()
    deps = deps[deps["pick"].isin(["H", "D", "A"])].assign(kind=lambda x: np.where(x["pick"] == "D", "draw", "side"))
    calls = deps.drop_duplicates(["slate", "game", "pick"])
    out = []
    for kind in ("draw", "side"):
        d, c = deps[deps["kind"] == kind], calls[calls["kind"] == kind]
        out.append({"change": kind, "picks_on_slips": len(d), "picks_right": f"{d['pick_right'].mean():.0%}" if len(d) else "-",
                    "distinct_calls": len(c), "calls_right": int(c["pick_right"].sum()),
                    "calls_right_pct": f"{c['pick_right'].mean():.0%}" if len(c) else "-",
                    "favourite_right_same_games": f"{c['fav_right'].mean():.0%}" if len(c) else "-"})
    return pd.DataFrame(out)


def style_report(slates: Optional[List[Dict]] = None) -> pd.DataFrame:
    """Per-style performance against the favourite, with an evidence-based verdict."""
    slates = load_slates() if slates is None else slates
    slip_rows = []
    for s in slates:
        played = sum(1 for g in s["games"] if g.get("result"))
        if not played:
            continue
        for slip in s["slips"]:
            slip_rows.append({"style": slip["style"], "pct": score_slip(s, slip["picks"].split()) / played})
    if not slip_rows:
        return pd.DataFrame()

    deps = departures(slates)
    out = []
    for style, grp in pd.DataFrame(slip_rows).groupby("style"):
        d = deps[deps["style"] == style]
        wins = int((d["pick_right"] & ~d["fav_right"]).sum())
        losses = int((d["fav_right"] & ~d["pick_right"]).sum())
        decided = wins + losses
        if len(d) == 0:
            verdict = "baseline (no changes from the favourite)"
        elif decided < MIN_DECIDED:
            verdict = f"not enough evidence yet ({decided}/{MIN_DECIDED} decided games)"
        else:
            p = binomtest(wins, decided, 0.5).pvalue
            if p >= 0.05:
                verdict = "no proven difference from the favourite"
            else:
                verdict = "beats the favourite" if wins > losses else "worse than the favourite"
        out.append({
            "style": style,
            "slips": len(grp),
            "avg_correct": f"{grp['pct'].mean():.0%}",
            "changes_from_favourite": len(d),
            "change_right": f"{d['pick_right'].mean():.0%}" if len(d) else "-",
            "favourite_right_same_games": f"{d['fav_right'].mean():.0%}" if len(d) else "-",
            "verdict": verdict,
        })
    return pd.DataFrame(out)


def tipster_scores(slate: Dict) -> List[Dict]:
    """Outside tipsters' scores on a slate. Entries either carry their own `picks` (scored
    here) or, for slates checked after the fact, a recorded `correct`/`games` total."""
    rows = []
    for t in slate.get("tipsters", []):
        if "picks" in t:
            picks = t["picks"].split()
            games = sum(1 for p, g in zip(picks, slate["games"]) if g.get("result") and p != "-")
            correct = score_slip(slate, picks)
            doubles = sum(len(p) == 2 for p in picks)
        else:
            correct, games, doubles = t["correct"], t["games"], t.get("doubles")
        if games:
            rows.append({"tipster": t["name"], "correct": correct, "games": games, "doubles": doubles})
    return rows


def tipster_report(slates: Optional[List[Dict]] = None) -> pd.DataFrame:
    """Every outside tipster's score next to the bookmaker favourites on the same slate."""
    slates = load_slates() if slates is None else slates
    rows = []
    for s in slates:
        played = sum(1 for g in s["games"] if g.get("result"))
        if not played:
            continue
        fav_pct = score_slip(s, [favourite(g["odds"]) for g in s["games"]]) / played
        for t in tipster_scores(s):
            rows.append({
                "slate": s["slate_id"], "tipster": t["tipster"],
                "score": f"{t['correct']}/{t['games']}", "pct": f"{t['correct'] / t['games']:.0%}",
                "double_chances": "?" if t["doubles"] is None else t["doubles"],
                "favourites_pct": f"{fav_pct:.0%}",
            })
    return pd.DataFrame(rows)


def slate_summary(slates: Optional[List[Dict]] = None) -> pd.DataFrame:
    """Per-slate: what a random slip and the favourites should score (from the odds), what
    the favourites, outside tipsters and our slips actually scored, and the best slip."""
    slates = load_slates() if slates is None else slates
    rows = []
    for s in slates:
        played_games = [g for g in s["games"] if g.get("result")]
        played = len(played_games)
        if not played:
            continue
        favs = [favourite(g["odds"]) for g in s["games"]]
        scores = {slip["name"]: score_slip(s, slip["picks"].split()) for slip in s["slips"]}
        best = max(scores, key=scores.get)
        singles = [t for t in tipster_scores(s) if t["doubles"] == 0]
        rows.append({
            "slate": s["slate_id"], "games": played,
            "random_expected": round(played / 3, 1),
            "favourites_expected": round(sum(max(devig(g["odds"])) for g in played_games), 1),
            "favourites_correct": score_slip(s, favs),
            "tipsters_avg": round(sum(t["correct"] / t["games"] for t in singles) / len(singles) * played, 1)
            if singles else None,
            "our_slips_avg": round(sum(scores.values()) / len(scores), 1),
            "best_slip": f"{best} ({scores[best]})",
            "best_expected": round(expected_best(s), 1),
            "draws": sum(g.get("result") == "D" for g in s["games"]),
        })
    return pd.DataFrame(rows)


def money_summary(slates: Optional[List[Dict]] = None) -> pd.DataFrame:
    """Money staked and won per slate, for slates where the stake was recorded, with a total.
    Memory keeps the near misses and forgets the running cost; this keeps both."""
    slates = load_slates() if slates is None else slates
    df = pd.DataFrame([{"slate": s["slate_id"], "staked_ksh": s["staked_ksh"], "won_ksh": s.get("won_ksh", 0)}
                       for s in slates if "staked_ksh" in s], columns=["slate", "staked_ksh", "won_ksh"])
    if not df.empty:
        df["net_ksh"] = df["won_ksh"] - df["staked_ksh"]
        df.loc[len(df)] = ["total", df["staked_ksh"].sum(), df["won_ksh"].sum(), df["net_ksh"].sum()]
    return df


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    print("Slates:")
    print(slate_summary().to_string(index=False))
    print()
    print("Prediction styles vs the bookmaker favourite:")
    print(style_report().to_string(index=False))
    print()
    print("Changes from the favourite, draw picks v side switches:")
    print(change_types().to_string(index=False))
    print()
    print("Changes by recorded reason (slips carry \"reasons\": {game: reason}):")
    print(reason_report().to_string(index=False))
    print()
    print("Outside tipsters (single picks only count towards tipsters_avg above):")
    print(tipster_report().to_string(index=False))
    print()
    money = money_summary()
    if money.empty:
        print("Money: not recorded yet. Add \"staked_ksh\" and \"won_ksh\" to each slate file.")
    else:
        print("Money:")
        print(money.to_string(index=False))
