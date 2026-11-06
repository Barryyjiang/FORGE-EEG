"""Keep every download and cache inside the project folder.

By default MNE puts datasets in ``~/mne_data`` and its config in
``%USERPROFILE%\\.mne``. This project redirects both to ``./data`` so the whole
thing is one self-contained directory you can move, archive or delete.

The redirect is an import side effect of :mod:`eegbench` (env vars are read by
MNE/MOABB at import time, so it has to happen early). Set
``EEGBENCH_NO_DATA_REDIRECT=1`` to opt out and use the ambient configuration.
"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MNE_DATA_DIR = DATA_DIR / "mne_data"
MOABB_CACHE_DIR = DATA_DIR / "moabb"
MNE_HOME_DIR = DATA_DIR / "mne_home"
RESULTS_DIR = PROJECT_ROOT / "results"

OPT_OUT_ENV = "EEGBENCH_NO_DATA_REDIRECT"


def configure_data_home(*, force: bool = True, verbose: bool = False) -> dict[str, str]:
    """Point MNE and MOABB caches at ``./data``.

    ``force=True`` overrides ambient values so that a stale ``MNE_DATA`` in
    your shell cannot silently scatter data outside the project. The escape
    hatch is ``EEGBENCH_NO_DATA_REDIRECT=1``.

    Returns the environment variables that were set (empty if opted out).
    """
    if os.environ.get(OPT_OUT_ENV) == "1":
        return {}

    for directory in (MNE_DATA_DIR, MOABB_CACHE_DIR, MNE_HOME_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    env = {
        # Datasets (pooch / NEMAR / MOABB downloads).
        "MNE_DATA": str(MNE_DATA_DIR),
        # MOABB's HDF5 result cache. Read by moabb.analysis.results via
        # mne.get_config(), which checks os.environ first.
        "MOABB_RESULTS": str(MOABB_CACHE_DIR),
        # MNE's ~1 KB of preferences. `_MNE_FAKE_HOME_DIR` is a private hook,
        # but it is exactly what MNE's own test-suite uses to isolate the
        # config directory.
        "_MNE_FAKE_HOME_DIR": str(MNE_HOME_DIR),
    }

    for key, value in env.items():
        if force or key not in os.environ:
            os.environ[key] = value

    if verbose:
        for key, value in env.items():
            print(f"  {key} -> {value}")
    return env


def describe() -> str:
    """Human-readable summary of the configured paths and their size."""
    def size_mb(path: Path) -> float:
        if not path.exists():
            return 0.0
        return sum(p.stat().st_size for p in path.rglob("*") if p.is_file()) / 2**20

    lines = [f"project    {PROJECT_ROOT}"]
    for label, path in (
        ("datasets", MNE_DATA_DIR),
        ("moabb cache", MOABB_CACHE_DIR),
        ("mne home", MNE_HOME_DIR),
        ("results", RESULTS_DIR),
    ):
        lines.append(f"{label:11s}{path}  ({size_mb(path):,.1f} MB)")
    return "\n".join(lines)
