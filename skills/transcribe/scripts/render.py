"""Render a corrected turns.txt into transcript.txt and transcript.srt.

    python3 render.py <turns.txt> <outdir> [--name transcript]

turns.txt lines: [mm:ss.s-mm:ss.s] <speaker>: <text>
Speaker names can be edited in place (e.g. "דובר 1" → "עלא"); timing is kept as is.
"""
import argparse
import os
import re

LINE = re.compile(r"^\[(\d+):([\d.]+)-(\d+):([\d.]+)\]\s*([^:]+):\s*(.*)$")


def srt_time(t):
    ms = round(t * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("turns")
    ap.add_argument("outdir")
    ap.add_argument("--name", default="transcript")
    args = ap.parse_args()

    turns = []
    with open(args.turns) as f:
        for raw in f:
            m = LINE.match(raw.strip())
            if m:
                a, b = int(m[1]) * 60 + float(m[2]), int(m[3]) * 60 + float(m[4])
                turns.append((a, b, m[5].strip(), m[6].strip()))

    os.makedirs(args.outdir, exist_ok=True)
    with open(os.path.join(args.outdir, args.name + ".txt"), "w") as f:
        prev = None
        for a, _, who, text in turns:
            stamp = f"[{int(a // 60):02d}:{int(a % 60):02d}]"
            if who != prev:
                f.write(f"\n{stamp} {who}:\n")
                prev = who
            f.write(f"{text}\n")
    with open(os.path.join(args.outdir, args.name + ".srt"), "w") as f:
        for i, (a, b, who, text) in enumerate(turns, 1):
            f.write(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{who}: {text}\n\n")


if __name__ == "__main__":
    main()
