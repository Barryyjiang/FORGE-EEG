"""Top-down electrode maps for the paper figures.

Positions come from ``docs/data/benchmark.json`` -> ``positions``: scalp sites
are standard 10-5 locations projected top-down, ear sites are schematic
(benchmarked datasets record ear electrodes that are not part of the 10-5
nomenclature).

Everything is drawn at the normalised scale used by that bundle: the head
outline is a circle of radius ~1 centred slightly below the origin.
"""

from __future__ import annotations

from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Ellipse, Polygon, Wedge

from figure_style import PALETTE

#: Head outline in normalised coordinates (matches the bundle positions).
HEAD_CENTER = (0.0, -0.04)
HEAD_RADIUS = 1.02

#: Channel labels that are ear electrodes rather than scalp sites.
EAR_HINTS = ("EL", "ER", "LF", "LB", "LO", "RF", "RB", "RO")


def is_ear(channel: str) -> bool:
    """True for the schematic ear labels used by Wu 2020 and ds004348."""

    return channel.startswith(EAR_HINTS)


@dataclass(frozen=True)
class MontageStyle:
    background: str = "#D8D8D8"
    foreground: str = PALETTE["blue_main"]
    edge: str = "#FFFFFF"
    background_size: float = 34.0
    highlight_size: float = 118.0
    outline: str = PALETTE["ink_soft"]
    linewidth: float = 1.6


def draw_head(
    ax,
    positions: dict[str, tuple[float, float]],
    highlight: dict[str, str] | None = None,
    style: MontageStyle | None = None,
    show_nose: bool = True,
    show_ears: bool = True,
    annotate: dict[str, str] | None = None,
    label_fontsize: int = 7,
) -> None:
    """Draw a top-down head with an optional coloured montage on top.

    ``highlight`` maps channel name -> colour. Channels in ``positions`` that
    are not in ``highlight`` are drawn as light background dots.
    """

    style = style or MontageStyle()
    highlight = highlight or {}
    annotate = annotate or {}

    cx, cy = HEAD_CENTER
    ax.add_patch(
        Circle(
            (cx, cy),
            HEAD_RADIUS,
            fill=False,
            edgecolor=style.outline,
            linewidth=style.linewidth,
            zorder=1,
        )
    )

    if show_nose:
        ax.add_patch(
            Polygon(
                [
                    (cx - 0.13, cy + HEAD_RADIUS - 0.02),
                    (cx + 0.13, cy + HEAD_RADIUS - 0.02),
                    (cx, cy + HEAD_RADIUS + 0.16),
                ],
                closed=True,
                facecolor="none",
                edgecolor=style.outline,
                linewidth=style.linewidth,
                zorder=1,
            )
        )

    if show_ears:
        for side in (-1, 1):
            ax.add_patch(
                Ellipse(
                    (cx + side * (HEAD_RADIUS + 0.06), cy - 0.02),
                    0.22,
                    0.52,
                    fill=False,
                    edgecolor=style.outline,
                    linewidth=style.linewidth * 0.8,
                    zorder=1,
                )
            )

    # Background electrodes first, so highlighted ones sit on top.
    background = [
        (name, xy)
        for name, xy in positions.items()
        if name not in highlight and not is_ear(name)
    ]
    if background:
        xs = [xy[0] for _, xy in background]
        ys = [xy[1] for _, xy in background]
        ax.scatter(
            xs,
            ys,
            s=style.background_size,
            facecolor=style.background,
            edgecolor="none",
            zorder=2,
        )

    if highlight:
        xs = [positions[name][0] for name in highlight if name in positions]
        ys = [positions[name][1] for name in highlight if name in positions]
        colors = [highlight[name] for name in highlight if name in positions]
        ax.scatter(
            xs,
            ys,
            s=style.highlight_size,
            facecolor=colors,
            edgecolor=style.edge,
            linewidths=1.1,
            zorder=3,
        )

    for name in annotate:
        if name not in positions:
            continue
        x, y = positions[name]
        ax.annotate(
            annotate[name],
            xy=(x, y),
            xytext=(0, -14),
            textcoords="offset points",
            ha="center",
            va="top",
            fontsize=label_fontsize,
            color=PALETTE["ink_soft"],
            zorder=4,
        )

    ax.set_aspect("equal")
    ax.set_xlim(cx - HEAD_RADIUS - 0.34, cx + HEAD_RADIUS + 0.34)
    ax.set_ylim(cy - HEAD_RADIUS - 0.22, cy + HEAD_RADIUS + 0.30)
    ax.set_axis_off()


def montage_map(
    positions: dict[str, tuple[float, float]],
    channels: list[str],
    color: str,
    background: list[str] | None = None,
) -> dict[str, str]:
    """Colour map for one montage: ``channels`` in ``color``."""

    return {name: color for name in channels if name in positions}


def combined_map(*maps: dict[str, str]) -> dict[str, str]:
    """Merge several montage maps (later entries win)."""

    merged: dict[str, str] = {}
    for mapping in maps:
        merged.update(mapping)
    return merged


def legend_swatch(ax, entries: list[tuple[str, str]], loc: str = "lower center", ncol: int = 3, size: float = 60.0, **kwargs):
    """Draw a standalone colour legend for montage maps.

    ``entries`` is a list of ``(colour, label)`` pairs.
    """

    handles = [
        ax.scatter([], [], s=size, facecolor=color, edgecolor="#FFFFFF", linewidths=1.0, label=label)
        for color, label in entries
    ]
    handles.append(
        ax.scatter([], [], s=size * 0.45, facecolor="#D8D8D8", edgecolor="none", label="other electrodes")
    )
    return ax.legend(handles=handles, loc=loc, ncol=ncol, handletextpad=0.4, columnspacing=1.1, borderpad=0.2, **kwargs)


def region_wedge(ax, region: str, color: str, alpha: float = 0.10) -> None:
    """Soft shaded region (used to explain anatomical groupings)."""

    spans = {
        "sensorimotor": (255, 75),
        "frontal": (45, 90),
        "temporal": (165, 55),
        "occipital": (255, 60),
    }
    if region not in spans:
        return
    theta1, extent = spans[region]
    cx, cy = HEAD_CENTER
    ax.add_patch(
        Wedge(
            (cx, cy),
            HEAD_RADIUS,
            theta1,
            theta1 + extent,
            facecolor=color,
            edgecolor="none",
            alpha=alpha,
            zorder=0,
        )
    )


def head_row(
    fig,
    axes,
    positions: dict[str, tuple[float, float]],
    panels: list[dict],
    background: list[str] | None = None,
) -> None:
    """Draw a row of montage panels with titles and value subtitles.

    Each panel is ``{"channels": [...], "color": str, "title": str,
    "subtitle": str}``.
    """

    for ax, panel in zip(axes, panels):
        highlight = montage_map(
            positions, panel["channels"], panel.get("color", PALETTE["blue_main"])
        )
        subset_positions = (
            {name: positions[name] for name in background if name in positions}
            if background
            else positions
        )
        draw_head(ax, subset_positions, highlight=highlight)
        ax.set_title(panel["title"], fontsize=plt.rcParams["font.size"] - 1, pad=2)
        if panel.get("subtitle"):
            ax.text(
                0.5,
                0.02,
                panel["subtitle"],
                transform=ax.transAxes,
                ha="center",
                va="bottom",
                fontsize=plt.rcParams["font.size"] + 1,
                fontweight="bold",
                color=panel.get("color", PALETTE["ink"]),
            )


def channels_in_region(positions: dict[str, tuple[float, float]], region: str) -> list[str]:
    """Channels whose normalised position falls in a coarse scalp region.

    Used for annotations only; benchmark montages come from the CSV rows, not
    from this helper.
    """

    out = []
    for name, (x, y) in positions.items():
        if is_ear(name):
            continue
        if region == "frontal" and y > 0.35:
            out.append(name)
        elif region == "sensorimotor" and -0.35 <= y <= 0.35 and abs(x) < 0.95:
            out.append(name)
        elif region == "temporal" and abs(x) > 0.6 and -0.45 < y < 0.25:
            out.append(name)
        elif region == "occipital" and y < -0.45:
            out.append(name)
    return sorted(out)


def map_extent(positions: dict[str, tuple[float, float]]) -> tuple[float, float]:
    """Largest |x| in the position set (for aspect sanity checks)."""

    xs = [abs(x) for x, _ in positions.values()]
    return (min(xs), max(xs))


def head_figure_grid(
    ncols: int,
    figsize: tuple[float, float],
    height_ratios: list[float] | None = None,
):
    """Create a grid whose top row holds montage panels."""

    fig, axes = plt.subplots(
        2 if height_ratios else 1,
        ncols,
        figsize=figsize,
        gridspec_kw={"height_ratios": height_ratios} if height_ratios else None,
    )
    return fig, np.atleast_1d(axes)
