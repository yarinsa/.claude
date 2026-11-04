"""Speaker diarization with ivrit.ai's Hebrew-tuned pyannote pipeline.

Run with the pyannote venv (torch lives there, not in the mlx venv):
    ~/.venvs/pyannote/bin/python diarize.py <audio.wav> <out.json> [--speakers N]

Writes [{"start", "end", "speaker"}, ...] sorted by start, seconds.
"""
import argparse
import json

import torch
from pyannote.audio import Pipeline

PIPELINE = "ivrit-ai/pyannote-speaker-diarization-3.1"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("out")
    ap.add_argument("--speakers", type=int, help="exact speaker count, when known")
    args = ap.parse_args()

    pipe = Pipeline.from_pretrained(PIPELINE)
    if torch.backends.mps.is_available():
        pipe.to(torch.device("mps"))
    kw = {"num_speakers": args.speakers} if args.speakers else {}
    ann = pipe(args.audio, **kw)
    turns = [
        {"start": round(t.start, 3), "end": round(t.end, 3), "speaker": spk}
        for t, _, spk in ann.itertracks(yield_label=True)
    ]
    with open(args.out, "w") as f:
        json.dump(sorted(turns, key=lambda t: t["start"]), f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
