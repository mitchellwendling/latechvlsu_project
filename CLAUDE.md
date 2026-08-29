# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A self-hosted Flask dashboard (single trip, hardcoded) that tracks price snapshots for a football road trip: Kentucky @ Oklahoma, Oct 17, 2026 (Gaylord Family Oklahoma Memorial Stadium, Norman, OK). It tracks three categories — flights (CVG→DFW; DFW is ~3 hrs from Norman, so the plan is fly-then-drive), hotels (Marriott properties near Oklahoma Memorial Stadium), and game tickets (resale get-in prices) — and charts how each moves over time as kickoff approaches. There is no auth, no multi-user/multi-trip support, and no test suite; it's a personal tool.

Trip specifics live in `trip.py` (dates, airports, venue, ticket links), the stadium coordinates + seed data in `seed.py`, the forecast location in `weather.py`, and the ESPN matchup filter in `game_info.py`. The app was previously themed for LA Tech @ LSU; it was re-pointed to this trip, so if you see stray Baton Rouge/LSU references, they're leftovers to fix.

## Commands

```bash
pip install -r requirements.txt
python seed.py           # (re)seed prices.db with a snapshot; safe to rerun, appends new rows
python app.py             # dev server on http://localhost:5050 (debug=True, auto-reloads)
```

Seed a specific dataset only, or backdate a snapshot's timestamp (useful for testing chart history):

```bash
python seed.py flights hotels        # omit "tickets"
python seed.py 2026-05-15T12:00:00+00:00   # any arg parseable as ISO-8601 backdates captured_at
```

Log a live SeatGeek ticket price (requires `SEATGEEK_CLIENT_ID`, see README):

```bash
export SEATGEEK_CLIENT_ID=your_client_id
python3 tickets_seatgeek.py
```

There is no lint/format/test command configured — no pytest, flake8, black, etc. in `requirements.txt` or elsewhere. Verify changes by running `python app.py` and checking the dashboard renders (`/`) and the three POST forms (`/log/ticket`, `/log/flight`, `/log/hotel`) work.

Production runs via `gunicorn app:app` (see `render.yaml`, deployed on Render's free tier). The Render build step runs `python seed.py` on every deploy, which appends a fresh snapshot each time.

## Architecture

**Append-only snapshot model.** Every "refresh" of prices — whether from `seed.py`, `tickets_seatgeek.py`, or a manual form submission — inserts new rows into SQLite (`prices.db`, gitignored) rather than updating existing ones. Each row is tagged with a shared `captured_at` timestamp. The dashboard always reads two things per category: the *latest* snapshot (`MAX(captured_at)`, for the current price table) and the *full history* (grouped by `captured_at`, for the Chart.js line charts). This split lives in `app.py`'s `fetch_latest()` / `history_series()` / `overall_min_history()` helpers — any new price category should follow the same pair-of-queries pattern.

**Module responsibilities:**
- `db.py` — the only place SQL schema/inserts live. Three tables: `flight_snapshot`, `hotel_snapshot`, `ticket_snapshot`, each independent (no foreign keys). `conn()` is a context manager that commits on clean exit; all DB access should go through it.
- `trip.py` — static config (dates, airports, ticket source links). Single source of truth the rest of the app imports from; changing the trip means editing this file, not scattering literals elsewhere.
- `seed.py` — hardcoded snapshot data (`FLIGHTS`, `HOTELS`, `TICKETS` lists) captured manually from Expedia/estimates, plus `haversine_miles()` for hotel-to-stadium distance. `app.py`'s `log_hotel` route imports `haversine_miles`/`STADIUM_LAT`/`STADIUM_LON` from here directly rather than duplicating the math.
- `weather.py` / `game_info.py` — external API pulls (NWS forecast, ESPN scoreboard), each independently disk-cached as JSON (`.cache_weather.json`, `.cache_game.json`, gitignored) with its own TTL, and each fails soft (returns an `error`/`None` shape rather than raising) since the dashboard should still render if an upstream API is down.
- `tickets_seatgeek.py` — standalone script (not imported by `app.py`), meant to run on a schedule via the `launchd/` launch agent on macOS. Compares each new price against the historical low for `source='SeatGeek'` and fires a native notification on a new all-time low under `PRICE_ALERT_THRESHOLD`.
- `app.py` — routes only: `/` renders the dashboard, `/log/{ticket,flight,hotel}` are POST-only manual-entry endpoints that redirect back to `/#<section>`. No blueprints/factory pattern — it's small enough to stay a single file.
- `templates/dashboard.html` — single template, no inheritance/includes. Inline `<style>` (CSS custom properties for the Kentucky blue/white palette, with Oklahoma crimson/cream used only in the matchup badge) and inline Chart.js setup, no separate static JS files. Legacy `--tech-*` token names are kept as aliases mapped to the Kentucky palette to avoid touching every rule.

**External data flow:** Flights and hotels are *not* fetched live — they were pulled once via Expedia MCP tools and hardcoded into `seed.py`; refreshing them means editing those lists (or using the in-app log forms) and rerunning `seed.py`. Tickets can be either manually logged via the dashboard forms or pulled live from the SeatGeek API (the only category with a real live-data path, since SeatGeek is the only reseller with a usable free API — StubHub/Vivid Seats require approved keys). Weather and kickoff time/network are fetched live and cached on disk automatically, no setup required.

When adding a new price category, expect to touch: `db.py` (new table + insert helper), `app.py` (fetch/history helpers + a `/log/<category>` route if manual entry is wanted), `seed.py` (initial data + `ALL_DATASETS`), and `templates/dashboard.html` (table + chart).
