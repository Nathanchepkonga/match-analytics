"""
Tail-optimised slip builder. Every slip takes the favourite on the clearer games and varies only on
the `m` closest games (smallest margin between the top two outcomes). That makes the chance that at
least one slip reaches the target score exact:

    P(any slip >= target) = sum over close-game outcomes o of P(o) * P(B >= target - best(o))

where best(o) is the most close games any slip gets right under outcome o, and B is how many of the
favourites on the other games come in (a Poisson-binomial count). Slips are picked greedily, then
improved by re-choosing one slip at a time until nothing improves. With independent games the
favourites slip is always the best single slip, so slip 1 is the favourites unless a draw minimum
forces otherwise. Validated on 12,580 historical cards in src/jackpot_sim.py.
"""

import itertools
import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

HOME, DRAW, AWAY = 0, 1, 2
DEFAULT_TARGET = {13: 10, 17: 12}
TILT_JSON = Path(__file__).parent.parent / "data" / "sportpesa_archive" / "tilt.json"


@lru_cache(maxsize=None)
def _patterns(m: int) -> Tuple[np.ndarray, np.ndarray]:
    """All 3^m pick patterns for the close games, and how many each gets right under every outcome."""
    pats = np.array(list(itertools.product(range(3), repeat=m)), dtype=np.int8)
    matches = np.zeros((len(pats), len(pats)), dtype=np.int16)
    for k in range(m):  # one column at a time keeps memory low for m = 8
        matches += pats[:, k][:, None] == pats[:, k][None, :]
    return pats, matches


def _tail(chances: np.ndarray) -> np.ndarray:
    """tail[x] = chance that at least x of these picks come in; the last entry is 0."""
    dist = np.array([1.0])
    for q in chances:
        dist = np.append(dist * (1 - q), 0.0) + np.append(0.0, dist * q)
    return np.append(np.cumsum(dist[::-1])[::-1], 0.0)


def draw_cost_order(probs) -> np.ndarray:
    """Games ordered by how little a draw pick gives up: favourite chance minus draw chance."""
    p = np.asarray(probs, dtype=float)
    return np.argsort(p.max(axis=1) - p[:, DRAW], kind="stable")


def optimise(probs, n_slips: int = 3, target: int = None, m: int = None,
             min_draws=0, max_rounds: int = 6, max_draws=None, vary=None) -> Dict:
    """Choose `n_slips` slips that maximise the chance at least one reaches `target` correct.
    `probs` is an (n, 3) array of margin-removed H/D/A chances. `min_draws` is the least number of
    draws on every slip, or a list with one minimum per slip (e.g. [0, 3, 3] keeps one free slip
    and two draw-carrying slips, all chosen together); draws are placed among the varying games.
    `max_draws` caps draws per slip (one number or one per slip). `vary` lists the game indices
    allowed to vary; by default the `m` closest games."""
    p = np.asarray(probs, dtype=float)
    n = len(p)
    target = target or DEFAULT_TARGET.get(n, int(round(0.75 * n)))
    m = min(m or (7 if n >= 17 else 6), n)  # 7 varying games tested best on 17-game cards
    fav = p.argmax(axis=1)
    top = np.sort(p, axis=1)
    if vary is not None:
        close = np.sort(np.asarray(vary, dtype=int))
        m = len(close)
    else:
        close = np.sort(np.argsort(top[:, 2] - top[:, 1], kind="stable")[:m])
    rest = np.setdiff1d(np.arange(n), close)
    pats, matches = _patterns(m)
    p_out = np.prod(p[close][np.arange(m), pats], axis=1)
    tail = _tail(p[rest, fav[rest]])
    last = len(tail) - 1

    minima = list(min_draws) if isinstance(min_draws, (list, tuple)) else [min_draws] * n_slips
    maxima = list(max_draws) if isinstance(max_draws, (list, tuple)) else [max_draws if max_draws is not None else n] * n_slips
    if len(minima) != n_slips or len(maxima) != n_slips:
        raise ValueError("give one draw minimum and maximum per slip")
    draws = (pats == DRAW).sum(axis=1) + int((fav[rest] == DRAW).sum())
    cands = [np.where((draws >= lo) & (draws <= hi))[0] for lo, hi in zip(minima, maxima)]
    if any(len(c) == 0 for c in cands):
        raise ValueError("a draw minimum can't be met among the close games; raise m")

    def values(best: np.ndarray, cand: np.ndarray) -> np.ndarray:
        combined = np.maximum(best[None, :], matches[cand])
        return tail[np.clip(target - combined, 0, last)] @ p_out

    chosen: List[int] = []
    best = np.full(len(pats), -10_000, dtype=np.int32)
    for j in sorted(range(n_slips), key=lambda j: minima[j]):  # least constrained first
        c = int(cands[j][np.argmax(values(best, cands[j]))])
        chosen.append((j, c))
        best = np.maximum(best, matches[c])
    chosen = [c for _, c in sorted(chosen)]
    for _ in range(max_rounds):
        changed = False
        for j in range(n_slips):
            others = np.full(len(pats), -10_000, dtype=np.int32)
            for k, c in enumerate(chosen):
                if k != j:
                    others = np.maximum(others, matches[c])
            c = int(cands[j][np.argmax(values(others, cands[j]))])
            if c != chosen[j]:
                chosen[j], changed = c, True
        if not changed:
            break
    best = np.full(len(pats), -10_000, dtype=np.int32)
    for c in chosen:
        best = np.maximum(best, matches[c])
    chance = float(tail[np.clip(target - best, 0, last)] @ p_out)
    slips = []
    for c in chosen:
        s = fav.copy()
        s[close] = pats[c]
        slips.append(s)
    return {"slips": slips, "target": target, "chance": chance, "close_games": close}


def chance(probs, slips, target: int, sims: int = 200_000, seed: int = 0) -> float:
    """Chance at least one of any `slips` reaches `target`: exact for up to 13 games, simulated
    above that. Use it to price a hand-made change before accepting it."""
    p = np.asarray(probs, dtype=float)
    n = len(p)
    slips = np.asarray(slips)
    if n <= 13:
        idx = np.array(list(itertools.product(range(3), repeat=n)), dtype=np.int8)
        prob = np.prod(p[np.arange(n), idx], axis=1)
        best = np.stack([(idx == s).sum(axis=1) for s in slips]).max(axis=0)
        return float(prob[best >= target].sum())
    u = np.random.default_rng(seed).random((sims, n, 1))
    res = np.minimum((u > p.cumsum(axis=1)[None]).sum(axis=2), 2)
    best = np.stack([(res == s).sum(axis=1) for s in slips]).max(axis=0)
    return float((best >= target).mean())


def as_letters(slip) -> str:
    return " ".join("HDA"[i] for i in slip)


def sportpesa_tilt(probs, fav: float = None, draw: float = None, dog: float = None) -> np.ndarray:
    """Scale each game's favourite / draw / underdog-side chances, then renormalise.
    On 2,462 priced games from 199 real Mega Jackpot Pro cards (documentation/sportpesa_archive_study.md)
    the underdog side won 2.8 pts less than its closing odds and the draw 1.8 pts more (factors about
    1.025 / 1.06 / 0.91). It only cleared out-of-sample testing in one direction, so it is used shrunk:
    factors not given come from data/sportpesa_archive/tilt.json (re-estimated by src.archive_study as
    new cards arrive), else half the first measurement. Games where the draw is the favourite are left
    as they are."""
    saved = json.loads(TILT_JSON.read_text(encoding="utf-8")) if TILT_JSON.exists() else {}
    fav = fav if fav is not None else saved.get("fav", 1.0125)
    draw = draw if draw is not None else saved.get("draw", 1.03)
    dog = dog if dog is not None else saved.get("dog", 0.955)
    p = np.array(probs, dtype=float)
    out = p.copy()
    for i, row in enumerate(p):
        f = int(row.argmax())
        if f == DRAW:
            continue
        d = AWAY if f == HOME else HOME
        out[i, f], out[i, DRAW], out[i, d] = row[f] * fav, row[DRAW] * draw, row[d] * dog
    return out / out.sum(axis=1, keepdims=True)


MEGA_CATEGORIES = {17: 12, 16: 11, 15: 10, 14: 10, 13: 10}   # games picked -> lowest bonus score


def mega_categories(probs, categories: Dict[int, int] = None) -> List[Dict]:
    """Mega Jackpot Pro lets a slip cover any 13-17 of the 17 games; each count is its own category
    with its own jackpot and bonus ladder. For each category, pick the k clearest games (highest
    favourite chance) and report one favourites slip's chance of a bonus and of all k correct.
    On 46 real cards the 15-game category won a bonus 3 times v once for 17 games (documentation/mega_categories.md)."""
    from src.jackpot_ledger import chance_at_least
    categories = categories or MEGA_CATEGORIES
    p = np.asarray(probs, float)
    fav = p.max(axis=1)
    order = np.argsort(-fav)
    out = []
    for k, need in sorted(categories.items(), reverse=True):
        keep = sorted(order[:k].tolist())
        sel = fav[keep]
        out.append({"games": k, "bonus_from": need, "keep": [i + 1 for i in keep],
                    "drop": [i + 1 for i in range(len(p)) if i not in keep],
                    "bonus_chance": chance_at_least(list(sel), need), "all_correct": float(np.prod(sel))})
    return out


def slate_probs(slate: Dict) -> np.ndarray:
    """Margin-removed chances per game: the freshest market average if saved, else the card odds."""
    from src.jackpot_ledger import devig
    return np.array([devig(g.get("market_odds_final") or g["odds"]) for g in slate["games"]])


if __name__ == "__main__":
    import argparse
    from src.jackpot_ledger import load_slates

    ap = argparse.ArgumentParser(description="Tail-optimised slips for a saved jackpot slate")
    ap.add_argument("slate_id")
    ap.add_argument("--slips", type=int, default=3)
    ap.add_argument("--target", type=int, default=None)
    ap.add_argument("--min-draws", default="0", help="one number for every slip, or one per slip, e.g. 0,0,3")
    ap.add_argument("--close", type=int, default=None, help="how many of the closest games may vary (default 6, or 7 for 17 games)")
    ap.add_argument("--tilt", action="store_true", help="apply sportpesa_tilt (draw up, underdog side down) first")
    args = ap.parse_args()
    slate = next(s for s in load_slates() if s["slate_id"] == args.slate_id)
    draws = [int(x) for x in args.min_draws.split(",")]
    probs = sportpesa_tilt(slate_probs(slate)) if args.tilt else slate_probs(slate)
    r = optimise(probs, args.slips, args.target, args.close, draws if len(draws) > 1 else draws[0])
    print(f"Target {r['target']}+; varying games {', '.join(str(i + 1) for i in r['close_games'])}")
    for i, s in enumerate(r["slips"], 1):
        print(f"  Slip {i}: {as_letters(s)}")
    print(f"Chance at least one slip reaches {r['target']}+: {100 * r['chance']:.3f}%")
