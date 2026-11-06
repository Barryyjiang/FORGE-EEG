"""Per-channel decodability diagnostic.

Answers a narrow question before blaming a decoder: does a *single* channel,
taken alone, carry linearly-decodable class information?

For each subject and electrode we fit LDA on one feature (log band-power in a
band) with stratified CV and report ROC-AUC. If scalp channels score well above
0.5 and ear channels do not, the multivariate pipeline is not the problem -- the
ear signal, under this preprocessing, is not there. If ear channels score above
0.5 individually, then the earlier CSP result was a decoder failure.

Usage::

    .\\.venv\\Scripts\\python.exe scripts\\channel_diagnostics.py --dataset wu2020 --subjects 6
"""

from __future__ import annotations

import argparse
import warnings

import numpy as np
import pandas as pd
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import StratifiedKFold, cross_val_score

EAR = ("LF", "LB", "LOU", "LOD", "RF", "RB", "ROU", "ROD")


def bandpower(epochs: np.ndarray, sfreq: float, band: tuple[float, float]) -> np.ndarray:
    """Log power in a frequency band, per epoch per channel.

    epochs: (n_epochs, n_chans, n_times) -> (n_epochs, n_chans)
    """
    from scipy.signal import butter, sosfiltfilt

    sos = butter(4, band, btype="bandpass", fs=sfreq, output="sos")
    filtered = sosfiltfilt(sos, epochs, axis=-1)
    return np.log(np.var(filtered, axis=-1) + 1e-20)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", default="wu2020", choices=["wu2020"])
    p.add_argument("--subjects", type=int, default=6)
    p.add_argument("--band", default="13,30", help="band in Hz, e.g. 13,30")
    p.add_argument("--out", default="results/channel_diagnostics.csv")
    args = p.parse_args()

    warnings.filterwarnings("ignore")
    import mne

    mne.set_log_level("ERROR")
    from moabb.datasets import Wu2020
    from moabb.paradigms import LeftRightImagery

    from eegbench.datasets import promote_channels

    band = tuple(float(x) for x in args.band.split(","))
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

        X = np.concatenate([e.get_data() for e in epochs], axis=0)
        ch_names = list(epochs[0].info["ch_names"])
        if X.shape[1] != len(ch_names):
            raise RuntimeError(
                f"epoch data has {X.shape[1]} channels but info lists "
                f"{len(ch_names)}"
            )

        feats = bandpower(X, epochs[0].info["sfreq"], band)
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)

        for i, ch in enumerate(ch_names):
            col = feats[:, i : i + 1]
            try:
                scores = cross_val_score(
                    LinearDiscriminantAnalysis(), col, y, cv=cv, scoring="roc_auc"
                )
                auc = float(np.mean(scores))
            except ValueError:
                auc = np.nan
            rows.append({"subject": subject, "channel": ch, "auc": auc,
                         "is_ear": ch in EAR})

        print(f"  n_epochs={len(y)} chans={len(ch_names)} "
              f"band={band[0]}-{band[1]}Hz", flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(args.out, index=False)

    summary = (
        df.groupby(["channel", "is_ear"])["auc"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .sort_values("mean", ascending=False)
    )
    print("\n--- top 12 channels (mean single-channel AUC) ---")
    print(summary.head(12).to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print("\n--- ear channels ---")
    print(summary[summary["is_ear"]].to_string(index=False,
                                               float_format=lambda v: f"{v:.3f}"))
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
