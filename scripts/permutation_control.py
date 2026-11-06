"""Permutation-label control: prove a pipeline can fail.

A decoder that scores well on real labels but *also* scores well on shuffled
labels is not decoding the task — it is exploiting structure in the split,
preprocessing, or label ordering. That failure looks exactly like a good result,
which is why this must run before any ranking is trusted.

For each subject we report ``real``, the mean over N label permutations, and the
gap. A valid decoder has the permuted score at chance. If it is above chance the
track is invalid and its results must not be used.

    .\\.venv\\Scripts\\python.exe scripts\\permutation_control.py --track mi_leftright_22ch --subjects 3
"""

from __future__ import annotations

import argparse
import warnings

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder

from eegbench import suite
from eegbench.pipelines import build as build_pipelines

warnings.filterwarnings("ignore")


def cv_score(make_clf, select, y, *, metric: str, seed: int = 0) -> float:
    """Stratified CV with a fresh estimator per fold.

    ``select(idx)`` returns the data (array or MNE Epochs) for a fold, so this
    works for pipelines that need raw arrays and for SSVEP_CCA which needs
    Epochs.
    """
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    scores = []
    for train, test in cv.split(np.zeros(len(y)), y):
        clf = make_clf()
        clf.fit(select(train), y[train])
        if metric == "roc_auc":
            proba = clf.predict_proba(select(test))[:, 1]
            scores.append(roc_auc_score(y[test], proba))
        else:
            scores.append(accuracy_score(y[test], clf.predict(select(test))))
    return float(np.mean(scores))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--track", required=True)
    p.add_argument("--subjects", type=int, default=3)
    p.add_argument("--pipeline", default=None,
                   help="decoder to test; defaults to the track's first")
    p.add_argument("--n-permutations", type=int, default=20,
                   help="20+ needed: at 5 shuffles the estimate is noisy enough "
                        "that a chance decoder can read 0.557")
    p.add_argument("--out", default="results/permutation_control.csv")
    args = p.parse_args()

    import mne
    import moabb.datasets as md
    import moabb.paradigms as mp

    from eegbench.datasets import configure_download_provider, promote_channels

    mne.set_log_level("ERROR")
    configure_download_provider("upstream")

    track = suite.get(args.track)
    pipeline_name = args.pipeline or track.pipelines[0]
    dataset = getattr(md, suite.DATASETS[track.dataset])()
    dataset.subject_list = dataset.subject_list[: args.subjects]
    if track.promote:
        promote_channels(dataset, track.promote)

    paradigm_cls = getattr(mp, suite.PARADIGMS[track.paradigm])
    kwargs = dict(track.paradigm_kwargs)
    if track.scorer:
        kwargs["scorer"] = track.scorer
    paradigm = paradigm_cls(channels=None, **kwargs)

    if pipeline_name == "ssvep_cca":
        from eegbench.pipelines import set_ssvep_frequencies

        set_ssvep_frequencies(list(dataset.event_id.keys()))

    rng = np.random.default_rng(0)
    rows = []

    for subject in dataset.subject_list:
        print(f"subject {subject}: loading...", flush=True)
        data, y, _ = paradigm.get_data(
            dataset, subjects=[subject], return_epochs=track.return_epochs
        )

        if track.return_epochs:
            data = data if isinstance(data, (list, tuple)) else [data]
            if len(data) > 1:
                data = [mne.concatenate_epochs(data)]
            data = data[0]

        y_enc = LabelEncoder().fit_transform(np.asarray(y))
        metric = "accuracy" if len(set(y_enc)) > 2 else "roc_auc"

        def select(idx):
            return data[idx]

        def make():
            return build_pipelines([pipeline_name])[pipeline_name]

        real = cv_score(make, select, y_enc, metric=metric)
        perm = [
            cv_score(make, select, rng.permutation(y_enc), metric=metric)
            for _ in range(args.n_permutations)
        ]

        rows.append({
            "track": track.name,
            "pipeline": pipeline_name,
            "subject": subject,
            "metric": metric,
            "n_classes": int(len(set(y_enc))),
            "real": real,
            "perm_mean": float(np.mean(perm)),
            "perm_sd": float(np.std(perm)),
            "gap": real - float(np.mean(perm)),
        })
        print(f"  real={real:.3f} perm={np.mean(perm):.3f}", flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(args.out, index=False)

    summary = df.groupby(["track", "pipeline"])[["real", "perm_mean", "gap"]].mean()
    print("\n--- summary (mean over subjects) ---")
    print(summary.to_string(float_format=lambda v: f"{v:.3f}"))
    print("\nperm_mean should sit at chance (0.5 AUC; 1/n for accuracy).")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
