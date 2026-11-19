"""Single entry point: run the whole benchmark and regenerate the report.

Sequence:
  1. benchmark tracks (open datasets)
  2. sleep-staging track (BIDS adapter)
  3. permutation controls on the exact headline subsets
  4. signal-quality table
  5. markdown report

    .\\.venv\\Scripts\\python.exe scripts\\run_all.py
    .\\.venv\\Scripts\\python.exe scripts\\run_all.py --skip-heavy   # no Wu2020/sleep

``--skip-heavy`` exists because the ear track re-reads a 900 MB Curry file per
montage and sleep reads nine overnight recordings. It is the only slow part of
the suite.

Shuffle counts are per task: 100 for MI, SSVEP and motor execution, 20 for
P300 (its null SD is small), and 200 block permutations for sleep. A circular
shift is not a valid null for the sleep track: it preserves the stage-run
structure and the band-power drift, so it sits near kappa 0.13 instead of 0.
Controls cover the full cohort of each track unless --subjects narrows them.
chosen so the standard error of each null mean is well below the 0.05
tolerance without turning the run into a week-long job.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable

#: track, pipeline, exact headline channels, label, shuffles
CONTROLS = [
    (
        "mi_leftright_22ch",
        "riemann_tslr",
        "Cz,C6,C5,CP4,CP3,FC4,FC3,C2",
        "region-sensorimotor_k8",
        100,
    ),
    (
        "mi_4class_22ch",
        "riemann_tslr",
        "Cz,C6,C5,CP4,CP3,FC4,FC3,C2",
        "region-sensorimotor_k8",
        100,
    ),
    (
        "p300_8ch",
        "xdawn_tslr",
        "Pz,Fz,PO8,PO7",
        "distributed_k4",
        20,
    ),
    (
        "ssvep_8ch",
        "ssvep_cca",
        "Oz,PO8,PO7,PO3",
        "distributed_k4",
        100,
    ),
    (
        "motor_execution_ear_vs_scalp",
        "riemann_tslr",
        "LF,LB,LOU,LOD,RF,RB,ROU,ROD",
        "wu2020_inear_k8",
        100,
    ),
]

SLEEP_SUBJECTS = "001,002,003,004,005,006,007,008,009"


def run(cmd: list[str], label: str) -> None:
    print(f"\n=== {label} ===", flush=True)
    proc = subprocess.run(cmd, cwd=ROOT)
    if proc.returncode != 0:
        raise SystemExit(f"FAILED: {label} (exit {proc.returncode})")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--skip-heavy", action="store_true",
                   help="skip the motor-execution and sleep tracks")
    p.add_argument("--skip-controls", action="store_true")
    p.add_argument("--overwrite", action="store_true",
                   help="re-run tracks whose CSV already exists")
    p.add_argument("--subjects", type=int, default=None,
                   help="limit benchmark subjects (smoke test)")
    args = p.parse_args()

    tracks = ["mi_leftright_22ch", "mi_4class_22ch", "p300_8ch",
              "ssvep_8ch"]
    if not args.skip_heavy:
        tracks.append("motor_execution_ear_vs_scalp")

    run([PY, "scripts/run_benchmark.py", "--suite", ",".join(tracks),
         "--n-random", "3"] + (["--overwrite"] if args.overwrite else [])
        + (["--subjects", str(args.subjects)] if args.subjects else []),
        "benchmark tracks")

    if not args.skip_heavy:
        run([PY, "scripts/sleep_track.py", "--subjects", SLEEP_SUBJECTS,
             "--permutations", "200"], "sleep staging")
        # The two paradigm-level extensions. Both read their own raw release
        # (the IEEE DataPort STEW zip, the Ear-SAAD .mat files), so they are in
        # the heavy group. The order matters: the drift control and the paper
        # check both read what the track scripts write.
        run([PY, "scripts/stew_raw_track.py"], "cognitive workload (STEW)")
        run([PY, "scripts/stew_drift_control.py"], "workload drift control")
        run([PY, "scripts/auditory_attention_track.py", "--subjects", "all"],
            "auditory attention (Ear-SAAD)")
        run([PY, "scripts/auditory_attention_control.py"],
            "attention permutation control")
        run([PY, "scripts/aad_channel_curve.py"],
            "attention channel-budget curve")
        run([PY, "scripts/earsaad_paper_check.py"],
            "attention reproduction check")
        # Emotion reads per-participant feature caches, not the raw BIDS
        # release; run scripts/faced_extract_features.py once to build them.
        run([PY, "scripts/faced_emotion_track.py"], "emotion (FACED)")
        run([PY, "scripts/faced_reference_check.py"],
            "emotion reference check")

    if not args.skip_controls:
        for track, pipeline, channels, label, n_perm in CONTROLS:
            if args.skip_heavy and track == "motor_execution_ear_vs_scalp":
                continue
            cmd = [PY, "scripts/permutation_control.py", "--track", track,
                   "--pipeline", pipeline,
                   "--channels", channels, "--label", label,
                   "--n-permutations", str(n_perm),
                   "--out", f"results/perm_control_{track}.csv"]
            # Controls run on the track's full cohort by default: a control on a
            # subset of subjects reports a `real` that is not the headline score,
            # which is exactly the mismatch this benchmark was fixed for.
            if args.subjects:
                cmd += ["--subjects", str(args.subjects)]
            run(cmd, f"permutation control: {track} / {label}")

    run([PY, "scripts/signal_quality.py", "--track", "mi_leftright_22ch",
         "--subjects", str(args.subjects or 3),
         "--out", "results/signal_quality_bnci.csv"], "signal quality")

    run([PY, "scripts/report.py"], "report")
    # Last, so it checks the state that will actually be published: every quoted
    # number traces to a CSV and the generated pages carry no placeholder.
    run([PY, "scripts/verify.py"], "consistency check")
    print("\nDone. See results/REPORT.md")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
