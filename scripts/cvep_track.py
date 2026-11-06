"""c-VEP track via custom epoching.

MOABB's ``CVEP`` paradigm exposes the stimulus *bit* stream (0/1), which makes
c-VEP a binary problem and sits at chance by construction. The command identity
is present in the raw data as the ``stim_trial`` channel (values 200..20N), but
the paradigm does not use it.

This bypasses the paradigm: onset-detect ``stim_trial`` transitions, epoch there,
and decode the command directly. That is the difference between a c-VEP track
and no c-VEP track.

    .\\.venv\\Scripts\\python.exe scripts\\cvep_track.py --subject 1 --epoch-seconds 2.0
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--subject", type=int, default=1)
    p.add_argument("--epoch-seconds", type=float, default=2.0)
    p.add_argument("--pipeline", default="riemann_tslr")
    p.add_argument("--out", type=Path,
                   default=Path("results/benchmark/cvep_local__within_session.csv"))
    args = p.parse_args()

    import mne
    from sklearn.model_selection import StratifiedKFold

    from eegbench.datasets import configure_download_provider
    from eegbench.pipelines import build

    mne.set_log_level("ERROR")
    configure_download_provider("upstream")

    from moabb.datasets import CastillosCVEP40

    dataset = CastillosCVEP40()
    dataset.subject_list = [args.subject]
    raw = next(iter(next(iter(dataset.get_data([args.subject])[args.subject].values())).values()))

    sfreq = raw.info["sfreq"]
    stim = raw.get_data(picks=["stim_trial"])[0]

    # Rising edges into a non-zero command code.
    onsets = np.flatnonzero((stim[:-1] == 0) & (stim[1:] != 0)) + 1
    labels_raw = stim[onsets]
    codes = np.unique(labels_raw)
    print(f"onsets: {len(onsets)}  command codes: {codes.astype(int).tolist()}")

    events = np.column_stack(
        [onsets, np.zeros(len(onsets), dtype=int), labels_raw.astype(int)]
    )

    eeg_picks = mne.pick_types(raw.info, meg=False, eeg=True, stim=False)
    epochs = mne.Epochs(
        raw, events, event_id={str(int(c)): int(c) for c in codes},
        tmin=0.0, tmax=args.epoch_seconds, baseline=None,
        picks=eeg_picks, preload=True, verbose=False,
    )
    epochs.filter(1.0, 40.0, verbose=False)

    X = epochs.get_data()
    y = epochs.events[:, 2]
    print(f"epochs: {X.shape[0]}  channels: {X.shape[1]}  times: {X.shape[2]}")
    counts = {int(c): int((y == c).sum()) for c in np.unique(y)}
    print(f"class counts: {counts}")

    if len(np.unique(y)) < 2:
        print("FAILED: fewer than 2 classes — custom epoching did not work")
        return 1

    clf_factory = lambda: build([args.pipeline])[args.pipeline]  # noqa: E731
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    accs = []
    for train, test in cv.split(X, y):
        clf = clf_factory()
        clf.fit(X[train], y[train])
        accs.append(float((clf.predict(X[test]) == y[test]).mean()))
    acc = float(np.mean(accs))
    chance = 1.0 / len(np.unique(y))
    print(f"accuracy: {acc:.3f}  chance: {chance:.3f}  folds: "
          f"{[round(a, 3) for a in accs]}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{
        "score": acc,
        "pipeline": args.pipeline,
        "subset": f"all_eeg_k{X.shape[1]}",
        "strategy": "full",
        "k": int(X.shape[1]),
        "n_classes": int(len(np.unique(y))),
        "subject": str(args.subject),
        "session": "0",
        "protocol": "within_session",
        "metric": "accuracy",
        "trial_seconds": args.epoch_seconds,
        "track": "cvep_local",
        "dataset_key": "castillos_cvep40",
        "channels": ",".join(epochs.info["ch_names"]),
    }]).to_csv(args.out, index=False)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
