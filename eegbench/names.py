"""Channel-name normalisation.

MOABB datasets disagree on capitalisation (``Cz`` vs ``CZ``) and some vendors
prefix channels with ``EEG``. Everything that matches electrode names goes
through here so the behaviour is identical everywhere.
"""

from __future__ import annotations


def normalize_name(name: str) -> str:
    """Case-insensitive key for an electrode name."""
    n = name.strip().upper().replace(" ", "").replace("-", "")
    if n.startswith("EEG"):
        n = n[3:]
    return n


def match_channels(
    requested: list[str] | tuple[str, ...], available: list[str] | tuple[str, ...]
) -> tuple[list[str], list[str]]:
    """Map ``requested`` names onto ``available`` ones.

    Returns ``(present, missing)`` where ``present`` uses the dataset's own
    spelling, in the order requested, with duplicates removed.
    """
    lookup = {normalize_name(c): c for c in available}
    present: list[str] = []
    missing: list[str] = []
    for ch in requested:
        hit = lookup.get(normalize_name(ch))
        if hit is None:
            missing.append(ch)
        elif hit not in present:
            present.append(hit)
    return present, missing
