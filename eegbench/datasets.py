"""Dataset wrappers for MOABB quirks that would otherwise silently lose data.

The concrete case: some datasets record wearable electrodes but type them
``misc`` instead of ``eeg`` (Wu2020's 8 in-ear channels). MOABB's paradigm
picker keeps only ``eeg``, so those channels vanish without an error — you get
an empty subset rather than a wrong number, which is the good failure, but it
still blocks the experiment.

Re-typing is an explicit modelling decision: it says "treat this electrode as
an EEG channel". It does not change the data.
"""

from __future__ import annotations

from typing import Any, Sequence

_PATCH_FLAG = "_eegbench_promoted"


def configure_download_provider(provider: str = "upstream") -> str:
    """Pin where MOABB fetches dataset files from.

    Default is ``"upstream"`` because ``"auto"`` makes MOABB mirror every
    dataset into a NEMAR store *in addition to* the extracted working copy.
    For Wu2020 that meant ~21 GB instead of ~7 GB, and deleting the store did
    not help: ``_prefetch_nemar_sourcedata`` silently re-created it on the next
    load. ``"upstream"`` makes MOABB use the dataset's own downloader (the
    Zenodo per-subject ZIPs) and skip the NEMAR store entirely.

    The choice is persisted in MNE's config, which this project keeps inside
    ``data/mne_home``, so it survives across processes.
    """
    from moabb.utils import set_download_provider

    set_download_provider(provider)
    return provider


def _iter_raws(obj: Any):
    """Yield every Raw in an arbitrarily nested MOABB data structure.

    ``_get_single_subject_data`` is dataset-specific: most return
    ``{session: {run: raw}}`` but some return ``{session: raw}`` directly.
    ``get_data`` normalises this later, so the patch has to cope with both.
    """
    if hasattr(obj, "set_channel_types") and hasattr(obj, "info"):
        yield obj
    elif isinstance(obj, dict):
        for value in obj.values():
            yield from _iter_raws(value)


def promote_channels(dataset: Any, channels: Sequence[str]) -> Any:
    """Make ``channels`` report as ``eeg`` so MOABB paradigms keep them.

    Patches the instance's ``_get_single_subject_data`` (which ``get_data``
    calls) so the re-typing survives MOABB's caching layer. Idempotent.

    Returns the same dataset instance, for chaining.
    """
    if getattr(dataset, _PATCH_FLAG, False):
        return dataset

    wanted = list(channels)
    original = dataset._get_single_subject_data

    def patched(subject):
        data = original(subject)
        for raw in _iter_raws(data):
            present = [c for c in wanted if c in raw.info["ch_names"]]
            if present:
                raw.set_channel_types({c: "eeg" for c in present})
        return data

    dataset._get_single_subject_data = patched
    setattr(dataset, _PATCH_FLAG, True)
    return dataset
