# Sourced by every script. Loads config.env if present, then applies defaults.
# Precedence: exported env var > config.env > default.
_CFG="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)/config.env"
if [ -f "$_CFG" ]; then
  set -a; . "$_CFG"; set +a
fi
GITHUB_ORG="${GITHUB_ORG:-}"
PROJECT_DIR="${PROJECT_DIR:-$PWD}"
LAUNCH_LABEL="${LAUNCH_LABEL:-com.claude.ghtoken}"
PIN="${PIN:-}"
