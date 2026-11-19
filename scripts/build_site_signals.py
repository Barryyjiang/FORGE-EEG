"""Extract small, real EEG illustrations for the GitHub Pages site.

Each task gets one honest visual: a real trial, a real ERP average, a real
spectrum, a real hypnogram. The arrays are downsampled and written to
``docs/data/signals.json``; the page draws them with its own SVG renderer, so
the figures follow the site's light/dark theme.

This script needs the raw datasets (``data/``). The JSON it produces is
committed, so building the site itself does not require them.

    .\\.venv\\Scripts\\python.exe scripts\\build_site_signals.py
"""

from __future__ import annotations

import json
import warnings
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "data" / "signals.json"


def _round(values, digits: int = 3):
    return [round(float(v), digits) for v in np.asarray(values).ravel()]


def _downsample(values, n: int):
    values = np.asarray(values, dtype=float).ravel()
    if len(values) <= n:
        return values
    idx = np.linspace(0, len(values) - 1, n)
    return np.interp(idx, np.arange(len(values)), values)


def _downsample_bits(values, n: int):
    values = np.asarray(values).ravel()
    if len(values) <= n:
        return values
    idx = np.linspace(0, len(values) - 1, n).astype(int)
    return values[idx]


def _series(name: str, values, t, n: int = 240, role: str = "accent"):
    y = _downsample(values, n)
    x = _downsample(t, n)
    return {
        "name": name,
        "role": role,
        "t": _round(x, 3),
        "values": _round(y, 2),
    }


def _set_mne():
    import mne

    mne.set_log_level("ERROR")


# ---------------------------------------------------------------------------
# Motor imagery: one real left-hand trial, C3 / Cz / C4
# ---------------------------------------------------------------------------

def motor_imagery() -> dict:
    from moabb.datasets import BNCI2014_001
    from moabb.paradigms import LeftRightImagery
    from scipy.signal import welch

    epochs, y, _ = LeftRightImagery().get_data(
        BNCI2014_001(), subjects=[1], return_epochs=True
    )
    picks = ["C3", "Cz", "C4"]
    X = epochs.get_data(picks=picks) * 1e6  # µV
    fs = epochs.info["sfreq"]
    t = epochs.times - epochs.times[0]

    # Pick a left-hand trial with a strong mu rhythm, so the illustration
    # actually shows the signal the decoder is using.
    left = np.where(y == "left_hand")[0]
    scores = []
    for i in left:
        f, p = welch(X[i, 0], fs=fs, nperseg=min(256, X.shape[-1]))
        scores.append(float(p[(f >= 8) & (f <= 13)].sum()))
    pick = int(left[int(np.argsort(scores)[int(0.9 * (len(scores) - 1))])])

    return {
        "type": "trace",
        "title": "One imagined left-hand trial",
        "unit": "µV",
        "xLabel": "time from cue (s)",
        "series": [
            _series(name, X[pick, i], t, n=220,
                    role=("accent" if name == "C4" else
                          "accent2" if name == "C3" else "muted"))
            for i, name in enumerate(picks)
        ],
        "source": "BNCI 2014-001, subject 1, left-hand motor imagery",
        "note": "C3 is over the left motor cortex, C4 over the right. The "
                "epoch is already band-passed 8–32 Hz by the benchmark, which "
                "is why the ~10 Hz mu rhythm is so visible.",
    }


# ---------------------------------------------------------------------------
# P300: target vs standard average at Pz
# ---------------------------------------------------------------------------

def p300() -> dict:
    from moabb.datasets import BNCI2014_008
    from moabb.paradigms import P300

    epochs, y, _ = P300().get_data(
        BNCI2014_008(), subjects=[1], return_epochs=True
    )
    t_ms = epochs.times * 1000.0
    base = (t_ms >= 0) & (t_ms <= 100)

    out = []
    for event, label, role in [("2", "Target", "accent"),
                               ("1", "Standard", "muted")]:
        x = epochs[event].get_data(picks=["Pz"]).mean(axis=0)[0] * 1e6
        x = x - x[base].mean()
        out.append(_series(label, x, t_ms, n=160, role=role))

    return {
        "type": "erp",
        "title": "Target vs standard flashes",
        "unit": "µV",
        "xLabel": "time after flash (ms)",
        "series": out,
        "highlight": [300, 500],
        "source": "BNCI 2014-008, subject 1, averaged at Pz "
                  "(700 target, 3,500 standard flashes)",
        "note": "The target average has a positive deflection around "
                "400 ms — the P300. It is small in a single trial, which is "
                "why the benchmark uses a decoder rather than a peak-picker.",
    }


# ---------------------------------------------------------------------------
# SSVEP: occipital spectrum for one flicker frequency
# ---------------------------------------------------------------------------

def ssvep() -> dict:
    from moabb.datasets import Nakanishi2015
    from moabb.paradigms import SSVEP
    from scipy.signal import welch

    epochs, y, _ = SSVEP().get_data(
        Nakanishi2015(), subjects=[1], return_epochs=True
    )
    target = "13.75"
    X = epochs[y == target].get_data(picks=["Oz"])[:, 0, :]
    fs = epochs.info["sfreq"]
    f, p = welch(X, fs=fs, nperseg=1024, axis=-1)
    p = p.mean(axis=0)
    keep = (f >= 5) & (f <= 45)
    power_db = 10.0 * np.log10(p[keep] * 1e12 + 1e-12)  # dB re 1 µV²/Hz

    return {
        "type": "spectrum",
        "title": "The flicker shows up in the spectrum",
        "unit": "dB (re 1 µV²/Hz)",
        "xLabel": "frequency (Hz)",
        "freq": _round(f[keep], 2),
        "power": _round(power_db, 2),
        "highlightFreqs": [13.75, 27.5],
        "targetFreq": 13.75,
        "source": "Nakanishi 2015, subject 1, 15 trials of the 13.75 Hz "
                  "target, electrode Oz",
        "note": "The peak sits exactly at the flicker frequency; the smaller "
                "peak near 27.5 Hz is its second harmonic. The CCA decoder "
                "looks for this pattern, not at the raw wiggle.",
    }


# ---------------------------------------------------------------------------
# Motor execution: single-channel beta AUC, scalp vs in-ear
# ---------------------------------------------------------------------------

def motor_auc() -> dict:
    path = ROOT / "results" / "channel_diagnostics_beta.csv"
    df = pd.read_csv(path)
    s = (
        df.groupby(["channel", "is_ear"])["auc"]
        .agg(["mean", "std", "count"])
        .reset_index()
    )
    scalp = s[~s["is_ear"]].sort_values("mean", ascending=False).head(4)
    ear = s[s["is_ear"]].sort_values("mean", ascending=False).head(4)
    items = []
    for _, r in pd.concat([scalp, ear]).iterrows():
        items.append({
            "label": r["channel"],
            "value": round(float(r["mean"]), 3),
            "sd": round(float(r["std"]), 3) if pd.notna(r["std"]) else None,
            "group": "ear" if bool(r["is_ear"]) else "scalp",
        })

    return {
        "type": "bars",
        "title": "One electrode, left vs right fist",
        "unit": "ROC-AUC",
        "chance": 0.5,
        "items": items,
        "source": "Wu 2020, 6 subjects, beta band 13–30 Hz, 5-fold CV",
        "note": "The best scalp electrode clears chance; no single ear "
                "electrode does. This is a per-electrode view of the same "
                "site-vs-count question the montage experiment asks.",
    }


# ---------------------------------------------------------------------------
# Sleep: hypnogram + one 30 s N3 window
# ---------------------------------------------------------------------------

def sleep() -> dict:
    import mne

    subject = "001"
    eeg_dir = ROOT / "data" / "openneuro" / f"sub-{subject}" / "ses-001" / "eeg"
    scoring = pd.read_csv(
        eeg_dir / f"sub-{subject}_ses-001_task-sleep_acq-scoring_events.tsv",
        sep="\t",
    )
    stages = scoring["staging"].astype(int).to_numpy()
    hours = scoring["onset"].to_numpy(dtype=float) / 3600.0

    # One 30 s N3 window, for a sense of what the model receives.
    n3 = np.flatnonzero(stages == 5)
    trace = None
    if len(n3):
        start = int(scoring["onset"].iloc[n3[0]])
        raw = mne.io.read_raw_eeglab(
            str(eeg_dir / f"sub-{subject}_ses-001_task-sleep_eeg.set"),
            preload=False,
            verbose=False,
        )
        seg = raw.copy().crop(start, start + 30.0).load_data()
        picks = [c for c in ("C3", "ELB") if c in seg.ch_names]
        data = seg.get_data(picks=picks) * 1e6
        t = np.arange(data.shape[1]) / seg.info["sfreq"]
        trace = {
            "unit": "µV",
            "xLabel": "time in 30 s window (s)",
            "series": [
                _series(name, data[i], t, n=180,
                        role=("accent" if name == "C3" else "violet"))
                for i, name in enumerate(picks)
            ],
        }

    return {
        "type": "hypnogram",
        "title": "One night, scored every 30 seconds",
        "xLabel": "hours after lights out",
        "hours": _round(hours, 2),
        "stages": [int(v) for v in stages],
        "stageLabels": {
            1: "Wake",
            2: "REM",
            3: "N1",
            4: "N2",
            5: "N3",
        },
        "trace": trace,
        "source": "OpenNeuro ds004348, subject 001, manual scoring",
        "note": "The model sees one 30-second window at a time. The visual is "
                "the sequence it is trying to recover. Stage codes come from "
                "the dataset's own events.json.",
    }


# ---------------------------------------------------------------------------
# Cognitive workload: rest vs multitasking spectrum at one frontal electrode
# ---------------------------------------------------------------------------

def stew() -> dict:
    import io
    import zipfile

    from scipy.signal import butter, sosfiltfilt, welch

    path = ROOT / "data" / "stew_raw" / "STEW Dataset.zip"
    sos = butter(4, [1.0, 30.0], btype="bandpass", fs=128, output="sos")
    with zipfile.ZipFile(path) as z:
        names = {n.rsplit("/", 1)[-1]: n for n in z.namelist()}
        traces = []
        for cond in ("lo", "hi"):
            raw = np.loadtxt(io.BytesIO(z.read(names[f"sub01_{cond}.txt"])))
            # Column 0 is AF3, the electrode the glasses-like montage keeps.
            traces.append(sosfiltfilt(sos, raw, axis=0)[:, 0])

    f, p = welch(np.stack(traces), fs=128, nperseg=1024, axis=1)
    keep = (f >= 1.0) & (f <= 30.0)
    db = 10.0 * np.log10(p[:, keep] * 1e12 + 1e-12)
    return {
        "type": "spectrum",
        "title": "Rest vs multitasking, one electrode",
        "unit": "dB (re 1 ÂµVÂ²/Hz)",
        "xLabel": "frequency (Hz)",
        "series": [
            _series("Rest", db[0], f[keep], n=int(keep.sum()), role="muted"),
            _series("Multitask", db[1], f[keep], n=int(keep.sum()),
                    role="accent"),
        ],
        "highlightFreqs": [10.0],
        "source": "STEW, subject 01, electrode AF3, whole 150 s recordings",
        "note": "The multitasking recording carries more power above ~13 Hz "
                "(muscle and movement) and a weaker alpha peak. The decoder "
                "reads band power, so these differences are its input â€” and "
                "they are also why rest-vs-task is easier than it looks.",
    }


# ---------------------------------------------------------------------------
# Auditory attention: 60 s accuracy per setup, from the results table
# ---------------------------------------------------------------------------

def earsaad() -> dict:
    path = (ROOT / "results" / "benchmark"
            / "auditory_attention_earsaad__within_session.csv")
    df = pd.read_csv(path)
    df = df[df["trial_seconds"] == 60.0]
    order = [
        ("scalp_29_k29", "Scalp 29", "scalp"),
        ("scalp_19_k19", "Scalp 19", "scalp"),
        ("scalp_12_k12", "Scalp 12", "scalp"),
        ("around_ear_19_k19", "Around-ear 19", "ear"),
        ("in_ear_12_k12", "In-ear 12", "ear"),
    ]
    items = []
    for key, label, group in order:
        g = df[df["subset"] == key]["score"]
        items.append({
            "label": label,
            "value": round(float(g.mean()), 3),
            "sd": round(float(g.std()), 3),
            "group": group,
        })

    return {
        "type": "bars",
        "title": "Decoding a followed voice, 60 s windows",
        "unit": "Accuracy",
        "chance": 0.5,
        "items": items,
        "source": "Ear-SAAD, 15 subjects, leave-one-trial-out, 60 s decisions",
        "note": "Grey bars are scalp references trimmed to the same channel "
                "count as the ear arrays, so the scalp-vs-ear gap is not a "
                "channel-count gap. Whiskers are Â±1 s.d. across subjects.",
    }


# ---------------------------------------------------------------------------
# Emotion: 60 s accuracy per setup, from the results table
# ---------------------------------------------------------------------------

def faced() -> dict:
    path = (ROOT / "results" / "benchmark"
            / "faced_emotion_123__within_session.csv")
    df = pd.read_csv(path)
    cohort = (df.drop_duplicates("subset").set_index("subset")["cohort_score"])
    order = [
        ("full_k30", "Full 30", "scalp"),
        ("posterior_4_k4", "Posterior 4", "scalp"),
        ("glasses_4_k4", "Glasses-like 4", "proxy"),
        ("temporal_4_k4", "Temporal 4", "proxy"),
    ]
    items = []
    for key, label, group in order:
        items.append({
            "label": label,
            "value": round(float(cohort[key]), 3),
            "sd": None,
            "group": group,
        })
    return {
        "type": "bars",
        "title": "Positive vs negative valence, by placement",
        "unit": "Balanced accuracy",
        "chance": 0.5,
        "items": items,
        "source": "FACED, 123 participants, participant-disjoint CV, 4 s windows",
        "note": "Every bar is close to chance, and that is the finding: the effect "
                "is real but small. The best four electrodes are posterior, not "
                "the frontal sites a glasses frame would use.",
    }


SIGNALS = {
    "mi": motor_imagery,
    "p300": p300,
    "ssvep": ssvep,
    "motor_auc": motor_auc,
    "sleep": sleep,
    "stew": stew,
    "earsaad": earsaad,
    "faced": faced,
}


def main() -> int:
    _set_mne()
    payload = {
        "generated": date.today().isoformat(),
        "signals": {},
        "errors": {},
    }
    for key, fn in SIGNALS.items():
        print(f"building {key} ...", flush=True)
        try:
            payload["signals"][key] = fn()
            print(f"  ok: {payload['signals'][key].get('title')}")
        except Exception as exc:  # noqa: BLE001 - the site degrades gracefully
            payload["errors"][key] = f"{type(exc).__name__}: {exc}"
            print(f"  FAILED: {type(exc).__name__}: {exc}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(payload, indent=1, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")
    return 0 if not payload["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
