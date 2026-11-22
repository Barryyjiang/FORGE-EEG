"""Render the paper page (``docs/index.html``) from ``paper/paper.html``.

    .\\.venv\\Scripts\\python.exe scripts\\build_paper.py

The template holds the prose; every number, table and BibTeX block is filled in
from the generated bundle (``docs/data/benchmark.json``) and the raw result CSVs
(``results/benchmark/*.csv``), so nothing on the page is transcribed by hand.

Placeholders
------------
``{{TABLE_NAME}}``      a generated table (see ``TABLES`` below)
``{{stat:track:field}}`` one number from a task's aggregates, e.g.
                         ``{{stat:p300_8ch:retainedPct}}``
``{{meta:field}}``       one field of the bundle's ``meta`` block
``{{generated}}``        the bundle's build date
``{{bibtex}}``           the citation entry

An unknown placeholder raises instead of shipping a broken page.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "figures"))
sys.path.insert(0, str(ROOT / "scripts"))

# The pair summary printed at the end contains Δ and →. A cp1252 console cannot
# encode them, and the script used to write the page and *then* die on the
# print, reporting failure for a build that had actually succeeded.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd  # noqa: E402
import paper_data as pd_  # noqa: E402  (path set above)

from build_site import TASKS  # noqa: E402  (task metadata: one source of truth)

TEMPLATE = ROOT / "paper" / "paper.html"
OUTPUT = ROOT / "docs" / "index.html"
FIGS = "assets/figures"

TITLE = "The Electrode Budget: A Wearable Centric EEG Benchmark"

#: Authors, in the order they appear on the page and in the citation.
AUTHORS = [
    "Barry Jiang",
    "Mishti Broor",
    "Sammy Mustafa",
    "Fyzeen Ahmad",
    "Chau Tr\u1ea7n",
]
AFFILIATION = "Northwestern University, Evanston, IL, USA"

#: Repository URL used by the citation and the Code button. The page works from
#: a sub-path (``<user>.github.io/<repo>/``).
REPO_URL = "https://github.com/Barryyjiang/FORGE-EEG"

TASK_ORDER = pd_.TASK_ORDER

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

METRIC_LABELS = {
    "roc_auc": "ROC-AUC",
    "accuracy": "Accuracy",
    "balanced_accuracy": "Balanced accuracy",
    "kappa": "Cohen\u2019s \u03ba",
}


# ---------------------------------------------------------------------------
# Aggregation helpers (all derived from the bundle and the raw CSVs)
# ---------------------------------------------------------------------------


def _itr_text(task: dict, score: float) -> str:
    """Information transfer rate, for tasks that have classes and a trial length."""

    if task.get("metric") != "accuracy" or not task.get("nClasses"):
        return "—"
    from eegbench.metrics import itr_bits_per_min

    trial = float(task.get("trialSeconds", 1.0))
    return f"{itr_bits_per_min(float(score), int(task['nClasses']), trial):.1f}"


@dataclass
class TaskNumbers:
    """Everything the page needs about one task."""

    track: str
    task: dict
    pipeline: str
    protocol: str
    reference_subset: str
    reference_label: str
    reference_k: int
    reference_score: float
    best_subset: str
    best_label: str
    best_k: int
    best_score: float
    paired: pd_.Paired

    @property
    def retained_pct(self) -> float:
        return pd_.pct(self.best_score, self.reference_score)

    @property
    def fields(self) -> dict[str, str]:
        task = self.task
        paired = self.paired
        return {
            "name": task["name"],
            "short": task["short"],
            "dataset": task["dataset"],
            "datasetName": task["datasetName"],
            "subjects": task["subjects"],
            "nLabel": task["nLabel"],
            "channels": task["channels"],
            "metricLabel": METRIC_LABELS.get(task["metric"], task["metricLabel"]),
            "chance": pd_.fmt(task["chance"], 3),
            "examples": f"{int(task['examples']):,}",
            "reference": pd_.fmt(self.reference_score),
            "referenceK": str(self.reference_k),
            "referenceLabel": self.reference_label,
            "best": pd_.fmt(self.best_score),
            "bestK": str(self.best_k),
            "bestLabel": self.best_label,
            "retainedPct": f"{self.retained_pct:.0f}",
            "retainedPct1": f"{self.retained_pct:.1f}",
            "itrReference": _itr_text(self.task, self.reference_score),
            "itrBest": _itr_text(self.task, self.best_score),
            "delta": pd_.fmt_delta(paired.delta),
            "delta_abs": pd_.fmt(abs(paired.delta)),
            "ci": paired.ci_text(3),
            "sign": paired.sign_summary(),
            "n": str(paired.n),
            "p": f"{paired.p_value:.3f}",
            "pipeline": PIPELINE_LABELS.get(self.pipeline, self.pipeline),
        }


def _resolve_task(track: str) -> TaskNumbers:
    """Headline numbers for one task, using the same rules as the site."""

    bundle = pd_.load_bundle()
    task = next(t for t in TASKS if t["id"] == track)
    pipeline = task["defaultPipeline"]
    protocol = task["defaultProtocol"]
    rows = bundle.rows[
        (bundle.rows["track"] == track)
        & (bundle.rows["pipeline"] == pipeline)
        & (bundle.rows["protocol"] == protocol)
    ]

    # Reference row. A task can name it explicitly (auditory attention compares
    # against a matched-k scalp subset, not the full 29-electrode cap).
    ref_subset = task.get("referenceSubset")
    if ref_subset:
        reference = rows[rows["subset"] == ref_subset].iloc[0]
        reference_subset = ref_subset
        reference_label = task.get("referenceLabel") or "Scalp subset"
    else:
        full = rows[rows["strategy"] == "full"]
        if not full.empty:
            reference = full.iloc[0]
            reference_subset = str(reference["subset"])
            reference_label = task.get("referenceLabel") or "Full cap"
        else:
            reference = rows[rows["subset"] == "scalp_6_k6"].iloc[0]
            reference_subset = "scalp_6_k6"
            reference_label = task.get("referenceLabel") or "Scalp 6 ch"

    headline_subset = task.get("headlineSubset")
    if headline_subset:
        best = rows[rows["subset"] == headline_subset].iloc[0]
    else:
        reduced = rows[
            rows["strategy"].isin(["region", "distributed", "wearable"])
            & (rows["k"] <= (14 if track == "sleep_staging_local" else 8))
        ]
        if track == "sleep_staging_local":
            # The headline compares like with like: six ear vs six scalp.
            reduced = reduced[reduced["subset"] == "ear_6_k6"]
        best = reduced.loc[reduced["score"].idxmax()]

    # A task scored at several decision windows must be paired at one of them;
    # without this the pairing averages across windows and compares numbers that
    # belong to no window.
    paired = pd_.paired(
        track,
        reference_subset,
        str(best["subset"]),
        pipeline=pipeline,
        protocol=protocol,
        trial_seconds=task.get("headlineWindowS"),
    )
    return TaskNumbers(
        track=track,
        task=task,
        pipeline=pipeline,
        protocol=protocol,
        reference_subset=reference_subset,
        reference_label=reference_label,
        reference_k=int(reference["k"]),
        reference_score=float(reference["score"]),
        best_subset=str(best["subset"]),
        best_label=str(best["subsetLabel"]),
        best_k=int(best["k"]),
        best_score=float(best["score"]),
        paired=paired,
    )


def task_numbers() -> dict[str, TaskNumbers]:
    return {track: _resolve_task(track) for track in TASK_ORDER}


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------


def _wrap(caption: str, header: list[str], rows: list[list[str]], aligns: list[str] | None = None) -> str:
    aligns = aligns or ["left"] * len(header)

    def cls(align: str) -> str:
        return ' class="num"' if align == "num" else ""

    head = "".join(
        f"<th{cls(a)}>{cell}</th>" for cell, a in zip(header, aligns)
    )
    body = []
    for row in rows:
        cells = "".join(
            f"<td{cls(a)}>{cell}</td>" for cell, a in zip(row, aligns)
        )
        body.append(f"      <tr>{cells}</tr>")
    return (
        '    <div class="table-wrap">\n'
        "    <table>\n"
        f"      <caption>{caption}</caption>\n"
        "      <thead>\n"
        f"        <tr>{head}</tr>\n"
        "      </thead>\n"
        "      <tbody>\n" + "\n".join(body) + "\n"
        "      </tbody>\n"
        "    </table>\n"
        "    </div>"
    )


def table_tasks(numbers: dict[str, TaskNumbers]) -> str:
    rows = []
    for track in TASK_ORDER:
        tn = numbers[track]
        f = tn.fields
        rows.append(
            [
                f"<strong>{f['short']}</strong>",
                f"<a href='{_dataset_url(track)}'>{f['datasetName']}</a>",
                f["subjects"],
                f["channels"],
                f"{f['metricLabel']}<br><span class='small'>chance {f['chance']}</span>",
                f"{f['reference']} <span class='small'>({f['referenceLabel'].lower()}, k={f['referenceK']})</span>",
                f["pipeline"],
            ]
        )
    return _wrap(
        table_label("TASKS") + "The nine tasks. Every task uses one "
        "public dataset, one fixed classical decoder, and the full published cohort. "
        "<em>Reference</em> is the montage every reduced result is compared against.",
        ["Task", "Dataset", "Participants", "Channels", "Metric", "Reference", "Decoder"],
        rows,
    )


def _workload_recording_line() -> str:
    """Recording-level balanced accuracies for the workload montages.

    The STEW literature and the team's independent reimplementation average the
    4 s window probabilities into one call per 150 s recording and score balanced
    accuracy. That aggregation ranks the two four-electrode sets differently from
    the window-level AUC the rest of the table uses, so both are shown.
    """
    path = pd_.ROOT / "results/benchmark/stew_workload_14ch__cross_subject.csv"
    if not path.exists():
        return ""
    df = pd.read_csv(path)
    df = df[df["protocol"] == "cross_subject"]
    wanted = (
        ("full_14_k14", "full\u00a014"),
        ("glasses_4_k4", "glasses-4"),
        ("posterior_4_k4", "posterior-4"),
    )
    parts = []
    for subset, label in wanted:
        sel = df[df["subset"] == subset]["recording_accuracy"]
        if sel.empty:
            return ""
        parts.append(f"{label}&nbsp;{sel.mean() * 100:.1f}%")
    return "recording-level: " + " / ".join(parts)


def table_results(numbers: dict[str, TaskNumbers]) -> str:
    rows = []
    workload_line = _workload_recording_line()
    for track in TASK_ORDER:
        tn = numbers[track]
        f = tn.fields
        sign_class = "delta-neg" if tn.paired.delta < 0 else "delta-pos"
        task_cell = f"<strong>{f['short']}</strong>"
        if track == "stew_workload_14ch" and workload_line:
            task_cell += f"<br><span class='small'>{workload_line}</span>"
        rows.append(
            [
                task_cell,
                f"{f['reference']}<br><span class='small'>{f['referenceLabel']}, k={f['referenceK']}</span>",
                f"{f['best']}<br><span class='small'>{f['bestLabel']}, k={f['bestK']}</span>",
                f"<strong>{f['retainedPct1']}%</strong>",
                f"<span class='{sign_class}'>{f['delta']}</span><br>"
                f"<span class='small nowrap'>[{f['ci'].strip('[]').replace(', ', ', ')}]</span>",
                f"{f['sign']}<br><span class='small'>n={f['n']}, p={f['p']}</span>",
            ]
        )
    return _wrap(
        table_label("RESULTS") + "Headline result per task: the best reduced "
        "montage against that task's reference, at the task's standard decoder. "
        "Deltas are paired on the same subject (or subject-session) with 95% paired "
        "<em>t</em> intervals recomputed from <code>results/benchmark/</code>. "
        "Scores are one decision per trial or per <em>n</em>-second window. "
        "Workload also shows its recording-level balanced accuracies, the "
        "aggregation the STEW literature and the team's independent "
        "reimplementation report; the two levels rank the two four-electrode sets "
        "differently.",
        ["Task", "Reference", "Best reduced montage", "Retained", "Paired Δ [95% CI]", "Agreement"],
        rows,
        aligns=["left", "left", "left", "num", "num", "left"],
    )


def table_wearable(numbers: dict[str, TaskNumbers]) -> str:
    rows = []

    def add(label, a_subset, b_subset, track, pipeline, a_name, b_name, metric, note=""):
        p = pd_.paired(track, a_subset, b_subset, pipeline=pipeline, protocol="within_session")
        sign_class = "delta-neg" if p.delta < 0 else "delta-pos"
        rows.append(
            [
                f"<strong>{label}</strong><br><span class='small'>{note}</span>",
                f"{a_name}<br><span class='small'>{pd_.fmt(p.mean_a)}</span>",
                f"{b_name}<br><span class='small'>{pd_.fmt(p.mean_b)}</span>",
                f"<span class='{sign_class}'>{pd_.fmt_delta(p.delta)} {metric}</span>"
                f"<br><span class='small nowrap'>95% CI {p.ci_text(3)}</span>",
                f"{p.n}",
                f"{p.sign_summary()}",
            ]
        )

    add(
        "Sensorimotor scalp vs in-ear",
        "region-sensorimotor_k8",
        "wu2020_inear_k8",
        "motor_execution_ear_vs_scalp",
        "riemann_tslr",
        "sensorimotor scalp, 8 ch",
        "in-ear, 8 ch",
        "AUC",
        "Wu 2020, same session, matched eight channels",
    )
    add(
        "Full cap vs sensorimotor 8",
        "full_k115",
        "region-sensorimotor_k8",
        "motor_execution_ear_vs_scalp",
        "riemann_tslr",
        "full cap, 115 ch",
        "sensorimotor scalp, 8 ch",
        "AUC",
        "what the 107 dropped electrodes were worth",
    )
    add(
        "Scalp vs ear at matched six",
        "scalp_6_k6",
        "ear_6_k6",
        "sleep_staging_local",
        "bandpower_lda",
        "scalp, 6 ch",
        "ear, 6 ch",
        "κ",
        "OpenNeuro ds004348, nine nights",
    )
    add(
        "Ear 6 vs all 14 ear",
        "ear_6_k6",
        "ear_14_k14",
        "sleep_staging_local",
        "bandpower_lda",
        "ear, 6 ch",
        "ear, 14 ch",
        "κ",
        "extra ear channels close part of the gap",
    )
    return _wrap(
        table_label("WEARABLE") + "Wearable comparisons. Both datasets record "
        "the wearable electrodes <em>simultaneously</em> with scalp electrodes, so each row "
        "is a physical measurement rather than a geometric stand-in for a product.",
        ["Comparison", "Montage A", "Montage B", "Paired Δ (B − A) [95% CI]", "n", "Agreement"],
        rows,
        aligns=["left", "left", "left", "num", "num", "left"],
    )


def table_controls(_numbers=None) -> str:
    bundle = pd_.load_bundle()
    short = {t["id"]: t["short"] for t in TASKS}
    order = {track: i for i, track in enumerate(TASK_ORDER)}
    controls = sorted(bundle.controls, key=lambda c: order.get(c["track"], 99))
    rows = []
    for control in controls:
        track = control["track"]
        if track == "sleep_staging_local":
            # The sleep control is stored per montage, not per night.
            units = f"{control['n_controls']} montages"
        else:
            n = control["n_subjects"]
            units = f"{n} subject" + ("" if n == 1 else "s")
        rows.append(
            [
                f"<strong>{short.get(track, track)}</strong>",
                f"<code>{control['subset']}</code>",
                pd_.fmt(control["real"]),
                f"{pd_.fmt(control['perm'])} ± {pd_.fmt(control['perm_sd'])}",
                pd_.fmt(control["chance"]),
                f"{control['n_permutations']:,}",
                units,
            ]
        )
    return _wrap(
        table_label("CONTROLS") + "Permutation controls: each headline decoder "
        "and channel subset re-run on shuffled labels (whole 20-epoch blocks permuted "
        "for sleep, where a circular shift is not a valid null). Every null sits within "
        "the benchmark's ±0.05 tolerance of chance. Control rows are the cohort mean "
        "under the control's own stratified 5-fold CV, so a task's <em>Real</em> here is "
        "close to, but not identical with, its score in the results tables.",
        ["Task", "Subset", "Real", "Shuffled mean ± s.d.", "Chance", "Shuffles", "Units"],
        rows,
        aligns=["left", "left", "num", "num", "num", "num", "num"],
    )


def table_decoders(_numbers=None) -> str:
    bundle = pd_.load_bundle()
    rows = []
    for task in TASKS:
        pipelines = sorted(
            {str(p) for p in bundle.rows[bundle.rows["track"] == task["id"]]["pipeline"].unique()}
        )
        headline = PIPELINE_LABELS.get(task["defaultPipeline"], task["defaultPipeline"])
        others = [
            f"<code>{PIPELINE_LABELS.get(p, p)}</code>" for p in pipelines if p != task["defaultPipeline"]
        ]
        rows.append(
            [
                f"<strong>{task['short']}</strong>",
                headline,
                ", ".join(others) if others else "<span class='small'>—</span>",
                METRIC_LABELS.get(task["metric"], task["metricLabel"]),
            ]
        )
    return _wrap(
        table_label("DECODERS") + "One decoder per task, fixed before the montage "
        "results and never tuned per montage. The alternatives are reported so the decoder "
        "axis can be judged instead of assumed.",
        ["Task", "Headline decoder", "Also evaluated", "Metric"],
        rows,
    )


def table_checks(_numbers=None) -> str:
    """The two checks that decide whether a headline number means what it says.

    Both are read from files the track scripts write, so the prose cannot drift
    away from the CSVs:
    ``results/stew_drift_control.csv`` (label-free session-drift control) and
    ``results/earsaad_paper_comparison.csv`` (reproduction against the paper's
    with- and without-artifact-removal columns).
    """
    rows = []

    drift_path = ROOT / "results" / "stew_drift_control.csv"
    if drift_path.exists():
        drift = pd.read_csv(drift_path)
        agg = (drift.groupby("layout")[["real_half_accuracy", "null_mean"]]
               .mean().sort_values("real_half_accuracy", ascending=False))
        labels = {
            "full_14": "STEW, full 14 ch",
            "glasses_4": "STEW, glasses-like 4 ch",
            "posterior_4": "STEW, posterior 4 ch",
            "forehead_2": "STEW, forehead 2 ch",
        }
        for layout, row in agg.iterrows():
            rows.append([
                "Session drift<br><span class='small'>label-free</span>",
                f"<strong>{labels.get(layout, layout)}</strong>",
                pd_.fmt(float(row["real_half_accuracy"])),
                f"{pd_.fmt(float(row['null_mean']))} shuffled halves",
                "recording drifts",
            ])

    check_path = ROOT / "results" / "earsaad_paper_comparison.csv"
    if check_path.exists():
        check = pd.read_csv(check_path)
        names = {
            "scalp_29": "Ear-SAAD, scalp 29 ch",
            "around_ear_19": "Ear-SAAD, around-ear 19 ch",
            "in_ear_12": "Ear-SAAD, in-ear 12 ch",
        }
        for _, row in check.iterrows():
            rows.append([
                "Reproduction<br><span class='small'>against the paper</span>",
                f"<strong>{names.get(row['setup'], row['setup'])}</strong>",
                f"{float(row['ours_pct']):.2f}%",
                f"{float(row['paper_full_pct']):.2f}% with ASR / "
                f"{float(row['paper_no_cleanup_pct']):.2f}% without",
                f"matches the full pipeline",
            ])

    if not rows:
        return ("<p class='small'>Confound and reproduction checks not generated. "
                "Run <code>scripts/stew_drift_control.py</code> and "
                "<code>scripts/earsaad_paper_check.py</code>.</p>")

    return _wrap(
        table_label("CHECKS") + "Confound and reproduction checks. The "
        "drift rows re-run the workload decoder on a label-free target \u2014 first half "
        "versus second half of the same recording \u2014 so a value above 0.50 means the "
        "recording itself moves over time. The reproduction rows compare this "
        "benchmark's 60-second attention accuracies with the two columns the original "
        "paper publishes; landing on the with-ASR column is the evidence that the "
        "released data is already artifact-cleaned.",
        ["Check", "Task", "Measured", "Comparator", "Reading"],
        rows,
        aligns=["left", "left", "num", "num", "left"],
    )


TABLES = {
    "TASKS": table_tasks,
    "RESULTS": table_results,
    "WEARABLE": table_wearable,
    "CONTROLS": table_controls,
    "DECODERS": table_decoders,
    "CHECKS": table_checks,
}


# ---------------------------------------------------------------------------
# Named comparisons used in the prose
# ---------------------------------------------------------------------------


def _pair_fields(p: pd_.Paired, metric: str) -> dict[str, str]:
    return {
        "meanA": pd_.fmt(p.mean_a),
        "meanB": pd_.fmt(p.mean_b),
        "delta": pd_.fmt_delta(p.delta),
        "delta_abs": pd_.fmt(abs(p.delta)),
        "ci": p.ci_text(3),
        "sign": p.sign_summary(),
        "n": str(p.n),
        "p": f"{p.p_value:.3f}",
        "metric": metric,
        "labelA": p.label_a,
        "labelB": p.label_b,
    }


def _stats_fields(s: pd_.DeltaStats, metric: str) -> dict[str, str]:
    return {
        "meanA": pd_.fmt(s.mean_a),
        "meanB": pd_.fmt(s.mean_b),
        "delta": pd_.fmt_delta(s.delta),
        "delta_abs": pd_.fmt(abs(s.delta)),
        "ci": s.ci_text(3),
        "sign": s.sign_summary(),
        "n": str(s.n),
        "p": f"{s.p_value:.3f}",
        "metric": metric,
        "labelA": "A",
        "labelB": "B",
    }


def named_pairs(numbers: dict[str, TaskNumbers]) -> dict[str, dict[str, str]]:
    """The comparisons the prose refers to, computed once and named."""

    ma = "motor_execution_ear_vs_scalp"
    sleep = "sleep_staging_local"
    out: dict[str, dict[str, str]] = {}

    out["inear_vs_senso"] = _pair_fields(
        pd_.paired(ma, "region-sensorimotor_k8", "wu2020_inear_k8",
                   pipeline="riemann_tslr", protocol="within_session"),
        "AUC",
    )
    out["cap_vs_senso"] = _pair_fields(
        pd_.paired(ma, "full_k115", "region-sensorimotor_k8",
                   pipeline="riemann_tslr", protocol="within_session"),
        "AUC",
    )
    out["sleep_scalp_vs_ear"] = _pair_fields(
        pd_.paired(sleep, "scalp_6_k6", "ear_6_k6",
                   pipeline="bandpower_lda", protocol="within_session"),
        "κ",
    )
    out["sleep_ear6_vs_ear14"] = _pair_fields(
        pd_.paired(sleep, "ear_6_k6", "ear_14_k14",
                   pipeline="bandpower_lda", protocol="within_session"),
        "κ",
    )
    out["p300_montage_xdawn"] = _pair_fields(
        pd_.paired("p300_8ch", "full_k8", "distributed_k4",
                   pipeline="xdawn_tslr", protocol="within_session"),
        "AUC",
    )

    # --- the two paradigm-level extensions --------------------------------
    # Workload is compared under the protocol where the decoder never sees the
    # test person, because that is the number the page quotes.
    stew = "stew_workload_14ch"
    out["stew_glasses_vs_full"] = _pair_fields(
        pd_.paired(stew, "full_14_k14", "glasses_4_k4",
                   pipeline="psd_lda", protocol="cross_subject"),
        "AUC",
    )
    out["stew_glasses_vs_posterior"] = _pair_fields(
        pd_.paired(stew, "posterior_4_k4", "glasses_4_k4",
                   pipeline="psd_lda", protocol="cross_subject"),
        "AUC",
    )

    # Attention is compared at matched channel count, at the paper's 60 s
    # decision window.
    aad = "auditory_attention_earsaad"
    out["aad_inear_vs_scalp12"] = _pair_fields(
        pd_.paired(aad, "scalp_12_k12", "in_ear_12_k12",
                   pipeline="ridge_reconstruction", protocol="within_session",
                   trial_seconds=60.0),
        "accuracy",
    )
    out["aad_around_vs_scalp19"] = _pair_fields(
        pd_.paired(aad, "scalp_19_k19", "around_ear_19_k19",
                   pipeline="ridge_reconstruction", protocol="within_session",
                   trial_seconds=60.0),
        "accuracy",
    )

    # Emotion is the largest cohort and the smallest effect: the reduction cost
    # has to be read against a six-point margin, not a large one.
    faced = "faced_emotion_123"
    out["faced_posterior_vs_full"] = _pair_fields(
        pd_.paired(faced, "full_k30", "posterior_4_k4",
                   pipeline="psd_lda", protocol="within_session"),
        "balanced accuracy",
    )
    out["faced_glasses_vs_posterior"] = _pair_fields(
        pd_.paired(faced, "posterior_4_k4", "glasses_4_k4",
                   pipeline="psd_lda", protocol="within_session"),
        "balanced accuracy",
    )

    # Different decoder, same channels: paired on the subject, not the montage.
    p300_decoders = pd_.unit_table(
        "p300_8ch",
        [("logvar", "logvar_lda", "full_k8"), ("xdawn", "xdawn_tslr", "full_k8")],
        protocol="within_session",
    )
    out["p300_decoder"] = _stats_fields(
        pd_.delta_stats(p300_decoders, "logvar", "xdawn"), "AUC"
    )

    mi_decoders = pd_.unit_table(
        "mi_leftright_22ch",
        [
            ("riemann", "riemann_tslr", "region-sensorimotor_k8"),
            ("logvar", "logvar_lda", "region-sensorimotor_k8"),
        ],
        protocol="within_session",
    )
    # Oriented so the delta is positive: the prose reads "Riemannian TSLR
    # beats log-variance by {delta_abs} (95% CI {ci})", so the interval has to
    # be the riemann - logvar interval, not its mirror image.
    out["mi_decoder"] = _stats_fields(pd_.delta_stats(mi_decoders, "logvar", "riemann"), "AUC")

    out["ssvep_cap_vs_spread4"] = _pair_fields(
        pd_.paired("ssvep_8ch", "full_k8", "distributed_k4",
                   pipeline="ssvep_cca", protocol="within_session"),
        "accuracy",
    )
    out["mi_cap_vs_senso8"] = _pair_fields(numbers["mi_leftright_22ch"].paired, "AUC")

    # Class count: the same cap, the same eight sensorimotor electrodes, four
    # classes instead of two. Scored in accuracy (chance 1/4), so the metric
    # label differs from the two-class track.
    out["mi4_senso_vs_full"] = _pair_fields(
        pd_.paired("mi_4class_22ch", "full_k22", "region-sensorimotor_k8",
                   pipeline="riemann_tslr", protocol="within_session"),
        "accuracy",
    )
    out["mini_decoder_ma"] = _stats_fields(
        pd_.delta_stats(
            pd_.unit_table(
                ma,
                [
                    ("riemann", "riemann_tslr", "region-sensorimotor_k8"),
                    ("logvar", "logvar_lda", "region-sensorimotor_k8"),
                ],
                protocol="within_session",
            ),
            "riemann",
            "logvar",
        ),
        "AUC",
    )
    return out


def cell_fields(track: str, subset: str) -> dict[str, str]:
    """Aggregate fields for one (task, subset) cell at the task's decoder."""

    bundle = pd_.load_bundle()
    task = next(t for t in TASKS if t["id"] == track)
    row = bundle.row(
        track, subset, pipeline=task["defaultPipeline"], protocol=task["defaultProtocol"]
    )
    return {
        "score": pd_.fmt(float(row["score"])),
        "label": str(row["subsetLabel"]),
        "k": str(int(row["k"])),
        "n": str(int(row["n"])),
        "delta": pd_.fmt_delta(float(row["delta"])),
        "referenceScore": pd_.fmt(float(row["referenceScore"])),
        "pipeline": PIPELINE_LABELS.get(str(row["pipeline"]), str(row["pipeline"])),
        "channels": ", ".join(row["channels"]) if row.get("channels") else "",
    }


def _dataset_url(track: str) -> str:
    return {
        "mi_leftright_22ch": "http://bnci-horizon-2020.eu/database/data-sets",
        "mi_4class_22ch": "http://bnci-horizon-2020.eu/database/data-sets",
        "p300_8ch": "http://bnci-horizon-2020.eu/database/data-sets",
        "ssvep_8ch": "https://doi.org/10.1371/journal.pone.0114853",
        "motor_execution_ear_vs_scalp": "https://doi.org/10.1088/1741-2552/abc1b6",
        "sleep_staging_local": "https://doi.org/10.18112/openneuro.ds004348.v1.0.5",
        "stew_workload_14ch": "https://doi.org/10.21227/44r8-ya50",
        "auditory_attention_earsaad": "https://zenodo.org/records/16536441",
        "faced_emotion_123": "https://nemar.org/dataexplorer/detail?dataset_id=nm000112",
    }[track]


# ---------------------------------------------------------------------------
# Placeholder resolution
# ---------------------------------------------------------------------------

TOKEN = re.compile(r"\{\{([^}]+)\}\}")

#: 1-based position of each table in the current template, filled by
#: :func:`resolve`. Numbering is derived rather than hardcoded so that adding or
#: removing a table cannot silently mislabel the rest.
_TABLE_INDEX: dict[str, int] = {}


def table_order(template: str) -> dict[str, int]:
    """The order in which each ``{{table:NAME}}`` appears in the template."""
    seen: dict[str, int] = {}
    for match in TOKEN.finditer(template):
        token = match.group(1).strip()
        if token.startswith("table:"):
            name = token.split(":", 1)[1]
            seen.setdefault(name, len(seen) + 1)
    return seen


def table_label(name: str) -> str:
    """``<span class='label'>Table N.</span>`` for the current template."""
    number = _TABLE_INDEX.get(name)
    if number is None:
        return ""
    return f"<span class='label'>Table {number}.</span> "


def bibtex() -> str:
    year = date.today().year
    authors = " and ".join(AUTHORS)
    return (
        "@misc{forge-eeg-benchmark,\n"
        f"  title        = {{{TITLE}}},\n"
        f"  author       = {{{authors}}},\n"
        f"  year         = {{{year}}},\n"
        f"  howpublished = {{\\url{{{REPO_URL}}}}},\n"
        f"  note         = {{Benchmark code and results. "
        f"{AFFILIATION}}}\n"
        "}"
    )


def curve_fields() -> dict[str, dict[int, float]]:
    """Accuracy against channel budget, from ``results/aad_channel_curve.csv``.

    Keyed ``setup -> k -> mean accuracy``. The paper quotes individual points on
    the ear curve, and they have to come from the CSV rather than from the prose.
    """
    path = ROOT / "results" / "aad_channel_curve.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    out: dict[str, dict[int, float]] = {}
    for setup, group in df.groupby("setup"):
        out[str(setup)] = {int(r.k): float(r.score_mean) for r in group.itertuples()}
    return out


def random_percentiles() -> dict[str, str]:
    """Where a hand-picked montage sits among random draws of the same size.

    A montage at the 90th percentile beats 90% of arbitrary montages with the
    same number of electrodes. That is the claim "this site was chosen well" in
    a form that cannot be cherry-picked, and it is read from the control files
    the track scripts write rather than typed into the prose.
    """
    out: dict[str, str] = {}
    bundle = pd_.load_bundle()
    specs = [
        ("stew_glasses", "stew_workload_14ch", "glasses_4_k4",
         ROOT / "results" / "stew_random_montages.csv"),
        ("faced_posterior", "faced_emotion_123", "posterior_4_k4",
         ROOT / "results" / "faced_random_4.csv"),
        ("faced_glasses", "faced_emotion_123", "glasses_4_k4",
         ROOT / "results" / "faced_random_4.csv"),
    ]
    for key, track, subset, path in specs:
        if not path.exists():
            continue
        draws = pd.read_csv(path)["score"].to_numpy()
        task = next(t for t in TASKS if t["id"] == track)
        row = bundle.row(track, subset, pipeline=task["defaultPipeline"],
                         protocol=task["defaultProtocol"])
        value = float(row["score"])
        out[key] = f"{100.0 * (draws <= value).mean():.0f}"
    return out


def resolve(template: str, numbers: dict[str, TaskNumbers]) -> str:
    bundle = pd_.load_bundle()
    meta = bundle.meta
    pairs = named_pairs(numbers)
    curves = curve_fields()
    randoms = random_percentiles()
    _TABLE_INDEX.clear()
    _TABLE_INDEX.update(table_order(template))
    unknown: list[str] = []

    def replace(match: re.Match) -> str:
        token = match.group(1).strip()
        if token == "generated":
            return str(bundle.raw["generated"])
        if token == "bibtex":
            return bibtex()
        if token == "repo":
            return REPO_URL
        if token.startswith("meta:"):
            field = token.split(":", 1)[1]
            if field not in meta:
                unknown.append(token)
                return match.group(0)
            return f"{meta[field]:,}" if isinstance(meta[field], int) else str(meta[field])
        if token.startswith("table:"):
            name = token.split(":", 1)[1].upper()
            if name not in TABLES:
                unknown.append(token)
                return match.group(0)
            return TABLES[name](numbers)
        if token.startswith("stat:"):
            _, track, field = token.split(":", 2)
            if track not in numbers:
                unknown.append(token)
                return match.group(0)
            fields = numbers[track].fields
            if field not in fields:
                unknown.append(token)
                return match.group(0)
            return fields[field]
        if token.startswith("cell:"):
            _, track, subset, field = token.split(":", 3)
            try:
                fields = cell_fields(track, subset)
            except KeyError:
                unknown.append(token)
                return match.group(0)
            if field not in fields:
                unknown.append(token)
                return match.group(0)
            return fields[field]
        if token.startswith("pair:"):
            _, name, field = token.split(":", 2)
            fields = pairs.get(name)
            if fields is None or field not in fields:
                unknown.append(token)
                return match.group(0)
            return fields[field]
        if token.startswith("curve:"):
            _, name, setup, k = token.split(":", 3)
            series = curves.get(setup) if name == "aad" else None
            if series is None or int(k) not in series:
                unknown.append(token)
                return match.group(0)
            return pd_.fmt(series[int(k)])
        if token.startswith("rand:"):
            key = token.split(":", 1)[1]
            if key not in randoms:
                unknown.append(token)
                return match.group(0)
            return randoms[key]
        unknown.append(token)
        return match.group(0)

    rendered = TOKEN.sub(replace, template)
    if unknown:
        raise ValueError(f"unknown or unusable placeholder(s): {sorted(set(unknown))}")
    return rendered


# ---------------------------------------------------------------------------
# Output checks
# ---------------------------------------------------------------------------

SRC = re.compile(r'(?:src|href)="((?!https?:|#|mailto:)[^"]+)"')


def check_assets(html: str) -> list[str]:
    """Every local asset the page references must exist."""

    missing = []
    for ref in sorted(set(SRC.findall(html))):
        if ref.startswith("/"):
            continue
        path = (OUTPUT.parent / ref).resolve()
        if not path.exists():
            missing.append(ref)
    return missing


def main() -> int:
    numbers = task_numbers()
    template = TEMPLATE.read_text(encoding="utf-8")
    html = resolve(template, numbers)
    missing = check_assets(html)
    if missing:
        print("missing assets referenced by the page:")
        for ref in missing:
            print(f"  {ref}")
        return 1
    OUTPUT.write_text(html, encoding="utf-8", newline="\n")
    size = OUTPUT.stat().st_size / 1024
    print(f"wrote {OUTPUT.relative_to(ROOT)} ({size:.0f} KB)")
    print(f"  {len(TABLES)} generated tables, {len(numbers)} tasks")
    for track in TASK_ORDER:
        fields = numbers[track].fields
        print(
            f"  {fields['short']:16s} ref {fields['reference']} (k={fields['referenceK']:>3}) → "
            f"best {fields['best']} (k={fields['bestK']:>2}) = {fields['retainedPct1']}%, "
            f"Δ {fields['delta']} {fields['ci']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
