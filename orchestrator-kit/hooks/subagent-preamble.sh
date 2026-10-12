#!/bin/sh
# SubagentStart hook: inject the subagent-preamble.md into every spawned subagent. Read-only.
f="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/subagent-preamble.md"
cat >/dev/null
[ -r "$f" ] || exit 0
if command -v jq >/dev/null 2>&1; then
  jq -Rsc '{hookSpecificOutput:{hookEventName:"SubagentStart",additionalContext:.}}' "$f"
else
  python3 -c 'import json,sys;print(json.dumps({"hookSpecificOutput":{"hookEventName":"SubagentStart","additionalContext":open(sys.argv[1]).read()}}))' "$f"
fi
