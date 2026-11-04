#!/usr/bin/env bash
# Read-only. Reports whether local transcription is ready to run.
set -uo pipefail
VENV="${MLX_WHISPER_VENV:-$HOME/.venvs/mlx-whisper}"
HUB="${HF_HOME:-$HOME/.cache/huggingface}/hub"
ok(){ printf '  ok    %s\n' "$1"; }
bad(){ printf '  FAIL  %s\n' "$1"; }

echo "== install =="
[ "$(uname -m)" = arm64 ] && ok "Apple Silicon" || bad "mlx needs Apple Silicon (got $(uname -m))"
command -v ffmpeg >/dev/null && ok "ffmpeg $(command -v ffmpeg)" || bad "ffmpeg missing: brew install ffmpeg"
if [ -x "$VENV/bin/mlx_whisper" ]; then
  ok "mlx-whisper $("$VENV/bin/python" -c 'import importlib.metadata as m; print(m.version("mlx-whisper"))' 2>/dev/null)"
else
  bad "no mlx_whisper in $VENV: see SKILL.md setup"
fi

echo "== models =="
for m in whisper-large-v3-turbo whisper-large-v3-mlx; do
  d="$HUB/models--mlx-community--$m/snapshots"
  if [ -d "$d" ] && [ -n "$(find -L "$d" -name 'weights.*' -size +100M 2>/dev/null | head -1)" ]; then
    ok "$m cached"
  else
    bad "$m not cached (first run downloads it)"
  fi
done
