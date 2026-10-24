#!/usr/bin/env bash
# Read-only. Reports the state of every moving part.
set -uo pipefail
. "$(dirname "$0")/_config.sh"
ok(){ printf '  ok    %s\n' "$1"; }
bad(){ printf '  FAIL  %s\n' "$1"; }

echo "== install =="
command -v uv >/dev/null && ok "uv $(uv --version | cut -d' ' -f2)" || bad "uv missing: brew install uv"
if [ -x "$VENV/bin/python" ]; then
  V=$("$VENV/bin/python" -c 'import importlib.metadata as m; print(m.version("iec-api"))' 2>/dev/null)
  [ "$V" = "$PIN" ] && ok "iec-api $V" || bad "iec-api ${V:-missing}, expected $PIN: run scripts/setup.sh"
else
  bad "no venv at $VENV: run scripts/setup.sh"
fi
[ -x "$IEC_DATA_DIR/iec" ] && ok "wrapper $IEC_DATA_DIR/iec" || bad "no wrapper: run scripts/setup.sh"

echo "== keychain =="
if command -v security >/dev/null; then
  for a in user-id token; do
    security find-generic-password -s iec-meter -a "$a" >/dev/null 2>&1 && ok "$a present" || bad "$a missing: run iec login"
  done
else
  [ -f "$IEC_DATA_DIR/secrets.json" ] && ok "secrets.json (no Keychain on this OS)" || bad "no secrets: run iec login"
fi

echo "== data =="
if [ -x "$IEC_DATA_DIR/iec" ]; then
  "$IEC_DATA_DIR/iec" status | sed 's/^/  /'
else
  IEC_DATA_DIR="$IEC_DATA_DIR" python3 -I "$(dirname "$0")/iec.py" status | sed 's/^/  /'
fi

echo "== schedule =="
if command -v launchctl >/dev/null; then
  launchctl print "gui/$(id -u)/$LAUNCH_LABEL" >/dev/null 2>&1 \
    && ok "$LAUNCH_LABEL loaded" || bad "$LAUNCH_LABEL not loaded: run scripts/install-launchd.sh"
fi
LOG="$IEC_DATA_DIR/logs/fetch.log"
if [ -f "$LOG" ]; then
  echo "  last log lines:"; tail -n 3 "$LOG" | sed 's/^/    /'
  grep -q "login required" <(tail -n 5 "$LOG") && bad "last run needs a fresh login: iec login"
fi
exit 0
