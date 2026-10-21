"""SportPesa Mega Jackpot Pro archive (every card since Dec 2022) joined to bookmaker odds.

The archive (data/sportpesa_archive/mega_archive.json, read from the jackpot widget's history
feed) has teams, kickoff, score and the prize/winner counts per tier, but no odds. Each game is
matched to a football-data.co.uk row by date (within a day), identical score and team-name
similarity, which gives the pre-match and closing average odds for the leagues that site covers.

Run: python -m src.sportpesa_archive
"""
import difflib
import glob
import json
import os
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
ARCHIVE = ROOT / "data" / "sportpesa_archive" / "mega_archive.json"
ODDS_DIR = ROOT / "data" / "football_data"
OUT_CSV = ROOT / "data" / "sportpesa_archive" / "mega_games.csv"
TIERS = {"Jackpot": 17, "Category1": 16, "Category2": 15, "Category3": 14, "Category4": 13, "Category5": 12}
PICK = {"Home": "H", "Draw": "D", "Away": "A"}
NOISE = {"fc", "afc", "cf", "sc", "ac", "as", "fk", "sk", "if", "bk", "club", "de", "cd", "ud", "sd", "rc",
         "calcio", "1905", "1912", "the", "of", "city", "town", "united", "utd", "athletic", "sporting",
         "real", "ssd", "us", "ss", "asd", "ca", "cs", "fsv", "vfl", "vfb", "tsv", "sv", "spvgg", "kv",
         "krc", "rsc", "royal", "sco", "ogc", "aj", "ea", "sm", "bb", "rcd", "afc", "aik", "ik", "ff",
         "olympique", "stade", "racing", "county", "rovers", "wanderers", "albion", "f.c.", "c.f."}


def load_archive(path: Path = ARCHIVE) -> tuple:
    """(games, cards): one row per jackpot game; one row per card with crowd winner counts."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    games, cards = [], []
    for j in raw:
        for n, kick, home, away, pick, score in j["e"]:
            # "PD:1" / "PD:X" / "PD:2" = postponed, settled by the operator's rule, not on the pitch
            postponed = score.startswith("PD")
            hg, ag = (np.nan, np.nan) if postponed else (int(x) for x in score.split(":"))
            games.append({"card": j["h"], "n": n, "kickoff": pd.Timestamp(kick), "home": home, "away": away,
                          "result": PICK[pick], "hg": hg, "ag": ag, "postponed": postponed})
        row = {"card": j["h"], "finished": pd.Timestamp(j["f"]),
               "pool_17": dict(j["p"]).get("17/17")}
        for cat, prize, count, amount in j["w"].get("17/17", []):
            row[f"winners_{TIERS[cat]}"] = count
            row[f"paid_{TIERS[cat]}"] = amount
        cards.append(row)
    games = pd.DataFrame(games)
    games["kickoff_eat"] = games["kickoff"].dt.tz_convert("Africa/Nairobi")
    return games, pd.DataFrame(cards)


def _clean(name: str) -> str:
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    words = [w for w in s.split() if w not in NOISE and not re.fullmatch(r"\d{4}", w)]
    return " ".join(words) or s.strip()


def similarity(a: str, b: str) -> float:
    """Name similarity in [0, 1]: best of whole-string ratio and word containment."""
    a, b = _clean(a), _clean(b)
    if not a or not b:
        return 0.0
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    wa, wb = set(a.split()), set(b.split())
    contain = len(wa & wb) / min(len(wa), len(wb))
    prefix = 1.0 if a.startswith(b) or b.startswith(a) else 0.0
    return max(ratio, contain, 0.9 * prefix)


def _devig(h, d, a):
    inv = 1 / np.column_stack([h, d, a]).astype(float)
    return inv / inv.sum(axis=1, keepdims=True)


def load_odds(directory: Path = ODDS_DIR) -> pd.DataFrame:
    """Every football-data match since mid-2022 with opening and closing average odds."""
    frames = []
    for p in glob.glob(str(directory / "*.csv")):
        name = os.path.basename(p)[:-4]
        df = pd.read_csv(p, encoding="utf-8-sig", encoding_errors="replace", on_bad_lines="skip", low_memory=False)
        g = df.get
        if name.startswith("new_"):
            if not {"Home", "Away", "HG", "AG"} <= set(df.columns):
                continue
            frames.append(pd.DataFrame({
                "league": df["Country"].astype(str) + " " + df["League"].astype(str), "date": df["Date"],
                "fd_home": df["Home"], "fd_away": df["Away"], "fhg": df["HG"], "fag": df["AG"],
                "oh": np.nan, "od": np.nan, "oa": np.nan,
                "ch": g("AvgCH"), "cd": g("AvgCD"), "ca": g("AvgCA"),
                "over": np.nan, "under": np.nan}))
        elif {"HomeTeam", "AwayTeam", "FTHG", "FTAG"} <= set(df.columns):
            frames.append(pd.DataFrame({
                "league": name.split("_")[0], "date": df["Date"], "fd_home": df["HomeTeam"],
                "fd_away": df["AwayTeam"], "fhg": df["FTHG"], "fag": df["FTAG"],
                "oh": g("AvgH"), "od": g("AvgD"), "oa": g("AvgA"),
                "ch": g("AvgCH"), "cd": g("AvgCD"), "ca": g("AvgCA"),
                "over": g("AvgC>2.5", g("Avg>2.5")), "under": g("AvgC<2.5", g("Avg<2.5"))}))
    d = pd.concat(frames, ignore_index=True)
    d["date"] = pd.to_datetime(d["date"], dayfirst=True, errors="coerce")
    for c in ("fhg", "fag", "oh", "od", "oa", "ch", "cd", "ca", "over", "under"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d[d["date"] >= "2022-11-01"].dropna(subset=["date", "fhg", "fag"])
    return d.reset_index(drop=True)


def match_odds(games: pd.DataFrame, odds: pd.DataFrame, threshold: float = 0.6) -> pd.DataFrame:
    """Add the football-data row (league, odds) for each jackpot game that can be matched.
    A match needs the same score, a date within one day and both team names similar
    (the weaker name at least `threshold`)."""
    odds = odds.assign(day=odds["date"].dt.normalize())
    by_key = {k: v for k, v in odds.groupby(["fhg", "fag"])}
    rows = []
    for g in games.itertuples():
        cand = None if g.postponed else by_key.get((g.hg, g.ag))
        best, best_s, strong = None, 0.0, []
        if cand is not None:
            day = g.kickoff.tz_convert(None).normalize()
            near = cand[(cand["day"] - pd.Timestamp(day)).abs() <= pd.Timedelta(days=1)]
            for r in near.itertuples():
                sh, sa = similarity(g.home, r.fd_home), similarity(g.away, r.fd_away)
                if min(sh, sa) > best_s:
                    best, best_s = r, min(sh, sa)
                if max(sh, sa) >= 0.85 and min(sh, sa) >= 0.3:
                    strong.append((r, min(sh, sa)))
        if best_s < threshold and len(strong) == 1:
            # same score, same day, one name clearly the same and the other plausible (Wolves,
            # Espanol, M'gladbach...): accept when no other fixture that day fits that well
            best, best_s = strong[0]
        if best is not None and (best_s >= threshold or len(strong) == 1):
            rows.append({"league": best.league, "fd_home": best.fd_home, "fd_away": best.fd_away,
                         "match_score": round(best_s, 3), "oh": best.oh, "od": best.od, "oa": best.oa,
                         "ch": best.ch, "cd": best.cd, "ca": best.ca, "over": best.over, "under": best.under})
        else:
            rows.append({"league": None, "match_score": round(best_s, 3)})
    cols = ["league", "fd_home", "fd_away", "match_score", "oh", "od", "oa", "ch", "cd", "ca", "over", "under"]
    out = pd.concat([games.reset_index(drop=True), pd.DataFrame(rows).reindex(columns=cols)], axis=1)
    for c in cols[4:]:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    # closing odds where present, else the pre-match average
    use_close = out[["ch", "cd", "ca"]].notna().all(axis=1) & (out[["ch", "cd", "ca"]] > 1.01).all(axis=1)
    h = np.where(use_close, out["ch"], out["oh"])
    d = np.where(use_close, out["cd"], out["od"])
    a = np.where(use_close, out["ca"], out["oa"])
    ok = ~(np.isnan(h.astype(float)) | np.isnan(d.astype(float)) | np.isnan(a.astype(float)))
    p = np.full((len(out), 3), np.nan)
    p[ok] = _devig(h[ok], d[ok], a[ok])
    out["pH"], out["pD"], out["pA"] = p.T
    out["has_odds"] = ok
    po = np.full((len(out), 3), np.nan)
    ok_open = out[["oh", "od", "oa"]].notna().all(axis=1).values
    po[ok_open] = _devig(out.loc[ok_open, "oh"], out.loc[ok_open, "od"], out.loc[ok_open, "oa"])
    out["oH"], out["oD"], out["oA"] = po.T
    out["pU"] = (1 / out["under"]) / (1 / out["under"] + 1 / out["over"])
    probs = out[["pH", "pD", "pA"]].values
    fav = np.where(ok, np.nanargmax(np.where(ok[:, None], probs, 0), axis=1), -1)
    out["fav"] = np.where(ok, np.array(list("HDA"))[np.clip(fav, 0, 2)], None)
    out["fav_p"] = np.where(ok, np.nanmax(np.where(ok[:, None], probs, 0), axis=1), np.nan)
    order = np.argsort(-np.where(ok[:, None], probs, 0), axis=1)
    out["second"] = np.where(ok, np.array(list("HDA"))[order[:, 1]], None)
    out["third"] = np.where(ok, np.array(list("HDA"))[order[:, 2]], None)
    return out


def build(save: bool = True) -> tuple:
    games, cards = load_archive()
    games = match_odds(games, load_odds())
    if save:
        games.drop(columns=["kickoff"]).to_csv(OUT_CSV, index=False)
    return games, cards


def merge_dumps(paths, archive: Path = ARCHIVE) -> int:
    """Add cards from saved browser dumps ('SPCHUNK<k>|<length>|<json list of compact cards>', as
    written by the widget-page script) to the archive; a card already there is replaced. Returns
    how many cards the archive holds afterwards."""
    cards = {c["h"]: c for c in json.loads(Path(archive).read_text(encoding="utf-8"))} if Path(archive).exists() else {}
    for p in paths:
        raw = json.loads(Path(p).read_text(encoding="utf-8"))
        text = "".join(x.get("text", "") for x in raw if x.get("type") == "text") if isinstance(raw, list) else raw
        text = text.strip()
        if text.startswith('"'):
            text = json.JSONDecoder().raw_decode(text)[0]
        m = re.search(r"SPCHUNK\d*\|(\d+)\|", text)
        payload = text[m.end():m.end() + int(m.group(1))]
        for c in json.loads(payload):
            cards[c["h"]] = c
    Path(archive).write_text(json.dumps([cards[k] for k in sorted(cards)], ensure_ascii=False), encoding="utf-8")
    return len(cards)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(f"archive now holds {merge_dumps(sys.argv[1:])} cards")
    g, c = build()
    print(f"{len(g)} games on {g['card'].nunique()} cards; with odds {g['has_odds'].sum()} "
          f"({g['has_odds'].mean():.0%}); cards fully priced {(g.groupby('card')['has_odds'].all()).sum()}")
