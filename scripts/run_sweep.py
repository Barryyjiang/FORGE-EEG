"""Run an electrode-subset sweep.

Examples
--------
Offline self-test (no download, ~1 minute)::

    .\\.venv\\Scripts\\python.exe scripts\\run_sweep.py --fake --out results/fake.csv

Equal-N comparison on a real dense dataset (downloads data)::

    .\\.venv\\Scripts\\python.exe scripts\\run_sweep.py ^
        --dataset thielen2015 --ks 4,8,16,24 --subjects 3 ^
        --allow-download --out results/thielen2015.csv

Wearable montages only::

    .\\.venv\\Scripts\\python.exe scripts\\run_sweep.py ^
        --dataset thielen2015 --mode wearables --allow-download
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from eegbench.benchmark import dataset_channels, summarise, sweep
from eegbench.montages import REGIONS, WEARABLES
from eegbench.names import match_channels
from eegbench.subsets import equal_n_specs, full_spec, wearable_spec

# dataset key -> (factory, default paradigm key)
DATASETS = {
    "bnci2014_001": ("BNCI2014_001", "leftright"),
    "thielen2015": ("Thielen2015", "cvep"),
    "thielen2021": ("Thielen2021", "cvep"),
    "wu2020": ("Wu2020", "leftright"),
    "lee2021_ssvep": ("Lee2021Mobile_SSVEP", "ssvep"),
    "lee2021_erp": ("Lee2021Mobile_ERP", "p300"),
}
PARADIGMS = {
    "cvep": "CVEP",
    "ssvep": "SSVEP",
    "p300": "P300",
    "leftright": "LeftRightImagery",
    "motor": "MotorImagery",
}


def build_dataset(key: str, *, subjects: int | None, subject_ids: list[int] | None,
                  fake: bool):
    if fake:
        from moabb.datasets.fake import FakeDataset

        # A spread of 10-10 names so region and distributed subsets differ.
        return FakeDataset(
            channels=(
                "F3", "F4", "Fz", "C3", "C4", "Cz", "CP3", "CP4",
                "P3", "P4", "Pz", "O1", "O2", "Oz",
            ),
            event_list=("left_hand", "right_hand"),
            paradigm="imagery",
            n_subjects=subjects or 3,
            n_sessions=1,
            n_runs=1,
            duration=120,
            sfreq=128,
            seed=42,
        )

    from moabb import datasets as moabb_datasets

    cls_name = DATASETS[key][0]
    cls = getattr(moabb_datasets, cls_name)
    ds = cls()
    if subject_ids:
        missing = [s for s in subject_ids if s not in ds.subject_list]
        if missing:
            raise ValueError(f"{key} has no subject(s) {missing}; "
                             f"available: {ds.subject_list}")
        ds.subject_list = list(subject_ids)
    elif subjects:
        ds.subject_list = ds.subject_list[:subjects]
    return ds


def build_paradigm(key: str):
    import moabb.paradigms as moabb_paradigms

    return getattr(moabb_paradigms, PARADIGMS[key])


def build_pipelines(which: str = "logvar,csp"):
    """Classifiers to compare. CSP is the field standard for motor imagery."""
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
    from sklearn.pipeline import make_pipeline

    from moabb.pipelines.features import LogVariance

    wanted = {w.strip() for w in which.split(",") if w.strip()}
    out = {}
    if "logvar" in wanted:
        out["LogVar+LDA"] = make_pipeline(LogVariance(), LDA())
    if "csp" in wanted:
        from mne.decoding import CSP

        out["CSP+LDA"] = make_pipeline(CSP(n_components=4, log=True), LDA())
    if not out:
        raise ValueError(f"no known pipeline in {which!r}")
    return out


def main(argv: list[str] | None = None) -> int:
    import warnings

    # Third-party noise: MOABB writes an HDF5 cache, h5py warns about it, and
    # MNE complains about MOABB's config key. None of it is actionable.
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", message=".*non-standard config type.*")
    warnings.filterwarnings("ignore", message=".*Creating a dataset without.*")
    import mne

    mne.set_log_level("ERROR")

    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dataset", default="fake", choices=[*DATASETS, "fake"])
    p.add_argument("--fake", action="store_true",
                   help="alias for --dataset fake (offline self-test)")
    p.add_argument("--paradigm", choices=list(PARADIGMS), default=None,
                   help="defaults to the dataset's natural paradigm")
    p.add_argument("--subjects", type=int, default=None,
                   help="limit to the first N subjects")
    p.add_argument("--subject-ids", default=None,
                   help="comma-separated subject ids, e.g. 4 or 4,6 "
                        "(avoids pulling subjects you do not need)")
    p.add_argument("--ks", default="4,8,16", help="comma-separated channel counts")
    p.add_argument("--mode", choices=["equal_n", "wearables", "both"], default="equal_n")
    p.add_argument("--random-seeds", type=int, default=3,
                   help="number of random-subset control conditions")
    p.add_argument("--pipelines", default="logvar,csp",
                   help="comma-separated: logvar, csp")
    p.add_argument("--min-channels", type=int, default=2)
    p.add_argument("--allow-download", action="store_true",
                   help="read channel names from data if metadata lacks them")
    p.add_argument("--promote", default=None,
                   help="comma-separated channels to re-type as EEG, e.g. "
                        "LF,LB,LOU,LOD,RF,RB,ROU,ROD for Wu2020's in-ear set")
    p.add_argument("--download-provider", default="upstream",
                   choices=["auto", "nemar", "upstream"],
                   help="'upstream' avoids MOABB mirroring every dataset into a "
                        "NEMAR store (roughly halves disk use)")
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--list", action="store_true", help="list montages and exit")
    p.add_argument("--paths", action="store_true",
                   help="show where data/caches are stored and exit")
    args = p.parse_args(argv)

    if args.paths:
        from eegbench.paths import describe

        print(describe())
        return 0

    if args.list:
        print("regions:", ", ".join(sorted(REGIONS)))
        for name, m in WEARABLES.items():
            print(f"  {name:16s} {m.n_channels:2d}ch {m.fidelity:8s} {m.note}")
        return 0

    fake = args.dataset == "fake" or args.fake
    if fake:
        args.dataset = "fake"
    if not fake:
        from eegbench.datasets import configure_download_provider

        configure_download_provider(args.download_provider)
    paradigm_key = args.paradigm or ("leftright" if fake else DATASETS[args.dataset][1])
    subject_ids = (
        [int(s) for s in args.subject_ids.split(",") if s.strip()]
        if args.subject_ids else None
    )
    dataset = build_dataset(args.dataset, subjects=args.subjects,
                            subject_ids=subject_ids, fake=fake)

    if args.promote:
        from eegbench.datasets import promote_channels

        promoted = [c.strip() for c in args.promote.split(",") if c.strip()]
        promote_channels(dataset, promoted)
        print(f"promoted to EEG: {promoted}")

    paradigm_cls = build_paradigm(paradigm_key)

    available = dataset_channels(dataset, allow_download=args.allow_download)
    print(f"dataset   : {type(dataset).__name__} "
          f"({len(dataset.subject_list)} subjects, {len(available)} channels)")
    print(f"paradigm  : {paradigm_cls.__name__}")
    print(f"channels  : {available}")

    specs = []
    if args.mode in ("equal_n", "both"):
        ks = [int(k) for k in args.ks.split(",") if k.strip()]
        for k in ks:
            specs.extend(equal_n_specs(available, k, n_random=args.random_seeds))
        # The full cap is the ceiling every subset is compared against.
        from eegbench.montages import positions_for

        positioned = [c for c in available if c in positions_for(available)]
        if positioned:
            specs.append(full_spec(positioned))
    if args.mode in ("wearables", "both"):
        for m in WEARABLES.values():
            spec = wearable_spec(m, available)
            if spec is not None:
                specs.append(spec)

    if not specs:
        print("No subsets could be built from this dataset's channels.",
              file=sys.stderr)
        return 1

    # de-duplicate by (channels) while keeping the first label
    seen: set[tuple[str, ...]] = set()
    unique = []
    for s in specs:
        key = tuple(sorted(s.channels))
        if key not in seen:
            seen.add(key)
            unique.append(s)
    specs = unique

    print(f"subsets    : {len(specs)}")
    df = sweep(
        dataset,
        paradigm_cls,
        specs,
        build_pipelines(args.pipelines),
        available=available,
        min_channels=args.min_channels,
    )

    print()
    table = summarise(df)
    with pd.option_context("display.width", 160, "display.max_rows", 200):
        print(table.to_string(index=False))

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(args.out, index=False)
        table.to_csv(args.out.with_name(args.out.stem + "_summary.csv"), index=False)
        print(f"\nwrote {args.out} and {args.out.with_name(args.out.stem + '_summary.csv')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
