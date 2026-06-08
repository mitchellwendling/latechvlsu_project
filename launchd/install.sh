#!/bin/bash
# Install the SeatGeek auto-refresh launch agent.
# Runs tickets_seatgeek.py every 6 hours and at login.
#
# Usage:
#   export SEATGEEK_CLIENT_ID=your_client_id
#   ./launchd/install.sh
#
# Uninstall:
#   launchctl unload ~/Library/LaunchAgents/com.user.latechvlsu.seatgeek.plist
#   rm ~/Library/LaunchAgents/com.user.latechvlsu.seatgeek.plist

set -e

if [ -z "$SEATGEEK_CLIENT_ID" ]; then
  echo "ERROR: set SEATGEEK_CLIENT_ID first."
  echo "  export SEATGEEK_CLIENT_ID=your_client_id"
  exit 1
fi

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_PATH="$(which python3)"
TEMPLATE="$PROJECT_DIR/launchd/com.user.latechvlsu.seatgeek.plist.template"
DEST="$HOME/Library/LaunchAgents/com.user.latechvlsu.seatgeek.plist"

mkdir -p "$HOME/Library/LaunchAgents"

sed \
  -e "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
  -e "s|__SEATGEEK_CLIENT_ID__|$SEATGEEK_CLIENT_ID|g" \
  -e "s|/usr/local/bin/python3|$PYTHON_PATH|g" \
  "$TEMPLATE" > "$DEST"

# Reload if already installed
launchctl unload "$DEST" 2>/dev/null || true
launchctl load "$DEST"

echo "Installed launch agent. It will run now, and every 6 hours."
echo "Logs: $PROJECT_DIR/.seatgeek.out.log  /  .seatgeek.err.log"
echo "Check status: launchctl list | grep latechvlsu"
