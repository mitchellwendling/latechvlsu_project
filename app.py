"""Dashboard for the LSU vs LA Tech trip (Sep 12, 2026).
Tracks CVG->BTR flights, Marriott hotels near Tiger Stadium, and game tickets.
"""
from collections import defaultdict
from datetime import datetime, timezone

from flask import Flask, redirect, render_template, request, url_for

from db import init_db, conn, insert_flight, insert_hotel, insert_ticket
from trip import TRIP, TICKET_SOURCES
import weather
import game_info

app = Flask(__name__)


def latest_snapshot_at(table):
    with conn() as c:
        row = c.execute(f"SELECT MAX(captured_at) AS t FROM {table}").fetchone()
        return row["t"] if row else None


def fetch_latest(table, order_by):
    ts = latest_snapshot_at(table)
    if not ts:
        return [], None
    with conn() as c:
        rows = c.execute(
            f"SELECT * FROM {table} WHERE captured_at = ? ORDER BY {order_by}",
            (ts,),
        ).fetchall()
    return [dict(r) for r in rows], ts


def history_series(table, value_expr, label_col):
    """Return {label: [(captured_at, value), ...]} for charting min price over time."""
    with conn() as c:
        rows = c.execute(
            f"""SELECT captured_at, {label_col} AS label, MIN({value_expr}) AS v
                FROM {table}
                GROUP BY captured_at, {label_col}
                ORDER BY captured_at"""
        ).fetchall()
    series = defaultdict(list)
    for r in rows:
        series[r["label"]].append((r["captured_at"], r["v"]))
    return series


def overall_min_history(table, value_expr):
    with conn() as c:
        rows = c.execute(
            f"""SELECT captured_at, MIN({value_expr}) AS v
                FROM {table} GROUP BY captured_at ORDER BY captured_at"""
        ).fetchall()
    return [(r["captured_at"], r["v"]) for r in rows]


def days_until_game():
    game = datetime.fromisoformat(TRIP["game_date"]).replace(tzinfo=timezone.utc)
    return (game - datetime.now(timezone.utc)).days


@app.route("/")
def dashboard():
    flights, flights_ts = fetch_latest("flight_snapshot", "total_price ASC")
    hotels, hotels_ts = fetch_latest("hotel_snapshot", "distance_to_stadium_mi ASC")
    tickets, tickets_ts = fetch_latest("ticket_snapshot", "get_in_price ASC")

    return render_template(
        "dashboard.html",
        trip=TRIP,
        ticket_sources=TICKET_SOURCES,
        forecast=weather.forecast(),
        game=game_info.kickoff(),
        flights=flights,
        flights_ts=flights_ts,
        hotels=hotels,
        hotels_ts=hotels_ts,
        tickets=tickets,
        tickets_ts=tickets_ts,
        flight_history=overall_min_history("flight_snapshot", "total_price"),
        hotel_history_by_name=history_series(
            "hotel_snapshot", "avg_nightly_price", "hotel_name"
        ),
        ticket_history_by_source=history_series(
            "ticket_snapshot", "get_in_price", "source"
        ),
        days_left=days_until_game(),
        cheapest_flight=min((f["total_price"] for f in flights), default=None),
        cheapest_hotel=min((h["avg_nightly_price"] for h in hotels), default=None),
        cheapest_ticket=min((t["get_in_price"] for t in tickets), default=None),
    )


@app.route("/log/ticket", methods=["POST"])
def log_ticket():
    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with conn() as c:
        insert_ticket(c, captured_at, {
            "source": request.form["source"].strip(),
            "section": request.form.get("section", "").strip() or None,
            "get_in_price": float(request.form["price"]),
            "listing_count": int(request.form["count"]) if request.form.get("count") else None,
            "note": request.form.get("note", "").strip() or None,
            "listing_url": request.form.get("url", "").strip() or None,
        })
    return redirect(url_for("dashboard") + "#tickets")


@app.route("/log/flight", methods=["POST"])
def log_flight():
    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with conn() as c:
        insert_flight(c, captured_at, {
            "airline": request.form["airline"].strip(),
            "stops": int(request.form.get("stops", 0)),
            "out_depart": request.form.get("out_depart", "").strip() or None,
            "out_arrive": request.form.get("out_arrive", "").strip() or None,
            "ret_depart": request.form.get("ret_depart", "").strip() or None,
            "ret_arrive": request.form.get("ret_arrive", "").strip() or None,
            "duration_out": None, "duration_ret": None,
            "layover_out": None, "layover_ret": None,
            "fare_name": request.form.get("fare_name", "").strip() or None,
            "total_price": float(request.form["price"]),
            "booking_url": request.form.get("url", "").strip() or None,
        })
    return redirect(url_for("dashboard") + "#flights")


@app.route("/log/hotel", methods=["POST"])
def log_hotel():
    from seed import haversine_miles, STADIUM_LAT, STADIUM_LON
    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lat = float(request.form["latitude"]) if request.form.get("latitude") else None
    lon = float(request.form["longitude"]) if request.form.get("longitude") else None
    dist = (haversine_miles(lat, lon, STADIUM_LAT, STADIUM_LON)
            if lat is not None and lon is not None else None)
    nightly = float(request.form["nightly"])
    nights = (datetime.fromisoformat(TRIP["return_date"])
              - datetime.fromisoformat(TRIP["depart_date"])).days
    with conn() as c:
        insert_hotel(c, captured_at, {
            "hotel_id": request.form.get("hotel_id", "manual").strip() or "manual",
            "hotel_name": request.form["name"].strip(),
            "star_rating": float(request.form["stars"]) if request.form.get("stars") else None,
            "guest_rating": float(request.form["rating"]) if request.form.get("rating") else None,
            "review_count": int(request.form["reviews"]) if request.form.get("reviews") else None,
            "avg_nightly_price": nightly,
            "total_price": nightly * nights,
            "distance_to_stadium_mi": dist,
            "latitude": lat, "longitude": lon,
            "booking_url": request.form.get("url", "").strip() or None,
        })
    return redirect(url_for("dashboard") + "#hotels")


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5050, debug=True)
