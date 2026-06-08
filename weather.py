"""National Weather Service forecast for Baton Rouge. Free, no API key.

NWS uses a two-step lookup: lat/lon -> gridpoint URL -> forecast.
Result is cached to disk so the dashboard doesn't hit NWS on every render.
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

CACHE = Path(__file__).parent / ".cache_weather.json"
CACHE_TTL_SEC = 60 * 60  # 1 hour
HEADERS = {"User-Agent": "LATechVsLSU-Dashboard (contact: localhost)"}

BATON_ROUGE_LAT = 30.4515
BATON_ROUGE_LON = -91.1871
GAME_DATE = "2026-09-12"
SHOW_WITHIN_DAYS = 10


def _fetch(url):
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=10) as r:
        return json.load(r)


def _days_until_game():
    game = datetime.fromisoformat(GAME_DATE).replace(tzinfo=timezone.utc)
    return (game - datetime.now(timezone.utc)).days


def forecast():
    """Return a list of {name, short, temp, wind, icon} for game day +/- 1 day, or None."""
    days_left = _days_until_game()
    if days_left < 0 or days_left > SHOW_WITHIN_DAYS:
        return None

    if CACHE.exists() and time.time() - CACHE.stat().st_mtime < CACHE_TTL_SEC:
        try:
            return json.loads(CACHE.read_text())
        except Exception:
            pass

    try:
        pt = _fetch(f"https://api.weather.gov/points/{BATON_ROUGE_LAT},{BATON_ROUGE_LON}")
        fc_url = pt["properties"]["forecast"]
        fc = _fetch(fc_url)
        periods = fc["properties"]["periods"]
        kept = []
        for p in periods:
            start = p.get("startTime", "")[:10]
            if start in {GAME_DATE,
                         "2026-09-11", "2026-09-13"}:
                kept.append({
                    "name": p.get("name"),
                    "short": p.get("shortForecast"),
                    "temp": f"{p.get('temperature')}{p.get('temperatureUnit', 'F')}",
                    "wind": f"{p.get('windSpeed', '')} {p.get('windDirection', '')}".strip(),
                    "icon": p.get("icon"),
                })
        CACHE.write_text(json.dumps(kept))
        return kept
    except Exception as e:
        return [{"name": "Forecast unavailable", "short": str(e)[:80], "temp": "", "wind": "", "icon": None}]
