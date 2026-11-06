"""Electrode montages: scalp regions and wearable layouts.

The `fidelity` field is the important one. It records how much we trust that the
electrode names correspond to a real device:

- ``measured``  electrodes of a real device, as published/documented
- ``proxy``     nearest standard 10-10 positions standing in for a device whose
                electrodes are not in the standard nomenclature (e.g. cEEGrid,
                in-ear cups). Good for geometry, NOT a claim about the device.
- ``synthetic`` invented layout for ablation only

Never report a ``proxy`` result as "accuracy of device X".
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

import numpy as np

from .names import normalize_name

Fidelity = Literal["measured", "proxy", "synthetic"]
Kind = Literal["region", "wearable", "full"]


@dataclass(frozen=True)
class Montage:
    """A named set of electrode names."""

    name: str
    channels: tuple[str, ...]
    kind: Kind
    fidelity: Fidelity
    note: str = ""

    @property
    def n_channels(self) -> int:
        return len(self.channels)

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return f"{self.name} ({self.n_channels}ch, {self.fidelity})"


# --------------------------------------------------------------------------
# Scalp regions. These are 10-10 names; most dense caps will only have a
# subset, so always intersect with the dataset before use.
# --------------------------------------------------------------------------

REGIONS: dict[str, Montage] = {
    "occipital": Montage(
        "occipital",
        ("Oz", "O1", "O2", "POz", "PO3", "PO4", "PO7", "PO8", "Iz"),
        "region",
        "measured",
        "Primary visual cortex. Default target region for SSVEP / c-VEP.",
    ),
    "parietal": Montage(
        "parietal",
        ("Pz", "P3", "P4", "P7", "P8", "P1", "P2", "P5", "P6", "POz"),
        "region",
        "measured",
        "Parietal association cortex; P300 / attention effects.",
    ),
    "sensorimotor": Montage(
        "sensorimotor",
        ("Cz", "C3", "C4", "FCz", "FC3", "FC4", "CPz", "CP3", "CP4",
         "C1", "C2", "C5", "C6"),
        "region",
        "measured",
        "Default target region for motor imagery.",
    ),
    "frontal": Montage(
        "frontal",
        ("Fz", "F3", "F4", "F7", "F8", "Fp1", "Fp2", "AF3", "AF4", "AF7",
         "AF8", "F1", "F2", "F5", "F6"),
        "region",
        "measured",
        "Frontal / prefrontal; also where dry headbands usually sit.",
    ),
    "temporal": Montage(
        "temporal",
        ("T7", "T8", "TP7", "TP8", "FT7", "FT8", "P7", "P8"),
        "region",
        "measured",
        "Lateral temporal; nearest scalp analogue of ear-EEG.",
    ),
}


# --------------------------------------------------------------------------
# Wearable layouts.
# --------------------------------------------------------------------------

WEARABLES: dict[str, Montage] = {
    # Commercial, documented electrode positions.
    "muse2": Montage(
        "muse2",
        ("TP9", "AF7", "AF8", "TP10"),
        "wearable",
        "measured",
        "InteraXon Muse 2 / Muse S. 4 dry electrodes, forehead + behind ears.",
    ),
    # A published, optimised 8-channel montage used in a real study.
    "thielen2021": Montage(
        "thielen2021",
        ("Fpz", "Iz", "O1", "O2", "Oz", "POz", "T7", "T8"),
        "wearable",
        "measured",
        "Thielen et al. 2021 c-VEP montage, optimised by Ahmadi et al. 2019. "
        "This is the strongest available 'subset beats a region' exemplar.",
    ),
    # Around-the-ear devices. cEEGrid electrodes are not in the 10-10
    # nomenclature, so these are the nearest ring of standard positions.
    "ceegrid_proxy": Montage(
        "ceegrid_proxy",
        ("FT9", "T7", "TP7", "TP9", "FT10", "T8", "TP8", "TP10"),
        "wearable",
        "proxy",
        "Nearest 10-10 ring approximating a cEEGrid (8 of the 20 electrodes). "
        "Geometry proxy only; cEEGrid is a flex-printed ear-adjacent array.",
    ),
    # Ear-EEG recorded simultaneously with a dense scalp cap: ground truth,
    # not a proxy, for the "does the wearable sit over the wrong cortex"
    # question.
    "wu2020_inear": Montage(
        "wu2020_inear",
        ("LF", "LB", "LOU", "LOD", "RF", "RB", "ROU", "ROD"),
        "wearable",
        "measured",
        "In-ear electrodes, Wu et al. 2020 (4 per ear: front, back, "
        "outer-upper, outer-down), recorded at the same time as a 122-channel "
        "scalp cap.",
    ),
    "earbud_proxy": Montage(
        "earbud_proxy",
        ("T7", "T8", "TP9", "TP10"),
        "wearable",
        "proxy",
        "Minimal in-ear / earbud proxy. Poorest expected SNR of the set.",
    ),
    "headband_proxy": Montage(
        "headband_proxy",
        ("Fp1", "Fp2", "AF7", "AF8"),
        "wearable",
        "proxy",
        "Frontal dry headband / sleep-band proxy.",
    ),
}


def montage(name: str) -> Montage:
    """Look up a montage by name across regions and wearables."""
    try:
        return REGIONS[name]
    except KeyError:
        pass
    try:
        return WEARABLES[name]
    except KeyError:
        raise KeyError(
            f"Unknown montage {name!r}. "
            f"Regions: {sorted(REGIONS)}. Wearables: {sorted(WEARABLES)}."
        ) from None


@lru_cache(maxsize=1)
def standard_positions() -> dict[str, np.ndarray]:
    """3-D positions from MNE's ``standard_1005`` montage.

    Returns name -> (x, y, z) in metres, head coordinates. Cached because
    building the montage is slow.
    """
    import warnings

    import mne

    # MNE 1.13 deprecated 'standard_1005' in favour of 'colin27_1005'.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        for candidate in ("colin27_1005", "standard_1005"):
            try:
                mont = mne.channels.make_standard_montage(candidate)
                break
            except (ValueError, KeyError):
                continue
        else:  # pragma: no cover - only if MNE renames again
            raise RuntimeError("No usable 1005 montage found in mne.channels")

    ch_pos = mont.get_positions()["ch_pos"]
    return {name: np.asarray(xyz, dtype=float) for name, xyz in ch_pos.items()}


def positions_for(ch_names: list[str]) -> dict[str, np.ndarray]:
    """Positions for the channels that exist in the standard 1005 montage.

    Matching is case-insensitive: datasets spell the same electrode ``Ft7`` and
    ``FT7``, and dropping the former silently shrinks the geometric subset.
    """
    all_pos = standard_positions()
    normalised = {normalize_name(name): xyz for name, xyz in all_pos.items()}
    found: dict[str, np.ndarray] = {}
    for ch in ch_names:
        xyz = normalised.get(normalize_name(ch))
        if xyz is not None:
            found[ch] = xyz
    return found


def resolve(m: Montage, available: list[str]) -> tuple[list[str], list[str]]:
    """Split a montage into (present, missing) w.r.t. a dataset's channels.

    Matching is case-insensitive and tolerant of an ``EEG`` prefix, because
    MOABB datasets disagree on capitalisation.
    """
    from .names import match_channels

    return match_channels(m.channels, available)
