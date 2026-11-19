"""Within-session drift control for STEW.

The rest and task recordings in STEW are separated in time: rest was always
recorded first. A decoder that separates rest from task might therefore be
reading *when in the session* a window was recorded rather than what the person
was doing. This control tests that directly without using any labels.

For each 150 s recording, split the windows into first half and second half and
train a classifier to predict which half a window came from. If that is
learnable, the recording drifts over time: electrode contact, posture, sweat,
amplifier warm-up, fatigue. Any rest-vs-task result on STEW then inherits that
drift as a confound, because rest and task are on opposite sides of it.

The control is run twice:

``half``
    First vs second half of each recording. This is the drift test.

``shuffled``
    The same halves, assigned at random. A valid null: if the real halves are
    no more separable than random halves, there is no drift to explain the
    rest-vs-task result.

    .\\.venv\\Scripts\\python.exe scripts\\stew_drift_control.py
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from stew_raw_track import (  # noqa: E402
    CHANNELS, LAYOUTS, bandpass, psd_features, read_dataset,
)


def half_accuracy(feats: np.ndarray, chidx: list[int], *, shuffle: bool,
                  rng: np.random.Generator) -> float:
    """Can a decoder tell the first half of a recording from the second?

    ``feats`` is (windows, channels, features) for one recording. The label is
    the window's position, never the rest/task condition, so this control uses
    no task information at all.
    """
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.metrics import accuracy_score
    from sklearn.model_selection import StratifiedKFold
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    x = feats[:, chidx, :].reshape(len(feats), -1)
    n = len(x)
    pos = np.arange(n) >= n // 2
    y = pos.astype(int)
    if shuffle:
        # Random halves of the same size: the null for "position is learnable".
        y = rng.permutation(y)

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    preds = np.full(n, -1)
    for tr, te in skf.split(x, y):
        clf = make_pipeline(StandardScaler(),
                            LinearDiscriminantAnalysis(solver="lsqr",
                                                       shrinkage="auto"))
        clf.fit(x[tr], y[tr])
        preds[te] = clf.predict(x[te])
    return float(accuracy_score(y, preds))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--zip", type=Path, default=Path("data/stew_raw/STEW Dataset.zip"))
    p.add_argument("--n-shuffles", type=int, default=20)
    p.add_argument("--out", type=Path,
                   default=Path("results/stew_drift_control.csv"))
    args = p.parse_args()

    recs = read_dataset(args.zip)
    feats_by_rec = [psd_features(bandpass(sig)) for _, _, sig in recs]
    labels = np.array([int(cond == "hi") for _, cond, _ in recs])
    groups = np.array([s for s, _, _ in recs])
    rng = np.random.default_rng(0)

    rows = []
    for layout, (chans, _strategy, _fidelity) in LAYOUTS.items():
        chidx = [CHANNELS.index(c) for c in chans]
        for rec_i, (subj, cond, _sig) in enumerate(recs):
            real = half_accuracy(feats_by_rec[rec_i], chidx, shuffle=False, rng=rng)
            nulls = [half_accuracy(feats_by_rec[rec_i], chidx, shuffle=True, rng=rng)
                     for _ in range(args.n_shuffles)]
            rows.append({
                "layout": layout,
                "k": len(chans),
                "subject": str(subj).zfill(2),
                "condition": cond,
                "real_half_accuracy": real,
                "null_mean": float(np.mean(nulls)),
                "null_sd": float(np.std(nulls)),
                "gap": real - float(np.mean(nulls)),
                "n_windows": int(feats_by_rec[rec_i].shape[0]),
                "n_shuffles": args.n_shuffles,
            })
        sub = [r for r in rows if r["layout"] == layout]
        print(f"  {layout:14s} first-vs-second-half acc="
              f"{np.mean([r['real_half_accuracy'] for r in sub]):.3f} "
              f"(null {np.mean([r['null_mean'] for r in sub]):.3f})", flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(args.out, index=False)
    print(f"\nwrote {args.out}")

    print("\n--- first half vs second half, per layout ---")
    print(df.groupby("layout")[["real_half_accuracy", "null_mean", "gap"]]
          .mean().round(3).to_string())
    print("\nchance = 0.50. A gap well above zero means the recording drifts, "
          "so rest-vs-task is partly 'which half of the session'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
