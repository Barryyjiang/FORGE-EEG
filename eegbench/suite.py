"""The benchmark definition.

A *track* is one (dataset, paradigm, protocol) combination with the montage
sizes and decoders to run on it. The suite is the whole list. This is
deliberately declarative: adding a dataset or a protocol is a data change, not
new code, which is what makes the benchmark extensible instead of a pile of
bespoke scripts.

Tracks carry a ``status``:

- ``ready``           runs here today
- ``needs_download``  defined, not yet fetched (size noted)
- ``excluded``        known-unsuitable; kept visible so nobody re-adds it
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
        note="6-class SSVEP, 8 electrodes. Accuracy is scored (not AUC) so that "
             "ITR is computable: this is the paradigm where bits/min, not AUC, "
             "decides whether a wearable is usable.",
        metric="accuracy",
        scorer="accuracy",
        pipelines=("ssvep_cca",),
        return_epochs=True,
    ),
    _t(
        name="cvep_trial_level",
        dataset="castillos_cvep40",
        paradigm="cvep",
        ks=(8, 16),
        status="excluded",
        note="Excluded after verification: the CVEP paradigm returns 2 classes "
             "('0','1' stimulus bits, 7020 epochs) even for datasets that ship "
             "trial-level command labels. Command-level c-VEP needs custom "
             "epoching from the dataset's internal cvep_data, which MOABB does "
             "not expose as events. Verified 2026-11 on CastillosCVEP40.",
    ),
    _t(
        name="sleep_staging_ear",
        dataset="openneuro_ds004348",
        paradigm="fixed_interval_windows",
        status="needs_adapter",
        task_type="regression",
        metric="kappa",
        pipelines=("bandpower_ridge",),
        note="Ear-EEG sleep staging (OpenNeuro ds004348, 9 subjects, 14 ear "
             "electrodes). The canonical wearable continuous task — and the one "
             "task family where ear-EEG has strong published results. Missing: "
             "no MOABB dataset and no fixed-interval paradigm that emits a "
             "continuous hypnogram target. Needs a BIDS adapter (~50 lines) "
             "plus annotation parsing; the metric and regression decoder are "
             "already in place.",
    ),
    _t(
        name="motor_execution_ear_vs_scalp",
        dataset="wu2020",
        paradigm="leftright",
        ks=(8,),
        wearables=True,
        promote=WU2020_EAR,
        note="Simultaneous 122-channel cap + 8 in-ear electrodes. The only "
             "ready track where 'wrong site' is testable directly. ~8 GB.",
    ),
    _t(
        name="ssvep_mobile_ear",
        dataset="lee2021_ssvep",
        paradigm="ssvep",
        ks=(4, 8, 16),
        wearables=True,
        status="needs_download",
        note="32 scalp + 14 ear while standing/walking/running. Ear channel "
             "names are only knowable after download.",
        appro_download="multi-GB",
    ),
    _t(
        name="p300_mobile_ear",
        dataset="lee2021_erp",
        paradigm="p300",
        ks=(4, 8, 16),
        wearables=True,
        status="needs_download",
        note="Same rig, ERP paradigm. Pairs with the SSVEP track.",
        appro_download="multi-GB",
    ),
    _t(
        name="cvep_dense_vs_lowchannel",
        dataset="thielen2015",
        paradigm="cvep",
        status="excluded",
        note="Excluded: Thielen event ids are stimulus bit on/off, so CVEP "
             "yields 2 classes and LogVar/LDA sits at AUC 0.5 by construction. "
             "Needs template matching / CCA before it is a classification task.",
    ),
    _t(
        name="cvep_lowchannel",
        dataset="thielen2021",
        paradigm="cvep",
        status="excluded",
        note="Same c-VEP event-marker problem as thielen2015.",
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
