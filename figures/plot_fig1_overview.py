"""Figure 1 — the benchmark in one panel: two channel budgets on one head, and
how much of the reference score a reduced montage keeps in every task.

Run:  .\\.venv\\Scripts\\python.exe figures\\plot_fig1_overview.py
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

TASK_COLORS = pd_.TASK_COLORS


def build(out_dir: Path | str = OUT, dpi: int = 300) -> list[Path]:
    apply_publication_style(STYLE)
    bundle = pd_.load_bundle()
    ma = "motor_execution_ear_vs_scalp"

    fig = plt.figure(figsize=(13.2, 7.6), layout="constrained")
    grid = fig.add_gridspec(1, 2, width_ratios=[0.92, 1.08])

    # ------------------------------------------------------------------ (a)
    ax_map = fig.add_subplot(grid[0, 0])
    cap = bundle.channels(ma, "full_k115", pipeline="riemann_tslr")
    sensorimotor = bundle.channels(ma, "region-sensorimotor_k8", pipeline="riemann_tslr")
    inear = bundle.channels(ma, "wu2020_inear_k8", pipeline="riemann_tslr")
    positions = {
        name: bundle.positions[name]
        for name in [*cap, *inear, *sensorimotor]
        if name in bundle.positions
    }
    highlight = eeg_maps.combined_map(
        eeg_maps.montage_map(bundle.positions, sensorimotor, COLORS["sensorimotor"]),
        eeg_maps.montage_map(bundle.positions, inear, COLORS["wearable"]),
    )
    eeg_maps.draw_head(ax_map, positions, highlight=highlight)
    eeg_maps.legend_swatch(
        ax_map,
        [
            (COLORS["sensorimotor"], "sensorimotor scalp, 8 ch"),
            (COLORS["wearable"], "in-ear, 8 ch"),
        ],
        loc="upper center",
        ncol=2,
        size=52.0,
        bbox_to_anchor=(0.5, -0.01),
    )
    ax_map.set_title(
        "One recording, two channel budgets\nWu 2020: 115 of 122 scalp + 8 in-ear, recorded together",
        fontsize=STYLE.font_size - 1,
        pad=6,
    )
    panel_label(ax_map, "a", dx=-0.02, dy=0.99)

    # ------------------------------------------------------------------ (b)
    ax_bar = fig.add_subplot(grid[0, 1])
    tasks = bundle.tasks
    labels = [pd_.SHORT[t["id"]] for t in tasks]
    retained = [float(t["stats"]["retainedPct"]) for t in tasks]
    refs = [float(t["stats"]["reference"]) for t in tasks]
    bests = [float(t["stats"]["best"]) for t in tasks]
    best_labels = [t["stats"]["bestLabel"] for t in tasks]
    best_ks = [int(t["stats"]["bestK"]) for t in tasks]
    ref_labels = [t["stats"]["referenceLabel"] for t in tasks]
    ref_ks = [int(t["stats"]["referenceK"]) for t in tasks]

    y = np.arange(len(tasks))[::-1]
    bars = ax_bar.barh(
        y,
        retained,
        height=0.62,
        color=[TASK_COLORS[t["id"]] for t in tasks],
        edgecolor="black",
        linewidth=0.9,
        zorder=3,
    )
    for yi, value, bar in zip(y, retained, bars):
        ax_bar.text(
            value + 1.2,
            yi,
            f"{value:.0f}%",
            va="center",
            ha="left",
            fontsize=STYLE.font_size + 1,
            fontweight="bold",
            color=bar.get_facecolor(),
        )
    ax_bar.set_yticks(y)
    ax_bar.set_yticklabels(labels)
    ax_bar.set_xlim(0, 118)
    ax_bar.set_xticks([0, 25, 50, 75, 100])
    ax_bar.set_xticklabels(["0", "25", "50", "75", "100%"])
    ax_bar.set_xlabel("score retained relative to the reference montage")
    reference_line(ax_bar, 100, None, COLORS["ink"], linestyle="--")
    tidy_axes(ax_bar, grid_axis="x")
    ax_bar.set_title(
        "A reduced montage keeps most of the score in every task",
        fontsize=STYLE.font_size,
        pad=6,
    )
    panel_label(ax_bar, "b", dx=-0.30, dy=1.02)

    # Absolute scores, so the bar is never the only number on the figure.
    for yi, task, best, best_label, best_k, ref, ref_label, ref_k in zip(
        y, tasks, bests, best_labels, best_ks, refs, ref_labels, ref_ks
    ):
        ax_bar.text(
            101,
            yi - 0.30,
            f"{best:.2f} · {best_label}, k={best_k}",
            va="center",
            ha="left",
            fontsize=STYLE.font_size - 4,
            color=COLORS["ink"],
        )
        ax_bar.text(
            101,
            yi + 0.28,
            f"reference {ref:.2f} · {ref_label}, k={ref_k}",
            va="center",
            ha="left",
            fontsize=STYLE.font_size - 4,
            color=COLORS["ink_soft"],
        )
    ax_bar.set_ylim(-0.7, len(tasks) - 0.3)

    finish(fig, pad=1.4)
    return save_figure(fig, out_dir, "fig1_overview", dpi=dpi)


if __name__ == "__main__":
    for path in build():
        print(f"wrote {path}")
