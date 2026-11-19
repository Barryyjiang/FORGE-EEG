"""Figure 3 — placement, not just count.

At a fixed eight electrodes in Wu 2020 (motor execution), moving the same
number of electrodes changes the score by more than adding electrodes does.
The top row shows where the eight electrodes sit; the bottom panel scores them.

Run:  .\\.venv\\Scripts\\python.exe figures\\plot_fig3_placement.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt
import numpy as np

import eeg_maps
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

STYLE = FigureStyle(font_size=13, axes_linewidth=1.6)
OUT = pd_.FIGURE_DIR

MA = "motor_execution_ear_vs_scalp"
PIPELINE = "riemann_tslr"

ROLES = [
    ("region-sensorimotor_k8", "Sensorimotor", COLORS["sensorimotor"], "sensorimotor"),
    ("region-frontal_k8", "Frontal", COLORS["frontal"], "frontal"),
    ("region-temporal_k8", "Temporal", COLORS["temporal"], "temporal"),
    ("wu2020_inear_k8", "In-ear", COLORS["wearable"], "wearable"),
]


def build(out_dir: Path | str = OUT, dpi: int = 300) -> list[Path]:
    apply_publication_style(STYLE)
    bundle = pd_.load_bundle()
    task = bundle.task(MA)
    cap = bundle.channels(MA, "full_k115", pipeline=PIPELINE)
    reference = bundle.score(MA, "full_k115", pipeline=PIPELINE)
    chance = float(task["chance"])

    fig = plt.figure(figsize=(13.4, 7.6), layout="constrained")
    grid = fig.add_gridspec(2, 4, height_ratios=[1.0, 0.92])

    # ------------------------------------------------------- top row: maps
    axes = [fig.add_subplot(grid[0, i]) for i in range(4)]
    for ax, (subset, title, color, _role) in zip(axes, ROLES):
        channels = bundle.channels(MA, subset, pipeline=PIPELINE)
        score = bundle.score(MA, subset, pipeline=PIPELINE)
        positions = {name: bundle.positions[name] for name in cap if name in bundle.positions}
        highlight = eeg_maps.montage_map(bundle.positions, channels, color)
        # Ear channels are not part of the scalp cap, so add them explicitly.
        for name in channels:
            if name not in positions and name in bundle.positions:
                positions[name] = bundle.positions[name]
        eeg_maps.draw_head(ax, positions, highlight=highlight)
        ax.set_title(f"{title} · 8 ch", fontsize=STYLE.font_size - 1, pad=3)
        ax.text(
            0.5,
            0.03,
            f"{score:.3f}",
            transform=ax.transAxes,
            ha="center",
            va="bottom",
            fontsize=STYLE.font_size + 2,
            fontweight="bold",
            color=color,
        )
    panel_label(axes[0], "a", dx=-0.02)

    # ------------------------------------------------- bottom: bar panel
    ax_bar = fig.add_subplot(grid[1, :])

    band = pd_.random_band(bundle, MA, 8, pipeline=PIPELINE, protocol="within_session")
    categories = [label for _s, label, _c, _r in ROLES] + ["Max-spread", "Random"]
    values = [bundle.score(MA, subset, pipeline=PIPELINE) for subset, _l, _c, _r in ROLES]
    values += [bundle.score(MA, "distributed_k8", pipeline=PIPELINE), band["mean"]]
    colors = [color for _s, _l, color, _r in ROLES] + [COLORS["spread"], COLORS["random"]]
    errors = [0, 0, 0, 0, 0, band["mean"] - band["min"]]

    x = np.arange(len(categories))
    bars = ax_bar.bar(
        x,
        values,
        width=0.62,
        color=colors,
        edgecolor="black",
        linewidth=1.0,
        zorder=3,
    )
    ax_bar.errorbar(
        x[-1],
        band["mean"],
        yerr=[[band["mean"] - band["min"]], [band["max"] - band["mean"]]],
        fmt="none",
        ecolor=COLORS["ink_soft"],
        elinewidth=1.4,
        capsize=6,
        zorder=4,
    )
    for xi, value in zip(x, values):
        ax_bar.annotate(
            f"{value:.3f}",
            xy=(xi, value),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            fontsize=STYLE.font_size - 1,
            fontweight="bold",
            color=COLORS["ink"],
        )
    ax_bar.set_xticks(x)
    ax_bar.set_xticklabels(categories)
    ax_bar.set_ylabel(task["metricLabel"])
    ax_bar.set_ylim(0.40, 0.90)
    ax_bar.set_yticks([0.4, 0.5, 0.6, 0.7, 0.8])
    tidy_axes(ax_bar)
    reference_line(ax_bar, reference, f"full 115-channel cap · {reference:.3f}", COLORS["reference"], label_dy=0.008)
    reference_line(ax_bar, chance, "chance", COLORS["chance"], linestyle=":", label_dy=-0.01, label_va="top")
    ax_bar.set_title(
        "Same eight electrodes, same session, same decoder — only the placement changes",
        fontsize=STYLE.font_size,
        pad=6,
    )
    panel_label(ax_bar, "b", dx=-0.06)

    finish(fig)
    return save_figure(fig, out_dir, "fig3_placement", dpi=dpi)


if __name__ == "__main__":
    for path in build():
        print(f"wrote {path}")
