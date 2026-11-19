"""Build the montage list for one track.

Shared by the single-dataset CLI and the suite runner so both produce the same
conditions. Keeping this in one place is what makes results across tracks
comparable.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from .montages import WEARABLES, positions_for
from .subsets import SubsetSpec, equal_n_specs, full_spec, wearable_spec


def build_specs(
    available: Sequence[str],
    ks: Iterable[int],
    *,
    wearables: bool = True,
    n_random: int = 3,
) -> list[SubsetSpec]:
    """Equal-N condition sets + full cap + wearable montages, de-duplicated.

    ``full`` is built from the positioned channels only, since EOG/ECG/ear
    channels cannot participate in geometric subsetting and would inflate the
    "full cap" baseline.
    """
    specs: list[SubsetSpec] = []

    # Full cap FIRST: when every channel is selected (e.g. an 8-electrode
    # dataset), the full cap is identical to the distributed subset and dedupe
    # would otherwise drop the reference that every delta is measured against.
    positioned = [c for c in available if c in positions_for(list(available))]
    if positioned:
        specs.append(full_spec(positioned))

    for k in ks:
        specs.extend(equal_n_specs(available, k, n_random=n_random))

    if wearables:
        for montage in WEARABLES.values():
            # Only physically measured wearable electrodes. Geometry proxies
            # (nearest 10-10 rings for cEEGrid/earbud/headband) are not device
            # measurements and are deliberately not part of the benchmark.
            if montage.fidelity != "measured":
                continue
            spec = wearable_spec(montage, available)
            if spec is not None:
                specs.append(spec)

    seen: set[tuple[str, ...]] = set()
    unique: list[SubsetSpec] = []
    for spec in specs:
        key = tuple(sorted(spec.channels))
        if key not in seen:
            seen.add(key)
            unique.append(spec)
    return unique
