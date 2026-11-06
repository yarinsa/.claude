#!/usr/bin/env bash
# Validate the advanced-react skill directory.
# - Checks all reference files exist
# - Reports whether the local cache is present
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SKILL_DIR"

fail=0
ok=0

check_file() {
  if [ -f "$1" ]; then ok=$((ok+1)); else echo "MISSING $1"; fail=$((fail+1)); fi
}

# Top-level
check_file SKILL.md
check_file template.md
check_file examples/sample.md

# References
for f in \
  references/layout-components.md \
  references/container-components.md \
  references/controlled-uncontrolled.md \
  references/hocs.md \
  references/custom-hooks.md \
  references/functional-patterns.md \
  references/more-patterns.md \
  references/advanced-concepts.md \
  references/clean-code.md \
  references/architecture.md \
  references/api-layer.md \
  references/react-query.md \
  references/state-management.md \
  references/performance.md \
  references/design-system.md \
  references/typescript.md
do
  check_file "$f"
done

echo "Files: $ok ok, $fail missing"

if [ -d .cache/extracted ]; then
  n=$(find .cache/extracted -maxdepth 2 -mindepth 2 -type d | wc -l | tr -d ' ')
  size=$(du -sh .cache/extracted | awk '{print $1}')
  echo "Cache: present ($n lectures, $size)"
else
  echo "Cache: absent (.cache/extracted not found — patterns still usable, deep references unavailable)"
fi

exit $fail
