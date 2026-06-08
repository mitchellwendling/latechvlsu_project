"""Fetch kickoff time and TV network from ESPN's public scoreboard endpoint.

No API key; the path is the same one ESPN.com uses client-side. The dashboard
caches the response on disk so we don't hammer ESPN on every render.
"""
import json
import time
from pathlib import Path
from urllib.request import Request, urlopen

CACHE = Path(__file__).parent / ".cache_game.json"
CACHE_TTL_SEC = 6 * 60 * 60  # 6 hours
URL = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard?dates=20260912&groups=80"
HEADERS = {"User-Agent": "LATechVsLSU-Dashboard/1.0"}


def _fetch():
    req = Request(URL, headers=HEADERS)
    with urlopen(req, timeout=10) as r:
        return json.load(r)


def kickoff():
    """Return {kickoff, network, status, venue} or None on failure."""
    if CACHE.exists() and time.time() - CACHE.stat().st_mtime < CACHE_TTL_SEC:
        try:
            return json.loads(CACHE.read_text())
        except Exception:
            pass
    try:
        data = _fetch()
        for ev in data.get("events", []):
            name = ev.get("name", "").lower()
            if "lsu" in name and ("louisiana tech" in name or "la tech" in name):
                comp = (ev.get("competitions") or [{}])[0]
                broadcasts = comp.get("broadcasts") or []
                networks = []
                for b in broadcasts:
                    networks.extend(b.get("names") or [])
                result = {
                    "kickoff": ev.get("date"),
                    "network": ", ".join(networks) if networks else "TBA",
                    "status": (ev.get("status") or {}).get("type", {}).get("description"),
                    "venue": (comp.get("venue") or {}).get("fullName"),
                }
                CACHE.write_text(json.dumps(result))
                return result
        return None
    except Exception:
        return None
