# Baton Rouge Trip Dashboard — LA Tech @ LSU, Sept 12, 2026

A self-hosted Flask dashboard that tracks three price categories for the trip:

- **Flights** — CVG → BTR round trip, 9/11–9/13
- **Hotels** — Marriott-brand properties near Tiger Stadium
- **Tickets** — LA Tech @ LSU "get-in" prices across the major resellers

Every snapshot is appended to `prices.db` (SQLite) so the dashboard charts how prices move as kickoff approaches.

## Quick start

```bash
pip install -r requirements.txt
python seed.py        # loads the initial Expedia snapshot + ticket estimates
python app.py         # http://localhost:5000
```

## How data flows

| Category | Source                                                                                  | How to refresh                                                                                              |
| -------- | --------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Flights  | Expedia (one-time pull via MCP, baked into `seed.py`)                                   | Edit the `FLIGHTS` list in `seed.py` with new quotes, then `python seed.py` — or use the in-app form        |
| Hotels   | Expedia (one-time pull via MCP, baked into `seed.py`) — Marriott brand, within ~5 mi    | Same as flights — edit `HOTELS` in `seed.py`, or log new quotes from the dashboard                          |
| Tickets  | User-logged (seeded with placeholder estimates)                                         | Click a source chip on the dashboard → check current get-in price → log it via the form                     |

Each rerun of `seed.py` appends a brand-new snapshot timestamp. The line charts only render once 2+ snapshots exist.

To backdate a snapshot for testing:

```bash
python seed.py 2026-05-15T12:00:00+00:00
```

## Files

- `app.py` — Flask routes (dashboard + manual-entry POSTs)
- `db.py` — SQLite schema + insert helpers
- `seed.py` — initial snapshot data + haversine distance to Tiger Stadium
- `trip.py` — trip constants and ticket-source links
- `templates/dashboard.html` — single-page dashboard with Chart.js line charts

## Why no live ticket scraping?

SeatGeek, StubHub, and Vivid Seats all block unauthenticated automated requests and require approved API keys for live data. The dashboard links you straight to each source so you can log the real number in two clicks.

### Live SeatGeek prices (optional, recommended)

SeatGeek has a free public API. Wire it up once and you get live get-in prices:

```bash
# 1. Sign up at https://seatgeek.com/account/develop and grab a Client ID.
# 2. Stash it (or put it in your shell rc file):
export SEATGEEK_CLIENT_ID=your_client_id_here

# 3. Run anytime to log a fresh snapshot:
python3 tickets_seatgeek.py
```

The dashboard picks it up automatically. Re-run before each browser refresh, or use the auto-refresh agent below.

### Auto-refresh + macOS price-drop alerts

A launch agent runs `tickets_seatgeek.py` every 6 hours and at login. When a new
all-time low under your threshold lands, you get a native macOS notification.

```bash
export SEATGEEK_CLIENT_ID=your_client_id
./launchd/install.sh
```

That sets up `~/Library/LaunchAgents/com.user.latechvlsu.seatgeek.plist`. Tune the alert with `PRICE_ALERT_THRESHOLD` (default $50) — edit the plist directly or re-run install with the env var set.

Check it's alive:

```bash
launchctl list | grep latechvlsu
tail -f .seatgeek.out.log
```

Uninstall:

```bash
launchctl unload ~/Library/LaunchAgents/com.user.latechvlsu.seatgeek.plist
rm ~/Library/LaunchAgents/com.user.latechvlsu.seatgeek.plist
```

### Weather + kickoff time

The dashboard pulls both automatically — no setup:

- **Weather**: National Weather Service (free, no key). Shown only inside 10 days of kickoff.
- **Kickoff time + TV network**: ESPN public scoreboard. Populated once the SEC announces the slot (~12 days out).

Both responses are cached on disk so we don't hammer the upstream APIs.
