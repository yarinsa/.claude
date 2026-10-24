#!/usr/bin/env bash
# Creates the venv with a pinned iec-api and the `iec` wrapper. Idempotent: re-run to upgrade PIN.
set -euo pipefail
. "$(dirname "$0")/_config.sh"
HERE="$(cd "$(dirname "$0")" && pwd)"
command -v uv >/dev/null || { echo "uv not found: brew install uv"; exit 1; }

mkdir -p "$IEC_DATA_DIR"
chmod 700 "$IEC_DATA_DIR"   # holds readings plus the CSV headers (name, address, contract)
[ -x "$VENV/bin/python" ] || uv venv -q --python 3.12 "$VENV"
VIRTUAL_ENV="$VENV" uv pip install -q "iec-api==$PIN"
echo "iec-api $("$VENV/bin/python" -c 'import importlib.metadata as m; print(m.version("iec-api"))') in $VENV"

# Wrapper so SKILL.md, launchd and you all run the same thing.
WRAP="$IEC_DATA_DIR/iec"
cat > "$WRAP" <<EOF
#!/bin/sh
export IEC_DATA_DIR="$IEC_DATA_DIR"
exec "$VENV/bin/python" -I "$HERE/iec.py" "\$@"
EOF
chmod +x "$WRAP"
echo "wrapper: $WRAP"
echo "next: \"$WRAP\" login"
