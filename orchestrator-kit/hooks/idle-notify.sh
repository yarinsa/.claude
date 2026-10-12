#!/usr/bin/env bash
# One desktop notification when a session is really done: QUIET_SECS after the main
# loop stops, only if no sub-agent, workflow or teammate is still in flight (Stop's
# background_tasks) and the session has not started a new turn since. The title
# carries the session name. Never blocks work.
#   Stop -> arm the timer, or disarm it while sub-agents run · fire -> internal · other args -> no-op
set -u
QUIET_SECS="${CLAUDE_IDLE_NOTIFY_SECS:-45}"
dir="${XDG_RUNTIME_DIR:-/tmp}/claude-idle-notify"

session_name() {  # latest /rename title, else agent name, else auto title
  local t v
  for t in custom-title:customTitle agent-name:agentName ai-title:aiTitle; do
    v=$(grep -aE "\"type\": ?\"${t%%:*}\"" "$1" 2>/dev/null | tail -1 | jq -r ".${t#*:} // empty" 2>/dev/null)
    [[ -n "$v" ]] && { printf '%s' "$v"; return; }
  done
}

if [[ "${1:-}" == fire ]]; then
  stamp=$2 token=$3 transcript=$4 size=$5 cwd=$6 last=$7
  sleep "$QUIET_SECS"
  [[ "$(cat "$stamp" 2>/dev/null)" == "$token" ]] || exit 0   # a newer Stop re-armed or disarmed us
  tail -c +"$((size + 1))" "$transcript" 2>/dev/null | grep -qaE '"type": ?"(user|assistant)"' && exit 0   # new turn started
  rm -f "$stamp"
  name=$(session_name "$transcript")
  body="Idle, no sub-agents running${cwd:+ · $(basename "$cwd")}${last:+
$last}"
  notify-send --app-name="Claude Code" --icon=dialog-information \
    "Claude · ${name:-$(basename "${cwd:-session}")}" "$(sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g' <<<"$body")"
  exit 0
fi
[[ "${1:-stop}" == stop ]] || exit 0

payload=$(cat 2>/dev/null || true)
j() { jq -r "$1" <<<"$payload" 2>/dev/null; }
mkdir -p "$dir"
sid=$(j '.session_id // "na"'); stamp="$dir/${sid:-na}"
j '{background_tasks, session_crons}' > "$stamp.last-stop"   # debug: what the last Stop saw
busy=$(j '[(.background_tasks // [])[]
  | select((.type // "") | test("agent|workflow|teammate"; "i"))
  | select((.status // "running") | test("^(completed|failed|killed|stopped|cancell?ed|done|error)$"; "i") | not)]
  + (.session_crons // []) | length')
if [[ "${busy:-0}" != 0 ]]; then rm -f "$stamp"; exit 0; fi

token=$(date +%s%N); printf '%s' "$token" > "$stamp"
transcript=$(j '.transcript_path // ""')
size=$(stat -c %s "$transcript" 2>/dev/null || echo 0)   # measured before forking, or a racing write slips in
cwd=$(j '.cwd // ""')
last=$(j '.last_assistant_message | strings' | grep -m1 -vE '^\s*(\||$)' | tr -d '*`#' | cut -c1-140)
setsid "${BASH_SOURCE[0]}" fire "$stamp" "$token" "$transcript" "$size" "$cwd" "$last" </dev/null >/dev/null 2>&1 &
disown 2>/dev/null || true
exit 0
