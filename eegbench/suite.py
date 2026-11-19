"""The benchmark definition.

A *track* is one (dataset, paradigm, protocol) combination with the montage
sizes and decoders to run on it. The suite is the whole list. This is
deliberately declarative: adding a dataset or a protocol is a data change, not
new code, which is what makes the benchmark extensible instead of a pile of
bespoke scripts.

Every track in the suite is ``ready`` and backed by a result CSV in
``results/benchmark/``. Incomplete or out-of-scope paradigms are not listed:
a public benchmark should not ship rows that are explicitly labelled
"not tested".

The suite covers four of the five published tasks. The fifth, sleep staging, is
not a MOABB paradigm: it is read from a BIDS recording and defined in
``scripts/sleep_track.py``, which writes
``results/benchmark/sleep_staging_local__within_session.csv`` in the same schema
so the leaderboard treats it like any other track.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: dataset key -> MOABB class name
DATASETS: dict[str, str] = {
    "bnci2014_001": "BNCI2014_001",
    "bnci2014_008": "BNCI2014_008",
    "nakanishi2015": "Nakanishi2015",
    "castillos_cvep40": "CastillosCVEP40",
    "wu2020": "Wu2020",
    "thielen2015": "Thielen2015",
    "thielen2021": "Thielen2021",
    "lee2021_ssvep": "Lee2021Mobile_SSVEP",
    "lee2021_erp": "Lee2021Mobile_ERP",
}

#: paradigm key -> MOABB class name
PARADIGMS: dict[str, str] = {
    "cvep": "CVEP",
    "ssvep": "SSVEP",
    "p300": "P300",
    "leftright": "LeftRightImagery",
    "motor": "MotorImagery",
}

#: protocol key -> MOABB evaluation class name
PROTOCOLS: dict[str, str] = {
    "within_session": "WithinSessionEvaluation",
    "cross_session": "CrossSessionEvaluation",
    "cross_subject": "CrossSubjectEvaluation",
}

#: In-ear channels Wu2020 stores as ``misc``; must be promoted to ``eeg``.
WU2020_EAR: tuple[str, ...] = ("LF", "LB", "LOU", "LOD", "RF", "RB", "ROU", "ROD")


@dataclass(frozen=True)
class Track:
    name: str
    dataset: str
    paradigm: str
    ks: tuple[int, ...] = ()
    wearables: bool = True
    protocols: tuple[str, ...] = ("within_session",)
    pipelines: tuple[str, ...] = ("logvar_lda", "csp_lda", "riemann_tslr")
    promote: tuple[str, ...] = ()
    status: str = "ready"
    note: str = ""
    appro_download: str = ""  # human-readable size, for needs_download tracks
    #: scoring metric name from :mod:`eegbench.metrics`
    metric: str = "roc_auc"
    #: MOABB scorer override; needed when ``metric`` is accuracy so that ITR is
    #: computable rather than approximated from an AUC.
    scorer: str | None = None
    #: extra kwargs for the paradigm constructor
    paradigm_kwargs: dict = field(default_factory=dict)
    #: "classification" | "regression"
    task_type: str = "classification"
    #: pass MNE Epochs (not arrays) to the pipeline; required by SSVEP_CCA
    return_epochs: bool = False

    def specs_args(self) -> dict:
        return {"ks": self.ks, "wearables": self.wearables}


def _t(**kw) -> Track:
    return Track(**kw)


SUITE: tuple[Track, ...] = (
    _t(
        name="mi_leftright_22ch",
        dataset="bnci2014_001",
        paradigm="leftright",
        ks=(4, 8, 16),
        wearables=False,
        note="Dense cap, binary MI. Tests count-vs-placement where a focal "
             "source is known. ~1.1 GB for all 9 subjects.",
    ),
    _t(
        name="mi_4class_22ch",
        dataset="bnci2014_001",
        paradigm="motor",
        ks=(4, 8, 16),
        wearables=False,
        # Four classes need a selection accuracy, so AUC is not the metric and
        # chance is 1/4 rather than 1/2.
        metric="accuracy",
        scorer="accuracy",
        paradigm_kwargs={"n_classes": 4},
        note="The same cap and the same nine people as mi_leftright_22ch, but "
             "four classes (left hand, right hand, feet, tongue). Class count is "
             "the axis this track adds: feet and tongue are midline and central, "
             "so a lateralised sensorimotor patch should lose far more here than "
             "it does on two classes. Reuses the cached BNCI2014_001 download.",
    ),
    _t(
        name="p300_8ch",
        dataset="bnci2014_008",
        paradigm="p300",
        ks=(4, 8),
        wearables=False,
        note="P300 speller, 8 electrodes — already wearable-scale. Tests whether "
             "a headband-sized montage reaches full-cap P300 performance.",
        pipelines=("xdawn_tslr", "logvar_lda"),
    ),
    _t(
        name="ssvep_8ch",
        dataset="nakanishi2015",
        paradigm="ssvep",
        ks=(4, 8),
        wearables=False,
        note="12-class SSVEP, 8 electrodes. Accuracy is scored (not AUC) so that "
             "ITR is computable: this is the paradigm where bits/min, not AUC, "
             "decides whether a wearable is usable.",
        metric="accuracy",
        scorer="accuracy",
        pipelines=("ssvep_cca",),
        return_epochs=True,
    ),
    _t(
        name="motor_execution_ear_vs_scalp",
        dataset="wu2020",
        paradigm="leftright",
        ks=(8,),
        wearables=True,
        promote=WU2020_EAR,
        note="Simultaneous 115-channel scalp EEG cap + 8 in-ear electrodes. "
             "The only track where 'wrong site' is testable directly. ~8 GB.",
    ),
)


def get(name: str) -> Track:
    for track in SUITE:
        if track.name == name:
            return track
    raise KeyError(f"unknown track {name!r}; available: {[t.name for t in SUITE]}")


def ready() -> list[Track]:
    return [t for t in SUITE if t.status == "ready"]


def by_status() -> dict[str, list[Track]]:
    out: dict[str, list[Track]] = {}
    for track in SUITE:
        out.setdefault(track.status, []).append(track)
    return out
