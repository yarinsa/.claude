"""Multi-model transcription with word timing and speaker labels.

Run with the mlx venv:
    ~/.venvs/mlx-whisper/bin/python transcribe.py <audio> <outdir> [--speakers N]
        [--models M1,M2,...] [--language he] [--no-diarize]

Writes into <outdir>:
  work/<model>.json   raw mlx-whisper output per model (word timestamps)
  work/speakers.json  diarization turns
  turns.txt           draft from the primary (first) model, one line per speaker turn:
                      [mm:ss.s-mm:ss.s] <speaker>: <text>
  alternates.txt      every model's text per turn window, for the merge step

turns.txt is the file to correct; render.py turns it into transcript.txt + .srt.
Timing always comes from the primary model's word timestamps, never from the merge.
"""
import argparse
import json
import os
import subprocess
import sys

import mlx_whisper

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODELS = [
    "mlx-community/ivrit-ai-whisper-large-v3-turbo-mlx",
    "mlx-community/whisper-large-v3-mlx",
]
PYANNOTE_PY = os.path.expanduser(os.environ.get("PYANNOTE_PY", "~/.venvs/pyannote/bin/python"))
GAP = 1.5  # seconds of silence that splits a turn even when the speaker stays


def fmt(t):
    return f"{int(t // 60):02d}:{t % 60:04.1f}"


def to_wav(src, dst):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ac", "1", "-ar", "16000", dst], check=True)


def run_model(wav, model, language):
    return mlx_whisper.transcribe(
        wav,
        path_or_hf_repo=model,
        language=language,
        word_timestamps=True,
        condition_on_previous_text=False,
        temperature=0.0,
    )


def words_of(result):
    """Words in order, each tagged with its segment index so lines can break at sentence ends."""
    return [
        dict(w, seg=i)
        for i, s in enumerate(result["segments"])
        for w in s.get("words", [])
        if w["word"].strip()
    ]


def speaker_at(start, end, turns):
    """Speaker with the most overlap with [start, end]; nearest turn if none overlaps."""
    best, best_ov = None, 0.0
    for t in turns:
        ov = min(end, t["end"]) - max(start, t["start"])
        if ov > best_ov:
            best, best_ov = t["speaker"], ov
    if best is None and turns:
        mid = (start + end) / 2
        best = min(turns, key=lambda t: min(abs(mid - t["start"]), abs(mid - t["end"])))["speaker"]
    return best


def group_turns(words, turns):
    """One line per Whisper segment, split further where the speaker changes or a long pause falls."""
    out = []
    for w in words:
        spk = speaker_at(w["start"], w["end"], turns) if turns else None
        last = out[-1] if out else None
        if last and last["seg"] == w["seg"] and last["speaker"] == spk and w["start"] - last["end"] < GAP:
            last["end"] = w["end"]
            last["text"] += w["word"]
        else:
            out.append({"start": w["start"], "end": w["end"], "speaker": spk, "seg": w["seg"], "text": w["word"]})
    for t in out:
        t["text"] = t["text"].strip()
    return out


def speaker_names(turns):
    """SPEAKER_00 → דובר 1, in order of first appearance."""
    names = {}
    for t in turns:
        if t["speaker"] is not None and t["speaker"] not in names:
            names[t["speaker"]] = f"דובר {len(names) + 1}"
    return names


def text_in(words, start, end):
    return "".join(w["word"] for w in words if w["start"] < end and w["end"] > start).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("outdir")
    ap.add_argument("--models", default=",".join(DEFAULT_MODELS))
    ap.add_argument("--language", default="he")
    ap.add_argument("--speakers", type=int)
    ap.add_argument("--no-diarize", action="store_true")
    args = ap.parse_args()

    work = os.path.join(args.outdir, "work")
    os.makedirs(work, exist_ok=True)
    wav = os.path.join(work, "audio.wav")
    to_wav(args.audio, wav)

    models = [m for m in args.models.split(",") if m]
    results = {}
    for m in models:
        print(f"transcribing with {m}", file=sys.stderr)
        results[m] = run_model(wav, m, args.language)
        with open(os.path.join(work, m.split("/")[-1] + ".json"), "w") as f:
            json.dump(results[m], f, ensure_ascii=False, indent=1)

    speakers = []
    if not args.no_diarize:
        print("diarizing", file=sys.stderr)
        spk_json = os.path.join(work, "speakers.json")
        cmd = [PYANNOTE_PY, os.path.join(HERE, "diarize.py"), wav, spk_json]
        if args.speakers:
            cmd += ["--speakers", str(args.speakers)]
        subprocess.run(cmd, check=True)
        with open(spk_json) as f:
            speakers = json.load(f)

    primary = words_of(results[models[0]])
    turns = group_turns(primary, speakers)
    names = speaker_names(turns)

    with open(os.path.join(args.outdir, "turns.txt"), "w") as f:
        for t in turns:
            who = names.get(t["speaker"], "דובר")
            f.write(f"[{fmt(t['start'])}-{fmt(t['end'])}] {who}: {t['text']}\n")

    others = {m: words_of(r) for m, r in results.items()}
    with open(os.path.join(args.outdir, "alternates.txt"), "w") as f:
        for t in turns:
            f.write(f"[{fmt(t['start'])}-{fmt(t['end'])}]\n")
            for m, ws in others.items():
                f.write(f"  {m.split('/')[-1]}: {text_in(ws, t['start'], t['end'])}\n")

    print(f"{len(turns)} turns, {len(names)} speakers → {args.outdir}/turns.txt", file=sys.stderr)


if __name__ == "__main__":
    main()
