"""Data access for the paper figures and tables.

Two sources, both already produced by the benchmark:

* ``docs/data/benchmark.json`` — the aggregate bundle the interactive site
  reads (per-cell means, chance levels, references, electrode positions).
* ``results/benchmark/*.csv`` — the raw per-subject rows, used for paired
  comparisons and per-subject figures.

Nothing here invents a number: aggregates come from the bundle, paired
statistics are recomputed from the raw rows with a paired t interval.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
RESULTS = ROOT / "results"
BENCHMARK_DIR = RESULTS / "benchmark"
BUNDLE_PATH = DOCS / "data" / "benchmark.json"
FIGURE_DIR = DOCS / "assets" / "figures"

#: Display order of the tasks.
TASK_ORDER = [
    "mi_leftright_22ch",
    "mi_4class_22ch",
    "p300_8ch",
    "ssvep_8ch",
    "motor_execution_ear_vs_scalp",
    "sleep_staging_local",
    "stew_workload_14ch",
    "auditory_attention_earsaad",
    "faced_emotion_123",
]

#: Compact axis labels (figures) per track.
SHORT = {
    "mi_leftright_22ch": "Motor imagery",
    "mi_4class_22ch": "MI, 4 classes",
    "p300_8ch": "P300",
    "ssvep_8ch": "SSVEP",
    "motor_execution_ear_vs_scalp": "Motor execution",
    "sleep_staging_local": "Sleep staging",
    "stew_workload_14ch": "Workload",
    "auditory_attention_earsaad": "Auditory attention",
    "faced_emotion_123": "Emotion",
}

#: Subset labels used in the figures, per track.
SUBSET = {    "full": "full_k22",
    "spread_4": "distributed_k4",
    "spread_8": "distributed_k8",
    "spread_16": "distributed_k16",
    "sensorimotor_4": "region-sensorimotor_k4",
    "sensorimotor_8": "region-sensorimotor_k8",
    "parietal_4": "region-parietal_k4",
    "frontal_8": "region-frontal_k8",
    "temporal_8": "region-temporal_k8",
    "inear_8": "wu2020_inear_k8",
    "scalp_6": "scalp_6_k6",
    "ear_6": "ear_6_k6",
    "ear_14": "ear_14_k14",
}

#: One colour per task, shared by every figure that shows all of them.
#: Values are figures4papers palette entries (see ``figure_style.PALETTE``)
#: except the last two, which are added here to keep seven tasks distinct.
TASK_COLORS = {
    "mi_leftright_22ch": "#8BCF8B",              # green_3
    "mi_4class_22ch": "#4E8F4E",                 # green, darker: same family
    "p300_8ch": "#3775BA",                       # blue_secondary
    "ssvep_8ch": "#9A4D8E",                      # violet
    "motor_execution_ear_vs_scalp": "#B64342",   # red_strong
    "sleep_staging_local": "#0F4D92",            # blue_main
    "stew_workload_14ch": "#C77C1F",             # amber
    "auditory_attention_earsaad": "#5B6B7C",     # slate
    "faced_emotion_123": "#B07AA1",              # muted violet
}

#: One marker per task, so the cross-task panels stay readable in greyscale.
TASK_MARKERS = {
    "mi_leftright_22ch": "o",
    "mi_4class_22ch": "h",
    "p300_8ch": "s",
    "ssvep_8ch": "^",
    "motor_execution_ear_vs_scalp": "D",
    "sleep_staging_local": "v",
    "stew_workload_14ch": "P",
    "auditory_attention_earsaad": "X",
    "faced_emotion_123": "*",
}


# ---------------------------------------------------------------------------
# Bundle (aggregates)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Bundle:
    """The generated site bundle, with convenience lookups."""

    raw: dict
    rows: pd.DataFrame
    positions: dict[str, tuple[float, float]]
    controls: list[dict]
    comparisons: list[dict]
    quality: pd.DataFrame
    meta: dict
    tasks: list[dict]

    def task(self, track: str) -> dict:
        for task in self.tasks:
            if task["id"] == track:
                return task
        raise KeyError(track)

    def row(
        self,
        track: str,
        subset: str,
        pipeline: str | None = None,
        protocol: str | None = None,
    ) -> pd.Series:
        return cell(self, track, subset, pipeline=pipeline, protocol=protocol)

    def score(
        self,
        track: str,
        subset: str,
        pipeline: str | None = None,
        protocol: str | None = None,
    ) -> float:
        row = self.row(track, subset, pipeline=pipeline, protocol=protocol)
        return float(row["score"])

    def channels(self, track: str, subset: str, pipeline: str | None = None) -> list[str]:
        row = self.row(track, subset, pipeline=pipeline)
        channels = row.get("channels")
        if channels is None or (isinstance(channels, float) and np.isnan(channels)):
            return []
        return [str(c) for c in channels]

    def reference(
        self, track: str, pipeline: str | None = None, protocol: str | None = None
    ) -> tuple[float, str, int]:
        """Reference score, its label and its channel count."""

        stats_block = self.task(track).get("stats") or {}
        if not stats_block:
            row = self.row(track, SUBSET["full"], pipeline, protocol)
            return float(row["referenceScore"]), "Full cap", int(row["k"])
        return (
            float(stats_block["reference"]),
            stats_block["referenceLabel"],
            int(stats_block["referenceK"]),
        )


@lru_cache(maxsize=1)
def load_bundle(path: str | Path | None = None) -> Bundle:
    """Read the generated benchmark bundle (cached)."""

    path = Path(path) if path else BUNDLE_PATH
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = pd.DataFrame(raw["rows"])
    quality = pd.DataFrame(raw.get("quality") or [])
    return Bundle(
        raw=raw,
        rows=rows,
        positions={k: tuple(v) for k, v in raw["positions"].items()},
        controls=list(raw.get("controls") or []),
        comparisons=list(raw.get("comparisons") or []),
        quality=quality,
        meta=raw["meta"],
        tasks=sorted(raw["tasks"], key=lambda t: t["order"]),
    )


def cell(
    bundle: Bundle,
    track: str,
    subset: str,
    pipeline: str | None = None,
    protocol: str | None = None,
) -> pd.Series:
    """One aggregate cell from the bundle."""

    frame = bundle.rows
    frame = frame[frame["track"] == track]
    if pipeline is not None:
        frame = frame[frame["pipeline"] == pipeline]
    if protocol is not None:
        frame = frame[frame["protocol"] == protocol]
    frame = frame[frame["subset"] == subset]
    if frame.empty:
        raise KeyError(f"no cell for {track!r}/{subset!r}/{pipeline!r}/{protocol!r}")
    if len(frame) > 1:
        raise KeyError(
            f"ambiguous cell for {track!r}/{subset!r}: "
            f"{len(frame)} rows (pass pipeline/protocol)"
        )
    return frame.iloc[0]


def random_band(
    bundle: Bundle,
    track: str,
    k: int,
    pipeline: str | None = None,
    protocol: str | None = None,
) -> dict:
    """Min/mean/max over random-subset seeds at a fixed k."""

    bands = bundle.raw.get("randomBands") or []
    hits = [
        b
        for b in bands
        if b["track"] == track
        and int(b["k"]) == int(k)
        and (pipeline is None or b["pipeline"] == pipeline)
        and (protocol is None or b["protocol"] == protocol)
    ]
    if not hits:
        raise KeyError(f"no random band for {track!r} k={k}")
    return max(hits, key=lambda b: b["nSeeds"])


def best_reduced(
    bundle: Bundle,
    track: str,
    pipeline: str | None = None,
    protocol: str | None = None,
    k_min: int | None = None,
    k_max: int | None = None,
    strategies: tuple[str, ...] = ("region", "distributed", "wearable"),
) -> pd.Series | None:
    """Highest-scoring non-random montage inside a k window."""

    frame = bundle.rows
    frame = frame[frame["track"] == track]
    if pipeline is not None:
        frame = frame[frame["pipeline"] == pipeline]
    if protocol is not None:
        frame = frame[frame["protocol"] == protocol]
    frame = frame[frame["strategy"].isin(strategies)]
    if k_min is not None:
        frame = frame[frame["k"] >= k_min]
    if k_max is not None:
        frame = frame[frame["k"] <= k_max]
    if frame.empty:
        return None
    return frame.loc[frame["score"].idxmax()]


# ---------------------------------------------------------------------------
# Raw per-subject rows (paired statistics)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def load_results() -> pd.DataFrame:
    """Every non-summary CSV under ``results/benchmark`` as one frame."""

    frames = []
    for path in sorted(BENCHMARK_DIR.glob("*.csv")):
        if path.stem.endswith("_summary"):
            continue
        frame = pd.read_csv(path)
        track, _, protocol_from_name = path.stem.partition("__")
        frame["track"] = track
        if "protocol" not in frame.columns or frame["protocol"].isna().all():
            frame["protocol"] = protocol_from_name or "within_session"
        frames.append(frame)
    if not frames:
        raise FileNotFoundError(f"no result CSVs in {BENCHMARK_DIR}")
    combined = pd.concat(frames, ignore_index=True)
    if "metric" not in combined.columns:
        combined["metric"] = "roc_auc"
    return combined


@lru_cache(maxsize=1)
def load_permutation_controls() -> pd.DataFrame:
    """Per-subject permutation controls from ``results/perm_control_*.csv``."""

    frames = []
    for path in sorted(RESULTS.glob("perm_control_*.csv")):
        frame = pd.read_csv(path)
        if "track" not in frame.columns:
            continue
        if "ear_vs_scalp_8ch" in frame["track"].unique():
            frame = frame[frame["track"] != "ear_vs_scalp_8ch"]
        frame = frame.copy()
        frame["source"] = path.name
        frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def unit_columns(frame: pd.DataFrame) -> list[str]:
    """Pairing unit: subject, plus session when the dataset has sessions."""

    cols = ["subject"]
    if "session" in frame.columns:
        values = frame["session"].dropna().unique()
        if len(values) > 1:
            cols.append("session")
    return cols


def unit_series(
    frame: pd.DataFrame,
    track: str,
    subset: str,
    pipeline: str | None = None,
    protocol: str | None = None,
    trial_seconds: float | None = None,
) -> pd.Series:
    """Mean score per pairing unit for one subset (seeds averaged).

    ``trial_seconds`` selects one decision window for tasks scored at several
    (auditory attention). Without it the groupby would average across windows
    and quietly compare the wrong numbers.
    """

    sub = frame[frame["track"] == track]
    if pipeline is not None:
        sub = sub[sub["pipeline"] == pipeline]
    if protocol is not None:
        sub = sub[sub["protocol"] == protocol]
    if trial_seconds is not None and "trial_seconds" in sub.columns:
        sub = sub[sub["trial_seconds"] == trial_seconds]
    sub = sub[sub["subset"] == subset]
    if sub.empty:
        raise KeyError(f"no raw rows for {track!r}/{subset!r}")
    cols = unit_columns(sub)
    series = sub.groupby(cols, dropna=False)["score"].mean()
    series.name = subset
    return series


@dataclass(frozen=True)
class DeltaStats:
    """Paired difference between two conditions on the same units.

    The interval is a paired t interval (95%), which is the interval the
    benchmark's README quotes.
    """

    n: int
    mean_a: float
    mean_b: float
    delta: float
    sd: float
    sem: float
    half_width: float
    t_stat: float
    p_value: float
    n_negative: int
    n_positive: int

    @property
    def ci(self) -> tuple[float, float]:
        return (self.delta - self.half_width, self.delta + self.half_width)

    def ci_text(self, digits: int = 3) -> str:
        low, high = self.ci
        return _minus(f"[{low:.{digits}f}, {high:.{digits}f}]")

    def sign_summary(self) -> str:
        if self.n_negative >= self.n_positive:
            return f"{self.n_negative}/{self.n} negative"
        return f"{self.n_positive}/{self.n} positive"


def delta_stats(table: pd.DataFrame, column_a: str = "a", column_b: str = "b") -> DeltaStats:
    """Compute paired statistics for two columns of the same table."""

    a = table[column_a].astype(float)
    b = table[column_b].astype(float)
    delta = b - a
    n = int(len(delta))
    mean_a = float(a.mean())
    mean_b = float(b.mean())
    mean_delta = float(delta.mean())
    sd = float(delta.std(ddof=1)) if n > 1 else float("nan")
    sem = sd / np.sqrt(n) if n else float("nan")
    if n > 1:
        half = float(stats.t.ppf(0.975, n - 1) * sem)
        t_stat = mean_delta / sem if sem else float("nan")
        p_value = float(2 * stats.t.sf(abs(t_stat), n - 1))
    else:
        half = float("nan")
        t_stat = float("nan")
        p_value = float("nan")
    return DeltaStats(
        n=n,
        mean_a=mean_a,
        mean_b=mean_b,
        delta=mean_delta,
        sd=sd,
        sem=sem,
        half_width=half,
        t_stat=t_stat,
        p_value=p_value,
        n_negative=int((delta < 0).sum()),
        n_positive=int((delta > 0).sum()),
    )


def unit_table(
    track: str,
    specs: list[tuple[str, str | None, str]],
    protocol: str | None = None,
    frame: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Align several unit series on the same participants.

    ``specs`` is a list of ``(column name, pipeline, subset)``; every series is
    reduced to one value per pairing unit (seeds averaged) and the result keeps
    only units present in all of them.
    """

    frame = load_results() if frame is None else frame
    columns = {
        name: unit_series(frame, track, subset, pipeline=pipeline, protocol=protocol)
        for name, pipeline, subset in specs
    }
    table = pd.concat(columns, axis=1, join="inner")
    table.columns = [name for name, _p, _s in specs]
    return table


def resolve_protocol(track: str, subset: str, frame: pd.DataFrame | None = None) -> str:
    """The protocol a track is reported with (its only one, in practice)."""

    frame = load_results() if frame is None else frame
    return str(frame[(frame["track"] == track) & (frame["subset"] == subset)]["protocol"].iloc[0])


@dataclass(frozen=True)
class Paired:
    """Paired comparison between two matched-k subsets."""

    track: str
    pipeline: str
    protocol: str
    subset_a: str
    subset_b: str
    label_a: str
    label_b: str
    metric: str
    metric_label: str
    per_unit: pd.DataFrame  # index = units, columns = a, b, delta
    stats: DeltaStats

    @property
    def n(self) -> int:
        return self.stats.n

    @property
    def mean_a(self) -> float:
        return self.stats.mean_a

    @property
    def mean_b(self) -> float:
        return self.stats.mean_b

    @property
    def delta(self) -> float:
        return self.stats.delta

    @property
    def ci(self) -> tuple[float, float]:
        return self.stats.ci

    @property
    def p_value(self) -> float:
        return self.stats.p_value

    @property
    def n_negative(self) -> int:
        return self.stats.n_negative

    @property
    def n_positive(self) -> int:
        return self.stats.n_positive

    def sign_summary(self) -> str:
        return self.stats.sign_summary()

    def ci_text(self, digits: int = 3) -> str:
        return self.stats.ci_text(digits)


def paired(
    track: str,
    subset_a: str,
    subset_b: str,
    pipeline: str | None = None,
    protocol: str | None = None,
    label_a: str | None = None,
    label_b: str | None = None,
    frame: pd.DataFrame | None = None,
    trial_seconds: float | None = None,
) -> Paired:
    """Pair two subsets unit-by-unit and return the paired statistics."""

    frame = load_results() if frame is None else frame
    bundle = load_bundle()
    task = bundle.task(track)
    # Resolve the protocol first: leaving it None would merge a task's
    # same-session and cross-session rows into one number.
    protocol = protocol or resolve_protocol(track, subset_a, frame)
    if pipeline is None:
        pipeline = str(
            frame[
                (frame["track"] == track)
                & (frame["subset"] == subset_a)
                & (frame["protocol"] == protocol)
            ]["pipeline"].iloc[0]
        )
    a = unit_series(frame, track, subset_a, pipeline=pipeline,
                    protocol=protocol, trial_seconds=trial_seconds)
    b = unit_series(frame, track, subset_b, pipeline=pipeline,
                    protocol=protocol, trial_seconds=trial_seconds)
    # Align by pairing unit; the intersection is what "paired" means.
    table = pd.concat([a, b], axis=1, join="inner")
    table.columns = ["a", "b"]
    table["delta"] = table["b"] - table["a"]
    resolved = {}
    for subset in (subset_a, subset_b):
        row = cell(bundle, track, subset, pipeline=pipeline, protocol=protocol)
        resolved[subset] = row["subsetLabel"]
    return Paired(
        track=track,
        pipeline=pipeline,
        protocol=protocol,
        subset_a=subset_a,
        subset_b=subset_b,
        label_a=label_a or resolved[subset_a],
        label_b=label_b or resolved[subset_b],
        metric=str(task["metric"]),
        metric_label=task["metricLabel"],
        per_unit=table,
        stats=delta_stats(table),
    )


# ---------------------------------------------------------------------------
# Formatting helpers (shared by figures and the generated tables)
# ---------------------------------------------------------------------------


MINUS = "\u2212"  # typographic minus, used in every printed number


def _minus(text: str) -> str:
    return text.replace("-", MINUS)


def fmt(value: float | None, digits: int = 3) -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "—"
    return _minus(f"{value:.{digits}f}")


def fmt_delta(value: float, digits: int = 3) -> str:
    if not np.isfinite(value):
        return "—"
    sign = MINUS if value < 0 else "+"
    return f"{sign}{abs(value):.{digits}f}"


def pct(part: float, whole: float, digits: int = 1) -> float:
    return 100.0 * part / whole if whole else float("nan")


def ci_digits(metric: str) -> int:
    return 2 if metric == "kappa" else 3
