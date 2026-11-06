"""Paired comparison of each subset against the full cap.

This is the headline number for the project: *how much accuracy do you lose with
k electrodes*, measured **within** the same subject-session so between-subject
variance cancels out.

Every subset was evaluated on the same subjects/sessions as the full cap, so the
comparison is paired. Reporting an unpaired mean difference would inflate the
apparent uncertainty enormously at small n.

Usage::

    .\\.venv\\Scripts\\python.exe scripts\\compare.py results\\bnci2014_001_s9.csv --pipeline "CSP+LDA"
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

KEY = ["subject", "session"]


def _ci95(values: np.ndarray) -> tuple[float, float]:
    n = len(values)
    if n < 2:
        return (np.nan, np.nan)
    sem = values.std(ddof=1) / np.sqrt(n)
    half = stats.t.ppf(0.975, n - 1) * sem
    return (values.mean() - half, values.mean() + half)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("csv", type=Path)
    p.add_argument("--pipeline", default=None)
    p.add_argument("--baseline", default="full",
                   help="subset-name prefix to compare against (default: full cap). "
                        "e.g. --baseline region-sensorimotor compares ear-EEG against "
                        "the sensorimotor scalp montage at matched k")
    args = p.parse_args()

    df = pd.read_csv(args.csv)
    if args.pipeline:
        df = df[df["pipeline"] == args.pipeline]
    if df.empty:
        raise SystemExit("no rows after filtering")

    pipes = sorted(df["pipeline"].unique())
    rows = []

    for pipe, sub in df.groupby("pipeline"):
        skipped_no_baseline = 0
        wide = sub.pivot_table(index=KEY, columns="subset", values="score")
        base_cols = [c for c in wide.columns if c.startswith(args.baseline)]
        if not base_cols:
            print(f"  [{pipe}] no column starting with {args.baseline!r}, skipping")
            continue
        base_k = {
            c: int(sub[sub["subset"] == c].iloc[0]["k"]) for c in base_cols
        }

        for col in wide.columns:
            if col in base_cols:
                continue
            meta = sub[sub["subset"] == col].iloc[0]
            k = int(meta["k"])

            # Require a baseline of the SAME channel count when comparing
            # placements: a k=16 subset against a k=4 baseline would confound
            # count with placement. The full cap is the one legitimate
            # exception -- it is the ceiling, so its k is meant to differ.
            same_k = [c for c in base_cols if base_k.get(c) == k]
            if same_k:
                base_col = same_k[0]
            else:
                ceiling = [
                    c for c in base_cols
                    if str(sub[sub["subset"] == c].iloc[0]["strategy"]) == "full"
                ]
                if ceiling:
                    base_col = ceiling[0]
                else:
                    skipped_no_baseline += 1
                    continue

            pair = pd.concat([wide[base_col], wide[col]], axis=1).dropna()
            delta = pair.iloc[:, 1].to_numpy() - pair.iloc[:, 0].to_numpy()
            lo, hi = _ci95(delta)

            p_val = np.nan
            if len(delta) >= 6 and np.any(delta != 0):
                try:
                    p_val = stats.wilcoxon(delta).pvalue
                except ValueError:
                    pass

            rows.append({
                "pipeline": pipe,
                "k": int(meta["k"]),
                "strategy": meta["strategy"],
                "subset": col,
                "baseline": base_col,
                "n_pairs": len(delta),
                "score": pair.iloc[:, 1].mean(),
                "delta": delta.mean(),
                "ci_lo": lo,
                "ci_hi": hi,
                "p_wilcoxon": p_val,
            })

        if skipped_no_baseline:
            print(f"  [{pipe}] skipped {skipped_no_baseline} subset(s): no "
                  f"{args.baseline!r} baseline at the same k")

    if not rows:
        print("No comparisons produced. Check --baseline and --pipeline.")
        return 0

    out = pd.DataFrame(rows).sort_values(["pipeline", "k", "strategy", "delta"])
    with pd.option_context("display.width", 200, "display.max_rows", 300):
        print(out.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))

    print()
    print(f"delta < 0 means the subset scored worse than the baseline "
          f"({args.baseline!r}).")
    print("CI spanning 0 => the difference is not distinguishable from noise.")
    if (out["n_pairs"] < 6).any():
        print("WARNING: some comparisons have n_pairs < 6; Wilcoxon p is unreliable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
