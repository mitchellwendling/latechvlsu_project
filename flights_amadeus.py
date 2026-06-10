"""Fetch live flight prices from Amadeus (CVG -> BTR) and append a snapshot.

Setup (once):
  1. Sign up at https://developers.amadeus.com
  2. Create an app (Self-Service) -> copy API Key + API Secret
  3. export AMADEUS_API_KEY=your_key
     export AMADEUS_API_SECRET=your_secret

Run anytime:
  python3 flights_amadeus.py

Appends flight_snapshot rows for every offer returned. The dashboard
picks them up automatically.

Free tier: 2,000 API calls/month (more than enough for daily checks).
"""
import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from db import init_db, conn, insert_flight

AUTH_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
SEARCH_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"

ORIGIN = "CVG"
DESTINATION = "BTR"
DEPART_DATE = "2026-09-11"
RETURN_DATE = "2026-09-13"
ADULTS = 1
MAX_RESULTS = 10


def get_token(api_key, api_secret):
    body = urlencode({
        "grant_type": "client_credentials",
        "client_id": api_key,
        "client_secret": api_secret,
    }).encode()
    req = Request(AUTH_URL, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urlopen(req, timeout=15) as r:
        return json.load(r)["access_token"]


def search_flights(token):
    params = {
        "originLocationCode": ORIGIN,
        "destinationLocationCode": DESTINATION,
        "departureDate": DEPART_DATE,
        "returnDate": RETURN_DATE,
        "adults": ADULTS,
        "max": MAX_RESULTS,
        "currencyCode": "USD",
        "nonStop": "false",
    }
    req = Request(f"{SEARCH_URL}?{urlencode(params)}")
    req.add_header("Authorization", f"Bearer {token}")
    with urlopen(req, timeout=30) as r:
        return json.load(r)


def parse_segment(seg):
    dep = seg.get("departure", {})
    arr = seg.get("arrival", {})
    carrier = seg.get("carrierCode", "")
    return {
        "depart_airport": dep.get("iataCode"),
        "arrive_airport": arr.get("iataCode"),
        "depart_at": dep.get("at", ""),
        "arrive_at": arr.get("at", ""),
        "carrier": carrier,
        "flight_number": f"{carrier}{seg.get('number', '')}",
        "duration": seg.get("duration", ""),
    }


def format_duration(iso_dur):
    """PT5H14M -> 5h 14m"""
    if not iso_dur:
        return ""
    d = iso_dur.replace("PT", "").replace("H", "h ").replace("M", "m").strip()
    return d


def parse_offer(offer, carriers):
    itineraries = offer.get("itineraries", [])
    if len(itineraries) < 2:
        return None

    out_it = itineraries[0]
    ret_it = itineraries[1]
    out_segs = [parse_segment(s) for s in out_it.get("segments", [])]
    ret_segs = [parse_segment(s) for s in ret_it.get("segments", [])]

    if not out_segs or not ret_segs:
        return None

    out_stops = len(out_segs) - 1
    ret_stops = len(ret_segs) - 1

    def layover_info(segs):
        if len(segs) <= 1:
            return ""
        parts = []
        for i in range(len(segs) - 1):
            parts.append(segs[i]["arrive_airport"])
        return ", ".join(parts)

    carrier_code = out_segs[0]["carrier"]
    airline = carriers.get(carrier_code, carrier_code)

    price_info = offer.get("price", {})
    total = float(price_info.get("grandTotal", price_info.get("total", 0)))

    return {
        "airline": airline,
        "stops": max(out_stops, ret_stops),
        "out_depart": out_segs[0]["depart_at"].replace("T", " "),
        "out_arrive": out_segs[-1]["arrive_at"].replace("T", " "),
        "ret_depart": ret_segs[0]["depart_at"].replace("T", " "),
        "ret_arrive": ret_segs[-1]["arrive_at"].replace("T", " "),
        "duration_out": format_duration(out_it.get("duration")),
        "duration_ret": format_duration(ret_it.get("duration")),
        "layover_out": layover_info(out_segs) if out_stops else "",
        "layover_ret": layover_info(ret_segs) if ret_stops else "",
        "fare_name": (offer.get("travelerPricings", [{}])[0]
                      .get("fareDetailsBySegment", [{}])[0]
                      .get("cabin", "ECONOMY")),
        "total_price": total,
    }


def snapshot():
    api_key = os.environ.get("AMADEUS_API_KEY")
    api_secret = os.environ.get("AMADEUS_API_SECRET")
    if not api_key or not api_secret:
        print("ERROR: set AMADEUS_API_KEY and AMADEUS_API_SECRET env vars first.",
              file=sys.stderr)
        print("  export AMADEUS_API_KEY=your_key", file=sys.stderr)
        print("  export AMADEUS_API_SECRET=your_secret", file=sys.stderr)
        print("  Sign up at https://developers.amadeus.com", file=sys.stderr)
        sys.exit(1)

    print("Authenticating with Amadeus...")
    token = get_token(api_key, api_secret)

    print(f"Searching flights {ORIGIN} -> {DESTINATION}, {DEPART_DATE} / {RETURN_DATE}...")
    data = search_flights(token)

    carriers = data.get("dictionaries", {}).get("carriers", {})
    offers = data.get("data", [])
    if not offers:
        print("No flight offers returned.", file=sys.stderr)
        sys.exit(2)

    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    init_db()
    count = 0
    with conn() as c:
        for offer in offers:
            parsed = parse_offer(offer, carriers)
            if parsed:
                insert_flight(c, captured_at, parsed)
                count += 1

    prices = sorted(
        [parse_offer(o, carriers)["total_price"]
         for o in offers if parse_offer(o, carriers)],
    )
    print(f"Logged {count} flights at {captured_at}")
    if prices:
        print(f"Cheapest: ${prices[0]:.2f} | Most expensive: ${prices[-1]:.2f}")


if __name__ == "__main__":
    snapshot()
