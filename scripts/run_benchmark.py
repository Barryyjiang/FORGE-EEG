"""Run the benchmark suite.

Iterates the tracks in :mod:`eegbench.suite`, evaluates every montage with every
registered decoder, and writes one CSV per (track, protocol) into
``results/benchmark``. :mod:`eegbench.leaderboard` then aggregates them.

Examples
--------
    .\\.venv\\Scripts\\python.exe scripts\\run_benchmark.py --list
    .\\.venv\\Scripts\\python.exe scripts\\run_benchmark.py --suite mi_leftright_22ch --subjects 2
    .\\.venv\\Scripts\\python.exe scripts\\run_benchmark.py --suite all
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import pandas as pd  # noqa: E402

from eegbench import suite  # noqa: E402
from eegbench.benchmark import dataset_channels, sweep  # noqa: E402
from eegbench.datasets import configure_download_provider, promote_channels  # noqa: E402
from eegbench.pipelines import available as available_pipelines  # noqa: E402
from eegbench.pipelines import build as build_pipelines  # noqa: E402
from eegbench.specs import build_specs  # noqa: E402


def build_dataset(key: str, subjects: int | None, subject_ids: list[int] | None):
    import moabb.datasets as md

    cls_name = suite.DATASETS[key]
    dataset = getattr(md, cls_name)()
    if subject_ids:
        dataset.subject_list = list(subject_ids)
    elif subjects:
        dataset.subject_list = dataset.subject_list[:subjects]
    return dataset


def print_tracks() -> None:
    for status, tracks in suite.by_status().items():
        print(f"\n[{status}]")
        for t in tracks:
            size = f"  ({t.appro_download})" if t.appro_download else ""
            print(f"  {t.name:28s} {t.dataset:16s} {t.paradigm:9s} "
                  f"ks={t.ks} wearables={t.wearables}{size}")
            if t.note:
                print(f"      {t.note}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--suite", default="all",
                   help="'all' (ready tracks) or comma-separated track names")
    p.add_argument("--subjects", type=int, default=None)
    p.add_argument("--subject-ids", default=None)
    p.add_argument("--pipelines", default=None,
                   help=f"override decoders; available: {available_pipelines()}")
    p.add_argument("--n-random", type=int, default=3)
    p.add_argument("--protocols", default=None,
                   help="override the track's protocols, e.g. cross_session")
    p.add_argument("--out-dir", type=Path, default=Path("results/benchmark"))
    p.add_argument("--overwrite", action="store_true",
                   help="re-run even if the output file already exists")
    p.add_argument("--reuse-cache", action="store_true",
                   help="allow MOABB's on-disk result cache (default: force "
                        "recompute). Stale cache entries return results labelled "
                        "with whatever pipeline name wrote them first, which "
                        "corrupts the leaderboard.")
    p.add_argument("--list", action="store_true", help="show tracks and exit")
    p.add_argument("--download-provider", default="upstream",
                   choices=["auto", "nemar", "upstream"])
    args = p.parse_args()

    if args.list:
        print_tracks()
        return 0

    import moabb.evaluations as moabb_evaluations
    import moabb.paradigms as moabb_paradigms
    import mne

    mne.set_log_level("ERROR")
    configure_download_provider(args.download_provider)

    if args.suite == "all":
        tracks = suite.ready()
    else:
        tracks = [suite.get(n.strip()) for n in args.suite.split(",") if n.strip()]

    subject_ids = (
        [int(s) for s in args.subject_ids.split(",") if s.strip()]
        if args.subject_ids else None
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for track in tracks:
        paradigm_cls = getattr(moabb_paradigms, suite.PARADIGMS[track.paradigm])
        names = (
            tuple(p.strip() for p in args.pipelines.split(",") if p.strip())
            if args.pipelines else track.pipelines
        )

        for protocol in (
            [p.strip() for p in args.protocols.split(",") if p.strip()]
            if args.protocols else track.protocols
        ):
            out = args.out_dir / f"{track.name}__{protocol}.csv"
            if out.exists() and not args.overwrite:
                print(f"{out.name}: exists, skipping (use --overwrite)")
                continue

            print(f"\n=== {track.name} / {protocol} ===")
            dataset = build_dataset(track.dataset, args.subjects, subject_ids)
            if track.promote:
                promote_channels(dataset, track.promote)
                print(f"  promoted to EEG: {list(track.promote)}")

            # CCA cannot infer stimulus frequencies once MOABB encodes labels,
            # so register the map before the pipeline is built.
            if "ssvep_cca" in names:
                from eegbench.pipelines import set_ssvep_frequencies

                freq_map = set_ssvep_frequencies(list(dataset.event_id.keys()))
                print(f"  ssvep freq_map ({len(freq_map)} classes)")

            pipelines = build_pipelines(names)
            available = dataset_channels(dataset, allow_download=True)
            specs = build_specs(
                available, track.ks, wearables=track.wearables, n_random=args.n_random
            )
            print(f"  dataset={track.dataset} subjects={len(dataset.subject_list)} "
                  f"channels={len(available)} subsets={len(specs)} "
                  f"pipelines={list(pipelines)}")

            evaluation_cls = getattr(moabb_evaluations, suite.PROTOCOLS[protocol])
            paradigm_kwargs = dict(track.paradigm_kwargs)
            if track.scorer:
                paradigm_kwargs["scorer"] = track.scorer

            df = sweep(
                dataset, paradigm_cls, specs, pipelines,
                evaluation_cls=evaluation_cls, available=available,
                paradigm_kwargs=paradigm_kwargs,
                evaluation_kwargs={
                    "overwrite": not args.reuse_cache,
                    "return_epochs": track.return_epochs,
                },
            )
            df["metric"] = track.metric
            df["track"] = track.name
            df["protocol"] = protocol
            df["dataset_key"] = track.dataset

            meta = getattr(dataset, "metadata", None)
            trial_seconds = getattr(
                getattr(meta, "experiment", None), "trial_duration", None
            )
            df["trial_seconds"] = trial_seconds
            df.to_csv(out, index=False)
            print(f"  wrote {out} ({len(df)} rows)")

    print("\nAggregate with:"
          f"\n  .\\.venv\\Scripts\\python.exe scripts\\leaderboard.py --dir {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
