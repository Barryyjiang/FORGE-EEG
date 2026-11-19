"""Figure 2 — the channel budget: what more electrodes buy, and where the
returns flatten.

Panel (a) is the motor-imagery sweep (max-spread vs sensorimotor region vs
random subsets). Panel (b) puts every task on one axis by expressing each
reduced montage as a percentage of that task's reference score.

Run:  .\\.venv\\Scripts\\python.exe figures\\plot_fig2_channel_budget.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt
import numpy as np

import paper_data as pd_
from figure_style import (
    COLORS,
    FigureStyle,
    apply_publication_style,
    finish,
    panel_label,
    save_figure,
    tidy_axes,
)

STYLE = FigureStyle(font_size=13, axes_linewidth=1.6)
OUT = pd_.FIGURE_DIR

MI = "mi_leftright_22ch"
MI_PIPELINE = "riemann_tslr"


def build(out_dir: Path | str = OUT, dpi: int = 300) -> list[Path]:
    apply_publication_style(STYLE)
    bundle = pd_.load_bundle()

    fig = plt.figure(figsize=(13.4, 5.4), layout="constrained")
    grid = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.0])

    # ------------------------------------------------------------------ (a)
    ax = fig.add_subplot(grid[0, 0])
    ks = [4, 8, 16]
    spread = [
        bundle.score(MI, f"distributed_k{k}", pipeline=MI_PIPELINE, protocol="within_session")
        for k in ks
    ]
    sensorimotor = [
        bundle.score(MI, f"region-sensorimotor_k{k}", pipeline=MI_PIPELINE, protocol="within_session")
        for k in (4, 8)
    ]
    bands = [
        pd_.random_band(bundle, MI, k, pipeline=MI_PIPELINE, protocol="within_session")
        for k in ks
    ]
    reference = bundle.score(MI, "full_k22", pipeline=MI_PIPELINE, protocol="within_session")
    chance = float(bundle.task(MI)["chance"])

    ax.fill_between(
        ks,
        [b["min"] for b in bands],
        [b["max"] for b in bands],
        color=COLORS["random"],
        alpha=0.55,
        linewidth=0,
        label="random subsets (min–max over seeds)",
        zorder=2,
    )
    ax.plot(
        ks,
        [b["mean"] for b in bands],
        color=COLORS["ink_soft"],
        linewidth=1.6,
        linestyle="--",
        marker="o",
        markersize=5,
        zorder=3,
    )
    ax.plot(
        ks,
        spread,
        color=COLORS["spread"],
        linewidth=2.4,
        marker="s",
        markersize=7,
        label="max-spread subset",
        zorder=4,
    )
    ax.plot(
        [4, 8],
        sensorimotor,
        color=COLORS["sensorimotor"],
        linewidth=2.4,
        marker="D",
        markersize=7,
        label="sensorimotor region",
        zorder=4,
    )
    ax.axhline(reference, color=COLORS["reference"], linestyle="--", linewidth=1.6, zorder=1)
    (cap_marker,) = ax.plot(
        [22], [reference], marker="*", markersize=15, color=COLORS["reference"], zorder=5,
        label="full cap (reference)",
    )
    (chance_line,) = ax.plot(
        [3.2, 26.5], [chance, chance], color=COLORS["chance"], linestyle=":", linewidth=1.5,
        zorder=1, label="chance",
    )

    handles = [
        plt.Line2D([], [], color=COLORS["spread"], marker="s", markersize=7, linewidth=2.4,
                   label="max-spread subset"),
        plt.Line2D([], [], color=COLORS["sensorimotor"], marker="D", markersize=7, linewidth=2.4,
                   label="sensorimotor region"),
        plt.Rectangle((0, 0), 1, 1, facecolor=COLORS["random"], alpha=0.55, linewidth=0,
                      label="random subsets (min–max)"),
        plt.Line2D([], [], color=COLORS["ink_soft"], marker="o", markersize=5, linewidth=1.6,
                   linestyle="--", label="random subsets (mean)"),
        cap_marker,
        chance_line,
    ]
    ax.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.14),
        ncol=3,
        fontsize=STYLE.font_size - 4,
        handletextpad=0.5,
        columnspacing=1.4,
    )

    ax.text(22.4, reference - 0.004, f"full cap, k=22 · {reference:.3f}",
            color=COLORS["reference"], fontsize=STYLE.font_size - 3, va="top", ha="left")

    for x, y in zip(ks, spread):
        ax.annotate(
            f"{y:.3f}",
            xy=(x, y),
            xytext=(0, -15),
            textcoords="offset points",
            ha="center",
            fontsize=STYLE.font_size - 4,
            color=COLORS["spread"],
        )
    for x, y in zip((4, 8), sensorimotor):
        ax.annotate(
            f"{y:.3f}",
            xy=(x, y),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            fontsize=STYLE.font_size - 4,
            color=COLORS["sensorimotor"],
        )

    ax.set_xlabel("electrodes used (k)")
    ax.set_ylabel(bundle.task(MI)["metricLabel"])
    ax.set_xlim(3.2, 26.5)
    ax.set_ylim(0.44, 0.95)
    ax.set_xticks([4, 8, 12, 16, 20, 22])
    tidy_axes(ax)
    ax.set_title(
        "Motor imagery: the first eight electrodes buy the most",
        fontsize=STYLE.font_size,
        pad=6,
    )
    panel_label(ax, "a", dx=-0.13)

    # ------------------------------------------------------------------ (b)
    ax2 = fig.add_subplot(grid[0, 1])
    reference_line_drawn = False
    for task in bundle.tasks:
        track = task["id"]
        pipeline = task["defaultPipeline"]
        protocol = task["defaultProtocol"]
        ref_value, ref_label, ref_k = bundle.reference(track, pipeline, protocol)
        reduced = bundle.rows[
            (bundle.rows["track"] == track)
            & (bundle.rows["pipeline"] == pipeline)
            & (bundle.rows["protocol"] == protocol)
            & (bundle.rows["strategy"].isin(["region", "distributed", "wearable"]))
        ]
        if task["id"] == "sleep_staging_local":
            # The matched six-channel comparison is the headline; the all-ear
            # montage is kept as the second point of the same series.
            reduced = reduced[reduced["subset"].isin(["ear_6_k6", "ear_14_k14"])]
        points = []
        for k, group in reduced.groupby("k"):
            best = group.loc[group["score"].idxmax()]
            points.append((int(k), 100.0 * float(best["score"]) / ref_value, best["subsetLabel"]))
        points.sort()
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        color = pd_.TASK_COLORS[track]
        marker = pd_.TASK_MARKERS[track]
        if len(points) > 1:
            ax2.plot(xs, ys, color=color, linewidth=1.6, alpha=0.75, zorder=3)
        label = (
            f"{pd_.SHORT[track]} (ref {ref_value:.2f} · {ref_label})"
            if task["id"] == "sleep_staging_local"
            else pd_.SHORT[track]
        )
        ax2.plot(
            xs,
            ys,
            linestyle="none",
            marker=marker,
            markersize=10,
            color=color,
            markeredgecolor="white",
            markeredgewidth=1.0,
            label=label,
            zorder=4,
        )
        for x, y, _label in points:
            below = y > 98
            ax2.annotate(
                f"{y:.0f}%",
                xy=(x, y),
                xytext=(0, -16 if below else 9),
                textcoords="offset points",
                ha="center",
                va="top" if below else "bottom",
                fontsize=STYLE.font_size - 4,
                color=color,
            )
        if not reference_line_drawn:
            ax2.axhline(100, color=COLORS["ink"], linestyle="--", linewidth=1.4, zorder=1)
            reference_line_drawn = True

    ax2.set_xlabel("electrodes used (k)")
    ax2.set_ylabel("score retained (% of the task's reference)")
    ax2.set_xlim(2.5, 17.5)
    ax2.set_ylim(70, 106)
    ax2.set_xticks([4, 6, 8, 10, 12, 14, 16])
    tidy_axes(ax2)
    ax2.legend(loc="lower right", ncol=1, fontsize=STYLE.font_size - 4)
    ax2.set_title(
        "Every task: four to eight electrodes recover most of the score",
        fontsize=STYLE.font_size,
        pad=6,
    )
    panel_label(ax2, "b", dx=-0.14)

    finish(fig)
    return save_figure(fig, out_dir, "fig2_channel_budget", dpi=dpi)


if __name__ == "__main__":
    for path in build():
        print(f"wrote {path}")
