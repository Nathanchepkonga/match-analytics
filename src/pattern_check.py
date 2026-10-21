"""
Hidden-pattern check across every jackpot in the ledger (and the two September cards in
data/fixture_intelligence). Tests whether favourites, draws, home/away, card position, close games,
clustering of upsets, late favourite changes or goals differ from what the odds say, with a
Bonferroni correction for testing many ideas at once. Run with `python -m src.pattern_check`.
"""

import json, glob, math, warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy.stats import norm, binomtest, chisquare
from src.jackpot_ledger import devig
rows = []
for p in sorted(glob.glob("data/jackpot_ledger/*.json")):
    s = json.load(open(p, encoding="utf-8")); n = len(s["games"])
    for g in s["games"]:
        pr = np.array(devig(g["odds"])); r = "HDA".index(g["result"]); srt = np.sort(pr)
        late = None
        if "market_odds_final" in g:
            early = g.get("market_odds_friday") or g["odds"]
            e, f = np.array(devig(early)).argmax(), np.array(devig(g["market_odds_final"])).argmax()
            late = (e, f)
        score = g.get("score")
        rows.append({"slate": s["slate_id"], "size": n, "pos": g["n"], "pH": pr[0], "pD": pr[1], "pA": pr[2], "fav": pr.argmax(), "fav_p": pr.max(),
                     "gap": srt[2] - srt[1], "res": r, "late": late, "kick": g.get("kickoff"), "score": score})
df = pd.DataFrame(rows)
tests = []
def zt(name, k, ps):
    ps = np.asarray(ps); E, V = ps.sum(), (ps * (1 - ps)).sum()
    z = (k - E) / math.sqrt(V); tests.append((name, f"{k} v {E:.1f} expected", 2 * norm.sf(abs(z))))
fav_win = (df.fav == df.res)
zt("Favourites win more/less than odds say", int(fav_win.sum()), df.fav_p)
zt("Draws more/less than odds say", int((df.res == 1).sum()), df.pD)
zt("Home wins more/less than odds say", int((df.res == 0).sum()), df.pH)
zt("Away wins more/less than odds say", int((df.res == 2).sum()), df.pA)
for side, nm in ((0, "Home favourites"), (2, "Away favourites")):
    m = df.fav == side; zt(f"{nm} win more/less than odds say", int(fav_win[m].sum()), df.fav_p[m])
m = df.gap < 0.05; zt("Close games (<5 pts): favourite under/over-performs", int(fav_win[m].sum()), df.fav_p[m])
m = df.gap >= 0.05; zt("Clearer games: favourite under/over-performs", int(fav_win[m].sum()), df.fav_p[m])
m = df.pos <= df["size"] / 2; zt("First half of the card: favourites", int(fav_win[m].sum()), df.fav_p[m])
m = df.pos > df["size"] / 2; zt("Second half of the card: favourites", int(fav_win[m].sum()), df.fav_p[m])
# runs test: are favourite wins/losses clustered along the card order?
runs, exp_runs, var_runs = 0, 0, 0
for _, g in df.sort_values(["slate", "pos"]).groupby("slate"):
    x = (g.fav == g.res).astype(int).values; n1, n0 = x.sum(), len(x) - x.sum()
    runs += 1 + (np.diff(x) != 0).sum(); mu = 1 + 2 * n1 * n0 / len(x); exp_runs += mu
    var_runs += 2 * n1 * n0 * (2 * n1 * n0 - len(x)) / (len(x) ** 2 * (len(x) - 1))
tests.append(("Upsets cluster together along the card (runs test)", f"{runs} runs v {exp_runs:.1f} expected", 2 * norm.sf(abs(runs - exp_runs) / math.sqrt(var_runs))))
# late favourite changes (2 slates)
lt = df.dropna(subset=["late"]); ch = lt[[e != f for e, f in lt.late]]
if len(ch):
    newr = sum(f == r for (e, f), r in zip(ch.late, ch.res)); oldr = sum(e == r for (e, f), r in zip(ch.late, ch.res))
    tests.append(("Late favourite changes: new favourite right more than old", f"new {newr} v old {oldr} of {len(ch)}", binomtest(newr, newr + oldr, 0.5).pvalue if newr + oldr else 1.0))
# results-only slates too (94 games): H/D/A split and goals
fi = []
for p in sorted(glob.glob("data/fixture_intelligence/*.json")):
    d = json.load(open(p, encoding="utf-8")); fx = d if isinstance(d, list) else d.get("fixtures", d)
    for f in fx:
        fi.append({"res": {"Home": 0, "Draw": 1, "Away": 2}[f["actual_result"]], "score": f.get("actual_score"), "time": f.get("kickoff_time"), "date": f.get("kickoff_date")})
allres = list(df.res) + [x["res"] for x in fi]
cnt = np.bincount(allres, minlength=3)
tests.append(("All 94 games: H/D/A split unusual v normal football (46/26/28%)", f"H {cnt[0]} D {cnt[1]} A {cnt[2]}", chisquare(cnt, np.array([0.46, 0.26, 0.28]) * len(allres)).pvalue))
goals = []
for sc in list(df.score.dropna()) + [x["score"] for x in fi if x["score"]]:
    a, b = sc.replace(":", "-").split("-"); goals.append(int(a) + int(b))
goals = np.array(goals)
tests.append((f"Goals per game ({len(goals)} games with scores) v typical 2.7", f"{goals.mean():.2f} per game", 2 * norm.sf(abs(goals.mean() - 2.7) / (goals.std(ddof=1) / math.sqrt(len(goals))))))
# upsets per card
per_card = df.groupby("slate").apply(lambda g: ((g.fav != g.res).sum(), (1 - g.fav_p).sum()))
print("Upsets per card (actual v expected):", {k: (int(v[0]), round(v[1], 1)) for k, v in per_card.items()})
print(f"\n{'Pattern tested':<66} {'What happened':<26} p-value   verdict")
m_tests = len(tests)
for name, what, p in tests:
    verdict = "REAL (survives correction)" if p < 0.05 / m_tests else ("hint only (luck likely)" if p < 0.05 else "noise")
    print(f"{name:<66} {what:<26} {p:7.3f}   {verdict}")
print(f"\n{m_tests} patterns tested; a pattern must reach p < {0.05/m_tests:.4f} to count after correcting for testing many ideas at once.")
