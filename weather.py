"""National Weather Service forecast for Norman, OK. Free, no API key.

NWS only forecasts ~7 days out, so before T-7 we just show the upcoming
5-day Norman forecast (helpful climate context). Once inside the window, we
filter to days that bracket kickoff (Oct 16-18, 2026).

Result is cached to disk so the dashboard doesn't hit NWS on every render.
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

CACHE = Path(__file__).parent / ".cache_weather.json"
CACHE_TTL_SEC = 60 * 60  # 1 hour
HEADERS = {"User-Agent": "UKvsOU-Dashboard (contact: localhost)"}

# Norman, OK (near Oklahoma Memorial Stadium)
NORMAN_LAT = 35.2226
NORMAN_LON = -97.4395
GAME_DAYS = {"2026-10-16", "2026-10-17", "2026-10-18"}


def _fetch(url):
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=10) as r:
        return json.load(r)


def _normalize(p):
    return {
        "name": p.get("name"),
        "short": p.get("shortForecast"),
        "temp": f"{p.get('temperature')}{p.get('temperatureUnit', 'F')}",
        "wind": f"{p.get('windSpeed', '')} {p.get('windDirection', '')}".strip(),
        "icon": p.get("icon"),
        "start": p.get("startTime", "")[:10],
    }


def forecast():
    """Return {mode, label, periods: [...]} where mode is 'game' or 'preview'."""
    if CACHE.exists() and time.time() - CACHE.stat().st_mtime < CACHE_TTL_SEC:
        try:
            return json.loads(CACHE.read_text())
        except Exception:
            pass

    try:
        pt = _fetch(f"https://api.weather.gov/points/{NORMAN_LAT},{NORMAN_LON}")
        fc = _fetch(pt["properties"]["forecast"])
        all_periods = [_normalize(p) for p in fc["properties"]["periods"]]

        game_periods = [p for p in all_periods if p["start"] in GAME_DAYS]
        if game_periods:
            result = {
                "mode": "game",
                "label": "Game weekend forecast (Norman, OK)",
                "periods": game_periods,
            }
        else:
            # Outside NWS window - daytime-only preview so they fit on one row.
            daytime = [p for p in all_periods
                       if p.get("name") and "night" not in p["name"].lower()]
            result = {
                "mode": "preview",
                "label": "Norman, OK - next 5 days (game-day forecast available ~7 days before kickoff)",
                "periods": daytime[:5],
            }
        CACHE.write_text(json.dumps(result))
        return result
    except Exception as e:
        return {
            "mode": "error",
            "label": "Weather unavailable",
            "periods": [{"name": "NWS error", "short": str(e)[:80],
                         "temp": "", "wind": "", "icon": None, "start": ""}],
        }
