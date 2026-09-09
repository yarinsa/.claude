#!/usr/bin/env bash
# Read-only. Reports the state of every moving part.
set -uo pipefail
. "$(dirname "$0")/_config.sh"
[ -n "${1:-}" ] && GITHUB_ORG="$1"
DESKTOP="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
ok(){ printf '  ok    %s\n' "$1"; }
bad(){ printf '  FAIL  %s\n' "$1"; }

echo "== gh CLI =="
if ! command -v gh >/dev/null; then bad "gh not installed"; exit 1; fi
gh auth status 2>&1 | sed 's/^/  /'
TOK=$(gh auth token 2>/dev/null)
[ -n "$TOK" ] && ok "token retrieved (${TOK:0:4}...)" || { bad "gh auth token empty; run: gh auth login"; exit 1; }

echo "== REST =="
C=$(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $TOK" https://api.github.com/user)
[ "$C" = 200 ] && ok "api.github.com 200" || bad "api.github.com $C"

echo "== Projects v2 =="
if [ -n "$GITHUB_ORG" ]; then
  Q="{ organization(login:\\\"$GITHUB_ORG\\\"){ projectsV2(first:1){ nodes{ title } } } }"
  WHO="org $GITHUB_ORG"
else
  Q="{ viewer { projectsV2(first:1){ nodes{ title } } } }"
  WHO="your user (set GITHUB_ORG to probe an org)"
fi
R=$(curl -s -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' \
  -d "{\"query\":\"$Q\"}" https://api.github.com/graphql)
case "$R" in
  *'"title"'*) ok "Projects v2 readable ($WHO)" ;;
  *'"nodes":[]'*) ok "Projects v2 readable ($WHO), none found" ;;
  *) bad "Projects v2 unreadable for $WHO (silent null = missing Projects permission)"; echo "        $R" ;;
esac

echo "== github-projects server =="
if command -v uvx >/dev/null; then
  printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"diag","version":"1"}}}' \
   | env -i HOME="$HOME" PATH=/usr/bin:/bin:/usr/sbin:/sbin /bin/sh -c \
     "export PATH=$(dirname "$(command -v uvx)"):\$PATH; export GITHUB_TOKEN=\"\$(gh auth token)\"; exec uvx mcp-github-projects" 2>/dev/null \
   | grep -q '"serverInfo"' && ok "initializes under GUI-like env" || bad "did not initialize"
else bad "uvx not installed (brew install uv)"; fi

echo "== legacy remote MCP endpoint =="
C=$(curl -s -o /dev/null -w '%{http_code}' -X POST https://api.githubcopilot.com/mcp/ \
  -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"diag","version":"1"}}}')
[ "$C" = 200 ] && ok "initialize 200" || bad "initialize $C"

echo "== running Claude Code process env =="
PID=$(pgrep -f 'claude' | head -1)
if [ -n "${PID:-}" ]; then
  CUR=$(ps eww -p "$PID" 2>/dev/null | tr ' ' '\n' | grep '^GITHUB_PERSONAL_ACCESS_TOKEN=' | cut -d= -f2)
  case "$CUR" in
    gho_*) ok "pid $PID has a gh token" ;;
    "")    bad "pid $PID has no token in env" ;;
    *)     bad "pid $PID holds a STALE token (${CUR:0:12}...); restart from a new terminal" ;;
  esac
fi

echo "== config =="
python3 - "$HOME/.claude/settings.json" <<'PY2'
import json,sys,pathlib
p=pathlib.Path(sys.argv[1])
v=(json.loads(p.read_text()).get('env',{}) if p.exists() else {}).get('GITHUB_PERSONAL_ACCESS_TOKEN')
print("  FAIL  settings.json env pins a token (%s...); it OVERRIDES the shell, delete the key"%v[:12]
      if v else "  ok    settings.json does not pin a token")
PY2
grep -q 'gh auth token' "$HOME/.zshrc" 2>/dev/null && ok "zshrc uses dynamic gh token" || bad "zshrc not wired (run setup-claude-code.sh)"
if [ -f "$DESKTOP" ]; then
  python3 - "$DESKTOP" <<'PY'
import json,sys
m=json.load(open(sys.argv[1])).get('mcpServers',{})
if 'github' in m: print("  WARN  desktop: legacy `github` server still present")
s=m.get('github-projects')
if not s: print("  FAIL  desktop: no github-projects server")
elif s.get('type')=='http': print("  FAIL  desktop: http entry, Desktop needs stdio")
elif s.get('command'): print("  ok    desktop: stdio entry")
PY
fi
launchctl getenv GITHUB_PERSONAL_ACCESS_TOKEN >/dev/null 2>&1 \
  && ok "launchctl env set ($(launchctl getenv GITHUB_PERSONAL_ACCESS_TOKEN | cut -c1-4)...)" \
  || bad "launchctl env unset (GUI apps blind; run install-launchagent.sh)"

echo
echo "Reminder: config changes need a FULL app restart. /mcp reconnect reuses the frozen env."
