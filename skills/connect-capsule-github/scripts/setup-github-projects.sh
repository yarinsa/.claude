#!/usr/bin/env bash
# Installs the Arclio github-projects MCP server (Projects V2) into Claude Code and
# Claude Desktop, and removes the older generic `github` server from both.
# Token is read from the gh keychain at spawn, so nothing is stored on disk.
# Pin a version with:  PIN=4.0.3 ./setup-github-projects.sh
set -euo pipefail
PROJECT_DIR="${PROJECT_DIR:-$HOME/Code/capsule}"
PKG="mcp-github-projects${PIN:+==$PIN}"
command -v gh  >/dev/null || { echo "gh not installed";  exit 1; }
UVX=$(command -v uvx) || { echo "uvx not installed (brew install uv)"; exit 1; }
BREW_BIN=$(dirname "$UVX")
SH_ARG="export PATH=$BREW_BIN:\$PATH; export GITHUB_TOKEN=\"\$(gh auth token)\"; exec uvx $PKG"

echo "== smoke test under a GUI-like environment =="
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"setup","version":"1"}}}' \
 | env -i HOME="$HOME" PATH=/usr/bin:/bin:/usr/sbin:/sbin /bin/sh -c "$SH_ARG" 2>/dev/null \
 | grep -q '"serverInfo"' && echo "  ok    server responds" || { echo "  FAIL  server did not initialize"; exit 1; }

D="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
if [ -f "$D" ]; then cp "$D" "$D.bak-$(date +%s)"; fi
SH_ARG="$SH_ARG" DESKTOP="$D" PROJECT_DIR="$PROJECT_DIR" python3 <<'PY'
import json,os,pathlib
sh=os.environ['SH_ARG']

d=pathlib.Path(os.environ['DESKTOP'])          # Desktop: stdio only, no "type" key
if d.exists():
    c=json.loads(d.read_text()); m=c.setdefault('mcpServers',{})
    m.pop('github',None)
    m['github-projects']={"command":"/bin/sh","args":["-c",sh]}
    d.write_text(json.dumps(c,indent=2)); print("  desktop: github-projects installed, github removed")

p=pathlib.Path.home()/'.claude.json'            # Claude Code: project scope
c=json.loads(p.read_text())
proj=c.setdefault('projects',{}).setdefault(os.environ['PROJECT_DIR'],{})
m=proj.setdefault('mcpServers',{})
m.pop('github',None)
m['github-projects']={"type":"stdio","command":"/bin/sh","args":["-c",sh]}
c.get('mcpServers',{}).pop('github',None)
p.write_text(json.dumps(c,indent=2)); print("  claude code: github-projects installed, github removed")
PY

# The official github plugin also registers an MCP server under the name `github`.
# It may be enabled in the repo's shared .claude/settings.json; disabling at local
# scope avoids editing a file the team shares.
if command -v claude >/dev/null; then
  claude plugin disable github@claude-plugins-official --scope local 2>/dev/null \
    && echo "  plugin github@claude-plugins-official disabled (local scope only)" || true
fi
echo "Done. Restart Claude Desktop, and Claude Code from a NEW terminal."
