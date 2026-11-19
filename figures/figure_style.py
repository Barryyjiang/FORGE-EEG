"""Publication figure toolkit for The Electrode Budget.

This module implements the house style documented by the
``scientific-figure-making`` skill in ChenLiu-1996/figures4papers: a semantic
palette, a ``FigureStyle`` preset, minimal spines, frameless legends, and
vector + raster export at 300 dpi.

Everything here is generic; the paper-specific data access lives in
``paper_data.py`` and the head-map drawing in ``eeg_maps.py``.

Usage::

    from figure_style import apply_publication_style, FigureStyle, finalize_figure
    apply_publication_style(FigureStyle(font_size=13, axes_linewidth=1.8))
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Semantic colour map for publication figures (figures4papers palette).
PALETTE = {
    "blue_main": "#0F4D92",
    "blue_secondary": "#3775BA",
    "green_1": "#DDF3DE",
    "green_2": "#AADCA9",
    "green_3": "#8BCF8B",
    "red_1": "#F6CFCB",
    "red_2": "#E9A6A1",
    "red_strong": "#B64342",
    "neutral": "#CFCECE",
    "highlight": "#FFD700",
    "teal": "#42949E",
    "violet": "#9A4D8E",
    "ink": "#272727",
    "ink_soft": "#4D4D4D",
    "grid": "#E4E4E4",
}

#: Ordered fallback colours when a helper is not given explicit colours.
DEFAULT_COLORS = [
    PALETTE["blue_main"],
    PALETTE["green_3"],
    PALETTE["red_strong"],
    PALETTE["teal"],
    PALETTE["violet"],
    PALETTE["neutral"],
]

#: Semantic roles used across the benchmark figures. Keeping the mapping in one
#: place is what makes montage colours comparable between panels.
COLORS = {
    "reference": PALETTE["blue_main"],      # full cap / dense scalp
    "spread": PALETTE["blue_secondary"],    # max-spread subset
    "sensorimotor": PALETTE["green_3"],     # sensorimotor region
    "frontal": PALETTE["teal"],
    "temporal": PALETTE["violet"],
    "parietal": PALETTE["green_2"],
    "wearable": PALETTE["red_strong"],      # in-ear / ear electrodes
    "wearable_light": PALETTE["red_2"],
    "random": PALETTE["neutral"],
    "chance": PALETTE["ink_soft"],
    "scalp": PALETTE["blue_main"],
    "ear": PALETTE["red_strong"],
    "decoder_alt": PALETTE["red_strong"],
    "ink": PALETTE["ink"],
    "ink_soft": PALETTE["ink_soft"],
    "highlight": PALETTE["highlight"],
}

SUPPORTED_FORMATS = ("pdf", "svg", "eps", "png", "jpg", "jpeg", "tif", "tiff")


# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FigureStyle:
    """rcParams preset for publication figures.

    ``font_size`` 13-16 suits compact paper panels; the figures4papers demos
    use 24 for large bar canvases. ``axes_linewidth`` 1.8-2.5 matches the
    spine weight those demos use at their canvas sizes.
    """

    font_size: int = 14
    axes_linewidth: float = 1.8
    use_tex: bool = False
    font_family: tuple[str, ...] = (
        "Arial",
        "Helvetica",
        "DejaVu Sans",
        "sans-serif",
    )


def resolve_font_stack(
    candidates: Sequence[str] | None = None,
) -> list[str]:
    """Keep the candidate fonts that are actually installed.

    The house style asks for an Arial/Helvetica stack; on a machine without
    Helvetica we would otherwise get a warning per text object. The generic
    ``sans-serif`` family is always kept as the final fallback.
    """

    candidates = list(candidates or FigureStyle().font_family)
    installed = {font.name for font in matplotlib.font_manager.fontManager.ttflist}
    stack = [name for name in candidates if name in installed]
    if "sans-serif" not in stack:
        stack.append("sans-serif")
    return stack


def apply_publication_style(style: FigureStyle | None = None) -> FigureStyle:
    """Configure matplotlib for print-quality, minimalist figures."""

    style = style or FigureStyle()
    plt.rcParams.update(
        {
            "font.family": resolve_font_stack(style.font_family),
            "font.size": style.font_size,
            "axes.titlesize": style.font_size + 1,
            "axes.labelsize": style.font_size,
            "xtick.labelsize": style.font_size - 2,
            "ytick.labelsize": style.font_size - 2,
            "legend.fontsize": style.font_size - 3,
            "axes.spines.right": False,
            "axes.spines.top": False,
            "axes.linewidth": style.axes_linewidth,
            "axes.edgecolor": PALETTE["ink"],
            "axes.labelcolor": PALETTE["ink"],
            "text.color": PALETTE["ink"],
            "xtick.color": PALETTE["ink_soft"],
            "ytick.color": PALETTE["ink_soft"],
            "xtick.direction": "out",
            "ytick.direction": "out",
            "legend.frameon": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "text.usetex": style.use_tex,
        }
    )
    return style


def create_subplots(nrows: int = 1, ncols: int = 1, figsize=None, **kwargs):
    """Return ``(fig, axes)`` with ``axes`` as a flat 1-D array."""

    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, **kwargs)
    return fig, np.atleast_1d(axes).ravel()


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def finalize_figure(
    fig,
    out_path: str | Path,
    formats: Sequence[str] | None = None,
    dpi: int = 300,
    close: bool = True,
    pad: float = 0.05,
) -> list[Path]:
    """Save ``fig`` to one or more formats next to ``out_path``.

    ``out_path`` may carry a suffix; it is stripped and replaced per format.
    Parent directories are created. Returns the written paths.
    """

    out = Path(out_path)
    if formats is None:
        formats = [out.suffix.lstrip(".") or "pdf"]
    formats = [f.lower().lstrip(".") for f in formats]
    bad = [f for f in formats if f not in SUPPORTED_FORMATS]
    if bad:
        raise ValueError(f"unsupported format(s): {bad}")

    base = out.with_suffix("")
    saved: list[Path] = []
    for fmt in formats:
        path = base.with_suffix(f".{fmt}")
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=dpi, bbox_inches="tight", pad_inches=pad)
        saved.append(path)
    if close:
        plt.close(fig)
    return saved


# ---------------------------------------------------------------------------
# Plot helpers
# ---------------------------------------------------------------------------


def _as_array(values, ndim: int = 1) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.ndim != ndim:
        raise ValueError(f"expected {ndim}-D data, got shape {arr.shape}")
    return arr


def make_grouped_bar(
    ax,
    categories: Sequence[str],
    series: Sequence[Sequence[float]],
    labels: Sequence[str],
    ylabel: str = "Value",
    colors: Sequence[str] | None = None,
    annotate: bool = False,
    fmt: str = "{:.2f}",
    width: float = 0.8,
    annotate_fontsize: int | None = None,
    edgecolor: str = "black",
    linewidth: float = 1.0,
):
    """Grouped bars: ``series[i][j]`` is group *i* at category *j*."""

    cats = list(categories)
    array = np.asarray(series, dtype=float)
    if array.ndim != 2:
        raise ValueError("series must be a list of equal-length sequences")
    if array.shape[1] != len(cats):
        raise ValueError(
            f"len(categories)={len(cats)} does not match series width "
            f"{array.shape[1]}"
        )
    colors = list(colors) if colors else DEFAULT_COLORS
    n_groups = array.shape[0]
    x = np.arange(len(cats), dtype=float)
    slot = width / n_groups
    last = None
    for i in range(n_groups):
        offset = (i - (n_groups - 1) / 2) * slot
        last = ax.bar(
            x + offset,
            array[i],
            slot * 0.92,
            label=labels[i],
            color=colors[i % len(colors)],
            edgecolor=edgecolor,
            linewidth=linewidth,
        )
        if annotate:
            annotate_bars(
                ax, last, fmt=fmt, fontsize=annotate_fontsize, padding=2
            )
    ax.set_xticks(x)
    ax.set_xticklabels(cats)
    ax.set_ylabel(ylabel)
    return last


def annotate_bars(ax, bars, fmt: str = "{:.2f}", fontsize: int | None = None, padding: int = 3):
    """Print each bar's value just above it."""

    for rect in bars:
        height = rect.get_height()
        if not math.isfinite(height):
            continue
        ax.annotate(
            fmt.format(height),
            xy=(rect.get_x() + rect.get_width() / 2, height),
            xytext=(0, padding),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=fontsize,
            color=PALETTE["ink"],
        )


def make_trend(
    ax,
    x: Sequence[float],
    y_series: Sequence[Sequence[float]],
    labels: Sequence[str],
    colors: Sequence[str] | None = None,
    ylabel: str | None = None,
    xlabel: str | None = None,
    show_shadow: bool = True,
    shadow: Sequence | None = None,
    marker: str = "o",
    linewidth: float = 2.2,
):
    """Plot one or more series against ``x``.

    ``shadow`` optionally supplies ``(lower, upper)`` bands, one per series,
    drawn with ``fill_between``.
    """

    x = _as_array(x)
    colors = list(colors) if colors else DEFAULT_COLORS
    lines = []
    for i, y in enumerate(y_series):
        y = _as_array(y)
        if y.shape[0] != x.shape[0]:
            raise ValueError("each series must have the same length as x")
        (line,) = ax.plot(
            x,
            y,
            marker=marker,
            color=colors[i % len(colors)],
            linewidth=linewidth,
            label=labels[i],
        )
        lines.append(line)
        if show_shadow and shadow is not None:
            lo, hi = shadow[i]
            ax.fill_between(
                x,
                _as_array(lo),
                _as_array(hi),
                color=colors[i % len(colors)],
                alpha=0.18,
                linewidth=0,
            )
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    return lines


def make_scatter(
    ax,
    x: Sequence[float],
    y: Sequence[float],
    label: str | None = None,
    color: str | None = None,
    size: float = 50,
    alpha: float = 0.7,
    **kwargs,
):
    """Single-series scatter."""

    x = _as_array(x)
    y = _as_array(y)
    if x.shape != y.shape:
        raise ValueError("x and y must have the same length")
    return ax.scatter(
        x,
        y,
        s=size,
        alpha=alpha,
        label=label,
        color=color or PALETTE["blue_main"],
        **kwargs,
    )


def make_heatmap(
    ax,
    matrix,
    x_labels: Sequence[str] | None = None,
    y_labels: Sequence[str] | None = None,
    cmap: str = "magma",
    cbar_label: str | None = None,
    annotate: bool = False,
    fmt: str = "{:.2f}",
):
    """Render a 2-D matrix as a heatmap."""

    matrix = _as_array(matrix, ndim=2)
    image = ax.imshow(matrix, cmap=cmap, aspect="auto")
    if x_labels is not None:
        ax.set_xticks(np.arange(len(x_labels)))
        ax.set_xticklabels(x_labels)
    if y_labels is not None:
        ax.set_yticks(np.arange(len(y_labels)))
        ax.set_yticklabels(y_labels)
    if annotate:
        for (i, j), value in np.ndenumerate(matrix):
            ax.text(
                j,
                i,
                fmt.format(value),
                ha="center",
                va="center",
                color="white" if value < matrix.mean() else PALETTE["ink"],
                fontsize=plt.rcParams["font.size"] - 3,
            )
    if cbar_label:
        cbar = ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.02)
        cbar.set_label(cbar_label, fontsize=plt.rcParams["font.size"] - 1)
        cbar.outline.set_visible(False)
    return image


def make_slopegraph(
    ax,
    table,
    columns: Sequence[str],
    labels: Sequence[str],
    colors: Sequence[str],
    marker: str = "o",
    subject_color: str = "#BFBFBF",
    subject_linewidth: float = 1.0,
    subject_markersize: float = 4.5,
    mean_markersize: float = 13.0,
    mean_linewidth: float = 2.6,
):
    """Paired slopegraph: one thin line per unit, one thick line for the mean.

    ``table`` is any mapping-like table with one column per condition
    (a pandas DataFrame works); every row is one participant/session.
    """

    x = np.arange(len(columns), dtype=float)
    for _, row in table.iterrows():
        values = [float(row[column]) for column in columns]
        ax.plot(x, values, color=subject_color, linewidth=subject_linewidth, zorder=2)
        ax.plot(
            x,
            values,
            linestyle="none",
            marker=marker,
            markersize=subject_markersize,
            color=subject_color,
            zorder=3,
        )
    means = [float(table[column].mean()) for column in columns]
    ax.plot(x, means, color=PALETTE["ink_soft"], linewidth=mean_linewidth, zorder=4)
    for xi, mean, color in zip(x, means, colors):
        ax.plot(
            [xi],
            [mean],
            linestyle="none",
            marker=marker,
            markersize=mean_markersize,
            color=color,
            markeredgecolor="white",
            markeredgewidth=1.4,
            zorder=5,
        )
    ax.set_xticks(x)
    ax.set_xticklabels(list(labels))
    ax.set_xlim(-0.35, len(columns) - 0.65)
    return means


def make_sphere_illustration(
    ax,
    light_dir: tuple[float, float, float] = (-0.5, 0.5, 0.8),
    resolution: int = 128,
    alpha: float = 0.6,
):
    """Draw a shaded disk that reads as a 3-D sphere (concept figures)."""

    grid = np.linspace(-1, 1, resolution)
    xx, yy = np.meshgrid(grid, grid)
    rr = xx**2 + yy**2
    inside = rr <= 1.0
    zz = np.zeros_like(xx)
    zz[inside] = np.sqrt(1.0 - rr[inside])
    light = np.asarray(light_dir, dtype=float)
    light = light / np.linalg.norm(light)
    shade = np.clip(xx * light[0] + yy * light[1] + zz * light[2], 0, 1)
    shade = np.where(inside, shade, np.nan)
    return ax.imshow(
        shade,
        cmap="Blues",
        origin="lower",
        extent=(-1, 1, -1, 1),
        alpha=alpha,
        vmin=0,
        vmax=1,
    )


# ---------------------------------------------------------------------------
# Paper-specific conveniences (kept here so every figure shares them)
# ---------------------------------------------------------------------------


def tidy_axes(ax, grid_axis: str | None = "y", gridcolor: str | None = None):
    """Light grid behind the data, drawn under the bars/lines."""

    if grid_axis:
        ax.grid(
            axis=grid_axis,
            color=gridcolor or PALETTE["grid"],
            linewidth=0.8,
            zorder=0,
        )
        ax.set_axisbelow(True)
    return ax


def line_label(
    ax,
    value: float,
    text: str,
    color: str | None = None,
    dy: float = 0.008,
    x: float = 0.02,
    va: str = "bottom",
    ha: str = "left",
    fontsize: int | None = None,
):
    """Label a horizontal line in data coordinates.

    x is an axes fraction, y is the line's data value plus ``dy``, so the same
    call works whatever the y-scale is.
    """

    from matplotlib.transforms import blended_transform_factory

    trans = blended_transform_factory(ax.transAxes, ax.transData)
    return ax.text(
        x,
        value + dy,
        text,
        transform=trans,
        color=color or PALETTE["blue_main"],
        fontsize=fontsize or plt.rcParams["font.size"] - 3,
        va=va,
        ha=ha,
        zorder=6,
    )


def reference_line(
    ax,
    value: float,
    label: str | None = None,
    color: str | None = None,
    linestyle: str = "--",
    linewidth: float = 1.6,
    label_dy: float = 0.008,
    label_va: str = "bottom",
    x: float = 0.02,
    label_ha: str = "left",
):
    """Horizontal reference line (full cap / chance) with an inline label."""

    color = color or PALETTE["blue_main"]
    ax.axhline(value, color=color, linestyle=linestyle, linewidth=linewidth, zorder=1)
    if label:
        line_label(
            ax, value, label, color=color, dy=label_dy, va=label_va, x=x, ha=label_ha
        )
    return ax


def panel_label(ax, text: str, dx: float = -0.085, dy: float = 1.06):
    """Bold panel letter (a, b, c) at the top-left of an axes."""

    ax.text(
        dx,
        dy,
        text,
        transform=ax.transAxes,
        fontsize=plt.rcParams["font.size"] + 2,
        fontweight="bold",
        va="bottom",
        ha="left",
        color=PALETTE["ink"],
    )
    return ax


def value_label(ax, x, y, text: str, color: str | None = None, dx: float = 0.0, dy: float = 0.0, ha: str = "center", va: str = "bottom", fontsize: int | None = None, fontweight: str = "normal"):
    """Free text annotation in data coordinates."""

    return ax.text(
        x + dx,
        y + dy,
        text,
        color=color or PALETTE["ink"],
        ha=ha,
        va=va,
        fontsize=fontsize,
        fontweight=fontweight,
    )


def finish(fig, pad: float = 1.2):
    """Consistent layout pass before export.

    Figures that already use a layout engine (constrained/tight) are left
    alone; calling ``tight_layout`` on them only warns.
    """

    if fig.get_layout_engine() is None:
        fig.tight_layout(pad=pad)
    return fig


def save_figure(fig, out_dir: str | Path, name: str, dpi: int = 300) -> list[Path]:
    """Export every paper figure as both PNG (page) and PDF (vector)."""

    return finalize_figure(
        fig, Path(out_dir) / name, formats=["png", "pdf"], dpi=dpi
    )


def wrap(text: str, width: int) -> str:
    """Tiny word wrapper for figure titles (avoids textwrap import noise)."""

    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = " ".join([*current, word])
        if len(trial) > width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines)


def iter_pairs(values: Iterable) -> Iterable[tuple]:
    """Yield consecutive pairs (used by the slopegraph helper)."""

    items = list(values)
    return zip(items[:-1], items[1:])
