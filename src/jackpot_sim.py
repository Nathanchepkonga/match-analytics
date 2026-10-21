"""
Jackpot simulator: rebuilds SportPesa-style cards from real past weekends and scores slip-building
strategies against the real results. A card is the most balanced Friday-Sunday games of one week
(favourite <= 45%), at most 2 per league, 4 random cards per week from the 40 most balanced games.
Odds are the average bookmaker odds before kickoff, margin removed. Needs the data downloaded by
`python -m src.draw_study`. Run with `python -m src.jackpot_sim` from the repo root.
"""

from typing import Callable, Dict, List

import numpy as np
import pandas as pd
from scipy.stats import binomtest, wilcoxon

from src.draw_study import load
from src.jackpot_ledger import draw_role
from src.slip_optimizer import optimise

HOME, DRAW, AWAY = 0, 1, 2
ROLE_RANK = {"draw-main": 0, "draw-backup": 1, "either-backup": 2, "side-backup": 3}


def build_cards(data: pd.DataFrame, size: int, per_week: int = 4, pool: int = 40,
                league_cap: int = 2, seed: int = 0) -> List[pd.DataFrame]:
    """Jackpot-like cards: `per_week` random draws of `size` games from each week's `pool` most
    balanced Friday-Sunday games, with at most `league_cap` games from one league."""
    rng = np.random.default_rng(seed)
    d = data[(data["fav_p"] <= 0.45) & data["date"].notna() & data["date"].dt.weekday.isin([4, 5, 6])]
    iso = d["date"].dt.isocalendar()
    p = d[["pH", "pD", "pA"]].values
    d = d.assign(week=iso["year"].astype(str) + "-" + iso["week"].astype(str).str.zfill(2),
                 balance=-(p * np.log(p)).sum(axis=1) / np.log(3))
    cards = []
    for week, g in d.groupby("week"):
        g = g.sort_values("balance", ascending=False).head(pool)
        if len(g) < size * 1.5:
            continue
        leagues = g["league"].values
        for _ in range(per_week):
            picked, count = [], {}
            for i in rng.permutation(len(g)):
                if count.get(leagues[i], 0) < league_cap:
                    picked.append(i)
                    count[leagues[i]] = count.get(leagues[i], 0) + 1
                if len(picked) == size:
                    cards.append(g.iloc[picked].assign(week=week))
                    break
    return cards


def _info(card: pd.DataFrame):
    p = card[["pH", "pD", "pA"]].values
    fav = p.argmax(axis=1)
    top2 = np.sort(p, axis=1)
    gap = top2[:, 2] - top2[:, 1]
    other = np.where(fav == HOME, AWAY, np.where(fav == AWAY, HOME, np.where(p[:, 0] >= p[:, 2], HOME, AWAY)))
    roles = [draw_role(list(1 / row), None if np.isnan(u) else u) for row, u in zip(p, card["pU"].values)]
    return p, fav, gap, other, roles


def _alternative(i, p, fav, other, roles):
    """The backup pick on game i under the draw study (R19); 'either' goes to the likelier option."""
    if roles[i] in ("draw-main", "draw-backup"):
        return DRAW
    if roles[i] == "either-backup":
        return DRAW if p[i, DRAW] >= p[i, other[i]] else other[i]
    return other[i]


def favourites_1(card, rng):
    _, fav, *_ = _info(card)
    return [fav.copy()]


def tweaks_3(card, rng):
    """Slip 1 favourites; slip 2 changes the closest game, slip 3 the next two closest, each to
    the draw study's backup pick (the evidence-based method without a draw quota)."""
    p, fav, gap, other, roles = _info(card)
    close = np.argsort(gap)
    s2, s3 = fav.copy(), fav.copy()
    s2[close[0]] = _alternative(close[0], p, fav, other, roles)
    for i in close[1:3]:
        s3[i] = _alternative(i, p, fav, other, roles)
    return [fav.copy(), s2, s3]


def _draw_games(p, gap, roles):
    clearest = set(np.argsort(-gap)[:3])
    ranked = sorted((i for i in range(len(p)) if i not in clearest), key=lambda i: (ROLE_RANK[roles[i]], -p[i, DRAW]))
    return ranked[:5]


def draw_heavy_3(card, rng):
    """The 9 Oct method: 3 draws per slip on the most draw-friendly games (draw-study role first,
    then draw chance), rotated d1-d2-d3 / d1-d2-d4 / d1-d3-d5, plus one side change on the closest
    side-backup game in slips 2 and 3. The 3 clearest favourites are never changed."""
    p, fav, gap, other, roles = _info(card)
    d = _draw_games(p, gap, roles)
    sides = [i for i in np.argsort(gap) if roles[i] == "side-backup" and i not in d[:5]]
    slips = []
    for k, draws in enumerate([(d[0], d[1], d[2]), (d[0], d[1], d[3]), (d[0], d[2], d[4])]):
        s = fav.copy()
        s[list(draws)] = DRAW
        if k and len(sides) >= k:
            s[sides[k - 1]] = other[sides[k - 1]]
        slips.append(s)
    return slips


def close_draws_3(card, rng):
    """3 draws per slip, but only on the 5 closest games (smallest favourite margin), preferring
    games where the draw study allows a draw; rotated d1-d2-d3 / d1-d2-d4 / d1-d3-d5."""
    p, fav, gap, other, roles = _info(card)
    close = list(np.argsort(gap)[:5])
    d = sorted(close, key=lambda i: (roles[i] == "side-backup", -p[i, DRAW]))
    slips = []
    for draws in [(d[0], d[1], d[2]), (d[0], d[1], d[3]), (d[0], d[2], d[4])]:
        s = fav.copy()
        s[list(draws)] = DRAW
        slips.append(s)
    return slips


def optimiser_3(card, rng):
    """Tail-optimised 3 slips (src/slip_optimizer.py): target 10/13 or 12/17, 6 closest games."""
    return optimise(card[["pH", "pD", "pA"]].values, 3)["slips"]


def optimiser_draws_3(card, rng):
    """Tail-optimised 3 slips with at least 3 draws on every slip."""
    return optimise(card[["pH", "pD", "pA"]].values, 3, min_draws=3)["slips"]


def optimiser_mix_003(card, rng):
    """Combination: two free slips plus one slip with at least 3 draws, chosen together."""
    return optimise(card[["pH", "pD", "pA"]].values, 3, min_draws=[0, 0, 3])["slips"]


def optimiser_mix_033(card, rng):
    """Combination: one free slip plus two slips with at least 3 draws, chosen together."""
    return optimise(card[["pH", "pD", "pA"]].values, 3, min_draws=[0, 3, 3])["slips"]


def draw_heavy_1(card, rng):
    return draw_heavy_3(card, rng)[:1]


def random_3(card, rng):
    return [rng.integers(0, 3, len(card)) for _ in range(3)]


STRATEGIES: Dict[str, Callable] = {
    "Favourites, 1 slip": favourites_1,
    "Favourites + 3 draws, 1 slip": draw_heavy_1,
    "Random, 3 slips": random_3,
    "Evidence tweaks (R19), 3 slips": tweaks_3,
    "Draw-heavy 3 per slip (9 Oct method), 3 slips": draw_heavy_3,
    "3 draws per slip on the 5 closest games, 3 slips": close_draws_3,
    "Tail optimiser, 3 slips": optimiser_3,
    "Tail optimiser, 3 draws per slip, 3 slips": optimiser_draws_3,
    "Optimiser combination 0/0/3 draws": optimiser_mix_003,
    "Optimiser combination 0/3/3 draws": optimiser_mix_033,
}


def run(cards: List[pd.DataFrame], thresholds: List[int], seed: int = 1, only: List[str] = None):
    """Per-card results for every strategy (or just `only`), plus every pick that differs from the favourite."""
    rng = np.random.default_rng(seed)
    strategies = {k: v for k, v in STRATEGIES.items() if only is None or k in only}
    rows, changes = [], []
    for c, card in enumerate(cards):
        res = card["res"].map({"H": HOME, "D": DRAW, "A": AWAY}).values
        p, fav, gap, other, roles = _info(card)
        for name, strat in strategies.items():
            slips = strat(card, rng)
            scores = [int((s == res).sum()) for s in slips]
            row = {"card": c, "week": card["week"].iloc[0], "strategy": name, "best": max(scores),
                   "slip_mean": np.mean(scores), "slip_expected": np.mean([p[np.arange(len(s)), s].sum() for s in slips])}
            row.update({f"{k}+": max(scores) >= k for k in thresholds})
            rows.append(row)
            if name != "Random, 3 slips":
                for s in slips:
                    for i in np.where(s != fav)[0]:
                        changes.append({"strategy": name, "match": card.index[i], "pick": int(s[i]), "role": roles[i],
                                        "half": "2019-22" if card["season"].iloc[i] <= 2022 else "2023-26",
                                        "pick_right": s[i] == res[i], "fav_right": fav[i] == res[i]})
    return pd.DataFrame(rows), pd.DataFrame(changes)


def report(size: int, thresholds: List[int], data: pd.DataFrame) -> None:
    cards = build_cards(data, size)
    allg = pd.concat(cards)
    print(f"\n=== {size}-game cards: {len(cards)} cards from {allg['week'].nunique()} weekends, 2019-2026 ===")
    p = allg[["pH", "pD", "pA"]].values
    print(f"Card realism: favourite chance {allg['fav_p'].mean():.3f}, balance "
          f"{(-(p * np.log(p)).sum(1) / np.log(3)).mean():.3f}, draws per card {allg['res'].eq('D').mean() * size:.2f} "
          f"(odds expected {allg['pD'].mean() * size:.2f}). SportPesa cards: favourite 0.39-0.45, balance 0.97-0.99.")
    res, ch = run(cards, thresholds)
    print(f"{'strategy':<48}{'best':>6}{'per slip':>10}{'expected':>10}" + "".join(f"{str(k) + '+':>8}" for k in thresholds))
    for name in STRATEGIES:
        r = res[res["strategy"] == name]
        print(f"{name:<48}{r['best'].mean():>6.2f}{r['slip_mean'].mean():>10.2f}{r['slip_expected'].mean():>10.2f}"
              + "".join(f"{100 * r[f'{k}+'].mean():>7.2f}%" for k in thresholds))
    # paired comparison by weekend (cards in the same weekend share games, so average within weekend)
    wk = res.groupby(["week", "strategy"])["best"].mean().unstack()
    a, b = "Draw-heavy 3 per slip (9 Oct method), 3 slips", "Evidence tweaks (R19), 3 slips"
    diff = wk[a] - wk[b]
    print(f"Draw-heavy minus evidence tweaks, best score per weekend: {diff.mean():+.3f} "
          f"(Wilcoxon p={wilcoxon(diff).pvalue:.3g}, {len(diff)} weekends)")
    for k in thresholds[-3:]:
        wk_k = res.groupby(["week", "strategy"])[f"{k}+"].mean().unstack()
        print(f"   {k}+ rate: draw-heavy {100 * wk_k[a].mean():.2f}% v evidence tweaks {100 * wk_k[b].mean():.2f}%")
    # every distinct changed pick once (cards in a weekend overlap)
    ch = ch.drop_duplicates(["strategy", "match", "pick"])
    print("Picks that differ from the favourite (each distinct pick counted once):")
    for name, g in ch.groupby("strategy"):
        for label, sub in [("all changes", g), ("draw picks", g[g["pick"] == DRAW]), ("side picks", g[g["pick"] != DRAW])]:
            if len(sub) == 0:
                continue
            w, l = int((sub.pick_right & ~sub.fav_right).sum()), int((sub.fav_right & ~sub.pick_right).sum())
            p_val = binomtest(w, w + l, 0.5).pvalue if w + l else float("nan")
            print(f"   {name:<46} {label:<12} n={len(sub):>6}  pick right {sub.pick_right.mean():.3f}  "
                  f"favourite right {sub.fav_right.mean():.3f}  p={p_val:.3g}")


if __name__ == "__main__":
    data = load()
    report(13, [7, 8, 9, 10, 11, 12], data)
    report(17, [9, 10, 11, 12, 13, 14], data)
