"""Live Betika and SportPesa feed adapters.

These adapters intentionally keep source-specific parsing here so the Streamlit
pages can consume one stable schema. The feeds are public website endpoints,
not an official prediction or betting API; callers must handle source errors.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json
from zoneinfo import ZoneInfo

import pandas as pd


NAIROBI = ZoneInfo("Africa/Nairobi")
BETIKA_MATCHES_URL = (
    "https://api.betika.com/v1/uo/matches?"
    "page=1&limit=1000&tab=&sub_type_id=1,186,340&sport_id=14&"
    "sort_id=1&period_id=-1&esports=false"
)
SPORTPESA_JACKPOT_URL = "https://jackpot-offer-api.ke.sportpesa.com/api/jackpots/active"


class FeedError(RuntimeError):
    """Raised when a live source cannot be fetched or validated."""


def _get_json(url: str, headers: Optional[Dict[str, str]] = None) -> Any:
    request_headers = {
        "Accept": "application/json",
        "User-Agent": "FootballMatchIntelligence/1.0",
    }
    if headers:
        request_headers.update(headers)
    request = Request(url, headers=request_headers)
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise FeedError(f"HTTP {error.code} while fetching {url}") from error
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        raise FeedError(f"Could not fetch valid JSON from {url}: {error}") from error


def _today_nairobi(now: Optional[datetime] = None) -> pd.Timestamp:
    current = now.astimezone(NAIROBI) if now else datetime.now(NAIROBI)
    return pd.Timestamp(current.date()).tz_localize(NAIROBI)


def _parse_utc(value: str) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    return timestamp.tz_convert(NAIROBI)


def fetch_betika_daily_matches(now: Optional[datetime] = None) -> pd.DataFrame:
    """Fetch Betika football fixtures whose Nairobi kickoff date is today."""
    payload = _get_json(BETIKA_MATCHES_URL)
    records = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(records, list):
        raise FeedError("Betika response did not contain a data list")

    today = _today_nairobi(now)
    rows: List[Dict[str, Any]] = []
    for item in records:
        if not isinstance(item, dict):
            continue
        start = item.get("start_time")
        if not start:
            continue
        kickoff = pd.Timestamp(start)
        if kickoff.tzinfo is None:
            kickoff = kickoff.tz_localize(NAIROBI)
        else:
            kickoff = kickoff.tz_convert(NAIROBI)
        if kickoff.normalize() != today:
            continue
        rows.append(
            {
                "source": "Betika",
                "match_id": str(item.get("match_id") or item.get("game_id") or ""),
                "kickoff": kickoff,
                "competition": item.get("competition_name") or "Unknown competition",
                "country": item.get("category") or "",
                "home_team": item.get("home_team") or "Unknown home team",
                "away_team": item.get("away_team") or "Unknown away team",
                "home_odds": _number(item.get("home_odd")),
                "draw_odds": _number(item.get("neutral_odd")),
                "away_odds": _number(item.get("away_odd")),
                "status": "scheduled",
            }
        )
    return pd.DataFrame(rows).sort_values("kickoff").reset_index(drop=True) if rows else _match_columns()


def fetch_sportpesa_jackpot() -> Dict[str, Any]:
    """Fetch the active SportPesa jackpot card and prize metadata."""
    payload = _get_json(
        SPORTPESA_JACKPOT_URL,
        headers={
            "Origin": "https://jackpot-widget.ke.sportpesa.com",
            "Referer": "https://jackpot-widget.ke.sportpesa.com/",
        },
    )
    if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
        raise FeedError("SportPesa response did not contain an events list")

    events = []
    for item in payload["events"]:
        competitors = item.get("competitors") or []
        if len(competitors) < 2:
            continue
        home = next((c for c in competitors if c.get("isHome")), competitors[0])
        away = next((c for c in competitors if not c.get("isHome")), competitors[1])
        score = item.get("score") or {}
        events.append(
            {
                "number": item.get("order"),
                "match_id": item.get("id"),
                "kickoff": _parse_utc(item["utcKickOffTime"]),
                "competition": item.get("tournamentName") or "",
                "country": item.get("countryName") or "",
                "home_team": home.get("competitorName") or "Unknown home team",
                "away_team": away.get("competitorName") or "Unknown away team",
                "home_odds": _number(item.get("home")),
                "draw_odds": _number(item.get("draw")),
                "away_odds": _number(item.get("away")),
                "status": item.get("bettingStatus") or ("finished" if score else "scheduled"),
                "home_score": score.get("home"),
                "away_score": score.get("away"),
            }
        )

    return {
        "source": "SportPesa",
        "jackpot_id": payload.get("id"),
        "human_id": payload.get("humanId"),
        "betting_status": payload.get("bettingStatus"),
        "number_of_events": payload.get("settings", {}).get("numberOfEvents"),
        "events": events,
        "settings": payload.get("settings", {}),
    }


def _number(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _match_columns() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "source", "match_id", "kickoff", "competition", "country",
            "home_team", "away_team", "home_odds", "draw_odds", "away_odds", "status",
        ]
    )
