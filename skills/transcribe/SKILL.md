---
name: transcribe
description: Transcribe a Hebrew (or other) audio recording locally and for free on Apple Silicon — ivrit.ai's Hebrew Whisper on MLX, a second model to cross-check, speaker labels and word-accurate timestamps — into one clean .txt and .srt. Use when the user gives an .m4a/.mp3/.wav file and wants its text, subtitles or a summary, instead of a paid transcription API.
---

# Transcribe audio locally

One clean transcript with speakers and accurate timing, built from open models
on this Mac. No API, no cost, no upload. A 90 s call takes about 45 s end to end.

Recordings and transcripts are **personal data**: work in the scratchpad, never
inside a repo, and never commit them.

## Pipeline

| Step | Tool | Why |
|---|---|---|
| 1. Transcribe (primary) | `mlx-community/ivrit-ai-whisper-large-v3-turbo-mlx` | ivrit.ai's Hebrew fine-tune of Whisper. Clearly best on Hebrew. Its word timestamps set all timing. |
| 2. Transcribe (check) | `mlx-community/whisper-large-v3-mlx` | Different errors from the primary; used only to cross-check words. |
| 3. Speakers | `ivrit-ai/pyannote-speaker-diarization-3.1` (pyannote 3.1.1) | Hebrew-tuned diarization. Ungated, no HF token. |
| 4. Merge | you (Claude) | Read the draft and the alternates, fix words and speakers, keep the timestamps. |
| 5. Render | `scripts/render.py` | Clean `.txt` grouped by speaker plus a matching `.srt`. |

For non-Hebrew audio, pass `--models mlx-community/whisper-large-v3-turbo,mlx-community/whisper-large-v3-mlx --language <code>`.

## Setup

Check first: `scripts/diagnose.sh` (read-only). Two venvs, because torch and MLX don't share well:

```bash
python3 -m venv ~/.venvs/mlx-whisper
~/.venvs/mlx-whisper/bin/pip install mlx-whisper
/opt/homebrew/bin/python3.12 -m venv ~/.venvs/pyannote
~/.venvs/pyannote/bin/pip install "torch==2.5.1" "torchaudio==2.5.1" "pyannote.audio==3.1.1" "numpy<2" "huggingface_hub<0.26"
```

The pins matter: pyannote 3.1.1 breaks on newer torchaudio (`set_audio_backend`
removed), on Python 3.13 (no torch 2.5 wheels) and on newer `huggingface_hub`
(`use_auth_token` removed). `ffmpeg` must be on PATH.

Models download on first use (~1.6 GB + ~3 GB). Hugging Face can stall at
~250 KB/s; `hf download <repo>` resumes. If a single blob stalls, resume it with
`curl -C -`, check the sha256 equals the blob name, link it into the snapshot,
and run with `HF_HUB_OFFLINE=1`.

## Run

Copy the recording to a plain name first (Hebrew, en-dashes and colons in
filenames trip tools), then:

```bash
export PATH=/opt/homebrew/bin:$PATH
S=<scratchpad>; mkdir -p $S/in && cp "<recording>" $S/in/clip.m4a
~/.venvs/mlx-whisper/bin/python -I scripts/transcribe.py $S/in/clip.m4a $S/out --speakers 2
```

`--speakers N` when the count is known (a phone call is 2). `--no-diarize` skips
step 3. Decoding always uses `condition_on_previous_text=False, temperature=0`:
without them a quiet recording looped on repeated lines.

It writes `out/turns.txt` (draft, one line per sentence:
`[mm:ss.s-mm:ss.s] דובר 1: text`), `out/alternates.txt` (every model's text for
each line's window) and `out/work/*.json` (raw output with word timestamps).

## Merge (your job)

Write `out/turns_final.txt` in the same line format:

- **Words:** start from the primary; where it reads as nonsense and the check
  model has a sensible reading for the same window, take that. Where both are
  unclear, write `[לא ברור]`, or `[word?]` for a best guess. Never invent content.
- **Speakers:** diarization is weak on phone audio, where the far side is quiet
  (it put almost everything under one speaker). Fix speakers from the dialogue
  (who asks, who answers) and name them when the filename or content says who
  they are (the caller is `אני`).
- **Timing:** a line that holds two speakers gets split at the word timings in
  `work/<primary>.json`. Don't make up times.
- Tell the user which passages are uncertain and that figures (dates, amounts,
  durations) should be checked against the audio.

## Render and deliver

```bash
python3 -I scripts/render.py $S/out/turns_final.txt ~/Downloads/תמלול-<topic> --name תמלול-סופי
```

The user reads the plain `.txt` (speaker blocks with `[mm:ss]`); the `.srt`
carries the exact per-line timing.
