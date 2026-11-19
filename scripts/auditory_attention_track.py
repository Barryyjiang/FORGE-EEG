"""Auditory-attention track on Ear-SAAD (Geirnaert, Kappel & Kidmose 2025).

The only public dataset that records scalp, around-ear and in-ear EEG
*simultaneously* during a selective-attention task, so it is the direct test of
"does the ear site work for this paradigm" rather than a geometric proxy.

Data
----
Zenodo record 16536441 (CC BY 4.0), ``preprocessedData.zip``. Each
``dataSubject<N>.mat`` holds six 10-minute trials at 20 Hz with:
    eegTrials[i]      (12000, 61)  channels, see ``channels``
    envelopes[i]      (12000, 2)   speech envelopes of the two talkers
    attSpeaker[i]     1 or 2       which talker was attended
    attendedEar[i]    1 or 2       which ear was attended (same as speaker)
    acousticEdges[i]  (12000, 2)   acoustic onsets of the two talkers
    videoCondition[i] 0 or 1       gaze condition

Decoder
-------
Forward stimulus reconstruction with ridge regression, the standard AAD
baseline: learn a linear map from EEG to the attended speech envelope, then
score each candidate talker by the correlation between the reconstructed
envelope and that talker's true envelope. The decoder is trained on five trials
and tested on the sixth (leave-one-trial-out), which is the paper's protocol.

Every montage is scored on the *same* trials with the *same* decoder and the
same decision window, so the comparison is matched by construction.

Preprocessing is already applied in the release
-----------------------------------------------
The published pipeline is heavier than this script: 1-9 Hz zero-phase
Butterworth, EOG regression (scalp only), bad-channel removal (correlation on
2 s segments below 0.45 against 95% of the other channels for at least half the
trial), **ASR with cutoff 5**, high-power window rejection, per-setup CAR,
downsample to 20 Hz, and per-trial Frobenius normalisation.

All of that is already inside ``dataSubject<N>.mat``. The authors' own
``preprocessFromBIDS.m`` calls ``rejectChannelsAndASR`` (``clean_channels_nolocs``
at 0.45, then ``clean_asr(...,5,...)``) on the scalp, in-ear and around-ear sets
separately and only then saves ``eegTrials``. The dead electrodes this script
drops (``ELC``, ``cEL3``, ``ERT``) are exactly the channels that function
flagged and set to NaN.

So there is nothing to re-run here, and re-running ASR on 20 Hz data would be
wrong. ``scripts/earsaad_paper_check.py`` confirms it numerically: our 60 s
accuracies land on the paper's *with-ASR* column (83.44 / 67.22 / 61.11), not on
its no-artifact-removal ablation (86.11 / 64.89 / 58.78).

    .\\.venv\\Scripts\\python.exe scripts\auditory_attention_track.py
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import loadmat

warnings.filterwarnings("ignore")

TRACK = "auditory_attention_earsaad"
DATASET_KEY = "earsaad"

#: Channel groups.
#:
#: The naming in the released data is *inverted* relative to the Zenodo
#: description: the ``c``-prefixed ``cEL*/cER*`` set is the 19-electrode wet
#: around-ear array (9 left + 10 right, the C-shaped cEEGrid-like holder), and
#: the plain ``EL*/ER*`` set is the 12-electrode dry in-ear set (six per ear,
#: custom silicone earpieces). The paper's electrode section is authoritative:
#:
#:   "Around-ear EEG was recorded using 19 Ag/AgCl-electrodes ... with 9 placed
#:    around the left ear and 10 around the right ear"
#:   "In-ear EEG was recorded using 12 dry Ag/AgCl-electrodes ... six per ear"
#:
#: Inter-electrode correlation in the data confirms it: both sets show strong
#: within-ear correlation and near-zero across-ear correlation, and the 19-set
#: is the symmetric 9+10 array.
#:
#: ``Fp1-cr`` is a re-referenced copy of Fp1 and M1/M2 are mastoid references,
#: so the scalp montage is the 29 EEG electrodes the paper reports.
SCALP = ["O1", "Pz", "P3", "P7", "CP1", "CP5", "M1", "Cz", "C3", "T7", "FC1",
         "FC5", "F3", "F7", "Fp1", "O2", "P4", "P8", "CP2", "CP6", "M2", "C4",
         "T8", "FC2", "FC6", "Fz", "F4", "F8", "Fp2"]
#: 19 wet electrodes on the C-shaped array around both ears.
AROUND_EAR = [f"cEL{i}" for i in range(1, 10)] + [f"cER{i}" for i in range(1, 11)]
#: 12 dry electrodes on custom earpieces, six per ear.
IN_EAR = ["ELA", "ELB", "ELC", "ELE", "ELI", "ELT",
          "ERA", "ERB", "ERC", "ERE", "ERI", "ERT"]

LAYOUTS: dict[str, tuple[list[str], str, str]] = {
    "scalp_29": (SCALP, "full", "measured"),
    "around_ear_19": (AROUND_EAR, "wearable", "measured"),
    "in_ear_12": (IN_EAR, "wearable", "measured"),
}


def _matched_scalp() -> dict[str, tuple[list[str], str, str]]:
    """Max-spread scalp subsets that match the ear arrays channel for channel.

    The three systems in this dataset were built with 29, 19 and 12 electrodes,
    so the paper's own comparison confounds site with count. The benchmark's
    rule is that a difference must be a difference in *placement*, which needs
    equal k on both sides. These two subsets supply that: the first 12 and the
    first 19 channels of a farthest-point ordering of the scalp cap, i.e. the
    most spatially spread k-electrode scalp montages available.

    They are ``distributed`` rather than ``full`` so they are never mistaken for
    the reference cap, and the reference for the matched comparison is the
    matched scalp subset itself.
    """
    from eegbench.subsets import farthest_point_order

    order = farthest_point_order(SCALP)
    return {
        "scalp_19": (order[:19], "distributed", "measured"),
        "scalp_12": (order[:12], "distributed", "measured"),
    }


LAYOUTS.update(_matched_scalp())

FS = 20.0
TRIAL_S = 600.0
#: Decision windows, in seconds. This is the paper's own grid, so the
#: accuracy-vs-window curve can be compared point for point. The paper's
#: headline is 60 s; the short end is the realistic wearable regime, and the
#: long end is where every setup converges towards 100%.
WINDOWS_S = (1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0)
#: The paper's filter taps span [0, 400] ms post-stimulus. At 20 Hz that is
#: 9 samples, and the lags are taken *after* the current sample (the neural
#: response follows the stimulus), so LAGS = 0..8 rather than a symmetric
#: window. Using a symmetric window around t was the first version's bug: it
#: puts most of the filter on the wrong side of the response.
LAG_MS = 400.0
#: Ridge penalty. The paper uses Ledoit-Wolf shrinkage; on data normalised to
#: unit Frobenius norm per trial a fixed small alpha reproduces its behaviour
#: (see the alpha sweep in the commit message). Accuracy is flat across
#: 1e-3..1e-1, so the choice is not load-bearing.
ALPHA = 0.01


def lags_for(fs: float) -> tuple[int, ...]:
    """Filter taps spanning [0, LAG_MS] ms post-stimulus."""
    return tuple(range(0, int(round(LAG_MS / 1000.0 * fs)) + 1))


def normalize_trial(x: np.ndarray) -> np.ndarray:
    """Scale a trial to unit Frobenius norm, as the paper does per trial.

    Without this the ridge penalty means something different for every montage
    and every subject, because the raw amplitudes differ by orders of
    magnitude between scalp and in-ear recordings.
    """
    n = np.linalg.norm(x)
    return x / n if n > 0 else x


def normalize_envelope(e: np.ndarray) -> np.ndarray:
    """Zero mean, unit variance per trial, as the paper does."""
    sd = e.std()
    return (e - e.mean()) / sd if sd > 0 else e


def load_subject(root: Path, subject: int) -> dict:
    """Load one subject, interpolating short NaN gaps.

    A few electrodes are dead for a whole trial (``ELC``, ``cEL3``, ``ERT`` and
    friends). Those are left as NaN here and dropped per-montage by
    :func:`usable_channels`, so a dead electrode removes one channel from the
    montage rather than corrupting the trial.
    """
    m = loadmat(root / f"dataSubject{subject}.mat", squeeze_me=True,
                struct_as_record=False)
    chans = [str(c) for c in m["channels"]]
    trials = []
    for raw in m["eegTrials"]:
        x = np.asarray(raw, dtype=float)
        # Linear-interpolate interior NaN gaps; a dead channel stays all-NaN.
        for c in range(x.shape[1]):
            col = x[:, c]
            bad = np.isnan(col)
            if bad.all() or not bad.any():
                continue
            idx = np.arange(len(col))
            x[bad, c] = np.interp(idx[bad], idx[~bad], col[~bad])
        trials.append(x)
    return {
        "channels": chans,
        "trials": trials,
        "envelopes": [np.asarray(e, dtype=float) for e in m["envelopes"]],
        "att_speaker": np.asarray(m["attSpeaker"]).astype(int).ravel(),
        "fs": float(m["fs"]),
    }


def usable_channels(sub: dict, channels: list[str]) -> list[str]:
    """Channels that are not dead in *any* trial of this subject."""
    dead = set()
    for t in sub["trials"]:
        for i, c in enumerate(sub["channels"]):
            if np.isnan(t[:, i]).all():
                dead.add(c)
    return [c for c in channels if c not in dead]


def lagged(x: np.ndarray, lags) -> np.ndarray:
    """Stack time-lagged copies of a (time, features) array.

    Rows whose lags fall outside the array are dropped rather than padded with
    NaN, so the returned array has ``len(x) - (max(lags) - min(lags))`` rows.
    """
    lo, hi = min(lags), max(lags)
    n = x.shape[0]
    start, stop = max(0, -lo), n - max(0, hi)
    out = []
    for lag in lags:
        out.append(x[start + lag:stop + lag])
    return np.concatenate(out, axis=1)


def fit_decoder(train_x, train_env, lags):
    """Fit the ridge EEG->envelope decoder once per fold.

    The decoder does not depend on the decision window length: the window only
    changes which test samples are averaged into a correlation. Fitting it once
    and reusing it across every window length turns an O(windows) loop into
    O(folds), which is the difference between minutes and hours.
    """
    from sklearn.linear_model import Ridge

    xt = lagged(train_x, lags)
    yt = train_env[: len(xt)]
    # The paper uses Ledoit-Wolf's analytical shrinkage estimator for lambda
    # rather than a fixed alpha; it adapts to the montage's channel count and
    # SNR, which matters because scalp and in-ear have very different scales.
    reg = Ridge(alpha=ALPHA)
    reg.fit(xt, yt)
    return reg


def window_accuracy(reg, test_x, cand_envs, lags, win: int) -> tuple[int, int]:
    """Score every non-overlapping ``win``-sample decision window of a trial."""
    xs = lagged(test_x, lags)
    recon = reg.predict(xs)
    n = len(recon)
    # ``lagged`` drops ``max(lags)`` samples off the end, so a window as long as
    # the whole trial (600 s) would leave nothing to score. Clamp instead of
    # silently returning an empty tally.
    win = min(win, n)
    correct = total = 0
    for start in range(0, n - win + 1, win):
        sl = slice(start, start + win)
        corrs = [np.corrcoef(recon[sl], cand_envs[sl, k])[0, 1]
                 for k in range(cand_envs.shape[1])]
        correct += int(np.argmax(corrs) == 0)   # talker 1 is index 0
        total += 1
    return correct, total


def evaluate(sub: dict, channels: list[str],
             windows_s: list[float]) -> tuple[dict[float, float], int]:
    """Leave-one-trial-out accuracy at each decision window, one fit per fold.

    Returns the accuracies and how many electrodes were dropped as dead, so the
    CSV can say when a montage did not actually have its nominal channel count.
    """
    requested = len(channels)
    channels = usable_channels(sub, channels)
    idx = [sub["channels"].index(c) for c in channels]
    att = sub["att_speaker"]
    lags = lags_for(sub["fs"])

    # Per-trial normalization, exactly as the paper specifies: EEG to unit
    # Frobenius norm, envelopes to zero mean / unit variance.
    trials = [normalize_trial(t[:, idx]) for t in sub["trials"]]
    envs = [normalize_envelope(e) for e in sub["envelopes"]]

    tally = {w: [0, 0] for w in windows_s}
    for held in range(len(trials)):
        train_trials = [t for t in range(len(trials)) if t != held]
        tx = np.concatenate([trials[t] for t in train_trials])
        te = np.concatenate([envs[t][:, att[t] - 1] for t in train_trials])
        reg = fit_decoder(tx, te, lags)

        env = envs[held]
        att_idx = att[held] - 1
        # Candidate envelopes, attended first.
        cand = np.stack([env[:, att_idx], env[:, 1 - att_idx]], axis=1)

        for w in windows_s:
            c, t = window_accuracy(reg, trials[held], cand, lags,
                                   int(w * sub["fs"]))
            tally[w][0] += c
            tally[w][1] += t

    return ({w: c / max(t, 1) for w, (c, t) in tally.items()},
            requested - len(channels))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("data/earsaad/preprocessedData"))
    p.add_argument("--subjects", default="1",
                   help="comma-separated subject numbers, or 'all'")
    p.add_argument("--windows", default=",".join(str(int(w)) for w in WINDOWS_S))
    p.add_argument("--out", type=Path,
                   default=Path("results/benchmark/auditory_attention_earsaad__within_session.csv"))
    args = p.parse_args()

    nums = (list(range(1, 16)) if args.subjects == "all"
            else [int(s) for s in args.subjects.split(",")])
    windows = [float(w) for w in args.windows.split(",")]

    rows = []
    for n in nums:
        sub = load_subject(args.root, n)
        for layout, (chans, strategy, fidelity) in LAYOUTS.items():
            accs, dropped = evaluate(sub, chans, windows)
            for w in windows:
                acc = accs[w]
                rows.append({
                    "score": acc,
                    "pipeline": "ridge_reconstruction",
                    "subset": f"{layout}_k{len(chans)}",
                    "strategy": strategy,
                    "k": len(chans),
                    "n_classes": 2,
                    "subject": str(n).zfill(3),
                    "session": "0",
                    "protocol": "within_session",
                    "metric": "accuracy",
                    "trial_seconds": w,
                    "track": TRACK,
                    "dataset_key": DATASET_KEY,
                    "channels": ",".join(chans),
                    "fidelity": fidelity,
                    "accuracy": acc,
                    "n_windows": int(TRIAL_S / w) * 6,
                    "n_dropped": dropped,
                })
            print(f"  sub{n:>2} {layout:16s} " +
                  " ".join(f"{int(w)}s={accs[w]:.3f}" for w in windows), flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.out, index=False)
    print(f"\nwrote {args.out}")

    df = pd.DataFrame(rows)
    print(df.groupby(["subset", "trial_seconds"])["score"]
          .agg(["mean", "sem"]).round(3).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
