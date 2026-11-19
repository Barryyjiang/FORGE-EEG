"""Aggregate every result file into one comparable table.

The benchmark's value is the *cross-track* view: which montage loses how much,
per decoder, on which paradigm. That requires a single schema, an explicit
chance level per row, and a delta against the full cap.

Chance level matters more than it looks. MOABB reports ROC-AUC for two-class
problems (chance 0.5) and accuracy for multi-class (chance 1/n). Mixing them in
one table without saying so produces meaningless rankings.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED = ("score", "pipeline", "subset", "strategy", "k")

#: The decision window each multi-window task is scored at in the leaderboard.
#: A task that reports an accuracy-versus-window curve has one row per subject
#: per window; averaging those into a single cell would produce a number that
#: belongs to no window at all. The curve is kept in the CSV and summarised
#: separately (see ``window_curve``).
HEADLINE_WINDOW_S = {
    "auditory_attention_earsaad": 60.0,
}


def load_results(directory: str | Path) -> pd.DataFrame:
    """Concatenate every ``*.csv`` result file in a directory."""
    directory = Path(directory)
    files = sorted(directory.glob("*.csv"))
    files = [f for f in files if not f.stem.endswith("_summary")]
    if not files:
        raise FileNotFoundError(f"no result CSVs in {directory}")

    frames = []
    for path in files:
        df = pd.read_csv(path)
        missing = [c for c in REQUIRED if c not in df.columns]
        if missing:
            raise ValueError(f"{path.name} missing columns {missing}")
        # Files are written as "{track}__{protocol}.csv"; keep the two axes
        # separate so tracks are comparable across protocols.
        stem = path.stem
        track, _, protocol_from_name = stem.partition("__")
        df["track"] = track
        if "protocol" not in df.columns or df["protocol"].isna().all():
            df["protocol"] = protocol_from_name or "unknown"
        df["source_file"] = path.name
        frames.append(df)
    raw = pd.concat(frames, ignore_index=True)

    for track, seconds in HEADLINE_WINDOW_S.items():
        if "trial_seconds" in raw.columns:
            drop = (raw["track"] == track) & (raw["trial_seconds"] != seconds)
            raw = raw[~drop]
    return raw


def window_curve(directory: str | Path) -> pd.DataFrame:
    """Mean score per (track, subset, decision window), for multi-window tasks.

    Kept out of the leaderboard because it is a curve, not a cell. Returns an
    empty frame when no task reports more than one window.
    """
    directory = Path(directory)
    frames = []
    for path in sorted(directory.glob("*.csv")):
        if path.stem.endswith("_summary"):
            continue
        df = pd.read_csv(path)
        if "trial_seconds" not in df.columns:
            continue
        if df["trial_seconds"].nunique() < 2:
            continue
        track = path.stem.partition("__")[0]
        frames.append(df.assign(track=track))
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    out = (df.groupby(["track", "subset", "trial_seconds"])["score"]
           .agg(["mean", "std", "count"]).reset_index()
           .rename(columns={"mean": "score_mean", "std": "score_sd",
                            "count": "n"}))
    out["score_sem"] = out["score_sd"] / out["n"].pow(0.5)
    return out


def add_chance(df: pd.DataFrame) -> pd.DataFrame:
    """Chance level, metric-aware.

    ROC-AUC is 0.5 for two classes, accuracy is 1/n, kappa and correlation are
    0. Reading chance off ``n_classes`` alone would silently mis-state kappa.
    """
    from .metrics import chance_level

    df = df.copy()
    n = df["n_classes"].astype(float) if "n_classes" in df.columns else pd.Series(
        2.0, index=df.index
    )
    known = {"roc_auc", "accuracy", "balanced_accuracy", "kappa", "pearson"}

    def _metric(m, c) -> str:
        # Files written before the metric column existed (MI, P300, motor
        # execution) carry no metric. Infer the historical default rather than
        # letting str(nan) fall through chance_level's kappa branch and report
        # chance=0 for an ROC-AUC track.
        text = str(m) if pd.notna(m) else ""
        if text in known:
            return text
        return "roc_auc" if float(c) <= 2 else "accuracy"

    if "metric" in df.columns:
        df["chance"] = [
            chance_level(_metric(m, c), int(c)) for m, c in zip(df["metric"], n)
        ]
    else:
        df["chance"] = [0.5 if c <= 2 else 1.0 / c for c in n]
    return df


def summarise(df: pd.DataFrame) -> pd.DataFrame:
    """Mean/sd/sem per (track, pipeline, subset), plus delta vs full cap."""
    df = add_chance(df)
    group = ["track", "protocol", "pipeline", "subset", "strategy", "k"]
    agg = (
        df.groupby(group, dropna=False)["score"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .rename(columns={"mean": "score_mean", "std": "score_sd", "count": "n"})
    )
    agg["score_sem"] = agg["score_sd"] / agg["n"].pow(0.5)

    chance = (
        df.groupby(["track", "protocol", "pipeline"], dropna=False)["chance"]
        .mean()
        .rename("chance")
        .reset_index()
    )
    agg = agg.merge(chance, on=["track", "protocol", "pipeline"], how="left")

    # Carry metric metadata so ITR can be computed where it is meaningful.
    keys = ["track", "protocol", "pipeline"]
    carry = {c: "first" for c in ("metric", "trial_seconds", "n_classes")
             if c in df.columns}
    if carry:
        meta = df.groupby(keys, dropna=False).agg(carry).reset_index()
        agg = agg.merge(meta, on=keys, how="left")

    full = (
        agg[agg["strategy"] == "full"][["track", "protocol", "pipeline", "score_mean"]]
        .rename(columns={"score_mean": "full_score"})
    )
    agg = agg.merge(full, on=["track", "protocol", "pipeline"], how="left")

    # A dataset with no dense cap (sleep) has no "full" row. Use its matched
    # scalp montage as the reference instead of leaving every delta blank.
    missing = agg["full_score"].isna()
    if missing.any():
        fallback = (
            agg[missing & (agg["strategy"] == "region")]
            .sort_values("k")
            .groupby(["track", "protocol", "pipeline"], as_index=False)
            .first()[["track", "protocol", "pipeline", "score_mean"]]
            .rename(columns={"score_mean": "fallback_score"})
        )
        agg = agg.merge(fallback, on=["track", "protocol", "pipeline"], how="left")
        agg["full_score"] = agg["full_score"].fillna(agg["fallback_score"])
        agg = agg.drop(columns=["fallback_score"])

    agg["delta_vs_reference"] = agg["score_mean"] - agg["full_score"]
    agg["above_chance"] = agg["score_mean"] - agg["chance"]

    agg = _add_itr(agg)

    return agg.sort_values(
        ["track", "protocol", "pipeline", "k", "score_mean"],
        ascending=[True, True, True, True, False],
    )


#: Tracks where the Wolpaw ITR formula does not apply. Auditory attention is a
#: continuous two-class decision, not an independent selection: consecutive
#: windows cover overlapping speech and the formula's independence assumption
#: fails, so a bits-per-minute figure would be meaningless next to SSVEP's.
NO_ITR_TRACKS = {"auditory_attention_earsaad"}


def _add_itr(agg: pd.DataFrame) -> pd.DataFrame:
    """Information transfer rate, only where the metric makes it valid.

    ITR needs a *selection accuracy*, a class count and a trial duration. AUC
    cannot be converted into it without assuming a criterion, so rows scored by
    AUC get NaN rather than a number that looks comparable but is not.
    """
    from .metrics import is_itr_eligible, itr_bits_per_min

    needed = {"metric", "trial_seconds", "n_classes"}
    if not needed.issubset(agg.columns):
        return agg

    values = []
    for _, row in agg.iterrows():
        n_classes = row["n_classes"]
        trial = row["trial_seconds"]
        if (
            pd.isna(n_classes)
            or pd.isna(trial)
            or str(row.get("track")) in NO_ITR_TRACKS
            or not is_itr_eligible(str(row["metric"]), int(n_classes), float(trial))
        ):
            values.append(float("nan"))
        else:
            values.append(itr_bits_per_min(float(row["score_mean"]),
                                           int(n_classes), float(trial)))
    agg = agg.copy()
    agg["itr_bpm"] = values
    return agg


def leaderboard(directory: str | Path) -> pd.DataFrame:
    """One row per (track, pipeline, subset) with chance-relative columns."""
    return summarise(load_results(directory))


def render(table: pd.DataFrame, *, width: int = 200) -> str:
    cols = [
        "track", "protocol", "pipeline", "subset", "k",
        "score_mean", "score_sem", "chance", "delta_vs_reference", "itr_bpm",
    ]
    cols = [c for c in cols if c in table.columns]
    with pd.option_context("display.width", width, "display.max_rows", 500):
        return table[cols].to_string(index=False, float_format=lambda v: f"{v:+.3f}")
