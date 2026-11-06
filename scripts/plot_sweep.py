"""Plot accuracy vs channel count from a sweep CSV.

Usage::

    .\\.venv\\Scripts\\python.exe scripts\\plot_sweep.py results\\bnci2014_001_s2.csv --pipeline "CSP+LDA"
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

# Region specs are collapsed into one line: with a handful of regions per k,
# separate lines would be noise at small n.
GROUPS = {"distributed": "distributed", "random": "random", "region": "region"}
COLORS = {"distributed": "#1f77b4", "region": "#d62728", "random": "#999999"}
ORDER = ["distributed", "region", "random"]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("csv", type=Path)
    p.add_argument("--pipeline", default=None,
                   help="pipeline to plot; defaults to all")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    df = pd.read_csv(args.csv)
    if args.pipeline:
        df = df[df["pipeline"] == args.pipeline]
    if df.empty:
        raise SystemExit(f"no rows (pipelines: {pd.read_csv(args.csv)['pipeline'].unique()})")

    df = df[df["strategy"] != "full"]
    df["group"] = df["strategy"].map(GROUPS).fillna(df["strategy"])

    fig, axes = plt.subplots(
        1, df["pipeline"].nunique(),
        figsize=(5 * df["pipeline"].nunique(), 4.2),
        sharey=True, squeeze=False,
    )

    for ax, (pipe, sub) in zip(axes[0], df.groupby("pipeline", sort=False)):
        for group in ORDER:
            g = sub[sub["group"] == group]
            if g.empty:
                continue
            agg = g.groupby("k")["score"].agg(["mean", "sem"]).sort_index()
            ax.errorbar(
                agg.index, agg["mean"], yerr=agg["sem"],
                marker="o", capsize=3, label=group, color=COLORS.get(group),
            )

        full = pd.read_csv(args.csv)
        full = full[(full["strategy"] == "full") & (full["pipeline"] == pipe)]
        if not full.empty:
            ax.axhline(full["score"].mean(), ls="--", color="black", lw=1,
                       label=f"full cap (k={int(full['k'].iloc[0])})")

        ax.axhline(0.5, ls=":", color="grey", lw=1, label="chance")
        ax.set_title(pipe)
        ax.set_xlabel("channels (k)")
        ax.set_ylabel("score (ROC-AUC)")
        ax.set_ylim(0.4, 1.0)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8, loc="lower right")

    n_sub = df["subject"].nunique()
    n_sess = df.groupby(["subject", "session"]).ngroups
    fig.suptitle(
        f"{Path(args.csv).stem} — {n_sub} subjects, {n_sess} subject-sessions "
        f"(error bars = SEM)"
    )
    fig.tight_layout()

    out = args.out or Path(args.csv).with_suffix(".png")
    fig.savefig(out, dpi=140)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
