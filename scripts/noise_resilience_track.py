"""Noise-resilience track: does the in-ear deficit depend on signal quality?

The question
------------
The benchmark's central claim is that electrode *placement* matters more than
electrode *count*. The obvious objection is that the ear simply has bad signal
quality. This track tests it directly: inject interference at known ratios and
see whether the ear-minus-scalp gap moves.

Predicted outcomes, stated before the run
-----------------------------------------
A. Signal unavailability -- the ear never carried the rhythm, so the gap is
   stable as noise rises.
B. Noise vulnerability -- ear contacts are more exposed to interference, so the
   gap widens.

Design
------
Wu2020 records 122 scalp and 8 in-ear channels *simultaneously*, so one trial
carries both montages. Both are degraded from a common source at identical SNR;
degrading only the ear would just rediscover that noise hurts. Channel count is
held at k=8 on both sides so placement is the only difference.

Noise models
------------
``white``  matched-SNR Gaussian, the conventional baseline.
``donor``  same-trial far-segment resampling, mean-projected per channel. Keeps
           real autocorrelation and interference character without carrying the
           trial's slow offset.

An earlier version drew donor segments from *opposite-class* trials to avoid
label leakage. That was wrong: the donor carried the other class's covariance
structure, so at low SNR the decoder read contradictory class information and
AUC fell below chance (0.374 scalp at -5 dB), which a covariance classifier
cannot do from noise alone. Same-trial resampling removes the leakage without
importing the other class.

Control
-------
A within-subject label-permutation control runs at the clean condition and at
0 dB. A valid decoder sits at chance on shuffled labels; if it does not, the
track is invalid and must not be used.

    .\\.venv\\Scripts\\python.exe scripts\\noise_resilience_track.py
"""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

TRACK = "noise_resilience_wu2020"
SEED = 0
SEGMENT_S = 1.0

#: Fixed, matched-k sets. Count is held constant so placement is isolated.
SCALP_8 = ["C3", "Cz", "C4", "CP3", "CP4", "FC3", "FC4", "FCz"]
EAR_8 = ["LF", "LB", "LOU", "LOD", "RF", "RB", "ROU", "ROD"]

#: ``None`` is the clean condition. Below 0 dB both montages approach chance on
#: Wu2020, which makes the gap meaningless, so the sweep stops at 0 dB.
SNRS = (None, 20.0, 15.0, 12.0, 10.0, 8.0, 5.0, 0.0)
MODELS = ("white", "donor")
CONTROL_SNRS = (None, 0.0)
N_PERMUTATIONS = 20


def load_subjects(n_subjects: int, cache: Path | None) -> list[dict]:
    """Return ``[{subject, X, y, ch}]`` with ``y`` encoded 0/1."""
    if cache and cache.exists():
        z = np.load(cache, allow_pickle=True)
        out = [
            {
                "subject": int(s),
                "X": z[f"X{i}"],
                "y": [str(v) for v in z[f"y{i}"]],
                "ch": [str(c) for c in z[f"ch{i}"]],
            }
            for i, s in enumerate(z["subjects"])
        ]
        print(f"loaded {len(out)} subjects from {cache}", flush=True)
        return out

    import mne
    from moabb.datasets import Wu2020
    from moabb.paradigms import LeftRightImagery

    from eegbench.datasets import promote_channels
    from eegbench.suite import WU2020_EAR

    mne.set_log_level("ERROR")
    dataset = Wu2020()
    dataset.subject_list = dataset.subject_list[:n_subjects]
    promote_channels(dataset, WU2020_EAR)
    paradigm = LeftRightImagery(channels=None)

    out = []
    for subject in dataset.subject_list:
        epochs, y, _ = paradigm.get_data(
            dataset, subjects=[subject], return_epochs=True
        )
        e = epochs if isinstance(epochs, list | tuple) else [epochs]
        X = np.concatenate([x.get_data() for x in e], axis=0).astype(np.float64)
        out.append(
            {
                "subject": subject,
                "X": X,
                "y": [str(v) for v in np.asarray(y)],
                "ch": list(e[0].info["ch_names"]),
            }
        )
        print(f"  sub-{subject:03d} {X.shape}", flush=True)
    return out


def _encode(labels: list[str]) -> np.ndarray:
    classes = sorted(set(labels))
    return np.array([classes.index(v) for v in labels], dtype=int)


def noise_white(shape, rng):
    return rng.standard_normal(shape)


def noise_donor(sig: np.ndarray, rng) -> np.ndarray:
    """Same-trial far-segment noise, mean-projected per channel."""
    n_ch, n_t = sig.shape
    seg = int(SEGMENT_S * 1000)
    parts = []
    for _ in range(int(np.ceil(n_t / seg))):
        t0 = int(rng.integers(0, max(1, n_t - seg)))
        parts.append(sig[:, t0 : t0 + seg])
    noise = np.concatenate(parts, axis=1)[:, :n_t]
    if noise.shape[1] < n_t:
        noise = np.concatenate([noise, noise[:, : n_t - noise.shape[1]]], axis=1)
    return noise - noise.mean(axis=1, keepdims=True)


def inject(X, ch_idx, snr_db, rng, model: str) -> np.ndarray:
    """Add noise to ``ch_idx`` at ``snr_db``, matched on measured signal power."""
    X = X.copy()
    if snr_db is None:
        return X
    for i in range(X.shape[0]):
        sig = X[i][ch_idx]
        nz = noise_white(sig.shape, rng) if model == "white" else noise_donor(sig, rng)
        p_sig = float(np.mean(sig**2))
        p_nz = float(np.mean(nz**2))
        if p_nz <= 0 or p_sig <= 0:
            continue
        X[i][ch_idx] = sig + nz * np.sqrt(p_sig / (10 ** (snr_db / 10.0)) / p_nz)
    return X


def _pipeline():
    from pyriemann.estimation import Covariances
    from pyriemann.tangentspace import TangentSpace
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline

    return make_pipeline(
        Covariances(estimator="lwf"),
        TangentSpace(metric="riemann"),
        LogisticRegression(max_iter=1000),
    )


def auc(X, y, ch_idx) -> float:
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import StratifiedKFold

    cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
    oof = np.zeros(len(y))
    for tr, te in cv.split(y, y):
        clf = _pipeline()
        clf.fit(X[tr][:, ch_idx], y[tr])
        oof[te] = clf.predict_proba(X[te][:, ch_idx])[:, 1]
    return float(roc_auc_score(y, oof))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--subjects", type=int, default=6)
    p.add_argument("--cache", type=Path, default=Path("internal/noise_cache_6.npz"))
    p.add_argument("--out", type=Path,
                   default=Path(f"results/benchmark/{TRACK}__within_session.csv"))
    p.add_argument("--perm-out", type=Path,
                   default=Path(f"results/perm_control_{TRACK}.csv"))
    p.add_argument("--skip-controls", action="store_true")
    args = p.parse_args()

    data = load_subjects(args.subjects, args.cache)

    rows = []
    for d in data:
        ch = d["ch"]
        if any(c not in ch for c in SCALP_8 + EAR_8):
            print(f"  sub-{d['subject']}: missing channels, skipped", flush=True)
            continue
        y = _encode(d["y"])
        s_idx = [ch.index(c) for c in SCALP_8]
        e_idx = [ch.index(c) for c in EAR_8]

        for model in MODELS:
            for snr in SNRS:
                rng = np.random.default_rng(SEED)
                a_s = auc(inject(d["X"], s_idx, snr, rng, model), y, s_idx)
                rng = np.random.default_rng(SEED)
                a_e = auc(inject(d["X"], e_idx, snr, rng, model), y, e_idx)
                rows.append({
                    "score": a_s,
                    "pipeline": "riemann_tslr",
                    "subset": f"scalp_{len(SCALP_8)}ch",
                    "strategy": "matched",
                    "k": len(SCALP_8),
                    "n_classes": 2,
                    "subject": str(d["subject"]).zfill(3),
                    "session": "0",
                    "protocol": "within_session",
                    "metric": "roc_auc",
                    "track": TRACK,
                    "dataset_key": "wu2020",
                    "noise_model": model,
                    "snr_db": "" if snr is None else f"{snr:g}",
                    "ear_auc": a_e,
                    "gap": a_e - a_s,
                })
                print(f"  sub-{d['subject']:03d} {model:5s} snr={str(snr):>5} "
                      f"scalp={a_s:.3f} ear={a_e:.3f} gap={a_e-a_s:+.3f}", flush=True)

    df = pd.DataFrame(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"\nwrote {args.out}")

    if args.skip_controls:
        return 0

    # --- permutation control -------------------------------------------
    # Shuffle labels within subject and re-score. A valid decoder sits at
    # chance on shuffled labels; anything above means the score is structure,
    # not signal.
    perm_rows = []
    for d in data:
        ch = d["ch"]
        if any(c not in ch for c in SCALP_8 + EAR_8):
            continue
        y = _encode(d["y"])
        s_idx = [ch.index(c) for c in SCALP_8]
        for snr in CONTROL_SNRS:
            rng = np.random.default_rng(SEED)
            X = inject(d["X"], s_idx, snr, rng, "white")
            real = auc(X, y, s_idx)
            nulls = []
            for k in range(N_PERMUTATIONS):
                r = np.random.default_rng(1000 + k)
                nulls.append(auc(X, r.permutation(y), s_idx))
            perm_rows.append({
                "track": TRACK,
                "subset": f"scalp_{len(SCALP_8)}ch",
                "pipeline": "riemann_tslr",
                "subject": str(d["subject"]).zfill(3),
                "protocol": "within_session",
                "snr_db": "" if snr is None else f"{snr:g}",
                "real": real,
                "perm_mean": float(np.mean(nulls)),
                "gap": real - float(np.mean(nulls)),
            })
            print(f"  perm sub-{d['subject']:03d} snr={str(snr):>5} "
                  f"real={real:.3f} null={np.mean(nulls):.3f}", flush=True)

    pd.DataFrame(perm_rows).to_csv(args.perm_out, index=False)
    print(f"wrote {args.perm_out}")

    # --- summary --------------------------------------------------------
    clean = df[df.snr_db == ""].set_index(["subject", "noise_model"])["gap"]
    print("\n== paired gap change vs clean ==")
    from scipy import stats

    summary = []
    for model in MODELS:
        for snr in SNRS[1:]:
            s = f"{snr:g}"
            cur = df[(df.snr_db == s) & (df.noise_model == model)].set_index("subject")["gap"]
            base = clean.xs(model, level="noise_model").reindex(cur.index)
            dlt = (cur - base).to_numpy()
            t, pv = stats.ttest_rel(cur.to_numpy(), base.to_numpy())
            half = stats.t.ppf(0.975, len(dlt) - 1) * dlt.std(ddof=1) / np.sqrt(len(dlt))
            summary.append({
                "model": model, "snr_db": snr, "n": len(dlt),
                "gap_mean": float(cur.mean()), "delta": float(dlt.mean()),
                "ci_low": float(dlt.mean() - half), "ci_high": float(dlt.mean() + half),
                "p": float(pv),
                "same_sign": int((np.sign(dlt) == np.sign(dlt.mean())).sum()),
            })
            print(f"  {model:5s} {s:>4} dB: gap={cur.mean():+.3f} "
                  f"d={dlt.mean():+.3f} [{dlt.mean()-half:+.3f},{dlt.mean()+half:+.3f}] p={pv:.3f}")

    Path("results/noise_resilience_summary.json").write_text(
        json.dumps(summary, indent=2)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
