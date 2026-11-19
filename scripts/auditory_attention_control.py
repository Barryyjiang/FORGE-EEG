"""Permutation control for the Ear-SAAD auditory-attention track.

Shuffles the attended-speaker label and re-runs the exact decoder. A valid
pipeline scores at chance (50%) on shuffled labels; if it does not, the track
is exploiting structure in the split or the preprocessing and its results must
not be reported.

The shuffle is applied at the *trial* level: each trial's attended speaker is
randomly reassigned, which changes which envelope the decoder is trained to
reconstruct and which candidate is scored as correct. Within-trial shuffling
would be meaningless here because the two candidates are the two talkers of the
same trial.

The control is written at COHORT level, one row per montage. The accuracy is a
mean over 15 participants and each participant only contributes six decisions
at a 60 s window, so a per-participant null with a handful of draws is far too
noisy to compare against chance at a 0.05 tolerance: single participants swing
to 0.7 on five draws while the cohort mean stays on 0.50. The claim the control
actually makes is about the pipeline, so the cohort mean is the test.

    .\\.venv\\Scripts\\python.exe scripts\auditory_attention_control.py
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from auditory_attention_track import (  # noqa: E402
    DATASET_KEY, LAYOUTS, TRACK, evaluate, load_subject,
)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("data/earsaad/preprocessedData"))
    p.add_argument("--subjects", default="all")
    p.add_argument("--window", type=float, default=60.0)
    p.add_argument("--permutations", type=int, default=5,
                   help="each permutation refits the decoder on every fold, so "
                        "this is the expensive knob; five draws already put the "
                        "cohort null mean well inside the 0.05 tolerance")
    p.add_argument("--out", type=Path,
                   default=Path("results/perm_control_auditory_attention_earsaad.csv"))
    args = p.parse_args()

    nums = (list(range(1, 16)) if args.subjects == "all"
            else [int(s) for s in args.subjects.split(",")])

    # Subject-outer so only one subject's trials are in memory at a time; the
    # per-draw cohort sums accumulate across subjects.
    real_acc: dict[str, list[float]] = {layout: [] for layout in LAYOUTS}
    draw_acc: dict[str, np.ndarray] = {
        layout: np.zeros(args.permutations) for layout in LAYOUTS
    }

    for n in nums:
        sub = load_subject(args.root, n)
        for layout, (chans, _strategy, _fidelity) in LAYOUTS.items():
            real = evaluate(sub, chans, [args.window])[0][args.window]
            real_acc[layout].append(real)
            for d in range(args.permutations):
                rng = np.random.default_rng((n, d))
                shuffled = dict(sub)
                shuffled["att_speaker"] = rng.permutation(sub["att_speaker"])
                draw_acc[layout][d] += evaluate(
                    shuffled, chans, [args.window])[0][args.window]
            print(f"  sub{n:>2} {layout:16s} real={real:.3f}", flush=True)

    rows = []
    for layout, (chans, _strategy, _fidelity) in LAYOUTS.items():
        real = float(np.mean(real_acc[layout]))
        nulls = draw_acc[layout] / len(nums)
        rows.append({
            "track": TRACK,
            "subset": f"{layout}_k{len(chans)}",
            "pipeline": "ridge_reconstruction",
            "metric": "accuracy",
            "n_classes": 2,
            "chance": 0.5,
            "subject": "cohort",
            "real": real,
            "perm_mean": float(nulls.mean()),
            "perm_sd": float(nulls.std()),
            "gap": real - float(nulls.mean()),
            "montage": layout,
            "channels": ",".join(chans),
            "null": "trial shuffle",
            "n_permutations": args.permutations,
        })

    args.out.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(args.out, index=False)
    print(f"\nwrote {args.out}")
    print(df[["subset", "real", "perm_mean", "gap"]].round(3).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
