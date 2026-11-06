"""Diagnose the SSVEP harness discrepancy.

The benchmark reports 0.928 for `ssvep_8ch`; the permutation-control harness
reports 0.683 on the same data and decoder. One of them is wrong, or they are
computing different quantities.

This script runs the same subject through both paths with instrumentation so the
difference is visible rather than guessed:

  1. our own 5-fold CV on paradigm epochs
  2. MOABB's WithinSessionEvaluation on the same epochs
  3. per-fold scores from each, plus epoch/label counts

    .\\.venv\\Scripts\\python.exe scripts\\diagnose_ssvep.py
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

from eegbench import suite

warnings.filterwarnings("ignore")


def main() -> int:
    import mne
    import moabb.datasets as md
    import moabb.paradigms as mp
    from moabb.evaluations import WithinSessionEvaluation
    from sklearn.metrics import accuracy_score
    from sklearn.preprocessing import LabelEncoder

    from eegbench.datasets import configure_download_provider
    from eegbench.pipelines import build, set_ssvep_frequencies

    mne.set_log_level("ERROR")
    configure_download_provider("upstream")

    track = suite.get("ssvep_8ch")
    dataset = getattr(md, suite.DATASETS[track.dataset])()
    dataset.subject_list = [1]
    set_ssvep_frequencies(list(dataset.event_id.keys()))

    paradigm_cls = getattr(mp, suite.PARADIGMS[track.paradigm])
    paradigm = paradigm_cls(scorer="accuracy")

    # --- path A: our CV on epochs -----------------------------------------
    data, y, _ = paradigm.get_data(dataset, subjects=[1], return_epochs=True)
    data = data if isinstance(data, (list, tuple)) else [data]
    if len(data) > 1:
        data = [mne.concatenate_epochs(data)]
    ep = data[0]
    y_enc = LabelEncoder().fit_transform(np.asarray(y))

    print("=== epoch / label inventory ===")
    print(f"epochs      : {len(ep)}")
    print(f"channels    : {len(ep.info['ch_names'])}")
    print(f"sfreq       : {ep.info['sfreq']}")
    print(f"tmin/tmax   : {ep.tmin:.3f} / {ep.tmax:.3f}")
    print(f"n_times     : {ep.get_data().shape[-1]}")
    print(f"classes     : {len(set(y_enc))}")
    print(f"label dtype : {np.asarray(y).dtype}")
    print(f"per-class n : {np.bincount(y_enc).tolist()}")

    clf_factory = lambda: build(["ssvep_cca"])["ssvep_cca"]  # noqa: E731

    print("\n=== path A: our StratifiedKFold(5, shuffle, seed=0) ===")
    fold_scores = []
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    for i, (train, test) in enumerate(cv.split(np.zeros(len(y_enc)), y_enc)):
        clf = clf_factory()
        clf.fit(ep[train], y_enc[train])
        acc = accuracy_score(y_enc[test], clf.predict(ep[test]))
        fold_scores.append(acc)
        print(f"  fold {i}: train={len(train):3d} test={len(test):3d} acc={acc:.3f}")
    print(f"  mean = {np.mean(fold_scores):.3f}")

    # --- path B: MOABB evaluation -----------------------------------------
    print("\n=== path B: MOABB WithinSessionEvaluation ===")
    ev = WithinSessionEvaluation(
        paradigm=paradigm, datasets=[dataset], overwrite=True, return_epochs=True
    )
    df = ev.process({"ssvep_cca": build(["ssvep_cca"])["ssvep_cca"]})
    print(df[["subject", "session", "score", "n_samples", "n_classes"]].to_string(index=False))
    print(f"  mean = {df['score'].mean():.3f}")

    print("\n=== verdict ===")
    print(f"our CV        : {np.mean(fold_scores):.3f}")
    print(f"MOABB eval    : {df['score'].mean():.3f}")
    print(f"difference    : {np.mean(fold_scores) - df['score'].mean():+.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
