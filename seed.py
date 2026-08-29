"""Seed the price database with a starter snapshot for the Norman trip
(Kentucky @ Oklahoma, Oct 17, 2026) plus reasonable ticket estimates.

NOTE: The flight (CVG->DFW) and hotel numbers below are ESTIMATES entered
by hand while the Expedia live pull was unavailable. Refresh them with real
figures anytime by editing the FLIGHTS / HOTELS lists (or via the in-app log
forms) and rerunning this script. History accumulates so the dashboard can
chart price movement toward kickoff.
"""
import math
import sys
from datetime import datetime, timezone

from db import init_db, conn, insert_flight, insert_hotel, insert_ticket

# Gaylord Family Oklahoma Memorial Stadium, Norman, OK
STADIUM_LAT, STADIUM_LON = 35.2058, -97.4422


def haversine_miles(lat1, lon1, lat2, lon2):
    r = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * r * math.asin(math.sqrt(a)), 2)


# ESTIMATES (CVG->DFW round trip, 10/16-10/18, 1 adult) - refresh from Expedia.
# Note: DFW is ~190 mi / ~3 hrs from Norman; plan a rental car for the drive.
FLIGHTS = [
    {"airline": "American", "stops": 0, "out_depart": "2026-10-16 8:15 AM",
     "out_arrive": "2026-10-16 9:52 AM", "ret_depart": "2026-10-18 6:40 PM",
     "ret_arrive": "2026-10-18 9:59 PM", "duration_out": "2h 37m",
     "duration_ret": "2h 19m", "layover_out": "", "layover_ret": "",
     "fare_name": "Main Cabin (est.)", "total_price": 258.0},
    {"airline": "American", "stops": 0, "out_depart": "2026-10-16 5:30 PM",
     "out_arrive": "2026-10-16 7:07 PM", "ret_depart": "2026-10-18 12:15 PM",
     "ret_arrive": "2026-10-18 3:34 PM", "duration_out": "2h 37m",
     "duration_ret": "2h 19m", "layover_out": "", "layover_ret": "",
     "fare_name": "Main Cabin (est.)", "total_price": 274.0},
    {"airline": "Delta", "stops": 1, "out_depart": "2026-10-16 7:05 AM",
     "out_arrive": "2026-10-16 11:20 AM", "ret_depart": "2026-10-18 4:10 PM",
     "ret_arrive": "2026-10-18 10:05 PM", "duration_out": "5h 15m",
     "duration_ret": "4h 55m", "layover_out": "1h 10m ATL",
     "layover_ret": "1h 20m ATL", "fare_name": "Main Cabin (est.)", "total_price": 297.0},
    {"airline": "United", "stops": 1, "out_depart": "2026-10-16 6:00 AM",
     "out_arrive": "2026-10-16 10:35 AM", "ret_depart": "2026-10-18 3:25 PM",
     "ret_arrive": "2026-10-18 9:40 PM", "duration_out": "5h 35m",
     "duration_ret": "5h 15m", "layover_out": "1h 25m ORD",
     "layover_ret": "1h 30m IAH", "fare_name": "Economy (est.)", "total_price": 318.0},
]

# ESTIMATES - Marriott-brand properties in Norman, OK, near the stadium.
# Prices are game-weekend guesses; refresh from Expedia for live rates.
HOTELS = [
    {"hotel_id": "est-courtyard-nor",
     "hotel_name": "Courtyard by Marriott Oklahoma City Norman",
     "star_rating": 3.0, "guest_rating": None, "review_count": None,
     "avg_nightly_price": 189, "total_price": 378,
     "latitude": 35.2163, "longitude": -97.4785,
     "booking_url": "https://www.marriott.com/en-us/hotels/okccn-courtyard-oklahoma-city-norman/"},
    {"hotel_id": "est-residence-nor",
     "hotel_name": "Residence Inn by Marriott Oklahoma City Norman",
     "star_rating": 3.0, "guest_rating": None, "review_count": None,
     "avg_nightly_price": 209, "total_price": 418,
     "latitude": 35.2185, "longitude": -97.4790,
     "booking_url": "https://www.marriott.com/en-us/hotels/okcnr-residence-inn-oklahoma-city-norman/"},
    {"hotel_id": "est-fairfield-nor",
     "hotel_name": "Fairfield Inn & Suites by Marriott Oklahoma City Norman",
     "star_rating": 2.5, "guest_rating": None, "review_count": None,
     "avg_nightly_price": 169, "total_price": 338,
     "latitude": 35.2090, "longitude": -97.4770,
     "booking_url": "https://www.marriott.com/en-us/hotels/okcfn-fairfield-inn-and-suites-oklahoma-city-norman/"},
]

# Estimated ticket "get-in" prices for Oklahoma vs Kentucky (SEC conference game).
# Replace with real numbers from SeatGeek/StubHub when you check.
TICKETS = [
    {"source": "SeatGeek", "section": "Upper level (get-in)",
     "get_in_price": 95.0, "listing_count": None,
     "note": "Estimate - check SeatGeek for live get-in price",
     "listing_url": "https://seatgeek.com/search?search=Oklahoma+Kentucky+October+17"},
    {"source": "StubHub", "section": "Upper level (get-in)",
     "get_in_price": 110.0, "listing_count": None,
     "note": "Estimate - StubHub typically runs a few dollars above SeatGeek",
     "listing_url": "https://www.stubhub.com/find/s/?q=Oklahoma+Kentucky"},
    {"source": "Vivid Seats", "section": "Upper level (get-in)",
     "get_in_price": 102.0, "listing_count": None,
     "note": "Estimate - SEC conference matchup pricing",
     "listing_url": "https://www.vividseats.com/search?searchTerm=Oklahoma+Kentucky"},
]


ALL_DATASETS = ("flights", "hotels", "tickets")


def run(datasets=ALL_DATASETS, captured_at=None):
    captured_at = captured_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    init_db()
    counts = []
    with conn() as c:
        if "flights" in datasets:
            for f in FLIGHTS:
                insert_flight(c, captured_at, f)
            counts.append(f"{len(FLIGHTS)} flights")
        if "hotels" in datasets:
            for h in HOTELS:
                h = dict(h)
                h["distance_to_stadium_mi"] = haversine_miles(
                    h["latitude"], h["longitude"], STADIUM_LAT, STADIUM_LON
                )
                insert_hotel(c, captured_at, h)
            counts.append(f"{len(HOTELS)} hotels")
        if "tickets" in datasets:
            for t in TICKETS:
                insert_ticket(c, captured_at, t)
            counts.append(f"{len(TICKETS)} ticket sources")
    print(f"Seeded snapshot at {captured_at}: {', '.join(counts)}")


if __name__ == "__main__":
    # Usage: python3 seed.py [flights] [hotels] [tickets]
    # No args = seed everything.
    args = [a.lower() for a in sys.argv[1:]]
    chosen = [d for d in ALL_DATASETS if d in args] or ALL_DATASETS
    bad = [a for a in args if a not in ALL_DATASETS]
    if bad:
        print(f"Unknown dataset(s): {', '.join(bad)}. "
              f"Valid options: {', '.join(ALL_DATASETS)}", file=sys.stderr)
        sys.exit(1)
    run(chosen)
