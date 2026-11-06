"""Generating electrode subsets.

The scientific point of this module is *equal-N comparison*. Asking "is a
region better than a subset?" is meaningless if the region has 9 electrodes and
the subset has 4. Every generator here produces fixed-size subsets so that
channel **count** is held constant and only channel **placement** varies.

`farthest_point_order` gives a nested ordering of all channels: the first k
entries are a spatially spread k-electrode subset. Prefixes of that one
ordering give a monotone accuracy-vs-k curve without re-running selection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
from scipy.spatial.distance import cdist

from .montages import Montage, positions_for


@dataclass(frozen=True)
class SubsetSpec:
    """One candidate electrode set to evaluate."""

    name: str
    channels: tuple[str, ...]
    strategy: str  # "full" | "region" | "distributed" | "random" | "wearable"
    fidelity: str = "measured"
    requested: int | None = None  # k before intersecting with the dataset

    @property
    def k(self) -> int:
        return len(self.channels)


def _distance_matrix(ch_names: Sequence[str]) -> tuple[list[str], np.ndarray]:
    pos = positions_for(list(ch_names))
    names = [c for c in ch_names if c in pos]
    if len(names) < 2:
        raise ValueError(
            "Need at least 2 channels with standard_1005 positions; got "
            f"{len(names)} of {len(ch_names)}. Pass positions explicitly or "
            "use a dataset with standard electrode names."
        )
    coords = np.array([pos[n] for n in names], dtype=float)
    return names, cdist(coords, coords)


def farthest_point_order(
    ch_names: Sequence[str],
    *,
    start: str | None = None,
) -> list[str]:
    """Order channels by greedy farthest-point sampling (max-min spread).

    Starts from the channel closest to the centroid (or ``start``), then
    repeatedly adds the channel farthest from everything already chosen. The
    resulting prefix of length k is a well-spread k-electrode subset.
    """
    names, dist = _distance_matrix(ch_names)

    if start is not None:
        if start not in names:
            raise KeyError(f"start={start!r} not among positioned channels")
        first = names.index(start)
    else:
        pos = positions_for(names)
        coords = np.array([pos[n] for n in names], dtype=float)
        centroid = coords.mean(axis=0)
        first = int(np.argmin(((coords - centroid) ** 2).sum(axis=1)))

    order = [first]
    nearest = dist[first].copy()
    nearest[first] = -np.inf
    while len(order) < len(names):
        nxt = int(np.argmax(nearest))
        order.append(nxt)
        nearest[nxt] = -np.inf
        nearest = np.minimum(nearest, dist[nxt])
    return [names[i] for i in order]


def random_order(ch_names: Sequence[str], *, seed: int = 0) -> list[str]:
    """A random ordering, for the chance-level control condition."""
    names = list(ch_names)
    np.random.default_rng(seed).shuffle(names)
    return names


def prefix_specs(
    ordering: Sequence[str],
    ks: Iterable[int],
    *,
    strategy: str,
    fidelity: str = "measured",
    name_prefix: str | None = None,
) -> list[SubsetSpec]:
    """Turn one nested ordering into one spec per k."""
    ordering = list(ordering)
    prefix = name_prefix or strategy
    specs = []
    for k in ks:
        k = min(int(k), len(ordering))
        if k < 2:
            continue
        specs.append(
            SubsetSpec(
                name=f"{prefix}_k{k}",
                channels=tuple(ordering[:k]),
                strategy=strategy,
                fidelity=fidelity,
                requested=k,
            )
        )
    return specs


def full_spec(available: Sequence[str]) -> SubsetSpec:
    """The whole cap — the ceiling every subset is compared against."""
    return SubsetSpec(
        name=f"full_k{len(available)}",
        channels=tuple(available),
        strategy="full",
        fidelity="measured",
        requested=len(available),
    )


def wearable_spec(m: Montage, available: Sequence[str]) -> SubsetSpec | None:
    """A wearable montage, intersected with what the dataset actually has."""
    from .names import match_channels

    present, _ = match_channels(m.channels, available)
    if len(present) < 2:
        return None
    return SubsetSpec(
        name=f"{m.name}_k{len(present)}",
        channels=tuple(present),
        strategy="wearable",
        fidelity=m.fidelity,
        requested=m.n_channels,
    )


def equal_n_specs(
    available: Sequence[str],
    k: int,
    *,
    regions: dict[str, Montage] | None = None,
    n_random: int = 3,
    seed: int = 0,
) -> list[SubsetSpec]:
    """Build every condition at a single fixed channel count ``k``.

    Produces, all with exactly ``k`` channels (unless the pool is smaller):

    - ``distributed``: globally spread subset (farthest-point prefix)
    - one ``region_*`` spec per region that has >= k channels
    - ``random_*``: ``n_random`` chance-level controls

    Compare ``distributed`` against ``region_*`` to answer "is it about
    location or about spread?" at matched N.
    """
    from .names import match_channels
    from .montages import REGIONS

    regions = REGIONS if regions is None else regions
    available = list(available)

    # Geometry-based strategies can only place channels that exist in the
    # standard montage. Datasets mix in EOG/ECG/ear channels with no 10-10
    # name; those must not enter farthest-point selection.
    positioned = positions_for(available)
    dropped = [c for c in available if c not in positioned]
    available = [c for c in available if c in positioned]
    if dropped:
        print(f"  (geometric subsets ignore {len(dropped)} non-10-10 "
              f"channel(s): {dropped})")

    if len(available) < k:
        return []

    specs: list[SubsetSpec] = []

    # Globally distributed subset.
    distributed = prefix_specs(
        farthest_point_order(available),
        [k],
        strategy="distributed",
        name_prefix="distributed",
    )
    specs.extend(distributed)

    # Each region, truncated to k by its own farthest-point ordering.
    for rname, mont in regions.items():
        present, _ = match_channels(mont.channels, available)
        if len(present) < k:
            continue
        ordered = farthest_point_order(present)
        specs.extend(
            prefix_specs(
                ordered,
                [k],
                strategy="region",
                name_prefix=f"region-{rname}",
            )
        )

    # Chance controls.
    for s in range(n_random):
        specs.extend(
            prefix_specs(
                random_order(available, seed=seed + s),
                [k],
                strategy="random",
                name_prefix=f"random-s{seed + s}",
            )
        )

    return specs
