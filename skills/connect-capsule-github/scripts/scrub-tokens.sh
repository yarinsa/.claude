#!/usr/bin/env bash
# Finds plaintext GitHub tokens in config locations. Redacts with --fix.
# Does NOT revoke anything: revoke fine-grained PATs at https://github.com/settings/tokens
set -uo pipefail
FIX=0; [ "${1:-}" = "--fix" ] && FIX=1
PAT='github_pat_[A-Za-z0-9_]\{20,\}\|ghp_[A-Za-z0-9]\{30,\}\|gho_[A-Za-z0-9]\{30,\}'
TARGETS=("$HOME/.zshrc" "$HOME/.zshenv" "$HOME/.bashrc" "$HOME/.profile"
         "$HOME/.claude.json" "$HOME/.claude/settings.json"
         "$HOME/Library/Application Support/Claude/claude_desktop_config.json")
while IFS= read -r f; do TARGETS+=("$f"); done < <(ls "$HOME"/.claude.json.bak-* \
  "$HOME/Library/Application Support/Claude/claude_desktop_config.json.bak-"* 2>/dev/null)

FOUND=0
for f in "${TARGETS[@]}"; do
  [ -f "$f" ] || continue
  if grep -q "$PAT" "$f" 2>/dev/null; then
    FOUND=1
    echo "TOKEN in $f"
    grep -o "$PAT" "$f" | sort -u | sed 's/\(.\{16\}\).*/  \1.../'
    if [ "$FIX" = 1 ]; then
      cp "$f" "$f.prescrub-$(date +%s)"
      LC_ALL=C sed -i '' "s/$PAT/REDACTED/g" "$f"
      echo "  redacted"
    fi
  fi
done
[ "$FOUND" = 0 ] && echo "No plaintext tokens found."
[ "$FIX" = 0 ] && [ "$FOUND" = 1 ] && echo "Re-run with --fix to redact."
echo "Revoke any exposed token at https://github.com/settings/tokens"
exit 0
