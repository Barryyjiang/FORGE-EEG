"""Extract per-participant PSD features from the FACED BIDS release.

FACED (``nm000112``) is 123 participants watching emotion-eliciting videos while
30 scalp electrodes are recorded. The BIDS release is continuous EEG plus an
``events.tsv`` per participant, so the features have to be cut from video onsets
rather than read from pre-epoched files.

This step is separate from :mod:`faced_emotion_track` because the BIDS download
is large and the extraction is slow: it runs once, caches one ``.npz`` per
participant under ``data/faced/participant_features/``, and the track then runs
in a couple of minutes from the cache.

The pipeline follows the team's own FACED notebook, which is the reference
implementation for this track:

* map legacy ``T3/T4/T5/T6`` to ``T7/T8/P7/P8`` (same physical electrodes)
* 4th-order zero-phase 1-30 Hz band-pass, resample to 250 Hz
* non-overlapping 4 s windows inside each video
* Welch PSD (``nperseg=500``) -> log power in theta/alpha/beta/broadband plus
  log(theta/alpha), five features per electrode

The two mastoid channels in the recording are excluded: they are references, and
a reference sitting next to the ear would turn a scalp-vs-wearable comparison
into an ear-vs-ear one.

    .\\.venv\\Scripts\\python.exe scripts\\faced_extract_features.py
"""

from __future__ import annotations

import argparse
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

#: Feature axis order. ``X[:, i, :]`` is this electrode.
CHANNELS = ["FP1", "FP2", "FZ", "F3", "F4", "F7", "F8", "FC1", "FC2", "FC5",
            "FC6", "CZ", "C3", "C4", "T7", "T8", "CP1", "CP2", "CP5", "CP6",
            "PZ", "P3", "P4", "P7", "P8", "PO3", "PO4", "OZ", "O1", "O2"]
LEGACY = {"T3": "T7", "T4": "T8", "T5": "P7", "T6": "P8"}
BANDS = {"theta": (4, 8), "alpha": (8, 13), "beta": (13, 30),
         "broadband": (1, 30)}
FS = 250
WINDOW_SECONDS = 4
EPS = 1e-12


def scalp_lookup(raw) -> dict[str, str]:
    out = {}
    for actual in raw.ch_names:
        key = LEGACY.get(actual.strip().upper(), actual.strip().upper())
        if key in out:
            raise ValueError(f"duplicate mapped channel: {key}")
        out[key] = actual
    return out


def features_for_window(window: np.ndarray) -> np.ndarray:
    from scipy.signal import welch

    freq, pxx = welch(window, fs=FS, nperseg=min(500, window.shape[-1]), axis=-1)
    powers = []
    for lo, hi in BANDS.values():
        mask = (freq >= lo) & (freq < hi)
        powers.append(np.trapezoid(pxx[:, mask], freq[mask], axis=1))
    powers = np.stack(powers, axis=-1)
    log_power = np.log10(np.maximum(powers, EPS))
    log_theta_alpha = np.log10(np.maximum(powers[:, 0], EPS)
                               / np.maximum(powers[:, 1], EPS))
    return np.column_stack([log_power, log_theta_alpha]).astype("float32")


def get_events(path: Path) -> pd.DataFrame:
    """Video onsets that carry a binary valence label."""
    e = pd.read_csv(path, sep="\t")
    required = {"onset", "duration", "emotion_label", "binary_label",
                "video_index"}
    missing = required - set(e.columns)
    if missing:
        raise ValueError(f"{path.name}: missing {sorted(missing)}")
    for c in ("onset", "duration", "video_index"):
        e[c] = pd.to_numeric(e[c], errors="coerce")
    e["binary_clean"] = e["binary_label"].astype(str).str.lower().str.strip()
    e = e[e["onset"].notna() & (e["duration"] > WINDOW_SECONDS)]
    e = e[e["video_index"].between(1, 28)]
    e = e[e["binary_clean"].isin(["positive", "negative"])].copy()
    e["label"] = (e["binary_clean"] == "positive").astype(int)
    return e.sort_values("onset").drop_duplicates(["video_index", "onset"])


def extract_subject(sid: str, bdf: Path, tsv: Path):
    import mne
    from scipy.signal import butter, resample_poly, sosfiltfilt

    events = get_events(tsv)
    raw = mne.io.read_raw_bdf(str(bdf), preload=False, verbose="ERROR")
    try:
        fs_in = float(raw.info["sfreq"])
        lookup = scalp_lookup(raw)
        absent = [c for c in CHANNELS if c not in lookup]
        if absent:
            raise ValueError(f"{sid}: missing channels {absent}")
        picks = mne.pick_channels(raw.ch_names,
                                  [lookup[c] for c in CHANNELS], ordered=True)
        sos = butter(4, [1, 30], btype="bandpass", fs=fs_in, output="sos")
        frac = Fraction(FS / fs_in).limit_denominator(10000)
        window_len = int(FS * WINDOW_SECONDS)
        xs, recs = [], []
        for _, e in events.iterrows():
            start = max(0, int(round(float(e.onset) * fs_in)))
            stop = min(raw.n_times,
                       int(round((float(e.onset) + float(e.duration)) * fs_in)))
            if stop - start < int(WINDOW_SECONDS * fs_in):
                continue
            signal = raw.get_data(picks=picks, start=start, stop=stop)
            if not np.isfinite(signal).all():
                continue
            signal = sosfiltfilt(sos, signal, axis=-1)
            if frac.numerator != frac.denominator:
                signal = resample_poly(signal, frac.numerator, frac.denominator,
                                       axis=-1)
            for wi in range(signal.shape[-1] // window_len):
                seg = signal[:, wi * window_len:(wi + 1) * window_len]
                xs.append(features_for_window(seg))
                recs.append((sid, f"{sid}_{int(e.video_index)}",
                             int(e.video_index), int(e.label), wi))
    finally:
        raw.close()
    if not recs:
        raise RuntimeError(f"{sid}: no positive/negative video windows")
    return (np.stack(xs).astype("float32"),
            pd.DataFrame(recs, columns=["subject", "trial_key", "trial",
                                        "label", "window"]))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--bids", type=Path, default=Path("data/faced/nm000112_v1.1.4"))
    p.add_argument("--out", type=Path,
                   default=Path("data/faced/participant_features"))
    p.add_argument("--subjects", type=int, default=None,
                   help="limit for a smoke test; default is all 123")
    args = p.parse_args()

    if not args.bids.exists():
        print(f"FACED BIDS release not found at {args.bids}.")
        print("Download nm000112 v1.1.4 from NEMAR/OpenNeuro and unpack it there.")
        return 1

    pairs = {}
    for bdf in sorted(args.bids.glob("sub-*/eeg/*_eeg.bdf")):
        tsv = list(bdf.parent.glob("*_events.tsv"))
        if len(tsv) == 1:
            pairs[bdf.parent.parent.name] = (bdf, tsv[0])
    if args.subjects:
        pairs = dict(list(pairs.items())[: args.subjects])
    print(f"participants found: {len(pairs)}")

    args.out.mkdir(parents=True, exist_ok=True)
    done = skipped = 0
    for sid, (bdf, tsv) in pairs.items():
        dest = args.out / f"{sid}_{FS}hz_{WINDOW_SECONDS}s.npz"
        if dest.exists() and dest.stat().st_size > 0:
            skipped += 1
            continue
        X, meta = extract_subject(sid, bdf, tsv)
        # Fixed-width strings, not object arrays, so the cache loads with
        # allow_pickle=False.
        np.savez_compressed(
            dest, X=X,
            subject=meta["subject"].to_numpy(dtype="U16"),
            trial_key=meta["trial_key"].to_numpy(dtype="U32"),
            trial=meta["trial"].to_numpy(dtype=np.int64),
            label=meta["label"].to_numpy(dtype=np.int64),
            window=meta["window"].to_numpy(dtype=np.int64),
        )
        done += 1
        print(f"  {sid}: {X.shape[0]} windows", flush=True)

    print(f"extracted={done} skipped={skipped} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
