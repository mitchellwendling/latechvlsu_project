"""SQLite layer for the Marathon Month mileage tracker."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "marathon.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    goal_key TEXT NOT NULL,
    goal_miles REAL NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mileage_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_date TEXT NOT NULL,
    activity TEXT NOT NULL,
    miles REAL NOT NULL,
    note TEXT,
    logged_at TEXT NOT NULL
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


def get_goal(c):
    row = c.execute("SELECT * FROM settings WHERE id = 1").fetchone()
    return dict(row) if row else None


def set_goal(c, goal_key, goal_miles, updated_at):
    c.execute(
        """INSERT INTO settings (id, goal_key, goal_miles, updated_at)
        VALUES (1, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            goal_key=excluded.goal_key,
            goal_miles=excluded.goal_miles,
            updated_at=excluded.updated_at""",
        (goal_key, goal_miles, updated_at),
    )


def insert_log(c, row):
    c.execute(
        """INSERT INTO mileage_log (log_date, activity, miles, note, logged_at)
        VALUES (?,?,?,?,?)""",
        (row["log_date"], row["activity"], row["miles"], row.get("note"), row["logged_at"]),
    )


def all_logs(c):
    rows = c.execute(
        "SELECT * FROM mileage_log ORDER BY log_date DESC, id DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def delete_log(c, log_id):
    c.execute("DELETE FROM mileage_log WHERE id = ?", (log_id,))


def total_miles(c):
    row = c.execute("SELECT COALESCE(SUM(miles), 0) AS t FROM mileage_log").fetchone()
    return row["t"]


def cumulative_by_date(c):
    """Return [(date, cumulative_miles), ...], one point per day that has an entry."""
    rows = c.execute(
        """SELECT log_date, SUM(miles) AS daily FROM mileage_log
        GROUP BY log_date ORDER BY log_date"""
    ).fetchall()
    series = []
    running = 0.0
    for r in rows:
        running += r["daily"]
        series.append((r["log_date"], round(running, 2)))
    return series
