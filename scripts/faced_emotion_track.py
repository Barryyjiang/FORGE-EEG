"""Emotion-recognition track on FACED (123 participants).

FACED is the largest cohort in the benchmark by a wide margin: 123 participants,
30 scalp electrodes, videos chosen to elicit nine emotions, labelled here as
binary valence (positive vs negative). It is the only affect task in the suite,
and the only one where the wearable question is asked of a *frontal* site.

Protocol
--------
Participant-disjoint ``GroupKFold``: every window of a participant lands in the
same fold, so a model never sees the person it is tested on. Windows are scored
individually and their probabilities averaged into **one prediction per video**,
which is the unit a person actually experiences. Scaling and the classifier are
fitted inside each training fold.

Metric
------
Balanced accuracy, chance 0.5. Raw accuracy would drift with the class balance,
and ROC-AUC is not what the team's FACED notebook reports, so the track keeps the
metric the reference implementation uses.

Montages
--------
``full_k30``
    The whole scalp montage, the reference.
``nested_k*``
    A wearable-inspired reduction path fixed *before* any results were seen:
    forehead -> frontal -> temporal -> central -> posterior. It is a
    location-specific path, not a claim that these are the optimal k electrodes.
``glasses_4`` / ``temporal_4`` / ``posterior_4``
    Three hand-picked four-electrode placements, so site can be compared at
    matched count.
``random-s*_k4``
    Random four-electrode draws, the control for "is this placement better than
    an arbitrary one".

The ``glasses_4`` set is a **scalp proxy**: FP1/FP2/F7/F8 are cap electrodes at
the sites a pair of glasses would use, not a measured glasses device. It carries
``fidelity: proxy`` for that reason.

Data
----
Reads the per-participant feature caches written by
``scripts/faced_extract_features.py``. Those come from the public FACED BIDS
release, so the track is reproducible without the team's Drive copy.

    .\\.venv\\Scripts\\python.exe scripts\\faced_emotion_track.py
"""

from __future__ import annotations

import argparse
import itertools
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TRACK = "faced_emotion_123"
DATASET_KEY = "faced"

#: Feature axis order in the cached arrays.
CHANNELS = ["FP1", "FP2", "FZ", "F3", "F4", "F7", "F8", "FC1", "FC2", "FC5",
            "FC6", "CZ", "C3", "C4", "T7", "T8", "CP1", "CP2", "CP5", "CP6",
            "PZ", "P3", "P4", "P7", "P8", "PO3", "PO4", "OZ", "O1", "O2"]

#: The reduction path, fixed before any results were seen.
ORDER = ["FP1", "FP2", "F7", "F8", "T7", "T8", "F3", "F4", "FC1", "FC2",
         "FC5", "FC6", "CZ", "C3", "C4", "FZ", "CP1", "CP2", "CP5", "CP6",
         "P3", "P4", "PZ", "PO3", "PO4", "P7", "P8", "O1", "O2", "OZ"]
NESTED = (2, 4, 6, 8, 12, 16, 20, 24)

PLACEMENTS: dict[str, tuple[list[str], str, str]] = {
    "glasses_4": (["FP1", "FP2", "F7", "F8"], "wearable", "proxy"),
    "temporal_4": (["F7", "F8", "T7", "T8"], "region", "measured"),
    "posterior_4": (["P7", "P8", "O1", "O2"], "region", "measured"),
}

N_FOLDS = 5
N_RANDOM = 20          # draws for the placement control
RANDOM_SEEDS = 3       # draws written into the main results table


def load_features(root: Path) -> tuple[np.ndarray, pd.DataFrame]:
    xs, metas = [], []
    for f in sorted(root.glob("*.npz")):
        with np.load(f, allow_pickle=True) as z:
            xs.append(z["X"])
            metas.append(pd.DataFrame({
                "subject": z["subject"].astype(str),
                "trial_key": z["trial_key"].astype(str),
                "trial": z["trial"].astype(int),
                "label": z["label"].astype(int),
                "window": z["window"].astype(int),
            }))
    if not xs:
        raise FileNotFoundError(
            f"no feature caches in {root}; run scripts/faced_extract_features.py")
    return np.concatenate(xs), pd.concat(metas, ignore_index=True)


def predict_trials(X, meta, channels, *, labels=None) -> pd.DataFrame:
    """One prediction per video, under participant-disjoint CV."""
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.model_selection import GroupKFold
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    idx = [CHANNELS.index(c) for c in channels]
    flat = X[:, idx, :].reshape(len(X), -1)
    y = meta["label"].to_numpy(dtype=int) if labels is None else labels
    groups = meta["subject"].to_numpy()

    out = []
    for tr, te in GroupKFold(n_splits=N_FOLDS).split(flat, y, groups):
        model = make_pipeline(
            StandardScaler(),
            LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto"),
        )
        model.fit(flat[tr], y[tr])
        proba = model.predict_proba(flat[te])
        held = meta.iloc[te][["subject", "trial_key", "label"]].copy()
        for j, c in enumerate(model.classes_):
            held[f"p{c}"] = proba[:, j]
        trial = held.groupby(["subject", "trial_key", "label"],
                             as_index=False).mean(numeric_only=True)
        cols = [f"p{c}" for c in model.classes_]
        trial["pred"] = model.classes_[np.argmax(trial[cols].to_numpy(), axis=1)]
        out.append(trial[["subject", "trial_key", "label", "pred"]])
    pred = pd.concat(out, ignore_index=True)
    if not pred["trial_key"].is_unique:
        raise RuntimeError("a trial was predicted more than once")
    return pred


def subject_scores(pred: pd.DataFrame) -> pd.DataFrame:
    """Balanced accuracy per participant, over their held-out videos."""
    from sklearn.metrics import balanced_accuracy_score

    rows = []
    for subject, g in pred.groupby("subject"):
        if g["label"].nunique() < 2:
            continue
        rows.append({
            "subject": subject,
            "score": balanced_accuracy_score(g["label"], g["pred"]),
            "n_trials": len(g),
        })
    return pd.DataFrame(rows)


def cohort_score(pred: pd.DataFrame) -> float:
    from sklearn.metrics import balanced_accuracy_score

    return float(balanced_accuracy_score(pred["label"], pred["pred"]))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path,
                   default=Path("data/faced/participant_features"))
    p.add_argument("--out", type=Path,
                   default=Path("results/benchmark/faced_emotion_123__within_session.csv"))
    p.add_argument("--random-out", type=Path,
                   default=Path("results/faced_random_4.csv"))
    p.add_argument("--perm-out", type=Path,
                   default=Path("results/perm_control_faced_emotion_123.csv"))
    p.add_argument("--permutations", type=int, default=100)
    p.add_argument("--skip-controls", action="store_true")
    args = p.parse_args()

    X, meta = load_features(args.root)
    print(f"windows={len(X)} participants={meta.subject.nunique()} "
          f"trials={meta.trial_key.nunique()}", flush=True)

    # key -> (channels, strategy, fidelity, subset base name)
    layouts: dict[str, tuple[list[str], str, str, str]] = {}
    layouts["full"] = (ORDER[:30], "full", "measured", "full")
    for k in NESTED:
        layouts[f"nested{k}"] = (ORDER[:k], "nested", "measured", "nested")
    for name, (chans, strategy, fidelity) in PLACEMENTS.items():
        layouts[name] = (chans, strategy, fidelity, name)

    # Random four-electrode draws, fixed seed, never selected on test accuracy.
    rng = np.random.default_rng(0)
    combos = list(itertools.combinations(CHANNELS, 4))
    order = rng.permutation(len(combos))
    random_draws = [list(combos[i]) for i in order[:N_RANDOM]]
    for seed in range(RANDOM_SEEDS):
        layouts[f"random-s{seed}"] = (random_draws[seed], "random", "measured",
                                      f"random-s{seed}")

    rows: list[dict] = []
    for name, (chans, strategy, fidelity, base) in layouts.items():
        pred = predict_trials(X, meta, chans)
        per_subject = subject_scores(pred)
        cohort = cohort_score(pred)
        for _, r in per_subject.iterrows():
            rows.append({
                "score": float(r["score"]),
                "pipeline": "psd_lda",
                "subset": f"{base}_k{len(chans)}",
                "strategy": strategy,
                "k": len(chans),
                "n_classes": 2,
                "subject": str(r["subject"]),
                "session": "0",
                "protocol": "within_session",
                "metric": "balanced_accuracy",
                "trial_seconds": 4.0,
                "track": TRACK,
                "dataset_key": DATASET_KEY,
                "channels": ",".join(chans),
                "fidelity": fidelity,
                "accuracy": float(r["score"]),
                "cohort_score": cohort,
                "n_windows": int((meta.subject == r["subject"]).sum()),
                "n_trials": int(r["n_trials"]),
                "n_dropped": 0,
            })
        print(f"  {base:16s} k={len(chans):2d} cohort={cohort:.4f} "
              f"subject_mean={per_subject['score'].mean():.4f}", flush=True)

    df = pd.DataFrame(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"\nwrote {args.out} ({len(df)} rows)")

    # --- placement control: where does each hand-picked 4 sit? ------------
    draws = []
    for i, chans in enumerate(random_draws):
        draws.append(cohort_score(predict_trials(X, meta, chans)))
        if (i + 1) % 5 == 0:
            print(f"  random draw {i + 1}/{N_RANDOM}", flush=True)
    draws = np.array(draws)
    args.random_out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"draw": np.arange(len(draws)), "score": draws}).to_csv(
        args.random_out, index=False)
    print(f"\nrandom k=4 (n={len(draws)}): median={np.median(draws):.4f} "
          f"p10={np.percentile(draws, 10):.4f} "
          f"p90={np.percentile(draws, 90):.4f}")
    for name in PLACEMENTS:
        value = float(df[df["subset"] == f"{name}_k4"]["cohort_score"].iloc[0])
        pct = 100.0 * (draws <= value).mean()
        print(f"  {name:14s} {value:.4f}  beats {int((draws <= value).sum())}"
              f"/{len(draws)} (percentile {pct:.0f})")

    if args.skip_controls:
        return 0

    # --- permutation control ---------------------------------------------
    # Labels are shuffled *within each participant*, so every participant keeps
    # one positive and one negative trial per video pair and the null preserves
    # the pairing the real design has. A free shuffle could hand a participant
    # only one class, which leaves their balanced accuracy undefined.
    rng2 = np.random.default_rng(0)
    perm_rows = []
    # Control the two four-electrode montages the prose compares. The 30-channel
    # reference is the same pipeline on more features, so it would add cost
    # without testing anything the k=4 rows do not already test.
    for name in ("glasses_4", "posterior_4"):
        chans = PLACEMENTS[name][0]
        subset = f"{name}_k4"
        real = float(df[df["subset"] == subset]["cohort_score"].iloc[0])
        nulls = []
        for _ in range(args.permutations):
            y_perm = meta["label"].to_numpy(dtype=int).copy()
            for _, g in meta.groupby("subject"):
                idx = g.index.to_numpy()
                y_perm[idx] = rng2.permutation(y_perm[idx])
            nulls.append(cohort_score(predict_trials(X, meta, chans,
                                                     labels=y_perm)))
        nulls = np.array(nulls)
        perm_rows.append({
            "track": TRACK,
            "subset": subset,
            "pipeline": "psd_lda",
            "metric": "balanced_accuracy",
            "n_classes": 2,
            "chance": 0.5,
            "subject": "cohort",
            "real": real,
            "perm_mean": float(nulls.mean()),
            "perm_sd": float(nulls.std()),
            "gap": real - float(nulls.mean()),
            "montage": name,
            "channels": ",".join(chans),
            "null": "within-subject shuffle",
            "n_permutations": args.permutations,
        })
        print(f"  {subset:16s} real={real:.4f} null={nulls.mean():.4f}",
              flush=True)

    pd.DataFrame(perm_rows).to_csv(args.perm_out, index=False)
    print(f"wrote {args.perm_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
