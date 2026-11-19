"""Figure 6 — permutation controls.

Every headline decoder and channel subset is re-run on shuffled labels. The
null must land on chance; the real score must not. The shaded band is the
benchmark's ±0.05 tolerance around chance, and each panel is annotated with
the number of permutations and the subjects covered.

Run:  .\\.venv\\Scripts\\python.exe figures\\plot_fig6_controls.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import paper_data as pd_
from figure_style import (
    COLORS,
    FigureStyle,
    apply_publication_style,
    finish,
    panel_label,
    reference_line,
    save_figure,
    tidy_axes,
)

STYLE = FigureStyle(font_size=12, axes_linewidth=1.5)
OUT = pd_.FIGURE_DIR

#: Panel order, x labels and y-limits per track.
PANELS = [
    ("mi_leftright_22ch", "Motor imagery\nROC-AUC", (0.3, 1.06)),
    ("mi_4class_22ch", "MI, 4 classes\naccuracy", (0.1, 1.06)),
    ("p300_8ch", "P300 speller\nROC-AUC", (0.3, 1.06)),
    ("ssvep_8ch", "SSVEP\naccuracy", (-0.12, 1.06)),
    ("motor_execution_ear_vs_scalp", "Motor execution\nROC-AUC", (0.3, 1.06)),
    ("sleep_staging_local", "Sleep staging\nCohen's κ", (-0.2, 0.86)),
    ("stew_workload_14ch", "Workload\nROC-AUC", (0.3, 1.06)),
    ("auditory_attention_earsaad", "Auditory attention\naccuracy", (0.3, 1.06)),
    ("faced_emotion_123", "Emotion\nbalanced acc.", (0.3, 1.06)),
]

#: Panels per row. Eight in a single strip is unreadable, so they wrap.
NCOLS = 4

TOLERANCE = 0.05


def build(out_dir: Path | str = OUT, dpi: int = 300) -> list[Path]:
    apply_publication_style(STYLE)
    controls = pd_.load_permutation_controls()
    bundle = pd_.load_bundle()

    nrows = -(-len(PANELS) // NCOLS)  # ceil
    fig, axes = plt.subplots(nrows, NCOLS, figsize=(16.0, 3.9 * nrows),
                             layout="constrained")
    axes = axes.ravel()

    for ax, (track, title, ylim) in zip(axes, PANELS):
        task = bundle.task(track)
        chance = float(task["chance"])
        rows = controls[controls["track"] == track].copy()
        if rows.empty:
            continue

        # Sleep has one row per montage instead of one row per subject; every
        # other track has one row per subject.
        # Sleep is controlled on every night now (3 montages x 9 nights), which
        # does not fit one panel. Collapse to one point per montage: the block
        # null varies by only ~0.02 across nights, so the mean is representative.
        if track == "sleep_staging_local":
            order = ["scalp_6", "ear_6", "ear_14"]
            rows = rows.groupby("montage", as_index=False).agg(
                perm_mean=("perm_mean", "mean"),
                perm_sd=("perm_sd", "mean"),
                real=("real", "mean"),
                n_permutations=("n_permutations", "max"),
                nights=("subject", "nunique"),
            )
            rows["montage"] = pd.Categorical(rows["montage"], categories=order, ordered=True)
            rows = rows.sort_values("montage")
            unit_labels = ["scalp\n6 ch", "ear\n6 ch", "ear\n14 ch"]
            footnote = (
                f"one row per montage · {int(rows['n_permutations'].max())} "
                f"block permutations × {int(rows['nights'].max())} nights"
            )
        elif rows["subject"].astype(str).eq("cohort").all():
            # A cross-subject decoder cannot be controlled per participant: in
            # any one draw roughly half the participants keep their true labels,
            # so an individual null scatters even when the cohort null is 0.50.
            # Those tracks write one cohort row per montage instead.
            rows = rows.sort_values("subset")
            unit_labels = [
                str(s).rsplit("_k", 1)[0].replace("_", " ") for s in rows["subset"]
            ]
            footnote = (
                f"{int(rows['n_permutations'].max())} shuffles, cohort mean"
            )
        else:
            rows = rows.sort_values("subject")
            unit_labels = [f"s{int(s)}" for s in rows["subject"]]
            footnote = (
                f"{str(rows['subset'].iloc[0])} · "
                f"{int(rows['n_permutations'].max())} shuffles"
            )

        x = np.arange(len(rows))
        ax.axhspan(
            chance - TOLERANCE,
            chance + TOLERANCE,
            color=COLORS["random"],
            alpha=0.45,
            linewidth=0,
            zorder=0,
        )
        ax.errorbar(
            x,
            rows["perm_mean"],
            yerr=rows["perm_sd"],
            fmt="s",
            markersize=6,
            color=COLORS["ink_soft"],
            ecolor=COLORS["ink_soft"],
            elinewidth=1.2,
            capsize=4,
            zorder=3,
            label="shuffled labels",
        )
        ax.plot(
            x,
            rows["real"],
            linestyle="none",
            marker="o",
            markersize=9,
            color=COLORS["reference"],
            markeredgecolor="white",
            markeredgewidth=1.0,
            zorder=4,
            label="real labels",
        )
        for xi, real, perm in zip(x, rows["real"], rows["perm_mean"]):
            ax.plot([xi, xi], [perm, real], color=COLORS["random"], linewidth=1.6, zorder=2)

        reference_line(
            ax,
            chance,
            f"chance ±{TOLERANCE:g}",
            COLORS["chance"],
            linestyle=":",
            label_dy=TOLERANCE + 0.012,
        )
        ax.set_xticks(x)
        ax.set_xticklabels(unit_labels, fontsize=STYLE.font_size - 3)
        ax.set_ylim(*ylim)
        ax.set_title(title, fontsize=STYLE.font_size, pad=6)
        ax.set_xlabel(footnote, fontsize=STYLE.font_size - 3, color=COLORS["ink_soft"])
        tidy_axes(ax)

    axes.flat[0].legend(loc="upper left", fontsize=STYLE.font_size - 4)
    for ax, letter in zip(axes.flat, "abcdefghi"):
        panel_label(ax, letter, dx=-0.12, dy=1.02)

    for ax in axes.flat[len(PANELS):]:
        ax.set_visible(False)

    finish(fig)
    return save_figure(fig, out_dir, "fig6_controls", dpi=dpi)


if __name__ == "__main__":
    for path in build():
        print(f"wrote {path}")
