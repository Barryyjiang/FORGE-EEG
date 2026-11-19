"""Cognitive-workload track on STEW, read from the raw IEEE DataPort release.

STEW (Lim, Sourina & Wang 2018) is 48 participants, an Emotiv EPOC (14 channels,
128 Hz), and two 150 s recordings each: ``subXX_lo`` (rest, recorded first) and
``subXX_hi`` (the SIMKAP multitasking test). The released ``ratings.txt``
confirms the mapping -- its second column is the rest rating (1-5) and its third
the task rating (4-9) -- so ``lo``/``hi`` are rest/task, not two task
difficulties.

Why the raw release and not a processed one
-------------------------------------------
The MONSTER HuggingFace release (``monster-monash/STEW``) is *not* the same
task. It labels windows by the self-reported rating (``> 4`` = high), not by
condition, and it ships 594 two-second windows per participant where the raw
recordings hold 150. Its windows are also independently processed, so they
cannot be re-filtered as continuous recordings. Scoring it produced 0.96-1.00
AUC here and chance under participant-disjoint CV -- both artefacts of the
release, not of STEW. This script reads the original files and filters each
150 s recording whole, which is what the reference implementation does.

Protocols
---------
``cross_subject``
    5-fold ``GroupKFold`` by participant, the protocol the team's own
    reimplementation and the STEW literature use. The decoder never sees the
    test person.

``within_session``
    5-fold over the windows of one participant, pooling that person's two
    recordings. A *calibration* protocol: the decoder is trained on part of a
    person's own session. It is near-ceiling on STEW, which is itself the
    finding -- see the drift control.

Two numbers per montage
-----------------------
``score`` (window level)
    ROC-AUC over a participant's own held-out 4 s windows, both recordings
    pooled (37 rest + 37 task). One decision per window, which is the rule the
    other tracks follow, and the only aggregation that cannot be inflated by
    averaging many correlated windows into one prediction.

``recording_auc`` / ``recording_accuracy`` (recording level)
    One decision per 150 s recording, i.e. the mean window probability. This is
    the number the STEW literature and the team's report quote (90.62%
    balanced accuracy for the full montage), so it is written alongside rather
    than instead of the window-level score. It is *easier* than the window-level
    number by construction and must not be presented as the harder task.

The confound
------------
Rest was always recorded before the task, so rest and task sit on opposite
sides of a session boundary. ``stew_drift_control.py`` measures that boundary
without labels: a decoder told only "first half vs second half of this
recording" reaches 0.613 against a shuffled-halves null of 0.501. The
rest-vs-task decoder is therefore reading condition *and* session position, and
the released data cannot separate the two. Report the result as
rest-vs-SIMKAP condition recognition, never as a validated workload score.

    .\\.venv\\Scripts\\python.exe scripts\\stew_raw_track.py
"""

from __future__ import annotations

import argparse
import io
import itertools
import random
import re
import warnings
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

TRACK = "stew_workload_14ch"
DATASET_KEY = "stew"

#: Emotiv EPOC channel order as released in STEW.
CHANNELS = ["AF3", "F7", "F3", "FC5", "T7", "P7", "O1", "O2",
            "P8", "T8", "FC6", "F4", "F8", "AF4"]

BANDS = {
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta": (13.0, 28.0),
    "broadband": (1.0, 30.0),
}

#: Named layouts. ``glasses_4`` and ``forehead_2`` are the wearable-like
#: layouts from the team document. They are scalp proxies cut from an EPOC, not
#: measured glasses hardware, so they carry fidelity ``proxy``.
LAYOUTS: dict[str, tuple[list[str], str, str]] = {
    "full_14": (CHANNELS, "full", "measured"),
    "glasses_4": (["AF3", "AF4", "F7", "F8"], "wearable", "proxy"),
    "posterior_4": (["P7", "P8", "O1", "O2"], "region", "measured"),
    "forehead_2": (["AF3", "AF4"], "wearable", "proxy"),
}

FS = 128
WINDOW_S = 4.0
N_FEATURES = len(BANDS) + 1          # four band powers + theta/alpha ratio


def read_dataset(zip_path: Path) -> list[tuple[int, str, np.ndarray]]:
    """Return ``[(participant, 'lo'|'hi', signal[time, 14])]``, sorted."""
    out = []
    with zipfile.ZipFile(zip_path) as z:
        names = sorted(n for n in z.namelist()
                       if re.search(r"sub\d{2}_(lo|hi)\.txt$", n)
                       and not n.startswith("__MACOSX/"))
        if len(names) != 96:
            raise ValueError(f"expected 96 recordings, found {len(names)}")
        for n in names:
            m = re.search(r"sub(\d{2})_(lo|hi)\.txt$", n)
            sig = np.loadtxt(io.BytesIO(z.read(n)))
            if sig.shape[1] != len(CHANNELS):
                raise ValueError(f"unexpected columns in {n}: {sig.shape}")
            out.append((int(m.group(1)), m.group(2), sig))
    return out


def bandpass(sig: np.ndarray) -> np.ndarray:
    """Zero-phase 1-30 Hz bandpass over the *whole* recording.

    Filtering the continuous recording and then cutting windows is not
    equivalent to filtering pre-cut windows: a zero-phase filter run over a 4 s
    window loses its edges and cannot see the slower components that a 150 s
    recording carries. That difference is why the pre-cut release scored at
    chance here.
    """
    from scipy.signal import butter, sosfiltfilt

    sos = butter(4, [1.0, 30.0], btype="bandpass", fs=FS, output="sos")
    return sosfiltfilt(sos, sig, axis=0)


def psd_features(filt: np.ndarray) -> np.ndarray:
    """Log band power + theta/alpha per 4 s window, per channel.

    Returns ``(windows, channels, features)``.
    """
    from scipy.signal import welch

    win = int(WINDOW_S * FS)
    n = filt.shape[0] // win
    seg = filt[: n * win].reshape(n, win, filt.shape[1])
    f, pxx = welch(seg, fs=FS, nperseg=win, axis=1, detrend="constant")
    feats = []
    for lo, hi in BANDS.values():
        mask = (f >= lo) & (f < hi)
        feats.append(np.log10(np.maximum(
            pxx[:, mask, :].sum(axis=1) * (f[1] - f[0]), 1e-12)))
    theta, alpha = feats[0], feats[1]
    feats.append(np.log10(np.maximum(10 ** theta / 10 ** alpha, 1e-12)))
    return np.stack(feats, axis=2)


def _flat(feats: np.ndarray, chidx: list[int]) -> np.ndarray:
    return feats[:, chidx, :].reshape(len(feats), len(chidx) * N_FEATURES)


def _classifier():
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    return make_pipeline(
        StandardScaler(),
        LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto"),
    )


def oof_probabilities(feats_by_rec, y, groups, chidx, protocol: str,
                      seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Out-of-fold window probabilities and the recording that owns each window.

    The decoder is refit once per fold and every window of the held-out
    recording is scored, so the returned probabilities are honest window-level
    predictions rather than averages.
    """
    from sklearn.model_selection import GroupKFold, StratifiedKFold

    n_rec = len(y)
    owner = np.concatenate([np.full(feats_by_rec[i].shape[0], i)
                            for i in range(n_rec)])
    probs = np.full(len(owner), np.nan)

    if protocol == "cross_subject":
        folds = list(GroupKFold(n_splits=5).split(
            np.zeros((n_rec, 1)), y, groups))
        for tr, te in folds:
            x = np.concatenate([_flat(feats_by_rec[i], chidx) for i in tr])
            t = np.concatenate([np.full(feats_by_rec[i].shape[0], y[i])
                                for i in tr])
            clf = _classifier().fit(x, t)
            for i in te:
                sel = owner == i
                probs[sel] = clf.predict_proba(
                    _flat(feats_by_rec[i], chidx))[:, 1]
        return probs, owner

    if protocol != "within_session":
        raise ValueError(f"unknown protocol {protocol!r}")

    for s in np.unique(groups):
        recs = np.where(groups == s)[0]
        # ``owner`` is laid out recording by recording in ascending order, so
        # the global window indices for these recordings are also ascending and
        # line up with the concatenated feature matrix below.
        gidx = np.where(np.isin(owner, recs))[0]
        x = np.concatenate([_flat(feats_by_rec[i], chidx) for i in recs])
        t = np.concatenate([np.full(feats_by_rec[i].shape[0], y[i])
                            for i in recs])
        for tr, te in StratifiedKFold(5, shuffle=True,
                                      random_state=seed).split(x, t):
            clf = _classifier().fit(x[tr], t[tr])
            probs[gidx[te]] = clf.predict_proba(x[te])[:, 1]
    return probs, owner


def subject_scores(probs, owner, y, groups) -> dict[int, dict]:
    """Per-participant window AUC / balanced accuracy and recording-level calls.

    A participant contributes one rest and one task recording, so their window
    AUC is always defined. It is skipped rather than returned as NaN if a caller
    ever hands over a single-class participant -- a NaN here silently poisons
    every mean downstream.
    """
    from sklearn.metrics import balanced_accuracy_score, roc_auc_score

    out = {}
    for s in np.unique(groups):
        recs = np.where(groups == s)[0]
        m = np.isin(owner, recs)
        p, t = probs[m], y[owner[m]]
        if len(np.unique(t)) < 2:
            continue
        rec_prob = {int(i): float(np.nanmean(probs[owner == i])) for i in recs}
        out[int(s)] = {
            "window_auc": float(roc_auc_score(t, p)),
            "window_accuracy": float(balanced_accuracy_score(
                t, (p >= 0.5).astype(int))),
            "recordings": rec_prob,
            "n_windows": int(m.sum()),
        }
    return out


def cohort_recording_scores(probs, owner, y) -> tuple[float, float]:
    """AUC and balanced accuracy after averaging windows into one call per recording."""
    from sklearn.metrics import balanced_accuracy_score, roc_auc_score

    rec = np.array([np.nanmean(probs[owner == i]) for i in range(len(y))])
    return (float(roc_auc_score(y, rec)),
            float(balanced_accuracy_score(y, (rec >= 0.5).astype(int))))


def run_layout(feats_by_rec, y, groups, chans, protocol, seed=0):
    chidx = [CHANNELS.index(c) for c in chans]
    probs, owner = oof_probabilities(feats_by_rec, y, groups, chidx, protocol,
                                     seed=seed)
    per_subject = subject_scores(probs, owner, y, groups)
    rec_auc, rec_acc = cohort_recording_scores(probs, owner, y)
    return per_subject, rec_auc, rec_acc


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--zip", type=Path,
                   default=Path("data/stew_raw/STEW Dataset.zip"))
    p.add_argument("--out-dir", type=Path, default=Path("results/benchmark"))
    p.add_argument("--perm-out", type=Path,
                   default=Path("results/perm_control_stew_workload_14ch.csv"))
    p.add_argument("--permutations", type=int, default=100)
    p.add_argument("--random-draws", type=int, default=100,
                   help="random k=4 montages for the placement control")
    p.add_argument("--skip-controls", action="store_true")
    args = p.parse_args()

    recs = read_dataset(args.zip)
    feats_by_rec = [psd_features(bandpass(sig)) for _, _, sig in recs]
    y = np.array([int(cond == "hi") for _, cond, _ in recs])
    groups = np.array([subj for subj, _, _ in recs])
    n_win = feats_by_rec[0].shape[0]
    print(f"recordings={len(y)} windows/recording={n_win} "
          f"subjects={len(np.unique(groups))}", flush=True)

    rows: list[dict] = []
    for protocol in ("within_session", "cross_subject"):
        for layout, (chans, strategy, fidelity) in LAYOUTS.items():
            per_subject, rec_auc, rec_acc = run_layout(
                feats_by_rec, y, groups, chans, protocol)
            for s, d in per_subject.items():
                rows.append({
                    "score": d["window_auc"],
                    "pipeline": "psd_lda",
                    "subset": f"{layout}_k{len(chans)}",
                    "strategy": strategy,
                    "k": len(chans),
                    "n_classes": 2,
                    "subject": str(s).zfill(3),
                    "session": "0",
                    "protocol": protocol,
                    "metric": "roc_auc",
                    "trial_seconds": WINDOW_S,
                    "track": TRACK,
                    "dataset_key": DATASET_KEY,
                    "channels": ",".join(chans),
                    "fidelity": fidelity,
                    "accuracy": d["window_accuracy"],
                    "recording_auc": rec_auc,
                    "recording_accuracy": rec_acc,
                    "n_windows": d["n_windows"],
                    "n_dropped": 0,
                })
            mean_auc = np.mean([d["window_auc"] for d in per_subject.values()])
            mean_acc = np.mean([d["window_accuracy"]
                                for d in per_subject.values()])
            print(f"  {layout:14s} {protocol:14s} "
                  f"window_auc={mean_auc:.3f} window_acc={mean_acc:.3f} | "
                  f"recording_auc={rec_auc:.3f} recording_acc={rec_acc:.3f}",
                  flush=True)

    df = pd.DataFrame(rows)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for protocol in ("within_session", "cross_subject"):
        path = args.out_dir / f"{TRACK}__{protocol}.csv"
        df[df["protocol"] == protocol].to_csv(path, index=False)
        print(f"wrote {path}")

    if args.skip_controls:
        return 0

    # --- permutation control ---------------------------------------------
    # The null swaps the two labels *within* each participant with probability
    # 1/2, rather than shuffling all 96 labels freely. Two reasons:
    #
    #   1. Correctness of the null. Each participant contributes exactly one
    #      rest and one task recording, so under H0 the pairing is exchangeable
    #      and a within-pair swap is the exact permutation. A free shuffle can
    #      hand a participant two recordings of the same class, which leaves
    #      their window AUC undefined and quietly turns the whole null into NaN.
    #   2. It keeps the class balance and the pairing that the real design has,
    #      so the null carries the same CV structure as the number it tests.
    #
    # The control is written at COHORT level, one row per montage. A per-subject
    # null is not meaningful here: the decoder is cross-subject, so in any one
    # draw roughly half the participants are unswapped and keep their true
    # labels, and their individual null AUCs scatter well above 0.5 even though
    # the cohort mean sits on chance. Only the cohort statistic is the test.
    rng = np.random.default_rng(0)
    pair_a = np.array([np.where((groups == s) & (y == 0))[0][0]
                       for s in np.unique(groups)])
    pair_b = np.array([np.where((groups == s) & (y == 1))[0][0]
                       for s in np.unique(groups)])

    perm_rows = []
    for layout, (chans, _strategy, _fidelity) in LAYOUTS.items():
        real_rows = df[(df["protocol"] == "cross_subject")
                       & (df["subset"] == f"{layout}_k{len(chans)}")]
        real_value = float(real_rows["score"].mean())
        nulls = []
        for _ in range(args.permutations):
            y_perm = y.copy()
            swap = rng.random(len(pair_a)) < 0.5
            y_perm[pair_a[swap]] = 1
            y_perm[pair_b[swap]] = 0
            per_subject, _, _ = run_layout(feats_by_rec, y_perm, groups, chans,
                                           "cross_subject")
            nulls.append(float(np.mean([d["window_auc"]
                                        for d in per_subject.values()])))
        nulls = np.array(nulls)
        perm_rows.append({
            "track": TRACK,
            "subset": f"{layout}_k{len(chans)}",
            "pipeline": "psd_lda",
            "metric": "roc_auc",
            "n_classes": 2,
            "chance": 0.5,
            "subject": "cohort",
            "real": real_value,
            "perm_mean": float(nulls.mean()),
            "perm_sd": float(nulls.std()),
            "gap": real_value - float(nulls.mean()),
            "montage": layout,
            "channels": ",".join(chans),
            "null": "within-pair swap",
            "n_permutations": args.permutations,
        })
        print(f"  {layout:14s} real={real_value:.3f} "
              f"perm null window_auc={nulls.mean():.3f}", flush=True)

    args.perm_out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(perm_rows).to_csv(args.perm_out, index=False)
    print(f"wrote {args.perm_out}")

    # --- placement control: random k=4 montages --------------------------
    # Answers "is glasses_4 better than an arbitrary four electrodes?" without
    # the selection bias of having picked it by hand.
    if args.random_draws:
        rng_py = random.Random(0)
        combos = list(itertools.combinations(CHANNELS, 4))
        rng_py.shuffle(combos)
        draws = []
        for combo in combos[: args.random_draws]:
            per_subject, _, _ = run_layout(feats_by_rec, y, groups, list(combo),
                                           "cross_subject")
            draws.append(float(np.mean([d["window_auc"]
                                        for d in per_subject.values()])))
        draws = np.array(draws)
        glasses = float(df[(df["protocol"] == "cross_subject")
                           & (df["subset"] == "glasses_4_k4")]["score"].mean())
        print(f"\nrandom k=4 montages (n={len(draws)}): "
              f"median={np.median(draws):.3f} "
              f"p10={np.percentile(draws, 10):.3f} "
              f"p90={np.percentile(draws, 90):.3f}")
        print(f"glasses_4={glasses:.3f} beats "
              f"{int((draws <= glasses).sum())}/{len(draws)} random draws "
              f"(percentile {100 * (draws <= glasses).mean():.0f})")
        pd.DataFrame({"draw": np.arange(len(draws)), "score": draws}).to_csv(
            args.out_dir.parent / "stew_random_montages.csv", index=False)

    # --- paired comparisons at matched k ---------------------------------
    from scipy import stats

    for protocol in ("within_session", "cross_subject"):
        sub = df[df["protocol"] == protocol]
        pivot = sub.pivot_table(index="subject", columns="subset", values="score")
        for a, b in (("glasses_4_k4", "full_14_k14"),
                     ("posterior_4_k4", "full_14_k14"),
                     ("glasses_4_k4", "posterior_4_k4")):
            if not {a, b}.issubset(pivot.columns):
                continue
            d = (pivot[a] - pivot[b]).dropna()
            n = len(d)
            half = stats.t.ppf(0.975, n - 1) * d.std(ddof=1) / np.sqrt(n)
            print(f"{protocol:14s} paired {a} - {b}: n={n} mean={d.mean():+.3f} "
                  f"95% CI [{d.mean() - half:+.3f}, {d.mean() + half:+.3f}] "
                  f"same_sign={int((np.sign(d) == np.sign(d.mean())).sum())}/{n}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
