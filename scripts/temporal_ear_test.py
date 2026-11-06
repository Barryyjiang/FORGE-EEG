"""Does a temporal-feature decoder recover in-ear signal?

The earlier result (ear at chance) used band-power over the whole epoch. That
discards the *time course* of event-related desynchronisation. This asks whether
the ear result survives when the decoder is given temporal structure:

- ``bandpower``  one log-power value per channel per band (what failed before)
- ``temporal``   log-power in consecutive windows -> ERD time course
- ``eegnet``     raw epochs; learns its own temporal filters
                 (MOABB records EEGNet as the classifier for Wu2020)

Everything is compared on the SAME 8 channels: in-ear vs the sensorimotor scalp
montage from the sweep. If temporal features lift ear above chance, the earlier
conclusion was a feature-choice artefact.

Usage::

    .\\.venv\\Scripts\\python.exe scripts\\temporal_ear_test.py --subjects 6
"""

from __future__ import annotations

import argparse
import warnings

import numpy as np
import pandas as pd
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

EAR = ("LF", "LB", "LOU", "LOD", "RF", "RB", "ROU", "ROD")
SCALP = ("Cz", "C6", "C5", "CP4", "CP3", "FC4", "FC3", "C2")  # sensorimotor k=8
BANDS = {"mu": (8.0, 13.0), "beta": (13.0, 30.0)}


def _bandpass(X: np.ndarray, sfreq: float, band: tuple[float, float]) -> np.ndarray:
    from scipy.signal import butter, sosfiltfilt

    sos = butter(4, band, btype="bandpass", fs=sfreq, output="sos")
    return sosfiltfilt(sos, X, axis=-1)


def bandpower(X: np.ndarray, sfreq: float) -> np.ndarray:
    """One feature per channel per band."""
    feats = []
    for band in BANDS.values():
        filtered = _bandpass(X, sfreq, band)
        feats.append(np.log(np.var(filtered, axis=-1) + 1e-20))
    return np.concatenate(feats, axis=1)


def temporal_bandpower(X: np.ndarray, sfreq: float, n_windows: int = 8) -> np.ndarray:
    """Band power in consecutive windows -> ERD time course."""
    feats = []
    edges = np.linspace(0, X.shape[-1], n_windows + 1, dtype=int)
    for band in BANDS.values():
        filtered = _bandpass(X, sfreq, band)
        for start, stop in zip(edges[:-1], edges[1:]):
            feats.append(np.log(np.var(filtered[..., start:stop], axis=-1) + 1e-20))
    return np.concatenate(feats, axis=1)


def eegnet_classifier(n_chans: int, n_times: int):
    from braindecode import EEGClassifier
    from braindecode.models import EEGNet

    net = EEGNet(n_chans=n_chans, n_outputs=2, n_times=n_times)
    return EEGClassifier(
        net,
        max_epochs=40,
        batch_size=16,
        lr=1e-3,
        optimizer__weight_decay=1e-4,
        train_split=None,
        verbose=0,
    )


def cv_auc(make_clf, X: np.ndarray, y: np.ndarray, seeds=(0, 1, 2)) -> float:
    """Stratified CV AUC, averaged over repeats (fresh estimator each fold)."""
    aucs = []
    for seed in seeds:
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
        for train, test in cv.split(X, y):
            clf = make_clf()
            clf.fit(X[train], y[train])
            proba = clf.predict_proba(X[test])[:, 1]
            aucs.append(roc_auc_score(y[test], proba))
    return float(np.mean(aucs))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--subjects", type=int, default=6)
    p.add_argument("--models", default="bandpower,temporal",
                   help="comma-separated subset of bandpower,temporal,eegnet")
    p.add_argument("--sfreq", type=float, default=250.0,
                   help="resample target (keeps EEGNet tractable)")
    p.add_argument("--out", default="results/temporal_ear.csv")
    args = p.parse_args()

    warnings.filterwarnings("ignore")
    import mne

    mne.set_log_level("ERROR")
    from moabb.datasets import Wu2020
    from moabb.paradigms import LeftRightImagery

    from eegbench.datasets import configure_download_provider, promote_channels

    configure_download_provider("upstream")
    models = {m.strip() for m in args.models.split(",") if m.strip()}

    dataset = Wu2020()
    dataset.subject_list = dataset.subject_list[: args.subjects]
    promote_channels(dataset, EAR)
    paradigm = LeftRightImagery(channels=None)

    rows = []
    for subject in dataset.subject_list:
        print(f"subject {subject}: loading...", flush=True)
        epochs, y, _ = paradigm.get_data(
            dataset, subjects=[subject], return_epochs=True
        )
        epochs = epochs if isinstance(epochs, (list, tuple)) else [epochs]
        if len(epochs) > 1:
            epochs = [mne.concatenate_epochs(epochs)]
        ep = epochs[0].copy().resample(args.sfreq, verbose=False)
        names = list(ep.info["ch_names"])
        X_all = ep.get_data()
        sfreq = ep.info["sfreq"]
        # skorch needs integer classes; sklearn estimators cope with strings.
        y_enc = LabelEncoder().fit_transform(y)

        picks = {
            "ear": [names.index(c) for c in EAR if c in names],
            "scalp_sensorimotor": [names.index(c) for c in SCALP if c in names],
        }

        for montage, idx in picks.items():
            if len(idx) != 8:
                print(f"  {montage}: expected 8 channels, got {len(idx)}; skipping")
                continue
            X = X_all[:, idx, :]

            if "bandpower" in models:
                auc = cv_auc(
                    lambda: make_pipeline(
                        StandardScaler(),
                        LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto"),
                    ),
                    bandpower(X, sfreq), y,
                )
                rows.append({"subject": subject, "montage": montage,
                             "model": "bandpower", "auc": auc})

            if "temporal" in models:
                auc = cv_auc(
                    lambda: make_pipeline(
                        StandardScaler(),
                        LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto"),
                    ),
                    temporal_bandpower(X, sfreq), y,
                )
                rows.append({"subject": subject, "montage": montage,
                             "model": "temporal", "auc": auc})

            if "eegnet" in models:
                import torch

                dev = "cuda" if torch.cuda.is_available() else "cpu"
                # EEG arrives in volts (~1e-5). Unscaled, the first conv sees
                # tiny activations and training stalls at chance -- observed as
                # an EEGNet "chance on scalp" result. Convert to microvolts.
                Xe = (X * 1e6).astype(np.float32)
                auc = cv_auc(
                    lambda: eegnet_classifier(X.shape[1], X.shape[2]).set_params(
                        device=dev
                    ),
                    Xe, y_enc, seeds=(0,),
                )
                rows.append({"subject": subject, "montage": montage,
                             "model": "eegnet", "auc": auc})

        print(f"  n_epochs={len(y)} done", flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(args.out, index=False)

    table = (
        df.groupby(["model", "montage"])["auc"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .sort_values(["model", "mean"], ascending=[True, False])
    )
    print("\n--- AUC by model and montage ---")
    print(table.to_string(index=False, float_format=lambda v: f"{v:.3f}"))

    pivot = df.pivot_table(index=["subject", "model"], columns="montage", values="auc")
    if {"ear", "scalp_sensorimotor"}.issubset(pivot.columns):
        print("\n--- per-subject: scalp minus ear ---")
        diff = (pivot["scalp_sensorimotor"] - pivot["ear"]).rename("scalp_minus_ear")
        print(diff.reset_index().to_string(index=False,
                                           float_format=lambda v: f"{v:+.3f}"))

    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
