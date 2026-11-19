"""Figure 4 — the wearable gap is task-dependent.

Paired per-subject (and per-night) comparisons between scalp and ear
electrodes at a matched channel count. Every line is one participant; the
thick line is the group mean; the annotation is the paired difference with a
95% paired-t interval recomputed from the raw result CSVs.

Run:  .\\.venv\\Scripts\\python.exe figures\\plot_fig4_wearable_gap.py
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
    make_slopegraph,
    panel_label,
    reference_line,
    save_figure,
    tidy_axes,
)

STYLE = FigureStyle(font_size=13, axes_linewidth=1.6)
OUT = pd_.FIGURE_DIR

MA = "motor_execution_ear_vs_scalp"
SLEEP = "sleep_staging_local"


def delta_box(ax, text: str, x: float = 0.5, y: float = 0.06, color: str | None = None) -> None:
    ax.text(
        x,
        y,
        text,
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=STYLE.font_size - 3,
        color=color or COLORS["ink"],
    )


def build(out_dir: Path | str = OUT, dpi: int = 300) -> list[Path]:
    apply_publication_style(STYLE)
    bundle = pd_.load_bundle()

    fig = plt.figure(figsize=(13.2, 5.6), layout="constrained")
    grid = fig.add_gridspec(1, 2, width_ratios=[0.82, 1.18])

    # ------------------------------------------------- (a) motor execution
    ax = fig.add_subplot(grid[0, 0])
    p = pd_.paired(
        MA,
        "region-sensorimotor_k8",
        "wu2020_inear_k8",
        pipeline="riemann_tslr",
        protocol="within_session",
        label_a="Sensorimotor\nscalp, 8 ch",
        label_b="In-ear\n8 ch",
    )
    table = p.per_unit[["a", "b"]]
    make_slopegraph(
        ax,
        table,
        ["a", "b"],
        ["sensorimotor scalp\n8 ch", "in-ear\n8 ch"],
        [COLORS["sensorimotor"], COLORS["wearable"]],
    )
    reference = bundle.score(MA, "full_k115", pipeline="riemann_tslr")
    reference_line(ax, reference, f"full cap · {reference:.3f}", COLORS["reference"], label_dy=0.012)
    reference_line(ax, 0.5, "chance", COLORS["chance"], linestyle=":", label_dy=-0.05, label_va="top")
    ax.set_ylabel(p.metric_label)
    # Every subject has to stay on scale, including the 0.98-AUC outlier.
    values = table.to_numpy().ravel()
    span = float(values.max() - values.min())
    ax.set_ylim(float(values.min()) - 0.12 * span, float(values.max()) + 0.12 * span)
    tidy_axes(ax)
    ax.set_title(
        f"Motor execution: {pd_.fmt_delta(p.delta)} AUC "
        f"({p.n_negative}/{p.n} subjects)",
        fontsize=STYLE.font_size,
        pad=6,
    )
    delta_box(
        ax,
        f"paired Δ = {pd_.fmt_delta(p.delta)}  95% CI {p.ci_text(3)}\n",
        x=0.5,
        y=0.02,
    )
    panel_label(ax, "a", dx=-0.16)

    # ------------------------------------------------------------- (b) sleep
    ax2 = fig.add_subplot(grid[0, 1])
    p1 = pd_.paired(
        SLEEP, "scalp_6_k6", "ear_6_k6", pipeline="bandpower_lda", protocol="within_session"
    )
    p2 = pd_.paired(
        SLEEP, "ear_6_k6", "ear_14_k14", pipeline="bandpower_lda", protocol="within_session"
    )
    table2 = p1.per_unit[["a"]].rename(columns={"a": "scalp_6"})
    table2["ear_6"] = p1.per_unit["b"]
    table2["ear_14"] = p2.per_unit["b"]
    make_slopegraph(
        ax2,
        table2,
        ["scalp_6", "ear_6", "ear_14"],
        ["scalp\n6 ch", "ear\n6 ch", "ear\n14 ch"],
        [COLORS["reference"], COLORS["wearable"], COLORS["wearable_light"]],
        marker="o",
    )
    reference_line(ax2, 0.0, "chance (κ = 0)", COLORS["chance"], linestyle=":", label_dy=-0.02, label_va="top")
    ax2.set_ylabel(p1.metric_label)
    values2 = table2.to_numpy().ravel()
    span2 = float(values2.max() - values2.min())
    ax2.set_ylim(float(values2.min()) - 0.14 * span2, float(values2.max()) + 0.10 * span2)
    tidy_axes(ax2)
    ax2.set_title(
        f"Sleep staging: {pd_.fmt_delta(p1.delta)} κ at matched six "
        f"({p1.n_negative}/{p1.n} nights)",
        fontsize=STYLE.font_size,
        pad=6,
    )
    ax2.text(
        1.0,
        0.14,
        f"6 ear vs 6 scalp: Δ = {pd_.fmt_delta(p1.delta)}, 95% CI {p1.ci_text(3)}",
        ha="center",
        va="bottom",
        fontsize=STYLE.font_size - 3,
        color=COLORS["ink"],
    )
    ax2.text(
        2.0,
        0.44,
        f"all 14 ear vs 6 ear:\nΔ = {pd_.fmt_delta(p2.delta)}, 95% CI {p2.ci_text(3)}\n"
        f"{p2.n_positive}/{p2.n} nights improve",
        ha="center",
        va="bottom",
        fontsize=STYLE.font_size - 3,
        color=COLORS["ink_soft"],
    )
    panel_label(ax2, "b", dx=-0.11)

    finish(fig)
    return save_figure(fig, out_dir, "fig4_wearable_gap", dpi=dpi)


if __name__ == "__main__":
    for path in build():
        print(f"wrote {path}")
