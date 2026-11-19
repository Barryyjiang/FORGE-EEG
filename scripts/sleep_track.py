"""Sleep-staging track on OpenNeuro ds004348 (ear-EEG).

The canonical wearable continuous task, and the task family where ear-EEG has
published positive results. Scored with Cohen's kappa (chance = 0), block-wise
CV so adjacent 30 s epochs cannot leak, and a matched 6-vs-6 montage so that
site is not confounded with channel count.

The dataset's scoring column also contains Arousal (6), Artefact (7) and
Unscored (8) epochs. Those are not sleep stages: they are dropped before the
features and labels are aligned, so every subject is a five-class problem.
The stage map (1=Wake, 2=REM, 3=N1, 4=N2, 5=N3) comes from the dataset's own
``*_acq-scoring_events.json``.

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
#: The five scored sleep stages. 6/7/8 are arousal, artefact and unscored.
STAGES = (1, 2, 3, 4, 5)
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


def permute_labels(y: np.ndarray, rng, mode: str, block: int = BLOCK) -> np.ndarray:
    """A null label sequence for the permutation control.

    ``shift``
        Circular shift. Preserves every run of stages exactly, so the rotated
        sequence is *not* exchangeable with the original when stage priors
        drift across the night (N2 dominates long stretches of every night).
        Kept for continuity with earlier runs, but it is the wrong null: it
        leaves the slow band-power drift partially aligned with the stage runs.
    ``block``
        Shuffle whole ``block``-epoch chunks. Keeps each chunk's internal run
        structure but destroys the long-range alignment between stage runs and
        the drift of band power — which is the association a valid null has to
        break.
    """
    y = np.asarray(y)
    if mode == "shift":
        shift = int(rng.integers(block, max(block + 1, len(y) - block)))
        return np.roll(y, shift)
    if mode == "block":
        idx = np.arange(len(y))
        chunks = [idx[i : i + block] for i in range(0, len(y), block)]
        order = rng.permutation(len(chunks))
        return y[np.concatenate([chunks[i] for i in order])]
    raise ValueError(f"unknown null mode {mode!r}")


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
                   help="label control on every night")
    p.add_argument("--null", choices=["shift", "block"], default="block",
                   help="null label sequence for the control. 'block' (default) "
                        "is the valid one; a circular shift preserves the run "
                        "and drift alignment and gives a null well above chance "
                        "(see permute_labels)")
    p.add_argument("--perm-out", type=Path,
                   default=Path("results/perm_control_sleep_staging_local.csv"),
                   help="where control rows go; point this elsewhere to compare "
                        "nulls without overwriting the committed control")
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
        stages = scoring["staging"].to_numpy()[:n_win]
        keep = np.isin(stages, STAGES)

        montages = {
            "scalp_6": [c for c in SCALP_6 if c in names],
            "ear_6": [c for c in EAR_6 if c in names],
            "ear_14": [c for c in names if c.startswith(("EL", "ER"))],
        }

        for montage, channels in montages.items():
            if len(channels) < 4:
                continue
            picks = [names.index(c) for c in channels]
            data = raw.get_data(picks=picks).astype(np.float32)
            feats = bandpower_windows(data, sfreq, n_win)[keep]
            del data
            y = stages[keep]
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
                "fidelity": "measured",
                "accuracy": acc,
                "n_windows": int(len(y)),
                "n_dropped": int((~keep).sum()),
            })

            if args.permutations:
                # Every night, not just the first: the control's `real` column
                # is read next to the cohort mean, so it has to be measured on
                # the same cohort as the result it validates. Seeded per subject
                # so a re-run reproduces.
                rng = np.random.default_rng(int(subject))
                shifts = []
                for _ in range(args.permutations):
                    shifts.append(run_cv(feats, permute_labels(y, rng, args.null))[0])
                perm_rows.append({
                    "track": "sleep_staging_local",
                    "subset": f"{montage}_k{len(channels)}",
                    "pipeline": "bandpower_lda",
                    "metric": "kappa",
                    "n_classes": int(len(np.unique(y))),
                    "chance": 0.0,
                    "subject": subject,
                    "real": kappa,
                    "perm_mean": float(np.mean(shifts)),
                    "perm_sd": float(np.std(shifts)),
                    "gap": kappa - float(np.mean(shifts)),
                    "montage": montage,
                    "channels": ",".join(channels),
                    "null": args.null,
                    "n_permutations": args.permutations,
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
        perm_out = args.perm_out
        perm_out.parent.mkdir(parents=True, exist_ok=True)
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

    # --- the same comparison with each montage's own null removed ----------
    # If the control does not sit at chance, and does not sit at the *same*
    # place for both montages, the raw pairing measures the null's montage
    # dependence as much as the site effect. Subtracting each montage's own
    # per-night null is a crude bias correction (kappa is not linear), but a
    # comparison that only survives without it is not a site result.
    if perm_rows and {"scalp_6_k6", "ear_6_k6"}.issubset(pivot.columns):
        pr = pd.DataFrame(perm_rows)
        pk = pr.pivot_table(index="subject", columns="montage", values="perm_mean")
        nulls = pk.copy()
        nulls.index = [str(i) for i in nulls.index]
        real = pivot.copy()
        real.index = [str(i) for i in real.index]
        if {"scalp_6", "ear_6"}.issubset(nulls.columns):
            for a, b in (("ear_6_k6", "scalp_6_k6"),):
                corr = ((real[a] - nulls["ear_6"]) -
                        (real[b] - nulls["scalp_6"])).dropna()
                cn = len(corr)
                from scipy import stats

                chalf = (stats.t.ppf(0.975, cn - 1) * corr.std(ddof=1) / np.sqrt(cn)
                         if cn >= 2 else float("nan"))
                print(f"\n\t(null-corrected) {a} - {b}: n={cn} "
                      f"mean={corr.mean():+.3f} 95% CI "
                      f"[{corr.mean() - chalf:+.3f}, {corr.mean() + chalf:+.3f}] "
                      f"| nulls: ear {nulls['ear_6'].mean():+.3f} "
                      f"scalp {nulls['scalp_6'].mean():+.3f}")
                print("  a comparison that only survives without the correction "
                      "is a null artifact, not a site effect")
        print(pr.groupby("subset")["perm_mean"]
              .agg(["mean", "min", "max"]).round(3).to_string())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
