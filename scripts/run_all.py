"""Single entry point: run the whole benchmark and regenerate the report.

Sequence:
  1. benchmark tracks (ready ones)
  2. permutation controls for every live paradigm
  3. signal-quality tables
  4. markdown report

    .\\.venv\\Scripts\\python.exe scripts\\run_all.py
    .\\.venv\\Scripts\\python.exe scripts\\run_all.py --skip-heavy   # no Wu2020

``--skip-heavy`` exists because the ear track re-reads a 946 MB Curry file per
montage; it is the only slow part of the suite.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable

CONTROLS = [
    ("mi_leftright_22ch", "riemann_tslr"),
    ("p300_8ch", "xdawn_tslr"),
    ("ssvep_8ch", "ssvep_cca"),
]


def run(cmd: list[str], label: str) -> None:
    print(f"\n=== {label} ===", flush=True)
    proc = subprocess.run(cmd, cwd=ROOT)
    if proc.returncode != 0:
        raise SystemExit(f"FAILED: {label} (exit {proc.returncode})")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--skip-heavy", action="store_true",
                   help="skip the ear track (slow: 946 MB Curry re-reads)")
    p.add_argument("--skip-controls", action="store_true")
    p.add_argument("--overwrite", action="store_true",
                   help="re-run tracks whose CSV already exists")
    p.add_argument("--subjects", type=int, default=None,
                   help="limit subjects (smoke test)")
    args = p.parse_args()

    tracks = ["mi_leftright_22ch", "p300_8ch", "ssvep_8ch"]
    if not args.skip_heavy:
        tracks.append("motor_execution_ear_vs_scalp")

    run([PY, "scripts/run_benchmark.py", "--suite", ",".join(tracks),
         "--n-random", "3"] + (["--overwrite"] if args.overwrite else [])
        + (["--subjects", str(args.subjects)] if args.subjects else []),
        "benchmark tracks")

    if not args.skip_controls:
        for track, pipeline in CONTROLS:
            run([PY, "scripts/permutation_control.py", "--track", track,
                 "--pipeline", pipeline, "--subjects",
                 str(args.subjects or 2), "--n-permutations", "20",
                 "--out", f"results/perm_control_{track}.csv"],
                f"permutation control: {track}")

    run([PY, "scripts/signal_quality.py", "--track", "mi_leftright_22ch",
         "--subjects", str(args.subjects or 3),
         "--out", "results/signal_quality_bnci.csv"], "signal quality")

    run([PY, "scripts/report.py"], "report")
    print("\nDone. See results/REPORT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
