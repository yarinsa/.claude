# Sourced by every script. Loads config.env if present, then applies defaults.
# Precedence: exported env var > config.env > default.
_CFG="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)/config.env"
if [ -f "$_CFG" ]; then
  set -a; . "$_CFG"; set +a
fi
if [ -z "${IEC_DATA_DIR:-}" ]; then
  case "$(uname)" in
    Darwin) IEC_DATA_DIR="$HOME/Library/Application Support/iec-meter" ;;
    *) IEC_DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/iec-meter" ;;
  esac
fi
export IEC_DATA_DIR
PIN="${PIN:-0.5.16}"
LAUNCH_LABEL="${LAUNCH_LABEL:-com.claude.iec-meter}"
FETCH_HOUR="${FETCH_HOUR:-7}"
FETCH_MINUTE="${FETCH_MINUTE:-13}"
VENV="$IEC_DATA_DIR/venv"
