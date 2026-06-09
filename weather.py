"""National Weather Service forecast for Baton Rouge. Free, no API key.

NWS only forecasts ~7 days out, so before T-7 we just show the upcoming
7-day BR forecast (helpful climate context). Once inside the window, we
filter to days that bracket kickoff (Sep 11-13, 2026).

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
GAME_DAYS = {"2026-09-11", "2026-09-12", "2026-09-13"}


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
        pt = _fetch(f"https://api.weather.gov/points/{BATON_ROUGE_LAT},{BATON_ROUGE_LON}")
        fc = _fetch(pt["properties"]["forecast"])
        all_periods = [_normalize(p) for p in fc["properties"]["periods"]]

        game_periods = [p for p in all_periods if p["start"] in GAME_DAYS]
        if game_periods:
            result = {
                "mode": "game",
                "label": "Game weekend forecast (Baton Rouge)",
                "periods": game_periods,
            }
        else:
            # Outside NWS window - daytime-only preview so they fit on one row.
            daytime = [p for p in all_periods
                       if p.get("name") and "night" not in p["name"].lower()]
            result = {
                "mode": "preview",
                "label": "Baton Rouge - next 7 days (game-day forecast available ~7 days before kickoff)",
                "periods": daytime[:7],
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
