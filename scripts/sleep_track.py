"""Sleep-staging track on OpenNeuro ds004348 (ear-EEG).

The canonical wearable continuous task, and the task family where ear-EEG has
published positive results. Scored with Cohen's kappa (chance = 0), block-wise
CV so adjacent 30 s epochs cannot leak, and a matched 6-vs-6 montage so that
site is not confounded with channel count.

Label semantics: the dataset codes stages 1-5 without documenting the mapping.
Kappa is invariant to it, so scoring is safe; interpretation must not assume
"4 = N3".

    .\\.venv\\Scripts\\python.exe scripts\\sleep_track.py --subjects 001,002,003
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

BANDS = {
    "delta": (0.5, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "sigma": (12.0, 16.0),
    "beta": (16.0, 30.0),
}
SCALP_6 = ["C3", "O1", "F3", "C4", "O2", "F4"]
#: 3 per ear, matched to the 6-channel scalp montage.
EAR_6 = ["ELB", "ELG", "ELK", "ERB", "ERG", "ERK"]
EPOCH_S = 30.0
BLOCK = 20


def bandpower_windows(X: np.ndarray, sfreq: float, n_win: int) -> np.ndarray:
    """Log band-power per 30 s window per channel -> (n_win, chans*bands).

    Filters each window independently rather than the whole night at once: a
    9-hour recording at 200 Hz is 6.5 M samples per channel, and filtering the
    full array needs a copy big enough to exhaust memory. Per-window filtering
    costs a little accuracy at the edges and prevents that.
    """
    from scipy.signal import butter, sosfiltfilt

    win = int(EPOCH_S * sfreq)
    n_chans = X.shape[0]
    feats = np.zeros((n_win, n_chans * len(BANDS)), dtype=np.float64)
    for bi, band in enumerate(BANDS.values()):
        sos = butter(4, band, btype="bandpass", fs=sfreq, output="sos")
        for i in range(n_win):
            seg = X[:, i * win : (i + 1) * win]
            if seg.shape[1] < win // 2:
                continue
            filtered = sosfiltfilt(sos, seg, axis=-1)
            feats[i, bi * n_chans : (bi + 1) * n_chans] = np.log(
                np.var(filtered, axis=-1) + 1e-20
            )
    return feats


def run_cv(feats: np.ndarray, labels: np.ndarray) -> tuple[float, float]:
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.metrics import cohen_kappa_score
    from sklearn.model_selection import GroupKFold

    groups = np.arange(len(labels)) // BLOCK
    preds = np.full(len(labels), -1)
    for train, test in GroupKFold(n_splits=5).split(feats, labels, groups):
        clf = LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")
        clf.fit(feats[train], labels[train])
        preds[test] = clf.predict(feats[test])
    mask = preds >= 0
    return (
        cohen_kappa_score(labels[mask], preds[mask]),
        float((preds[mask] == labels[mask]).mean()),
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--subjects", default="001",
                   help="comma-separated subject ids, e.g. 001,002,003")
    p.add_argument("--session", default="001")
    p.add_argument("--root", type=Path, default=Path("data/openneuro"))
    p.add_argument("--out", type=Path,
                   default=Path("results/benchmark/sleep_staging_local__within_session.csv"))
    p.add_argument("--permutations", type=int, default=0,
                   help="circular-shift label control on the first subject")
    args = p.parse_args()

    import mne

    mne.set_log_level("ERROR")
    subjects = [s.strip().zfill(3) for s in args.subjects.split(",") if s.strip()]

    rows: list[dict] = []
    perm_rows: list[dict] = []

    for subject in subjects:
        eeg_dir = args.root / f"sub-{subject}" / f"ses-{args.session}" / "eeg"
        set_path = eeg_dir / f"sub-{subject}_ses-{args.session}_task-sleep_eeg.set"
        if not set_path.exists():
            print(f"sub-{subject}: not downloaded, skipping")
            continue

        scoring = pd.read_csv(
            eeg_dir / f"sub-{subject}_ses-{args.session}_task-sleep_acq-scoring_events.tsv",
            sep="\t",
        )
        print(f"sub-{subject}: loading ...", flush=True)
        raw = mne.io.read_raw_eeglab(str(set_path), preload=True, verbose=False)
        names = raw.info["ch_names"]
        sfreq = raw.info["sfreq"]
        n_win = min(len(scoring), raw.n_times // int(EPOCH_S * sfreq))
        y = scoring["staging"].to_numpy()[:n_win]

        montages = {
            "scalp_6": [c for c in SCALP_6 if c in names],
            "ear_6": [c for c in EAR_6 if c in names],
            "ear_13": [c for c in names if c.startswith(("EL", "ER"))],
        }

        for montage, channels in montages.items():
            if len(channels) < 4:
                continue
            picks = [names.index(c) for c in channels]
            data = raw.get_data(picks=picks).astype(np.float32)
            feats = bandpower_windows(data, sfreq, n_win)
            del data
            kappa, acc = run_cv(feats, y)
            print(f"  [{montage}] {len(channels)}ch kappa={kappa:.3f} acc={acc:.3f}",
                  flush=True)
            rows.append({
                "score": kappa,
                "pipeline": "bandpower_lda",
                "subset": f"{montage}_k{len(channels)}",
                "strategy": "wearable" if montage.startswith("ear") else "region",
                "k": len(channels),
                "n_classes": int(len(np.unique(y))),
                "subject": subject,
                "session": args.session,
                "protocol": "within_session",
                "metric": "kappa",
                "trial_seconds": EPOCH_S,
                "track": "sleep_staging_local",
                "dataset_key": "openneuro_ds004348",
                "channels": ",".join(channels),
                "accuracy": acc,
            })

            if args.permutations and subject == subjects[0]:
                rng = np.random.default_rng(0)
                shifts = []
                for _ in range(args.permutations):
                    shift = int(rng.integers(BLOCK, n_win - BLOCK))
                    shifts.append(run_cv(feats, np.roll(y, shift))[0])
                perm_rows.append({
                    "track": "sleep_staging_local",
                    "pipeline": "bandpower_lda",
                    "metric": "kappa",
                    "n_classes": int(len(np.unique(y))),
                    "real": kappa,
                    "perm_mean": float(np.mean(shifts)),
                    "perm_sd": float(np.std(shifts)),
                    "gap": kappa - float(np.mean(shifts)),
                    "montage": montage,
                })
                print(f"  [{montage}] perm kappa={np.mean(shifts):.3f}", flush=True)

        del raw
        import gc

        gc.collect()

    if not rows:
        print("no subjects processed")
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.out, index=False)
    print(f"\nwrote {args.out}")

    if perm_rows:
        perm_out = Path("results/perm_control_sleep_staging_local.csv")
        pd.DataFrame(perm_rows).to_csv(perm_out, index=False)
        print(f"wrote {perm_out}")

    # --- paired comparison at matched k -----------------------------------
    df = pd.DataFrame(rows)
    pivot = df.pivot_table(index="subject", columns="subset", values="score")
    if {"scalp_6_k6", "ear_6_k6"}.issubset(pivot.columns):
        delta = (pivot["ear_6_k6"] - pivot["scalp_6_k6"]).dropna()
        n = len(delta)
        mean = delta.mean()
        if n >= 2:
            from scipy import stats

            sem = delta.std(ddof=1) / np.sqrt(n)
            half = stats.t.ppf(0.975, n - 1) * sem
        else:
            half = float("nan")
        print(f"\npaired ear_6 - scalp_6: n={n} mean={mean:+.3f} "
              f"95% CI [{mean - half:+.3f}, {mean + half:+.3f}]")
        print(delta.rename("delta").to_string())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
