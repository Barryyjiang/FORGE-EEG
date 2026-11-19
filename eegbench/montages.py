"""Electrode montages: scalp regions and measured wearable layouts.

The `fidelity` field records how much we trust that the electrode names
correspond to a real device:

- ``measured``  electrodes of a real device, as published/documented
- ``synthetic`` invented layout for ablation only

Only measured wearable montages belong in the benchmark. A nearest-10-10 ring
is a geometry experiment, not a measurement of the device, and mixing the two
makes a result impossible to interpret.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

import numpy as np

from .names import normalize_name

Fidelity = Literal["measured", "proxy", "synthetic"]
Kind = Literal["region", "wearable", "full"]

#: Schematic positions for ear electrodes, normalised to the head circle
#: (x = left/right, y = front/back, origin at the centre of the head).
#:
#: These labels are not in the 10-5 nomenclature — ``cEL1`` is a wet electrode on
#: a C-shaped holder, not a scalp site — so they are drawn and subset from this
#: table rather than looked up in MNE's montage. The values are schematic: enough
#: to pick a spatially spread subset and draw a head map, not a claim about where
#: the electrodes actually sat. The released Ear-SAAD data ships no coordinates.
EAR_POSITIONS: dict[str, tuple[float, float]] = {
    # Wu2020: four per ear (front, back, outer-upper, outer-down)
    "LF": (-0.98, 0.16), "LB": (-0.98, -0.10),
    "LOU": (-1.06, 0.07), "LOD": (-1.06, -0.02),
    "RF": (0.98, 0.16), "RB": (0.98, -0.10),
    "ROU": (1.06, 0.07), "ROD": (1.06, -0.02),
    # ds004348: seven per ear, arranged around the ear
    "ELA": (-0.94, 0.20), "ELE": (-1.02, 0.15), "ELI": (-1.07, 0.06),
    "ELB1": (-1.07, -0.03), "ELB": (-1.03, -0.12), "ELG": (-0.96, -0.19),
    "ELK": (-0.88, -0.24),
    "ERA": (0.94, 0.20), "ERE": (1.02, 0.15), "ERI": (1.07, 0.06),
    "ERB1": (1.07, -0.03), "ERB": (1.03, -0.12), "ERG": (0.96, -0.19),
    "ERK": (0.88, -0.24),
    # Ear-SAAD in-ear: six per ear on the custom earpieces. ELC/ELT/ERC/ERT are
    # the four this dataset has that ds004348 does not.
    "ELC": (-1.06, -0.03), "ELT": (-0.95, -0.20),
    "ERC": (1.06, -0.03), "ERT": (0.95, -0.20),
}

#: Ear-SAAD around-ear: 19 wet electrodes on a C-shaped holder, 9 left and 10
#: right, placed on an arc hugging the outside of each ear.
for _i in range(1, 10):
    _deg = 110.0 + (250.0 - 110.0) * (_i - 1) / 8.0
    EAR_POSITIONS[f"cEL{_i}"] = (
        round(-1.0 + 0.20 * np.cos(np.radians(_deg)), 4),
        round(0.20 * np.sin(np.radians(_deg)), 4),
    )
for _i in range(1, 11):
    _deg = 70.0 - (70.0 + 70.0) * (_i - 1) / 9.0
    EAR_POSITIONS[f"cER{_i}"] = (
        round(1.0 + 0.20 * np.cos(np.radians(_deg)), 4),
        round(0.20 * np.sin(np.radians(_deg)), 4),
    )

#: Head radius in metres, used to lift the schematic ear coordinates into the
#: same units as the 10-5 montage so the two can be compared and mixed.
_HEAD_RADIUS_M = 0.09


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
    # Ear-EEG recorded simultaneously with a dense scalp cap: ground truth for
    # the "does the wearable sit over the wrong cortex" question.
    "wu2020_inear": Montage(
        "wu2020_inear",
        ("LF", "LB", "LOU", "LOD", "RF", "RB", "ROU", "ROD"),
        "wearable",
        "measured",
        "In-ear electrodes, Wu et al. 2020 (4 per ear: front, back, "
        "outer-upper, outer-down), recorded at the same time as a 115-channel "
        "scalp EEG cap.",
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
    """Positions for the channels the benchmark can place.

    Scalp names come from MNE's 10-5 montage. Matching there is case-insensitive:
    datasets spell the same electrode ``Ft7`` and ``FT7``, and dropping the former
    silently shrinks the geometric subset.

    Ear labels (``cEL1``, ``ELA``, ``LF`` …) are not in the nomenclature, so they
    fall back to the schematic :data:`EAR_POSITIONS` table, lifted into the same
    units as the scalp montage. That is what lets a farthest-point subset span an
    ear array at all; the coordinates are schematic, not measured.
    """
    all_pos = standard_positions()
    normalised = {normalize_name(name): xyz for name, xyz in all_pos.items()}
    found: dict[str, np.ndarray] = {}
    for ch in ch_names:
        xyz = normalised.get(normalize_name(ch))
        if xyz is None:
            xy = EAR_POSITIONS.get(ch)
            if xy is not None:
                xyz = np.array([xy[0], xy[1], 0.0]) * _HEAD_RADIUS_M
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
