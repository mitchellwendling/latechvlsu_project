"""Seed the price database with a real snapshot captured 2026-06-08
from Expedia (flights + Marriott hotels) and reasonable ticket estimates.

Rerun this script anytime to append a new snapshot - history accumulates
so the dashboard can chart price movement toward kickoff.
"""
import math
import sys
from datetime import datetime, timezone

from db import init_db, conn, insert_flight, insert_hotel, insert_ticket

# Tiger Stadium, Baton Rouge
STADIUM_LAT, STADIUM_LON = 30.4119, -91.1838


def haversine_miles(lat1, lon1, lat2, lon2):
    r = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * r * math.asin(math.sqrt(a)), 2)


# Captured 2026-06-10 via Expedia search_flights (CVG->BTR 9/11-9/13, 1 adult).
FLIGHTS = [
    {"airline": "United", "stops": 1, "out_depart": "2026-09-11 5:14 PM",
     "out_arrive": "2026-09-11 9:28 PM", "ret_depart": "2026-09-13 6:14 PM",
     "ret_arrive": "2026-09-13 11:59 PM", "duration_out": "5h 14m",
     "duration_ret": "4h 45m", "layover_out": "1h 23m IAH",
     "layover_ret": "41m IAH", "fare_name": "Basic Economy", "total_price": 308.40},
    {"airline": "United", "stops": 1, "out_depart": "2026-09-11 6:35 AM",
     "out_arrive": "2026-09-11 11:13 AM", "ret_depart": "2026-09-13 6:14 PM",
     "ret_arrive": "2026-09-13 11:59 PM", "duration_out": "5h 38m",
     "duration_ret": "4h 45m", "layover_out": "1h 48m IAH",
     "layover_ret": "41m IAH", "fare_name": "Basic Economy", "total_price": 340.27},
    {"airline": "American", "stops": 1, "out_depart": "2026-09-11 1:12 PM",
     "out_arrive": "2026-09-11 4:58 PM", "ret_depart": "2026-09-13 5:56 AM",
     "ret_arrive": "2026-09-13 2:14 PM", "duration_out": "4h 46m",
     "duration_ret": "7h 18m", "layover_out": "1h 1m CLT",
     "layover_ret": "3h 16m DFW", "fare_name": "Basic Economy", "total_price": 383.40},
    {"airline": "American", "stops": 1, "out_depart": "2026-09-11 6:00 AM",
     "out_arrive": "2026-09-11 10:51 AM", "ret_depart": "2026-09-13 5:56 AM",
     "ret_arrive": "2026-09-13 2:14 PM", "duration_out": "5h 51m",
     "duration_ret": "7h 18m", "layover_out": "1h 48m DFW",
     "layover_ret": "3h 16m DFW", "fare_name": "Basic Economy", "total_price": 383.40},
    {"airline": "United", "stops": 1, "out_depart": "2026-09-11 5:14 PM",
     "out_arrive": "2026-09-11 9:28 PM", "ret_depart": "2026-09-13 4:10 PM",
     "ret_arrive": "2026-09-13 11:59 PM", "duration_out": "5h 14m",
     "duration_ret": "6h 49m", "layover_out": "1h 23m IAH",
     "layover_ret": "2h 48m IAH", "fare_name": "Basic Economy", "total_price": 404.92},
    {"airline": "American", "stops": 1, "out_depart": "2026-09-11 1:12 PM",
     "out_arrive": "2026-09-11 4:58 PM", "ret_depart": "2026-09-13 8:15 AM",
     "ret_arrive": "2026-09-13 2:14 PM", "duration_out": "4h 46m",
     "duration_ret": "4h 59m", "layover_out": "1h 1m CLT",
     "layover_ret": "57m DFW", "fare_name": "Basic Economy", "total_price": 407.40},
]

# Captured 2026-06-08 via Expedia search_hotels, Marriott-brand properties only.
HOTELS = [
    {"hotel_id": "23356809",
     "hotel_name": "Courtyard by Marriott Baton Rouge Downtown",
     "star_rating": 3.0, "guest_rating": 8.8, "review_count": 627,
     "avg_nightly_price": 258, "total_price": 622,
     "latitude": 30.449163, "longitude": -91.188032,
     "booking_url": "https://www.expedia.com/.h23356809.Hotel-Information?chkin=2026-09-11&chkout=2026-09-13"},
    {"hotel_id": "1668442",
     "hotel_name": "Residence Inn by Marriott Baton Rouge near LSU",
     "star_rating": 3.0, "guest_rating": 8.8, "review_count": 288,
     "avg_nightly_price": 232, "total_price": 539,
     "latitude": 30.430536, "longitude": -91.117408,
     "booking_url": "https://www.expedia.com/.h1668442.Hotel-Information?chkin=2026-09-11&chkout=2026-09-13"},
    {"hotel_id": "66087376",
     "hotel_name": "Element by Marriott Baton Rouge South",
     "star_rating": 3.0, "guest_rating": 9.2, "review_count": 451,
     "avg_nightly_price": 229, "total_price": 534,
     "latitude": 30.397511, "longitude": -91.095729,
     "booking_url": "https://www.expedia.com/.h66087376.Hotel-Information?chkin=2026-09-11&chkout=2026-09-13"},
    {"hotel_id": "2780250",
     "hotel_name": "SpringHill Suites by Marriott Baton Rouge North/Airport",
     "star_rating": 3.0, "guest_rating": 8.8, "review_count": 1013,
     "avg_nightly_price": 116, "total_price": 271,
     "latitude": 30.521, "longitude": -91.156784,
     "booking_url": "https://www.expedia.com/.h2780250.Hotel-Information?chkin=2026-09-11&chkout=2026-09-13"},
]

# Estimated ticket "get-in" prices for LSU vs LA Tech (non-conference, early season).
# Replace with real numbers from SeatGeek/StubHub when you check.
TICKETS = [
    {"source": "SeatGeek", "section": "Upper deck (get-in)",
     "get_in_price": 38.0, "listing_count": None,
     "note": "Estimate - check SeatGeek for live get-in price",
     "listing_url": "https://seatgeek.com/search?search=LSU+Louisiana+Tech+September+12"},
    {"source": "StubHub", "section": "Upper deck (get-in)",
     "get_in_price": 45.0, "listing_count": None,
     "note": "Estimate - StubHub typically runs a few dollars above SeatGeek",
     "listing_url": "https://www.stubhub.com/find/s/?q=LSU+Louisiana+Tech"},
    {"source": "Vivid Seats", "section": "Upper deck (get-in)",
     "get_in_price": 42.0, "listing_count": None,
     "note": "Estimate - non-conference home opener pricing",
     "listing_url": "https://www.vividseats.com/search?searchTerm=LSU+Louisiana+Tech"},
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
