"""SQLite layer. Stores price snapshots so we can chart history over time."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "prices.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS flight_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    captured_at TEXT NOT NULL,
    airline TEXT NOT NULL,
    stops INTEGER NOT NULL,
    out_depart TEXT,
    out_arrive TEXT,
    ret_depart TEXT,
    ret_arrive TEXT,
    duration_out TEXT,
    duration_ret TEXT,
    layover_out TEXT,
    layover_ret TEXT,
    fare_name TEXT,
    total_price REAL NOT NULL,
    booking_url TEXT
);

CREATE TABLE IF NOT EXISTS hotel_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    captured_at TEXT NOT NULL,
    hotel_id TEXT NOT NULL,
    hotel_name TEXT NOT NULL,
    star_rating REAL,
    guest_rating REAL,
    review_count INTEGER,
    avg_nightly_price REAL NOT NULL,
    total_price REAL NOT NULL,
    distance_to_stadium_mi REAL,
    latitude REAL,
    longitude REAL,
    booking_url TEXT
);

CREATE TABLE IF NOT EXISTS ticket_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    captured_at TEXT NOT NULL,
    source TEXT NOT NULL,
    section TEXT,
    get_in_price REAL NOT NULL,
    listing_count INTEGER,
    note TEXT,
    listing_url TEXT
);
"""


@contextmanager
def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init_db():
    with conn() as c:
        c.executescript(SCHEMA)


def insert_flight(c, captured_at, row):
    c.execute(
        """INSERT INTO flight_snapshot
        (captured_at, airline, stops, out_depart, out_arrive, ret_depart, ret_arrive,
         duration_out, duration_ret, layover_out, layover_ret, fare_name, total_price, booking_url)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (captured_at, row["airline"], row["stops"], row["out_depart"], row["out_arrive"],
         row["ret_depart"], row["ret_arrive"], row["duration_out"], row["duration_ret"],
         row["layover_out"], row["layover_ret"], row["fare_name"], row["total_price"],
         row.get("booking_url")),
    )


def insert_hotel(c, captured_at, row):
    c.execute(
        """INSERT INTO hotel_snapshot
        (captured_at, hotel_id, hotel_name, star_rating, guest_rating, review_count,
         avg_nightly_price, total_price, distance_to_stadium_mi, latitude, longitude, booking_url)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (captured_at, row["hotel_id"], row["hotel_name"], row["star_rating"],
         row["guest_rating"], row["review_count"], row["avg_nightly_price"],
         row["total_price"], row["distance_to_stadium_mi"], row["latitude"],
         row["longitude"], row.get("booking_url")),
    )


def insert_ticket(c, captured_at, row):
    c.execute(
        """INSERT INTO ticket_snapshot
        (captured_at, source, section, get_in_price, listing_count, note, listing_url)
        VALUES (?,?,?,?,?,?,?)""",
        (captured_at, row["source"], row.get("section"), row["get_in_price"],
         row.get("listing_count"), row.get("note"), row.get("listing_url")),
    )
