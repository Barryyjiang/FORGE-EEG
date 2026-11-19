"""Figure 5 — decoder choice rivals montage choice.

Panel (a) holds the channels fixed and swaps the P300 decoder per subject.
Panel (b) shows both decoders at the full eight channels and at a
max-spread four, so the decoder gap can be read against the montage gap.
Panel (c) repeats the check on motor imagery with three decoders.

Run:  .\\.venv\\Scripts\\python.exe figures\\plot_fig5_decoder.py
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
    make_grouped_bar,
    make_slopegraph,
    panel_label,
    reference_line,
    save_figure,
    tidy_axes,
)

STYLE = FigureStyle(font_size=13, axes_linewidth=1.6)
OUT = pd_.FIGURE_DIR

P300 = "p300_8ch"
MI = "mi_leftright_22ch"

DECODER_LABELS = {
    "riemann_tslr": "Riemannian TSLR",
    "csp_lda": "CSP + LDA",
    "logvar_lda": "Log-variance + LDA",
    "xdawn_tslr": "xDAWN + Riemannian",
    "ssvep_cca": "CCA",
    "bandpower_lda": "Band-power + LDA",
}


def build(out_dir: Path | str = OUT, dpi: int = 300) -> list[Path]:
    apply_publication_style(STYLE)
    bundle = pd_.load_bundle()

    fig = plt.figure(figsize=(15.0, 5.2), layout="constrained")
    grid = fig.add_gridspec(1, 3, width_ratios=[0.9, 1.05, 1.05])

    # ------------------------------------------------------------------ (a)
    ax = fig.add_subplot(grid[0, 0])
    table = pd_.unit_table(
        P300,
        [
            ("logvar", "logvar_lda", "full_k8"),
            ("xdawn", "xdawn_tslr", "full_k8"),
        ],
        protocol="within_session",
    )
    stats = pd_.delta_stats(table, "logvar", "xdawn")
    means = make_slopegraph(
        ax,
        table,
        ["logvar", "xdawn"],
        ["log-variance\n+ LDA", "xDAWN +\nRiemannian"],
        [COLORS["wearable"], COLORS["reference"]],
    )
    reference_line(ax, 0.5, "chance", COLORS["chance"], linestyle=":", label_dy=0.012)
    ax.set_ylabel(bundle.task(P300)["metricLabel"])
    span = float(table.to_numpy().max() - table.to_numpy().min())
    ax.set_ylim(
        float(table.to_numpy().min()) - 0.18 * span,
        float(table.to_numpy().max()) + 0.12 * span,
    )
    tidy_axes(ax)
    ax.set_title("P300: eight channels, two decoders", fontsize=STYLE.font_size, pad=6)
    ax.text(
        0.5,
        0.02,
        f"mean {means[0]:.3f} → {means[1]:.3f}   Δ = {pd_.fmt_delta(stats.delta, 3)}\n"
        f"95% CI {stats.ci_text(3)}\n{stats.n_positive}/{stats.n} subjects improve",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=STYLE.font_size - 4,
        color=COLORS["ink"],
    )
    panel_label(ax, "a", dx=-0.17)

    # ------------------------------------------------------------------ (b)
    ax2 = fig.add_subplot(grid[0, 1])
    categories = ["Full cap\n8 ch", "Max-spread\n4 ch"]
    series = [
        [
            bundle.score(P300, "full_k8", pipeline="logvar_lda"),
            bundle.score(P300, "distributed_k4", pipeline="logvar_lda"),
        ],
        [
            bundle.score(P300, "full_k8", pipeline="xdawn_tslr"),
            bundle.score(P300, "distributed_k4", pipeline="xdawn_tslr"),
        ],
    ]
    make_grouped_bar(
        ax2,
        categories,
        series,
        ["Log-variance + LDA", "xDAWN + Riemannian"],
        ylabel=bundle.task(P300)["metricLabel"],
        colors=[COLORS["wearable"], COLORS["reference"]],
        annotate=True,
        fmt="{:.3f}",
        annotate_fontsize=STYLE.font_size - 2,
    )
    reference_line(
        ax2, 0.5, "chance", COLORS["chance"], linestyle=":", label_dy=0.012,
        x=0.98, label_ha="right",
    )
    ax2.set_ylim(0.4, 1.0)
    tidy_axes(ax2)
    ax2.legend(loc="upper left", fontsize=STYLE.font_size - 4)
    ax2.set_title("Montage effect vs decoder effect", fontsize=STYLE.font_size, pad=6)
    panel_label(ax2, "b", dx=-0.14)

    # ------------------------------------------------------------------ (c)
    ax3 = fig.add_subplot(grid[0, 2])
    decoders = ["riemann_tslr", "csp_lda", "logvar_lda"]
    values = [
        bundle.score(MI, "region-sensorimotor_k8", pipeline=decoder, protocol="within_session")
        for decoder in decoders
    ]
    errors = [
        float(bundle.row(MI, "region-sensorimotor_k8", pipeline=decoder, protocol="within_session")["sem"])
        for decoder in decoders
    ]
    x = np.arange(len(decoders))
    bars = ax3.bar(
        x,
        values,
        width=0.6,
        color=[COLORS["reference"], COLORS["spread"], COLORS["wearable"]],
        edgecolor="black",
        linewidth=1.0,
        zorder=3,
        yerr=errors,
        error_kw={"ecolor": COLORS["ink_soft"], "elinewidth": 1.3, "capsize": 5},
    )
    for xi, value, error in zip(x, values, errors):
        ax3.annotate(
            f"{value:.3f}",
            xy=(xi, value + (error if np.isfinite(error) else 0.0)),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            fontsize=STYLE.font_size - 1,
            fontweight="bold",
            color=COLORS["ink"],
        )
    reference = bundle.score(MI, "full_k22", pipeline="riemann_tslr", protocol="within_session")
    reference_line(ax3, reference, f"full cap · {reference:.3f}", COLORS["reference"], label_dy=0.006)
    reference_line(
        ax3, 0.5, "chance", COLORS["chance"], linestyle=":", label_dy=-0.012,
        label_va="top", x=0.98, label_ha="right",
    )
    ax3.set_xticks(x)
    ax3.set_xticklabels([DECODER_LABELS[d].replace(" + ", " +\n") for d in decoders])
    ax3.set_ylabel(bundle.task(MI)["metricLabel"])
    ax3.set_ylim(0.45, 1.0)
    tidy_axes(ax3)
    ax3.set_title("Motor imagery: same 8 sensorimotor channels", fontsize=STYLE.font_size, pad=6)
    panel_label(ax3, "c", dx=-0.16)

    finish(fig)
    return save_figure(fig, out_dir, "fig5_decoder", dpi=dpi)


if __name__ == "__main__":
    for path in build():
        print(f"wrote {path}")
