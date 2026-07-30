# Marathon Month Mileage Tracker

Standalone Flask app for tracking daily mileage during Marathon Month (Aug 1-31): pick a distance goal — Half (13.1 mi), Full (26.2 mi), or Ultra (31.1 mi) — then log miles from treadmill, bike, or strider classes each day and watch progress toward the goal.

Independent of the LA Tech @ LSU trip dashboard in the repo root — separate app, separate SQLite database (`marathon.db`), separate port.

## Quick start

```bash
cd marathon_tracker
pip install -r requirements.txt
python app.py         # http://localhost:5051
```

## How it works

- `/` — dashboard: goal picker (first visit), progress stats, cumulative-mileage chart vs. goal pace, and the mileage log
- `/goal` (POST) — set or change your distance goal
- `/log` (POST) — log a day's miles (date, activity, distance, optional note)
- `/log/<id>/delete` (POST) — remove a logged entry

Progress math lives in `app.py`: `remaining` is goal miles minus total logged, `pace_needed` is remaining miles divided by days left in the challenge, and the chart plots your cumulative mileage against a straight-line pace from 0 to the goal across Aug 1-31.

## Files

- `app.py` — Flask routes (calls `init_db()` at import time, so the schema exists whether started with `python app.py` or `gunicorn app:app`)
- `db.py` — SQLite schema (`settings` for the chosen goal, `mileage_log` for entries) + query helpers
- `challenge.py` — challenge dates and goal options (edit here to change the month or distances)
- `templates/dashboard.html` — single-page dashboard with a Chart.js progress chart

## Deploying

This app is registered as a second service (`marathon-month-tracker`) in the repo root's `render.yaml`, alongside the trip dashboard, using Render's `rootDir` to point at this subfolder. Production runs via `gunicorn app:app`, same as the trip dashboard.

If your Render account is already connected to this repo via the existing Blueprint, push to the default branch and sync the Blueprint (Render dashboard → Blueprints → your instance → **Manual Sync**) to pick up the new service. Otherwise, create it as a new Web Service pointing at this repo with **Root Directory** set to `marathon_tracker`.

There's no build-time seed step — the mileage log starts empty and you fill it in from the dashboard.
