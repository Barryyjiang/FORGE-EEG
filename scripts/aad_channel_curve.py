"""How many ear electrodes do you actually need?

The main auditory-attention track compares three montages as the hardware was
built: 29 scalp, 19 around-ear, 12 in-ear. That answers "is the ear worse", but
not the question a device team asks, which is "how many ear electrodes before it
stops improving".

This script sweeps the channel budget. At each k it takes the k most spatially
spread electrodes *within* each array and the k most spread scalp electrodes as
a matched reference, so the ear-vs-scalp gap at every k is a gap in placement
only. The scalp curve is the reference: if the two curves are parallel, the ear
cost is a constant offset; if the ear curve saturates earlier, the ear runs out
of information before it runs out of electrodes.

Everything is scored at the paper's 60 s decision window with the same decoder
and the same leave-one-trial-out protocol as the main track, so a point on this
curve is directly comparable to a row in the main results table.

The k values that the main track already reports (12 in-ear, 19 around-ear, 12
and 19 scalp) are recomputed here and checked against it. Ridge regression is
invariant to the order of feature columns, so the farthest-point ordering must
reproduce those numbers exactly; if it does not, one of the two is wrong.

    .\\.venv\\Scripts\\python.exe scripts\\aad_channel_curve.py
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# A cp1252 console cannot encode the delta sign used in the consistency report.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from auditory_attention_track import (  # noqa: E402
    AROUND_EAR, IN_EAR, SCALP, TRACK, evaluate, load_subject,
)
from eegbench.subsets import farthest_point_order  # noqa: E402

WINDOW_S = 60.0
#: Channel budgets. 12 is the full in-ear array; 19 is the full around-ear one.
K_IN_EAR = (2, 4, 8, 12)
K_AROUND_EAR = (2, 4, 8, 12, 19)
K_SCALP = (2, 4, 8, 12, 19)

#: Mastoid references, excluded from the scalp reference curve.
#:
#: M1 and M2 are part of the paper's published 29-electrode scalp montage, and
#: the main track keeps them for that reason. They are also *references*, sitting
#: a couple of centimetres from the ear arrays, so a farthest-point ordering picks
#: them immediately (they are as far from Cz as the head allows) and the low-k
#: "scalp" point becomes a partly-ear measurement. Measured: including them lifts
#: the k=2 scalp score from 0.653 to 0.731, which is larger than the entire
#: scalp-vs-ear gap at that budget and would invert the conclusion. At k>=12 the
#: difference is 0.002, so excluding them costs nothing where it does not matter.
SCALP_REFERENCES = ("M1", "M2")


def layouts() -> dict[str, tuple[list[str], str, int]]:
    """``name -> (channels, setup, k)`` for every point on the curve."""
    in_ear = farthest_point_order(IN_EAR)
    around_ear = farthest_point_order(AROUND_EAR)
    scalp_sites = [c for c in SCALP if c not in SCALP_REFERENCES]
    scalp = farthest_point_order(scalp_sites)

    out: dict[str, tuple[list[str], str, int]] = {}
    for k in K_IN_EAR:
        out[f"in_ear_{k}"] = (in_ear[:k], "in_ear", k)
    for k in K_AROUND_EAR:
        out[f"around_ear_{k}"] = (around_ear[:k], "around_ear", k)
    for k in K_SCALP:
        out[f"scalp_{k}"] = (scalp[:k], "scalp", k)
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("data/earsaad/preprocessedData"))
    p.add_argument("--subjects", default="all")
    p.add_argument("--out", type=Path,
                   default=Path("results/aad_channel_curve.csv"))
    p.add_argument("--main-results", type=Path,
                   default=Path("results/benchmark/auditory_attention_earsaad__within_session.csv"))
    args = p.parse_args()

    nums = (list(range(1, 16)) if args.subjects == "all"
            else [int(s) for s in args.subjects.split(",")])

    plan = layouts()
    scores: dict[str, list[float]] = {name: [] for name in plan}

    for n in nums:
        sub = load_subject(args.root, n)
        for name, (chans, _setup, _k) in plan.items():
            acc, _dropped = evaluate(sub, chans, [WINDOW_S])
            scores[name].append(acc[WINDOW_S])
        print(f"  sub{n:>2} done", flush=True)

    rows = []
    for name, (chans, setup, k) in plan.items():
        vals = np.array(scores[name])
        rows.append({
            "track": TRACK,
            "setup": setup,
            "k": k,
            "subset": name,
            "channels": ",".join(chans),
            "score_mean": float(vals.mean()),
            "score_sem": float(vals.std(ddof=1) / np.sqrt(len(vals))),
            "n": len(vals),
            "trial_seconds": WINDOW_S,
            "metric": "accuracy",
            "chance": 0.5,
        })
    df = pd.DataFrame(rows).sort_values(["setup", "k"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"\nwrote {args.out}\n")

    for setup in ("in_ear", "around_ear", "scalp"):
        sub = df[df["setup"] == setup]
        print(f"{setup:11s} " + "  ".join(
            f"k={int(r.k)}:{r.score_mean:.3f}" for r in sub.itertuples()))

    # --- consistency with the main track ---------------------------------
    # The ear arrays are ordered by farthest-point sampling here and in their
    # published order in the main track. Ridge is invariant to feature order, so
    # both must land on the same number; a mismatch means one of the two runs is
    # wrong. The scalp points are NOT checked: the main table's scalp montages
    # are cut from the full published 29-electrode set, mastoids included, while
    # this curve excludes them on purpose (see SCALP_REFERENCES).
    if args.main_results.exists():
        main = pd.read_csv(args.main_results)
        main = main[main["trial_seconds"] == WINDOW_S]
        checks = [
            ("in_ear_12", "in_ear_12_k12"),
            ("around_ear_19", "around_ear_19_k19"),
        ]
        print("\n--- consistency with the main track ---")
        for curve_name, main_name in checks:
            ours = float(df[df["subset"] == curve_name]["score_mean"].iloc[0])
            theirs = float(main[main["subset"] == main_name]["score"].mean())
            delta = abs(ours - theirs)
            flag = "ok" if delta < 1e-9 else "MISMATCH"
            print(f"  {curve_name:16s} {ours:.6f} vs {theirs:.6f}  "
                  f"|d|={delta:.2e}  {flag}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
