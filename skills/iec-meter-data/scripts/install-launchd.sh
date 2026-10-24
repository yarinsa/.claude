#!/usr/bin/env bash
# Daily `iec fetch` via a user LaunchAgent. Idempotent; backs up an existing plist.
# --uninstall removes it. The plist holds no secret: the token stays in the Keychain.
set -euo pipefail
. "$(dirname "$0")/_config.sh"
PLIST="$HOME/Library/LaunchAgents/$LAUNCH_LABEL.plist"
DOMAIN="gui/$(id -u)"

if [ "${1:-}" = "--uninstall" ]; then
  launchctl bootout "$DOMAIN/$LAUNCH_LABEL" 2>/dev/null || true
  rm -f "$PLIST"; echo "removed $LAUNCH_LABEL"; exit 0
fi

WRAP="$IEC_DATA_DIR/iec"
[ -x "$WRAP" ] || { echo "run scripts/setup.sh first"; exit 1; }
mkdir -p "$HOME/Library/LaunchAgents" "$IEC_DATA_DIR/logs"
[ -f "$PLIST" ] && cp "$PLIST" "$PLIST.bak.$(date +%Y%m%d%H%M%S)"
cat > "$PLIST" <<PEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LAUNCH_LABEL</string>
  <key>ProgramArguments</key>
  <array><string>$WRAP</string><string>fetch</string></array>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>$FETCH_HOUR</integer><key>Minute</key><integer>$FETCH_MINUTE</integer></dict>
  <key>StandardOutPath</key><string>$IEC_DATA_DIR/logs/fetch.log</string>
  <key>StandardErrorPath</key><string>$IEC_DATA_DIR/logs/fetch.log</string>
</dict>
</plist>
PEOF
plutil -lint "$PLIST"
launchctl bootout "$DOMAIN/$LAUNCH_LABEL" 2>/dev/null || true
launchctl bootstrap "$DOMAIN" "$PLIST"
printf 'installed %s: daily at %02d:%02d (missed runs fire on wake)\n' "$LAUNCH_LABEL" "$FETCH_HOUR" "$FETCH_MINUTE"
echo "run now: launchctl kickstart $DOMAIN/$LAUNCH_LABEL"
