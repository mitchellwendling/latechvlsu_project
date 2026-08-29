"""Fetch live SeatGeek prices for Kentucky vs Oklahoma and append a snapshot.

Setup (once):
  1. Sign up at https://seatgeek.com/account/develop
  2. Create an app -> copy the "Client ID"
  3. export SEATGEEK_CLIENT_ID=your_client_id_here

Run anytime:
  python3 tickets_seatgeek.py

This appends a ticket_snapshot row with the current lowest listing price,
average price, and listing count. The dashboard will pick it up automatically.

Optional: set PRICE_ALERT_THRESHOLD (default 50) to fire a macOS notification
when the new get-in price is BOTH below the threshold AND a new all-time low.
"""
import os
import subprocess
import sys
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

from db import init_db, conn, insert_ticket

API = "https://api.seatgeek.com/2/events"
QUERY = "Oklahoma Kentucky"
DATE_FROM = "2026-10-17"
DATE_TO = "2026-10-18"
UA = "Mozilla/5.0 (compatible; UKvsOU-Dashboard/1.0)"


def find_event(client_id):
    params = {
        "client_id": client_id,
        "q": QUERY,
        "datetime_local.gte": DATE_FROM,
        "datetime_local.lte": DATE_TO,
        "per_page": 5,
    }
    req = Request(f"{API}?{urlencode(params)}", headers={"User-Agent": UA})
    with urlopen(req, timeout=15) as r:
        data = json.load(r)
    events = data.get("events", [])
    if not events:
        return None
    for e in events:
        title = e.get("title", "").lower()
        if "oklahoma" in title and "kentucky" in title:
            return e
    return events[0]


def previous_low():
    with conn() as c:
        row = c.execute(
            "SELECT MIN(get_in_price) AS p FROM ticket_snapshot WHERE source='SeatGeek'"
        ).fetchone()
    return row["p"] if row and row["p"] is not None else None


def mac_notify(title, message):
    """Best-effort macOS desktop notification. Silently no-ops on non-Mac."""
    if sys.platform != "darwin":
        return
    safe_msg = message.replace('"', '\\"')
    safe_title = title.replace('"', '\\"')
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{safe_msg}" with title "{safe_title}" sound name "Glass"'],
            check=False, timeout=5,
        )
    except Exception:
        pass


def snapshot():
    client_id = os.environ.get("SEATGEEK_CLIENT_ID")
    if not client_id:
        print("ERROR: set SEATGEEK_CLIENT_ID env var first.", file=sys.stderr)
        print("  export SEATGEEK_CLIENT_ID=your_client_id", file=sys.stderr)
        print("  Get one at https://seatgeek.com/account/develop", file=sys.stderr)
        sys.exit(1)

    threshold = float(os.environ.get("PRICE_ALERT_THRESHOLD", "50"))
    prev_low = previous_low()

    event = find_event(client_id)
    if not event:
        print(f"No SeatGeek event found for '{QUERY}' on {DATE_FROM}.", file=sys.stderr)
        sys.exit(2)

    stats = event.get("stats") or {}
    lowest = stats.get("lowest_price")
    if lowest is None:
        print(f"Event found ({event.get('title')}) but no lowest_price yet.", file=sys.stderr)
        sys.exit(3)

    lowest = float(lowest)
    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    init_db()
    with conn() as c:
        insert_ticket(c, captured_at, {
            "source": "SeatGeek",
            "section": "Get-in (cheapest listing)",
            "get_in_price": lowest,
            "listing_count": stats.get("listing_count"),
            "note": (f"avg ${stats.get('average_price')}, "
                     f"median ${stats.get('median_price')}, "
                     f"{stats.get('listing_count')} listings"),
            "listing_url": event.get("url"),
        })
    print(f"Logged SeatGeek snapshot at {captured_at}: "
          f"${lowest:.2f} get-in, {stats.get('listing_count')} listings")
    print(f"Event: {event.get('title')} - {event.get('datetime_local')}")

    is_new_low = prev_low is None or lowest < prev_low
    if is_new_low and lowest <= threshold:
        delta = f" (was ${prev_low:.2f})" if prev_low is not None else ""
        msg = f"Get-in ${lowest:.2f}{delta}. {stats.get('listing_count')} listings."
        mac_notify(f"Kentucky vs Oklahoma ticket drop - new low!", msg)
        print(f"ALERT fired: new low at ${lowest:.2f} (under threshold ${threshold:.0f})")
    elif is_new_low:
        print(f"New all-time low (${lowest:.2f}), but above alert threshold ${threshold:.0f}.")


if __name__ == "__main__":
    snapshot()

