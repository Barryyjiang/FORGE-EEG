"""Build the static GitHub Pages data bundle from benchmark outputs.

The site is deliberately data-driven: every number shown on the page is read
from ``results/benchmark/*.csv`` and written to ``docs/data/benchmark.json``.
No result is transcribed into HTML by hand.

    .\\.venv\\Scripts\\python.exe scripts\\build_site.py

Optional real-data illustrations (EEG traces, ERP, spectrum, hypnogram) are
generated separately by ``scripts/build_site_signals.py``. They are committed
to ``docs/data/signals.json`` so the page also works without the raw datasets.
"""

from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "benchmark"
DOCS = ROOT / "docs"
OUT = DOCS / "data"


# ---------------------------------------------------------------------------
# Editorial content. Numbers are filled in from the results below; the prose is
# the part that makes the benchmark legible to people outside EEG.
# ---------------------------------------------------------------------------

TASKS = [
    {
        "id": "mi_leftright_22ch",
        "order": 1,
        "name": "Imagine moving a hand",
        "short": "Motor imagery",
        "kicker": "Motor imagery",
        "paradigm": "Motor imagery",
        "dataset": "BNCI2014_001",
        "datasetName": "BNCI 2014-001",
        "subjects": "9 people × 2 sessions",
        "nLabel": "18 subject-sessions",
        "channels": "22 EEG",
        "sfreq": "250 Hz",
        "examples": 2592,
        "metric": "roc_auc",
        "metricLabel": "ROC-AUC",
        "chance": 0.5,
        "defaultPipeline": "riemann_tslr",
        "defaultProtocol": "within_session",
        "pipelines": ["riemann_tslr", "csp_lda", "logvar_lda"],
        "protocols": ["within_session", "cross_session"],
        "person": "A cue appears. Without moving, the participant imagines "
                  "opening and closing the left or right hand for four seconds.",
        "computer": "The decoder looks for a drop in the 8–13 Hz mu rhythm "
                    "over the motor cortex, on the side opposite the imagined "
                    "hand.",
        "why": "The classic brain–computer interface task, and the cleanest "
               "test of placement: the signal is focal, so a small "
               "sensorimotor patch should beat electrodes spread evenly over "
               "the head.",
        "headline": "Eight electrodes over the motor cortex keep about 91% of "
                    "full-cap accuracy.",
        "signalKey": "mi",
        "signalTitle": "One imagined left-hand trial",
        "signalCaption": "C3 and C4 sit over the left and right motor cortex. "
                         "The ~10 Hz wiggle is the mu rhythm the decoder uses; "
                         "it drops over the hand being imagined.",
        "illustration": "mi",
        "accent": "teal",
    },
    {
        "id": "p300_8ch",
        "order": 2,
        "name": "Spot the target",
        "short": "P300 speller",
        "kicker": "Evoked response",
        "paradigm": "P300",
        "dataset": "BNCI2014_008",
        "datasetName": "BNCI 2014-008",
        "subjects": "8 people",
        "nLabel": "8 subjects",
        "channels": "8 EEG",
        "sfreq": "256 Hz",
        "examples": 33600,
        "metric": "roc_auc",
        "metricLabel": "ROC-AUC",
        "chance": 0.5,
        "defaultPipeline": "xdawn_tslr",
        "defaultProtocol": "within_session",
        "pipelines": ["xdawn_tslr", "logvar_lda"],
        "protocols": ["within_session"],
        "person": "Letters or icons flash one at a time. The participant "
                  "silently counts the flashes that contain the target.",
        "computer": "A rare target flash produces a positive voltage bump "
                    "about 300–500 ms later — the P300 — which xDAWN + "
                    "Riemannian decoding picks up.",
        "why": "P300 is a slow, widespread response, so this is the case where "
               "a headband-sized montage has a real chance. The cap is already "
               "only eight electrodes.",
        "headline": "Half the electrodes still keep about 95% of P300 "
                    "performance.",
        "signalKey": "p300",
        "signalTitle": "Target vs standard flashes",
        "signalCaption": "Averaged at Pz. The target (teal) has a clear "
                         "positive bump around 400 ms; standard flashes "
                         "(gray) do not.",
        "illustration": "p300",
        "accent": "amber",
    },
    {
        "id": "ssvep_8ch",
        "order": 3,
        "name": "Stare at a flicker",
        "short": "SSVEP",
        "kicker": "Steady-state visual evoked potential",
        "paradigm": "SSVEP",
        "dataset": "nakanishi2015",
        "datasetName": "Nakanishi 2015",
        "subjects": "10 people",
        "nLabel": "10 subjects",
        "channels": "8 occipital",
        "sfreq": "256 Hz",
        "examples": 1800,
        "metric": "accuracy",
        "metricLabel": "Accuracy",
        "chance": 1.0 / 12.0,
        "nClasses": 12,
        "trialSeconds": 4.0,
        "defaultPipeline": "ssvep_cca",
        "defaultProtocol": "within_session",
        "pipelines": ["ssvep_cca"],
        "protocols": ["within_session"],
        "person": "The participant looks at one of twelve targets. Each target "
                  "flickers at a different fixed frequency.",
        "computer": "The visual cortex echoes the flicker. A CCA decoder reads "
                    "the frequency from the occipital EEG and reports which "
                    "target was chosen.",
        "why": "SSVEP is fast and accuracy-scored, so it can be summarized as "
               "information transfer rate (bits/min) — the metric that decides "
               "whether a wearable BCI is actually usable.",
        "headline": "Four occipital electrodes keep 98% of full-cap accuracy "
                    "and 43 of 44.5 bits/min.",
        "signalKey": "ssvep",
        "signalTitle": "The flicker shows up in the spectrum",
        "signalCaption": "Occipital EEG while one target flickers at "
                         "13.75 Hz. The peak at the flicker frequency and its "
                         "harmonic is the signature the decoder reads.",
        "illustration": "ssvep",
        "accent": "violet",
    },
    {
        "id": "motor_execution_ear_vs_scalp",
        "order": 4,
        "name": "Clench a fist",
        "short": "Motor execution",
        "kicker": "Motor execution",
        "paradigm": "Motor execution",
        "dataset": "wu2020",
        "datasetName": "Wu 2020",
        "subjects": "6 people",
        "nLabel": "6 subjects",
        "channels": "115 of 122 scalp + 8 in-ear",
        "sfreq": "1000 Hz",
        "examples": 1114,
        "metric": "roc_auc",
        "metricLabel": "ROC-AUC",
        "chance": 0.5,
        "defaultPipeline": "riemann_tslr",
        "defaultProtocol": "within_session",
        "pipelines": ["riemann_tslr", "csp_lda", "logvar_lda"],
        "protocols": ["within_session"],
        "person": "On cue, the participant clenches the left or right fist. "
                  "EEG is recorded at the same time from a dense scalp cap and "
                  "eight in-ear electrodes.",
        "computer": "The decoder tries to tell left from right. On the scalp, "
                    "motor cortex carries the signal; in the ear, the same "
                    "movement is much harder to read.",
        "why": "The only dataset here where the same person, in the same "
               "session, has both a dense cap and a wearable. It separates "
               "electrode site from channel count.",
        "headline": "At the same eight channels, scalp scores 0.739 and "
                    "in-ear scores 0.464.",
        "signalKey": "motor_auc",
        "signalTitle": "One electrode, left vs right fist",
        "signalCaption": "Single-channel beta-band AUC, averaged over "
                         "subjects. On this averaged view the best scalp "
                         "electrode is above chance and the best ear electrode "
                         "is not; individual ear channels do cross chance in "
                         "some subjects, so the montage-level comparison at "
                         "matched channel count is the reported result.",
        "illustration": "motor",
        "accent": "coral",
    },
    {
        "id": "sleep_staging_local",
        "order": 5,
        "name": "Score a night’s sleep",
        "short": "Sleep staging",
        "kicker": "Continuous task",
        "paradigm": "Sleep staging",
        "dataset": "openneuro_ds004348",
        "datasetName": "OpenNeuro ds004348",
        "subjects": "9 nights",
        "nLabel": "9 nights",
        "channels": "6 scalp + 14 ear",
        "sfreq": "200 Hz",
        "examples": 7410,
        "metric": "kappa",
        "metricLabel": "Cohen’s κ",
        "chance": 0.0,
        "defaultPipeline": "bandpower_lda",
        "defaultProtocol": "within_session",
        "pipelines": ["bandpower_lda"],
        "protocols": ["within_session"],
        "person": "The participant sleeps at home wearing scalp and ear "
                  "electrodes. Each 30-second window is scored as Wake, REM, "
                  "N1, N2 or N3.",
        "computer": "A simple band-power + LDA model predicts the stage from "
                    "each window. Scoring uses Cohen’s κ, where zero is "
                    "chance.",
        "why": "Sleep is the wearable-native continuous task. Unlike a focal "
               "motor rhythm, slow sleep waves are broad, so the ear has a "
               "better chance.",
        "headline": "The ear is close, not equal: −0.056 κ at matched six "
                    "channels.",
        "signalKey": "sleep",
        "signalTitle": "One night, scored every 30 seconds",
        "signalCaption": "Hypnogram from subject 001. The model sees only "
                         "30-second windows; the benchmark asks how well it "
                         "recovers this sequence from scalp vs ear electrodes.",
        "illustration": "sleep",
        "accent": "indigo",
        "noFullCap": True,
        "referenceLabel": "Scalp 6 ch",
    },
    {
        "id": "stew_workload_14ch",
        "order": 6,
        "name": "Sit still, then multitask",
        "short": "Cognitive workload",
        "kicker": "Cognitive workload",
        "paradigm": "Cognitive workload",
        "dataset": "stew",
        "datasetName": "STEW (Lim 2018)",
        "subjects": "48 people",
        "nLabel": "48 subjects",
        "channels": "14 (Emotiv EPOC)",
        "sfreq": "128 Hz",
        "examples": 3552,
        "metric": "roc_auc",
        "metricLabel": "ROC-AUC",
        "chance": 0.5,
        "defaultPipeline": "psd_lda",
        # The honest protocol is the one where the decoder never sees the test
        # person. The within-person calibration number is kept as a second
        # protocol because it is what the STEW literature reports.
        "defaultProtocol": "cross_subject",
        "pipelines": ["psd_lda"],
        "protocols": ["within_session", "cross_subject"],
        "referenceLabel": "Full 14 ch",
        "person": "The participant sits quietly for two and a half minutes, "
                  "then works through the SIMKAP multitasking test for two and "
                  "a half minutes, wearing a 14-channel Emotiv EPOC.",
        "computer": "Band power in four bands per 4-second window, classified "
                    "by shrinkage LDA. The decoder has to tell a resting "
                    "recording from a multitasking one.",
        "why": "The largest cohort here (48 people) and the only headset rather "
               "than cap, so it is the one place where a frontal "
               "\u201cglasses-like\u201d four-electrode subset can be measured "
               "against a full montage. Its four-electrode sets are scalp "
               "proxies, labelled as such, not measured glasses hardware.",
        "headline": "Four frontal electrodes keep 97% of the 14-channel score.",
        "signalKey": "stew",
        "signalTitle": "Rest vs multitasking, one electrode",
        "signalCaption": "AF3 from subject 01: the resting recording, then the "
                         "first ten seconds of the SIMKAP task. The task "
                         "recording carries more high-frequency muscle activity "
                         "and a weaker alpha rhythm \u2014 part of what the "
                         "decoder is reading.",
        "illustration": "stew",
        "accent": "accent2",
    },
    {
        "id": "auditory_attention_earsaad",
        "order": 7,
        "name": "Follow one voice",
        "short": "Auditory attention",
        "kicker": "Auditory attention",
        "paradigm": "Auditory attention decoding",
        "dataset": "earsaad",
        "datasetName": "Ear-SAAD (Geirnaert 2025)",
        "subjects": "15 people",
        "nLabel": "15 subjects",
        "channels": "29 scalp + 19 around-ear + 12 in-ear",
        "sfreq": "20 Hz",
        "examples": 90,
        "metric": "accuracy",
        "metricLabel": "Accuracy",
        "chance": 0.5,
        "defaultPipeline": "ridge_reconstruction",
        "defaultProtocol": "within_session",
        "pipelines": ["ridge_reconstruction"],
        "protocols": ["within_session"],
        # Matched-k is the benchmark rule, so the headline compares the 12 in-ear
        # electrodes against the 12 most spread scalp electrodes. The as-built
        # 29/19/12 comparison is reported too, because that is the paper's.
        "referenceSubset": "scalp_12_k12",
        "headlineSubset": "in_ear_12_k12",
        "referenceLabel": "Scalp 12 ch",
        # The decision window every headline number for this task is taken at.
        "headlineWindowS": 60.0,
        "person": "Two talkers speak at once. The participant attends to one of "
                  "them while scalp, around-ear and in-ear EEG are recorded at "
                  "the same time.",
        "computer": "A ridge decoder reconstructs the attended speech envelope "
                    "from EEG, and the talker whose envelope correlates more "
                    "with the reconstruction wins. Decisions are made on 60 s "
                    "windows, the paper's headline length.",
        "why": "The only public dataset that records all three systems "
               "simultaneously, so it is a direct test of the ear site for this "
               "paradigm rather than a geometric proxy. It is also the task "
               "where the ear costs the most.",
        "headline": "At twelve electrodes each, the in-ear set keeps 78% of the "
                    "matched scalp score.",
        "signalKey": "earsaad",
        "signalTitle": "Envelope tracking, scalp vs in-ear",
        "signalCaption": "Correlation between the reconstructed and the true "
                         "attended envelope, per subject, for the scalp cap and "
                         "the in-ear set. The scalp decoder tracks the speech "
                         "envelope; the in-ear decoder tracks it less.",
        "illustration": "earsaad",
        "accent": "slate",
    },
    {
        "id": "mi_4class_22ch",
        "order": 8,
        "name": "Imagine a hand, a foot or a tongue",
        "short": "Motor imagery, 4 classes",
        "kicker": "Motor imagery",
        "paradigm": "Motor imagery (4-class)",
        "dataset": "BNCI2014_001",
        "datasetName": "BNCI 2014-001",
        "subjects": "9 people \u00d7 2 sessions",
        "nLabel": "18 subject-sessions",
        "channels": "22 EEG",
        "sfreq": "250 Hz",
        # 288 trials per session x 18 sessions: the four-class task uses all of
        # them, where the two-class task keeps only the left/right halves.
        "examples": 5184,
        "metric": "accuracy",
        "metricLabel": "Accuracy",
        "chance": 0.25,
        "nClasses": 4,
        "trialSeconds": 4.0,
        "defaultPipeline": "riemann_tslr",
        "defaultProtocol": "within_session",
        "pipelines": ["riemann_tslr", "csp_lda", "logvar_lda"],
        "protocols": ["within_session"],
        "person": "The same nine people and the same cap as the two-class task, "
                  "but four cues: left hand, right hand, both feet, tongue.",
        "computer": "Same decoder, same montages, four classes instead of two. "
                    "Feet and tongue are represented near the midline, so a "
                    "lateralised sensorimotor patch has less to work with.",
        "why": "Class count is an axis the rest of the benchmark holds fixed. "
               "If the cost of a small montage grows when you ask it to "
               "distinguish more things, then 'eight electrodes are enough' is "
               "only true for the two-class version of a task.",
        "headline": "The same eight sensorimotor electrodes keep 91% of a "
                    "two-class score but only 85% of a four-class one.",
        "signalKey": "mi",
        "signalTitle": "One imagined left-hand trial",
        "signalCaption": "C3 and C4 sit over the left and right motor cortex. The "
                         "~10 Hz wiggle is the mu rhythm the decoder uses; it "
                         "drops over the hand being imagined. The four-class task "
                         "adds feet and tongue, which are not lateralised.",
        "illustration": "mi",
        "accent": "accent",
    },
    {
        "id": "faced_emotion_123",
        "order": 9,
        "name": "Watch a video, read the mood",
        "short": "Emotion recognition",
        "kicker": "Affect",
        "paradigm": "Emotion recognition",
        "dataset": "faced",
        "datasetName": "FACED (Chen 2022)",
        "subjects": "123 people",
        "nLabel": "123 subjects",
        "channels": "30 EEG",
        "sfreq": "250 Hz",
        "examples": 2952,
        "metric": "balanced_accuracy",
        "metricLabel": "Balanced accuracy",
        "chance": 0.5,
        "defaultPipeline": "psd_lda",
        "defaultProtocol": "within_session",
        "pipelines": ["psd_lda"],
        "protocols": ["within_session"],
        # The headline is the best four-electrode placement, not the best of the
        # whole nested path: 24 channels score above 30 by noise, and quoting
        # that as "retained 100%" would be misleading.
        "referenceSubset": "full_k30",
        "headlineSubset": "posterior_4_k4",
        "referenceLabel": "Full 30 ch",
        "person": "The participant watches short videos chosen to elicit a "
                  "particular emotion, while 30 scalp electrodes record.",
        "computer": "Band power in four bands per 4-second window, classified "
                    "as positive or negative valence. A video gets one "
                    "prediction, averaged over its windows.",
        "why": "The largest cohort here by a wide margin (123 people) and the "
               "only affect task. It is also the one where the wearable "
               "question is asked of a frontal site, and where the answer is "
               "uncomfortably small: the effect is only about six points above "
               "chance to begin with.",
        "headline": "Four posterior electrodes keep 98% of a 30-channel score "
                    "that is itself only six points above chance.",
        "signalKey": "faced",
        "signalTitle": "One video, positive vs negative",
        "signalCaption": "Band power at four electrodes, averaged over "
                         "participants, for the two valence classes. The "
                         "separation is small and it is not where a glasses "
                         "frame would put its electrodes.",
        "illustration": "faced",
        "accent": "violet",
    },
]

PIPELINE_LABELS = {
    "riemann_tslr": "Riemannian TSLR",
    "csp_lda": "CSP + LDA",
    "logvar_lda": "Log-variance + LDA",
    "xdawn_tslr": "xDAWN + Riemannian",
    "ssvep_cca": "CCA (SSVEP)",
    "bandpower_lda": "Band-power + LDA",
    "psd_lda": "PSD + LDA",
    "ridge_reconstruction": "Ridge reconstruction",
}

#: Per-track montage names. The generic rules below cannot name these: a
#: four-electrode subset of an Emotiv is not a "full cap", and "in_ear_12_k12"
#: title-cases into nonsense.
SUBSET_LABELS = {
    "stew_workload_14ch": {
        "full_14_k14": "Full 14 ch",
        "glasses_4_k4": "Glasses-like 4 ch",
        "posterior_4_k4": "Posterior 4 ch",
        "forehead_2_k2": "Forehead 2 ch",
    },
    "auditory_attention_earsaad": {
        "scalp_29_k29": "Scalp 29 ch",
        "scalp_19_k19": "Scalp 19 ch (spread)",
        "scalp_12_k12": "Scalp 12 ch (spread)",
        "around_ear_19_k19": "Around-ear 19 ch",
        "in_ear_12_k12": "In-ear 12 ch",
    },
    "faced_emotion_123": {
        "full_k30": "Full 30 ch",
        "glasses_4_k4": "Glasses-like 4 ch",
        "temporal_4_k4": "Temporal 4 ch",
        "posterior_4_k4": "Posterior 4 ch",
    },
}

PROTOCOL_LABELS = {
    "within_session": "Same session",
    "cross_session": "New session",
    "cross_subject": "New person",
}

REGION_LABELS = {
    "occipital": "Occipital",
    "parietal": "Parietal",
    "sensorimotor": "Sensorimotor",
    "frontal": "Frontal",
    "temporal": "Temporal",
}

WEARABLE_LABELS = {
    "wu2020_inear": "In-ear (Wu 2020)",
}

#: The decision window the site quotes for tasks that are scored at several.
#: Imported so the site, the leaderboard and the report cannot disagree.
from eegbench.leaderboard import HEADLINE_WINDOW_S  # noqa: E402

# Schematic ear positions live in eegbench.montages, so the farthest-point
# subsetting and the head maps draw from one table instead of two.
from eegbench.montages import EAR_POSITIONS  # noqa: E402


def _json_default(value):
    if isinstance(value, (pd.Timestamp, date)):
        return value.isoformat()
    if pd.isna(value):
        return None
    raise TypeError(f"not JSON serialisable: {type(value)!r}")


def _clean_float(value, digits: int = 4):
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value):
        return None
    return round(value, digits)


def _parse_channels(value) -> list[str]:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return []
    return [c.strip() for c in str(value).split(",") if c.strip()]


def _subset_label(track: str, subset: str, strategy: str) -> str:
    subset = str(subset)
    if track in SUBSET_LABELS and subset in SUBSET_LABELS[track]:
        return SUBSET_LABELS[track][subset]
    if track == "sleep_staging_local":
        return {
            "scalp_6_k6": "Scalp 6 ch",
            "ear_6_k6": "Ear 6 ch",
            "ear_14_k14": "Ear all 14 ch",
        }.get(subset, subset.replace("_", " "))
    if strategy == "full" or subset.startswith("full"):
        return "Full cap"
    if subset.startswith("nested_k"):
        # A hand-fixed reduction path, not a geometric spread.
        return f"Nested {subset.split('_k', 1)[1]} ch"
    if subset.startswith("region-"):
        region = subset.split("_", 1)[0].replace("region-", "")
        return f"{REGION_LABELS.get(region, region.title())} region"
    if subset.startswith("distributed"):
        return "Max-spread subset"
    if subset.startswith("random-"):
        return "Random subset"
    for key, label in WEARABLE_LABELS.items():
        if subset.startswith(key):
            return label
    return subset.replace("_", " ").title()


def _strategy_label(strategy: str) -> str:
    return {
        "full": "Full cap",
        "region": "Region",
        "distributed": "Max spread",
        "nested": "Nested path",
        "random": "Random",
        "wearable": "Wearable",
    }.get(strategy, str(strategy).title())


def _load_results() -> pd.DataFrame:
    files = sorted(RESULTS.glob("*.csv"))
    frames = []
    for path in files:
        if path.stem.endswith("_summary"):
            continue
        df = pd.read_csv(path)
        track, _, protocol_from_name = path.stem.partition("__")
        df["track"] = track
        if "protocol" not in df.columns or df["protocol"].isna().all():
            df["protocol"] = protocol_from_name or "within_session"
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"no result CSVs in {RESULTS}")
    raw = pd.concat(frames, ignore_index=True)

    # A task scored at several decision windows has one row per subject per
    # window. The site's tables show one number per cell, so they use the task's
    # headline window; the full curve stays in the CSV and in REPORT.md.
    for track, seconds in HEADLINE_WINDOW_S.items():
        if "trial_seconds" in raw.columns:
            drop = (raw["track"] == track) & (raw["trial_seconds"] != seconds)
            raw = raw[~drop]
    return raw


def _summary(raw: pd.DataFrame) -> pd.DataFrame:
    """Same aggregation as eegbench.leaderboard, with task-aware chance.

    ``leaderboard.add_chance`` cannot infer a metric for the older MI/P300/
    motor rows because those files predate the ``metric`` column. The site is
    public-facing, so a wrong chance line is not acceptable: infer it from the
    task definition instead.
    """
    group = ["track", "protocol", "pipeline", "subset", "strategy", "k"]
    agg = (
        raw.groupby(group, dropna=False)["score"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .rename(columns={"mean": "score", "std": "sd", "count": "n"})
    )
    agg["sem"] = agg["sd"] / agg["n"].pow(0.5)

    # Chance and metric are task properties, not per-row guesses.
    by_track = {t["id"]: t for t in TASKS}
    agg["metric"] = agg["track"].map(lambda t: by_track[t]["metric"])
    agg["chance"] = agg["track"].map(lambda t: by_track[t]["chance"])

    # Preserve a few fields that are constant per cell.
    carry = [c for c in ("fidelity", "channels") if c in raw.columns]
    if carry:
        meta = (
            raw.groupby(["track", "protocol", "pipeline", "subset"], dropna=False)
            [carry].first().reset_index()
        )
        agg = agg.merge(
            meta, on=["track", "protocol", "pipeline", "subset"], how="left"
        )

    # Reference is the full cap, except for sleep where no full-density cap
    # exists. For sleep the reference is the 6-channel scalp montage and the
    # page says so explicitly.
    refs = {}
    for (track, protocol, pipeline), g in agg.groupby(
        ["track", "protocol", "pipeline"], dropna=False
    ):
        full = g[g["strategy"] == "full"]
        if not full.empty:
            refs[(track, protocol, pipeline)] = float(full["score"].iloc[0])
        elif track == "sleep_staging_local":
            scalp = g[g["subset"] == "scalp_6_k6"]
            if not scalp.empty:
                refs[(track, protocol, pipeline)] = float(scalp["score"].iloc[0])

    agg["reference_score"] = [
        refs.get((t, p, pi)) for t, p, pi in zip(
            agg["track"], agg["protocol"], agg["pipeline"]
        )
    ]
    agg["delta_vs_reference"] = agg["score"] - agg["reference_score"]
    return agg


def _positions_for(channels: set[str]) -> dict[str, list[float]]:
    """Normalised 2-D positions for every channel in the results.

    Scalp positions come from MNE's 10-5 montage, projected top-down. Ear
    labels are schematic because they are not in the nomenclature.
    """
    from eegbench.montages import standard_positions
    from eegbench.names import normalize_name

    standard = {normalize_name(k): v for k, v in standard_positions().items()}
    out: dict[str, list[float]] = {}
    for name in channels:
        if name in EAR_POSITIONS:
            out[name] = [round(EAR_POSITIONS[name][0], 4),
                         round(EAR_POSITIONS[name][1], 4)]
            continue
        xyz = standard.get(normalize_name(name))
        if xyz is None:
            continue
        x, y, _ = (float(v) for v in xyz)
        # The 10-5 origin is not the centre of the head outline: the nasion is
        # at y≈+0.09 and the inion at y≈-0.12. Recentre so the drawing looks
        # like the flat top-down maps EEG researchers expect.
        nx = x / 0.100
        ny = (y + 0.015) / 0.105
        out[name] = [round(nx, 4), round(ny, 4)]
    return out


def _controls() -> list[dict]:
    """One permutation-control row per live track.

    ``perm_control_ear_s1.csv`` duplicates subject 1 of the motor track, so it
    is skipped rather than double-counted. Sleep is controlled per night and per
    montage (3 x 9 rows); those are collapsed into one control story for the
    track, which is what the site's single control chart needs.
    """
    rows = []
    for path in sorted((ROOT / "results").glob("perm_control_*.csv")):
        df = pd.read_csv(path)
        if "track" not in df.columns:
            continue
        for track, g in df.groupby("track"):
            if track == "ear_vs_scalp_8ch":
                continue
            metric = str(g["metric"].iloc[0]) if "metric" in g.columns else "roc_auc"
            n_classes = int(g["n_classes"].iloc[0]) if "n_classes" in g.columns else 2
            # kappa's chance level is 0, not 1/n. Getting this wrong made the
            # sleep control look like it had a chance line at 0.20.
            chance = (
                0.5 if metric == "roc_auc"
                else 0.0 if metric == "kappa"
                else 1.0 / max(n_classes, 1)
            )
            subset_label = (
                str(g["subset"].iloc[0]) if "subset" in g.columns else "full"
            )
            if track == "sleep_staging_local":
                subset_label = "scalp + ear (3 montages × 9 nights)"
            rows.append({
                "track": track,
                "subset": subset_label,
                "metric": metric,
                "chance": chance,
                "real": _clean_float(g["real"].mean()),
                "perm": _clean_float(g["perm_mean"].mean()),
                "perm_sd": _clean_float(g["perm_sd"].mean()),
                "gap": _clean_float(g["gap"].mean()),
                "n_controls": int(len(g)),
                "n_subjects": int(g["subject"].nunique()) if "subject" in g.columns else 1,
                "n_permutations": (
                    int(g["n_permutations"].iloc[0])
                    if "n_permutations" in g.columns else None
                ),
            })

    frame = pd.DataFrame(rows)
    if frame.empty:
        return []
    out = []
    for track, g in frame.groupby("track"):
        out.append({
            "track": track,
            "subset": g["subset"].iloc[0],
            "metric": g["metric"].iloc[0],
            "chance": _clean_float(g["chance"].mean()),
            "real": _clean_float(g["real"].mean()),
            "perm": _clean_float(g["perm"].mean()),
            "perm_sd": _clean_float(g["perm_sd"].mean()),
            "gap": _clean_float(g["gap"].mean()),
            "n_controls": int(g["n_controls"].sum()),
            "n_subjects": int(g["n_subjects"].max()),
            "n_permutations": (
                int(g["n_permutations"].max())
                if g["n_permutations"].notna().any() else None
            ),
        })
    return sorted(out, key=lambda r: r["track"])


def _quality() -> list[dict]:
    path = ROOT / "results" / "signal_quality_bnci.csv"
    if not path.exists():
        return []
    df = pd.read_csv(path)
    keep = ["track", "subset", "k", "reject_rate", "line_noise_ratio",
            "effective_rank", "mean_abs_corr"]
    keep = [c for c in keep if c in df.columns]
    return [
        {k: (_clean_float(v) if isinstance(v, float) else v) for k, v in row.items()}
        for row in df[keep].to_dict(orient="records")
    ]


def main() -> int:
    from eegbench.metrics import itr_bits_per_min

    raw = _load_results()
    summary = _summary(raw)
    task_by_id = {t["id"]: t for t in TASKS}

    # Per-task reference row, used for the headline stats.
    for task in TASKS:
        sub = summary[(summary["track"] == task["id"]) &
                      (summary["protocol"] == task["defaultProtocol"]) &
                      (summary["pipeline"] == task["defaultPipeline"])]
        if sub.empty:
            task["stats"] = None
            continue
        # Reference row for the headline stat. A task can name it explicitly
        # (auditory attention compares against a matched-k scalp subset, not the
        # full 29-electrode cap), otherwise the full montage is the reference
        # and a dataset with no dense cap falls back to its matched scalp set.
        ref_subset = task.get("referenceSubset")
        if ref_subset:
            ref_rows = sub[sub["subset"] == ref_subset]
            if ref_rows.empty:
                task["stats"] = None
                continue
            ref = ref_rows.iloc[0]
            ref_label = task.get("referenceLabel") or _subset_label(
                task["id"], ref_subset, ref["strategy"])
        else:
            full = sub[sub["strategy"] == "full"]
            if not full.empty:
                ref = full.iloc[0]
                ref_label = task.get("referenceLabel") or "Full cap"
            else:
                ref = sub[sub["subset"] == "scalp_6_k6"].iloc[0]
                ref_label = task.get("referenceLabel") or "Scalp 6 ch"

        headline_subset = task.get("headlineSubset")
        if headline_subset:
            rows = sub[sub["subset"] == headline_subset]
            best = rows.iloc[0] if not rows.empty else None
        else:
            reduced = sub[
                (sub["strategy"].isin(["region", "distributed", "wearable"])) &
                (sub["k"] <= (14 if task["id"] == "sleep_staging_local" else 8))
            ]
            if task["id"] == "sleep_staging_local":
                # The headline compares like with like: 6 ear vs 6 scalp.
                # The all-14-ear montage is reported separately, not used as the
                # "best" montage.
                reduced = reduced[reduced["subset"] == "ear_6_k6"]
            best = None if reduced.empty else reduced.loc[reduced["score"].idxmax()]
        def _itr(score):
            if task["metric"] != "accuracy" or not task.get("nClasses"):
                return None
            return _clean_float(itr_bits_per_min(
                float(score), int(task["nClasses"]),
                float(task.get("trialSeconds", 1.0)),
            ))

        task["stats"] = {
            # Six decimals: these are printed to three, and a value that lands
            # on a rounding boundary (0.8715) must not print as 0.872.
            "reference": _clean_float(ref["score"], 6),
            "referenceLabel": ref_label,
            "referenceK": int(ref["k"]),
            "referenceItr": _itr(ref["score"]),
            "best": _clean_float(best["score"], 6) if best is not None else None,
            "bestLabel": _subset_label(
                task["id"], best["subset"], best["strategy"]
            ) if best is not None else None,
            "bestK": int(best["k"]) if best is not None else None,
            "bestItr": _itr(best["score"]) if best is not None else None,
            "retainedPct": (
                _clean_float(100.0 * best["score"] / ref["score"], 1)
                if best is not None and ref["score"] else None
            ),
            "delta": _clean_float(best["score"] - ref["score"])
            if best is not None else None,
        }

    # Matched-k comparison callouts, computed from the same summary table.
    def _cell(track, protocol, pipeline, subset):
        g = summary[
            (summary["track"] == track) &
            (summary["protocol"] == protocol) &
            (summary["pipeline"] == pipeline) &
            (summary["subset"] == subset)
        ]
        return g.iloc[0] if not g.empty else None

    comparisons = []
    ear = _cell("motor_execution_ear_vs_scalp", "within_session",
                "riemann_tslr", "wu2020_inear_k8")
    sens = _cell("motor_execution_ear_vs_scalp", "within_session",
                 "riemann_tslr", "region-sensorimotor_k8")
    if ear is not None and sens is not None:
        comparisons.append({
            "track": "motor_execution_ear_vs_scalp",
            "title": "Same eight channels, same session",
            "left": "Sensorimotor scalp",
            "leftScore": _clean_float(sens["score"], 6),
            "right": "In-ear",
            "rightScore": _clean_float(ear["score"], 6),
            "delta": _clean_float(ear["score"] - sens["score"], 6),
            "metricLabel": "ROC-AUC",
            "note": "Negative in 6/6 subjects; paired 95% CI "
                    "[−0.378, −0.173] AUC. Same session, same eight channels, "
                    "same decoder.",
        })
    ear6 = _cell("sleep_staging_local", "within_session",
                 "bandpower_lda", "ear_6_k6")
    scalp6 = _cell("sleep_staging_local", "within_session",
                   "bandpower_lda", "scalp_6_k6")
    if ear6 is not None and scalp6 is not None:
        comparisons.append({
            "track": "sleep_staging_local",
            "title": "Matched six channels, nine nights",
            "left": "Scalp",
            "leftScore": _clean_float(scalp6["score"], 6),
            "right": "Ear",
            "rightScore": _clean_float(ear6["score"], 6),
            "delta": _clean_float(ear6["score"] - scalp6["score"], 6),
            "metricLabel": "Cohen’s κ",
            "note": "Negative in 9/9 nights; paired 95% CI "
                    "[−0.104, −0.009] κ.",
        })

    # Rows for the explorer.
    rows = []
    for _, r in summary.iterrows():
        task = task_by_id[r["track"]]
        channels = _parse_channels(r.get("channels")) if "channels" in r else []
        itr = None
        if task["metric"] == "accuracy" and task.get("nClasses"):
            itr = itr_bits_per_min(
                float(r["score"]), int(task["nClasses"]),
                float(task.get("trialSeconds", 1.0)),
            )
        rows.append({
            "track": r["track"],
            "protocol": r["protocol"],
            "protocolLabel": PROTOCOL_LABELS.get(r["protocol"], r["protocol"]),
            "pipeline": r["pipeline"],
            "pipelineLabel": PIPELINE_LABELS.get(r["pipeline"], r["pipeline"]),
            "subset": r["subset"],
            "subsetLabel": _subset_label(r["track"], r["subset"], r["strategy"]),
            "strategy": r["strategy"],
            "strategyLabel": _strategy_label(r["strategy"]),
            "k": int(r["k"]),
            "score": _clean_float(r["score"], 6),
            "sem": _clean_float(r["sem"], 6),
            "sd": _clean_float(r["sd"], 6),
            "n": int(r["n"]) if pd.notna(r["n"]) else None,
            "chance": _clean_float(task["chance"]),
            "metric": task["metric"],
            "metricLabel": task["metricLabel"],
            "delta": _clean_float(r["delta_vs_reference"], 6),
            "referenceScore": _clean_float(r["reference_score"], 6),
            "itr": _clean_float(itr, 6),
            "fidelity": r.get("fidelity") if pd.notna(r.get("fidelity")) else None,
            "channels": channels,
            "isFull": r["strategy"] == "full",
            "isRandom": r["strategy"] == "random",
            "isWearable": r["strategy"] == "wearable",
        })

    # Aggregate random seeds into one band per (track, protocol, pipeline, k).
    random_bands = []
    for (track, protocol, pipeline, k), g in summary[
        summary["strategy"] == "random"
    ].groupby(["track", "protocol", "pipeline", "k"]):
        random_bands.append({
            "track": track,
            "protocol": protocol,
            "pipeline": pipeline,
            "k": int(k),
            "mean": _clean_float(g["score"].mean(), 6),
            "min": _clean_float(g["score"].min(), 6),
            "max": _clean_float(g["score"].max(), 6),
            "nSeeds": int(len(g)),
        })

    all_channels = {c for row in rows for c in row["channels"]}
    positions = _positions_for(all_channels)
    missing_positions = sorted(all_channels - set(positions))

    payload = {
        "generated": date.today().isoformat(),
        "meta": {
            "title": "The Electrode Budget",
            "subtitle": "How much EEG accuracy survives when a lab cap "
                        "becomes a wearable?",
            "nTasks": len(TASKS),
            "nExamples": sum(t["examples"] for t in TASKS),
            "nRows": len(rows),
            "nSources": len({t["dataset"] for t in TASKS}),
        },
        "tasks": TASKS,
        "rows": rows,
        "randomBands": random_bands,
        "comparisons": comparisons,
        "controls": _controls(),
        "quality": _quality(),
        "positions": positions,
        "positionNote": "Scalp positions are standard 10-5 locations projected "
                        "top-down. Ear positions are schematic; they are not "
                        "part of the 10-5 nomenclature.",
        "missingPositions": missing_positions,
    }

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "benchmark.json"
    path.write_text(
        json.dumps(payload, indent=1, ensure_ascii=False, default=_json_default),
        encoding="utf-8",
    )
    print(f"wrote {path} ({path.stat().st_size / 1024:.0f} KB)")
    print(f"  {len(rows)} rows, {len(TASKS)} tasks, "
          f"{len(positions)} electrode positions")
    if missing_positions:
        print(f"  note: no position for {missing_positions}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
