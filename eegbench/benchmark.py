"""Run MOABB evaluations over many electrode subsets.

MOABB ties the electrode set to the *paradigm* (``paradigm = P300(channels=[...])``),
so a channel sweep is one evaluation per subset. This module automates that and
stitches the results into one tidy DataFrame with the subset metadata attached.

Caching warning: MOABB caches results keyed by dataset + pipeline, and different
subsets of the same dataset look similar. Each run gets a unique ``suffix`` so
subsets never overwrite each other in the cache.
"""

from __future__ import annotations

import warnings
from typing import Any, Mapping, Sequence

import pandas as pd

from .names import match_channels
from .subsets import SubsetSpec


def dataset_channels(
    dataset: Any,
    *,
    allow_download: bool = False,
    verbose: bool = True,
) -> list[str]:
    """Electrode names of a MOABB dataset, ideally without downloading.

    Resolution order:

    1. ``dataset.channels`` (synthetic / fake datasets set this directly)
    2. ``dataset.metadata.acquisition.sensors`` (free, but not every dataset
       fills it in)
    3. load subject 1's data -- requires ``allow_download=True``
    """
    attr = getattr(dataset, "channels", None)
    if attr:
        return list(attr)

    meta = getattr(dataset, "metadata", None)
    sensors = getattr(getattr(meta, "acquisition", None), "sensors", None)
    if sensors:
        return list(sensors)

    if not allow_download:
        raise ValueError(
            f"{type(dataset).__name__} does not expose its channel names via "
            "metadata. Pass allow_download=True to read them from subject 1 "
            "(this downloads data), or pass `available=` explicitly."
        )

    subject = dataset.subject_list[0]
    if verbose:
        print(f"  reading channel names from {type(dataset).__name__} "
              f"subject {subject} (downloads data)...")
    data = dataset.get_data([subject])
    sessions = data[subject]
    raw = next(iter(next(iter(sessions.values())).values()))
    return [ch for ch in raw.info["ch_names"] if raw.get_channel_types([ch])[0] == "eeg"]


def subset_channels(spec: SubsetSpec, available: Sequence[str]) -> tuple[list[str], list[str]]:
    """Intersect a spec with a dataset's channels."""
    return match_channels(spec.channels, available)


def sweep(
    dataset: Any,
    paradigm_cls: Any,
    specs: Sequence[SubsetSpec],
    pipelines: Mapping[str, Any],
    *,
    evaluation_cls: Any | None = None,
    paradigm_kwargs: Mapping[str, Any] | None = None,
    evaluation_kwargs: Mapping[str, Any] | None = None,
    available: Sequence[str] | None = None,
    min_channels: int = 2,
    verbose: bool = True,
) -> pd.DataFrame:
    """Evaluate every subset of ``specs`` on one dataset.

    Returns one row per (subset, pipeline, subject, session) with the subset
    metadata attached as columns. Feed it to :func:`summarise` for the table
    you actually plot.
    """
    from moabb.evaluations import WithinSessionEvaluation

    evaluation_cls = evaluation_cls or WithinSessionEvaluation
    paradigm_kwargs = dict(paradigm_kwargs or {})
    evaluation_kwargs = dict(evaluation_kwargs or {})

    if available is None:
        available = dataset_channels(dataset)

    frames: list[pd.DataFrame] = []
    skipped: list[tuple[str, str]] = []

    for spec in specs:
        present, missing = subset_channels(spec, available)
        if len(present) < min_channels:
            skipped.append((spec.name, f"only {len(present)} channels available"))
            continue
        if missing and verbose:
            print(f"  {spec.name}: {len(missing)} electrode(s) absent from "
                  f"{type(dataset).__name__}, ignoring: {missing}")

        if verbose:
            print(f"[{spec.name}] {len(present)} ch: {present}")

        paradigm = paradigm_cls(channels=present, **paradigm_kwargs)
        eval_kwargs = dict(evaluation_kwargs)
        eval_kwargs.setdefault("suffix", f"-{spec.name}")

        try:
            evaluation = evaluation_cls(
                paradigm=paradigm,
                datasets=[dataset],
                **eval_kwargs,
            )
            df = evaluation.process(dict(pipelines))
        except Exception as exc:  # noqa: BLE001 - a bad subset must not kill the sweep
            skipped.append((spec.name, f"{type(exc).__name__}: {exc}"))
            if verbose:
                print(f"  SKIPPED: {type(exc).__name__}: {exc}")
            continue

        if df is None or len(df) == 0:
            skipped.append((spec.name, "no results"))
            continue

        df = df.copy()
        df["subset"] = spec.name
        df["strategy"] = spec.strategy
        df["fidelity"] = spec.fidelity
        df["k"] = len(present)
        df["requested_k"] = spec.requested if spec.requested is not None else len(present)
        df["channels"] = ",".join(present)
        frames.append(df)

    if skipped:
        warnings.warn(
            "Some subsets were skipped: "
            + "; ".join(f"{n} ({why})" for n, why in skipped),
            stacklevel=2,
        )

    if not frames:
        raise RuntimeError(
            "No subset produced results. Check that the paradigm matches the "
            "dataset and that the montages intersect its channels."
        )

    return pd.concat(frames, ignore_index=True)


def summarise(df: pd.DataFrame) -> pd.DataFrame:
    """Mean / sd / n of the score, per subset and pipeline."""
    group = ["subset", "strategy", "k", "pipeline"]
    agg = df.groupby(group, dropna=False)["score"].agg(["mean", "std", "count"])
    agg = agg.rename(columns={"mean": "score_mean", "std": "score_sd", "count": "n"})
    agg["score_sem"] = agg["score_sd"] / agg["n"].pow(0.5)
    return agg.reset_index().sort_values(["k", "strategy", "score_mean"],
                                         ascending=[True, True, False])
