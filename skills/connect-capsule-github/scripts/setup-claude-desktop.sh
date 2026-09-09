#!/usr/bin/env bash
# Claude Desktop accepts stdio servers only. Proxy the remote endpoint via mcp-remote,
# fetching the token from the gh keychain at spawn so nothing is stored on disk.
set -euo pipefail
D="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
[ -f "$D" ] || { echo "Claude Desktop config not found at $D"; exit 1; }
NPX=$(command -v npx) || { echo "npx not found"; exit 1; }
BREW_BIN=$(dirname "$NPX")   # GUI PATH lacks this; npx needs node beside it
cp "$D" "$D.bak-$(date +%s)"

BREW_BIN="$BREW_BIN" python3 - "$D" <<'PY'
import json,os,sys,pathlib
p=pathlib.Path(sys.argv[1]); d=json.loads(p.read_text())
d.setdefault('mcpServers',{})['github']={
 "command":"/bin/sh",
 "args":["-c",
   f'export PATH={os.environ["BREW_BIN"]}:$PATH; '
   'exec npx -y mcp-remote https://api.githubcopilot.com/mcp/ '
   '--header "Authorization: Bearer $(gh auth token)"']}
p.write_text(json.dumps(d,indent=2)); print(json.dumps(d['mcpServers']['github'],indent=2))
PY
echo "Done. Quit and reopen Claude Desktop."
