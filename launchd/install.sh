#!/bin/bash
# Install launch agents for auto-refreshing ticket + flight data.
#
# Usage:
#   export SEATGEEK_CLIENT_ID=your_client_id
#   export AMADEUS_API_KEY=your_key
#   export AMADEUS_API_SECRET=your_secret
#   ./launchd/install.sh
#
# Either set of env vars is optional — only the agents with credentials get installed.
#
# Uninstall:
#   launchctl unload ~/Library/LaunchAgents/com.user.latechvlsu.seatgeek.plist
#   launchctl unload ~/Library/LaunchAgents/com.user.latechvlsu.flights.plist
#   rm ~/Library/LaunchAgents/com.user.latechvlsu.*.plist

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_PATH="$(which python3)"
AGENTS_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$AGENTS_DIR"
INSTALLED=0

# --- SeatGeek (tickets) ---
if [ -n "$SEATGEEK_CLIENT_ID" ]; then
  DEST="$AGENTS_DIR/com.user.latechvlsu.seatgeek.plist"
  sed \
    -e "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
    -e "s|__SEATGEEK_CLIENT_ID__|$SEATGEEK_CLIENT_ID|g" \
    -e "s|/usr/local/bin/python3|$PYTHON_PATH|g" \
    "$PROJECT_DIR/launchd/com.user.latechvlsu.seatgeek.plist.template" > "$DEST"
  launchctl unload "$DEST" 2>/dev/null || true
  launchctl load "$DEST"
  echo "Installed SeatGeek agent (every 6h). Logs: $PROJECT_DIR/.seatgeek.out.log"
  INSTALLED=$((INSTALLED + 1))
else
  echo "Skipping SeatGeek — SEATGEEK_CLIENT_ID not set."
fi

# --- Amadeus (flights) ---
if [ -n "$AMADEUS_API_KEY" ] && [ -n "$AMADEUS_API_SECRET" ]; then
  DEST="$AGENTS_DIR/com.user.latechvlsu.flights.plist"
  sed \
    -e "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
    -e "s|__AMADEUS_API_KEY__|$AMADEUS_API_KEY|g" \
    -e "s|__AMADEUS_API_SECRET__|$AMADEUS_API_SECRET|g" \
    -e "s|/usr/local/bin/python3|$PYTHON_PATH|g" \
    "$PROJECT_DIR/launchd/com.user.latechvlsu.flights.plist.template" > "$DEST"
  launchctl unload "$DEST" 2>/dev/null || true
  launchctl load "$DEST"
  echo "Installed Amadeus flights agent (every 12h). Logs: $PROJECT_DIR/.flights.out.log"
  INSTALLED=$((INSTALLED + 1))
else
  echo "Skipping Amadeus — AMADEUS_API_KEY / AMADEUS_API_SECRET not set."
fi

if [ $INSTALLED -eq 0 ]; then
  echo ""
  echo "No agents installed. Set at least one pair of env vars and re-run."
  exit 1
fi

echo ""
echo "Check status: launchctl list | grep latechvlsu"
