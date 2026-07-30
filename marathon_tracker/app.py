"""Dashboard for tracking daily mileage during Marathon Month (Aug 1-31).

Pick a distance goal (half / full / ultra), log miles each day (tread, bike,
strider, or outdoor run), and track progress toward the goal by Aug 31.
"""
from datetime import date, datetime, timedelta, timezone

from flask import Flask, redirect, render_template, request, url_for

from db import (
    init_db, conn, get_goal, set_goal, insert_log, all_logs, delete_log,
    total_miles, cumulative_by_date,
)
from challenge import CHALLENGE, GOALS, ACTIVITIES

app = Flask(__name__)
init_db()

GOALS_BY_KEY = {g["key"]: g for g in GOALS}


def challenge_dates():
    return date.fromisoformat(CHALLENGE["start_date"]), date.fromisoformat(CHALLENGE["end_date"])


def challenge_length():
    start, end = challenge_dates()
    return (end - start).days + 1


def days_left():
    _, end = challenge_dates()
    return max((end - date.today()).days + 1, 0)


def elapsed_days():
    start, end = challenge_dates()
    today = min(max(date.today(), start), end)
    return (today - start).days + 1


def pace_line(goal_miles):
    """Linear expected-cumulative-miles line from start_date to end_date."""
    start, _ = challenge_dates()
    total_days = challenge_length()
    return [
        ((start + timedelta(days=i)).isoformat(), round(goal_miles * (i + 1) / total_days, 2))
        for i in range(total_days)
    ]


@app.route("/")
def dashboard():
    with conn() as c:
        goal = get_goal(c)
        logs = all_logs(c)
        total = total_miles(c)
        cumulative = cumulative_by_date(c)

    goal_miles = goal["goal_miles"] if goal else None
    remaining = max(goal_miles - total, 0) if goal_miles is not None else None
    dleft = days_left()
    pace_needed = (remaining / dleft) if (remaining is not None and dleft > 0) else remaining
    percent = min(100, round(total / goal_miles * 100, 1)) if goal_miles else 0
    expected_to_date = (
        round(goal_miles * elapsed_days() / challenge_length(), 2) if goal_miles else None
    )

    return render_template(
        "dashboard.html",
        challenge=CHALLENGE,
        goals=GOALS,
        activities=ACTIVITIES,
        goal=goal,
        goal_info=GOALS_BY_KEY.get(goal["goal_key"]) if goal else None,
        logs=logs,
        total=round(total, 2),
        goal_miles=goal_miles,
        remaining=round(remaining, 2) if remaining is not None else None,
        days_left=dleft,
        pace_needed=round(pace_needed, 2) if pace_needed is not None else None,
        percent=percent,
        expected_to_date=expected_to_date,
        cumulative=cumulative,
        pace=pace_line(goal_miles) if goal_miles else [],
        today=date.today().isoformat(),
    )


@app.route("/goal", methods=["POST"])
def choose_goal():
    info = GOALS_BY_KEY.get(request.form["goal"])
    if info:
        with conn() as c:
            set_goal(c, info["key"], info["miles"], datetime.now(timezone.utc).isoformat(timespec="seconds"))
    return redirect(url_for("dashboard"))


@app.route("/log", methods=["POST"])
def log_run():
    with conn() as c:
        insert_log(c, {
            "log_date": request.form["date"],
            "activity": request.form.get("activity") or "Run",
            "miles": float(request.form["miles"]),
            "note": request.form.get("note", "").strip() or None,
            "logged_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
    return redirect(url_for("dashboard") + "#log")


@app.route("/log/<int:log_id>/delete", methods=["POST"])
def delete_run(log_id):
    with conn() as c:
        delete_log(c, log_id)
    return redirect(url_for("dashboard") + "#log")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5051, debug=True)
