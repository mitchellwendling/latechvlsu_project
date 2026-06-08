"""Fetch live SeatGeek prices for LSU vs LA Tech and append a snapshot.

Setup (once):
  1. Sign up at https://seatgeek.com/account/develop
  2. Create an app -> copy the "Client ID"
  3. export SEATGEEK_CLIENT_ID=your_client_id_here

Run anytime:
  python3 tickets_seatgeek.py

This appends a ticket_snapshot row with the current lowest listing price,
average price, and listing count. The dashboard will pick it up automatically.
"""
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import urlopen
import json

from db import init_db, conn, insert_ticket

API = "https://api.seatgeek.com/2/events"
QUERY = "LSU Louisiana Tech"
DATE_FROM = "2026-09-12"
DATE_TO = "2026-09-13"


def find_event(client_id):
    params = {
        "client_id": client_id,
        "q": QUERY,
        "datetime_local.gte": DATE_FROM,
        "datetime_local.lte": DATE_TO,
        "per_page": 5,
    }
    with urlopen(f"{API}?{urlencode(params)}", timeout=15) as r:
        data = json.load(r)
    events = data.get("events", [])
    if not events:
        return None
    # Prefer events whose title mentions both teams.
    for e in events:
        title = e.get("title", "").lower()
        if "lsu" in title and ("louisiana tech" in title or "la tech" in title):
            return e
    return events[0]


def snapshot():
    client_id = os.environ.get("SEATGEEK_CLIENT_ID")
    if not client_id:
        print("ERROR: set SEATGEEK_CLIENT_ID env var first.", file=sys.stderr)
        print("  export SEATGEEK_CLIENT_ID=your_client_id", file=sys.stderr)
        print("  Get one at https://seatgeek.com/account/develop", file=sys.stderr)
        sys.exit(1)

    event = find_event(client_id)
    if not event:
        print(f"No SeatGeek event found for '{QUERY}' on {DATE_FROM}.", file=sys.stderr)
        sys.exit(2)

    stats = event.get("stats") or {}
    lowest = stats.get("lowest_price")
    if lowest is None:
        print(f"Event found ({event.get('title')}) but no lowest_price yet.", file=sys.stderr)
        sys.exit(3)

    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    init_db()
    with conn() as c:
        insert_ticket(c, captured_at, {
            "source": "SeatGeek",
            "section": "Get-in (cheapest listing)",
            "get_in_price": float(lowest),
            "listing_count": stats.get("listing_count"),
            "note": (f"avg ${stats.get('average_price')}, "
                     f"median ${stats.get('median_price')}, "
                     f"{stats.get('listing_count')} listings"),
            "listing_url": event.get("url"),
        })
    print(f"Logged SeatGeek snapshot at {captured_at}: "
          f"${lowest} get-in, {stats.get('listing_count')} listings")
    print(f"Event: {event.get('title')} - {event.get('datetime_local')}")


if __name__ == "__main__":
    snapshot()
