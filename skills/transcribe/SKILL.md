---
name: transcribe
description: Transcribe a Hebrew (or other) audio recording locally and for free with open-source mlx-whisper on Apple Silicon. Use when the user gives an .m4a/.mp3/.wav file and wants its text, subtitles or a summary, instead of a paid transcription API.
---

# Transcribe audio locally (mlx-whisper)

Runs `mlx-community/whisper-large-v3-turbo` on this Mac. No API, no cost, no
upload. A 90-second clip takes about 5 seconds once the model is cached.

Recordings and transcripts are **personal data**: write outputs outside the
repo (scratchpad or `~/Documents`), never commit them.

## One-time setup

Check state first with `scripts/diagnose.sh` (read-only).


```bash
python3 -m venv ~/.venvs/mlx-whisper
~/.venvs/mlx-whisper/bin/pip install mlx-whisper
```

`ffmpeg` must be on PATH (`/opt/homebrew/bin/ffmpeg`). The first run downloads
the model (~1.5 GB) into `~/.cache/huggingface`; it is already cached on this
machine. If the download stalls (Hugging Face can drop to ~250 KB/s), resume the
weights blob with `curl -C -`, check the sha256 equals the blob name, link it as
`weights.safetensors` in the snapshot dir, then run with `HF_HUB_OFFLINE=1`.

## Run

```bash
export PATH=/opt/homebrew/bin:$PATH
~/.venvs/mlx-whisper/bin/mlx_whisper "<audio file>" \
  --model mlx-community/whisper-large-v3-turbo --language he \
  --output-dir <outdir> --output-format all \
  --condition-on-previous-text False --temperature 0
```

- **Always pass `--condition-on-previous-text False --temperature 0`.** Without
  them a quiet recording degenerated into endless repeated "תעת." lines after
  ~1:36.
- Filenames with Hebrew, en-dashes or colons can trip tools; copy the file to a
  plain name (`in/clip.m4a`) first.
- Change `--language` for other languages; omit it to auto-detect.
- Outputs: `.txt`, `.srt`, `.vtt`, `.tsv`, `.json` (with timestamps).

## After transcribing

- Whisper is weak on fast, quiet, two-speaker phone audio and on numbers. Flag
  garbled phrases and tell the user to verify figures (amounts, dates, durations)
  against the audio before relying on them.
- For hard audio, also run `--model mlx-community/whisper-large-v3-mlx` (~3 GB,
  already cached here, ~16 s per 90 s clip) and cross-check. Neither model
  wins outright: on a noisy Hebrew call, large-v3 got dates and floors right
  while turbo got other phrases right.
- Deliver results to `~/Downloads/תמלול-<topic>/`, one subfolder per model. The
  user reads the plain `.txt`, so lead with that.
