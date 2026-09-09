#!/usr/bin/env bash
# Publishes the gh token to GUI-launched apps, which never source ~/.zshrc.
# Stores the COMMAND, not the token, so the plist holds no secret.
set -euo pipefail
. "$(dirname "$0")/_config.sh"
LABEL="$LAUNCH_LABEL"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
GH=$(command -v gh) || { echo "gh not found"; exit 1; }
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<PEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/sh</string>
    <string>-c</string>
    <string>launchctl setenv GITHUB_PERSONAL_ACCESS_TOKEN "\$($GH auth token)"</string>
  </array>
  <key>RunAtLoad</key><true/>
</dict>
</plist>
PEOF
plutil -lint "$PLIST"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
launchctl kickstart "gui/$(id -u)/$LABEL"
sleep 1
V=$(launchctl getenv GITHUB_PERSONAL_ACCESS_TOKEN || true)
[ -n "$V" ] && echo "launchctl env set (${V:0:4}...)" || { echo "FAILED to set env"; exit 1; }
echo "Runs once per login. Force a refresh with: launchctl kickstart gui/\$(id -u)/$LABEL"
