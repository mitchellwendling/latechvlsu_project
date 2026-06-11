"""Fetch live flight prices from Kiwi.com Tequila and append snapshots.

Setup (once):
  1. Sign up at https://tequila.kiwi.com
  2. Create a "Search API" solution -> copy API key
  3. export KIWI_API_KEY=your_key

Run anytime:
  python3 flights_kiwi.py

Appends one flight_snapshot row per offer (up to 10). The dashboard
picks them up automatically.
"""
import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from db import init_db, conn, insert_flight

SEARCH_URL = "https://api.tequila.kiwi.com/v2/search"

# Kiwi expects dates in DD/MM/YYYY format.
ORIGIN = "CVG"
DESTINATION = "BTR"
DEPART_DATE = "11/09/2026"
RETURN_DATE = "13/09/2026"
ADULTS = 1
MAX_RESULTS = 10


def search(api_key):
    params = {
        "fly_from": ORIGIN,
        "fly_to": DESTINATION,
        "date_from": DEPART_DATE,
        "date_to": DEPART_DATE,
        "return_from": RETURN_DATE,
        "return_to": RETURN_DATE,
        "adults": ADULTS,
        "curr": "USD",
        "limit": MAX_RESULTS,
        "sort": "price",
        "max_stopovers": 2,
    }
    req = Request(f"{SEARCH_URL}?{urlencode(params)}")
    req.add_header("apikey", api_key)
    req.add_header("User-Agent", "LATechVsLSU-Dashboard/1.0")
    with urlopen(req, timeout=30) as r:
        return json.load(r)


def parse_offer(offer):
    routes = offer.get("route", [])
    if not routes:
        return None

    outbound = [r for r in routes if r.get("return") == 0]
    inbound = [r for r in routes if r.get("return") == 1]
    if not outbound or not inbound:
        return None

    def stops_list(legs):
        return ", ".join(legs[i].get("flyTo", "") for i in range(len(legs) - 1))

    def fmt_time(ts):
        # Kiwi gives local-time strings like "2026-09-11T17:14:00.000Z"
        return ts[:16].replace("T", " ") if ts else ""

    airline_code = outbound[0].get("airline", "")
    airline_name = offer.get("airlines", [airline_code])[0] if offer.get("airlines") else airline_code

    return {
        "airline": airline_name,
        "stops": max(len(outbound) - 1, len(inbound) - 1),
        "out_depart": fmt_time(outbound[0].get("local_departure")),
        "out_arrive": fmt_time(outbound[-1].get("local_arrival")),
        "ret_depart": fmt_time(inbound[0].get("local_departure")),
        "ret_arrive": fmt_time(inbound[-1].get("local_arrival")),
        "duration_out": "",
        "duration_ret": "",
        "layover_out": stops_list(outbound),
        "layover_ret": stops_list(inbound),
        "fare_name": "Economy",
        "total_price": float(offer.get("price", 0)),
    }


def snapshot():
    api_key = os.environ.get("KIWI_API_KEY")
    if not api_key:
        print("ERROR: set KIWI_API_KEY env var first.", file=sys.stderr)
        print("  export KIWI_API_KEY=your_key", file=sys.stderr)
        print("  Get one at https://tequila.kiwi.com", file=sys.stderr)
        sys.exit(1)

    print(f"Searching flights {ORIGIN} -> {DESTINATION}, {DEPART_DATE} / {RETURN_DATE}...")
    data = search(api_key)
    offers = data.get("data", [])
    if not offers:
        print("No flight offers returned. Full response head:", file=sys.stderr)
        print(json.dumps(data)[:500], file=sys.stderr)
        sys.exit(2)

    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    init_db()
    count = 0
    prices = []
    with conn() as c:
        for offer in offers:
            parsed = parse_offer(offer)
            if parsed:
                insert_flight(c, captured_at, parsed)
                prices.append(parsed["total_price"])
                count += 1

    print(f"Logged {count} flights at {captured_at}")
    if prices:
        print(f"Cheapest: ${min(prices):.2f} | Most expensive: ${max(prices):.2f}")


if __name__ == "__main__":
    snapshot()
