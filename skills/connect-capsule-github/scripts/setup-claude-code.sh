#!/usr/bin/env bash
# Wires ~/.zshrc to the gh keychain token and removes duplicate/stale github MCP entries.
set -euo pipefail
command -v gh >/dev/null || { echo "gh not installed"; exit 1; }
LINE='export GITHUB_PERSONAL_ACCESS_TOKEN="$(gh auth token 2>/dev/null)"'

python3 - "$LINE" <<'PY'
import re,sys,pathlib
line=sys.argv[1]; p=pathlib.Path.home()/'.zshrc'
s=p.read_text() if p.exists() else ''
if re.search(r'^export GITHUB_PERSONAL_ACCESS_TOKEN=',s,re.M):
    s=re.sub(r'^export GITHUB_PERSONAL_ACCESS_TOKEN=.*$',line,s,flags=re.M)
else:
    s=s.rstrip('\n')+'\n'+line+'\n'
p.write_text(s); print("zshrc wired")
PY

# Drop hand-rolled github servers. The official plugin owns the name and already has
# the correct config; duplicate names across scopes collide.
CJ="$HOME/.claude.json"
if [ -f "$CJ" ]; then
  cp "$CJ" "$CJ.bak-$(date +%s)"
  python3 - "$CJ" <<'PY'
import json,sys,pathlib
p=pathlib.Path(sys.argv[1]); d=json.loads(p.read_text()); n=0
if d.get('mcpServers',{}).pop('github',None): n+=1
for proj in d.get('projects',{}).values():
    if isinstance(proj,dict) and proj.get('mcpServers',{}).pop('github',None): n+=1
p.write_text(json.dumps(d,indent=2)); print(f"removed {n} hand-rolled github entr{'y' if n==1 else 'ies'}")
PY
fi
echo "Done. Quit Claude Code and relaunch it from a NEW terminal window."
