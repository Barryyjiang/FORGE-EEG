"""Aggregate benchmark results into one comparable leaderboard.

    .\\.venv\\Scripts\\python.exe scripts\\leaderboard.py --dir results/benchmark
"""

from __future__ import annotations

import argparse
from pathlib import Path

from eegbench.leaderboard import leaderboard, render


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dir", type=Path, default=Path("results/benchmark"))
    p.add_argument("--track", default=None, help="filter to one track")
    p.add_argument("--pipeline", default=None, help="filter to one decoder")
    p.add_argument("--out", type=Path, default=None, help="write CSV here")
    args = p.parse_args()

    table = leaderboard(args.dir)
    if args.track:
        table = table[table["track"] == args.track]
    if args.pipeline:
        table = table[table["pipeline"] == args.pipeline]
    if table.empty:
        print("no rows after filtering")
        return 1

    print(render(table))

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        table.to_csv(args.out, index=False)
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
