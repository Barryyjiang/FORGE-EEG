"""Signal-quality axis, computed on raw continuous data.

    .\\.venv\\Scripts\\python.exe scripts\\signal_quality.py --track mi_leftright_22ch --subjects 3

Deliberately bypasses the paradigm: quality must be measured before band-pass
filtering, or the mains frequency is gone and artefact thresholds mean nothing.
"""

from __future__ import annotations

import argparse
import warnings

import numpy as np
import pandas as pd

from eegbench import suite
from eegbench.quality import signal_quality

warnings.filterwarnings("ignore")


def _raws_for(dataset, subject):
    """Yield every Raw for a subject, whatever the nesting convention."""
    def walk(obj):
        if hasattr(obj, "get_data") and hasattr(obj, "info"):
            yield obj
        elif isinstance(obj, dict):
            for value in obj.values():
                yield from walk(value)

    yield from walk(dataset.get_data([subject])[subject])


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--track", required=True)
    p.add_argument("--subjects", type=int, default=None)
    p.add_argument("--line-freq", type=float, default=50.0)
    p.add_argument("--reject-uv", type=float, default=150.0)
    p.add_argument("--out", default="results/signal_quality.csv")
    args = p.parse_args()

    import mne
    import moabb.datasets as md

    from eegbench.benchmark import dataset_channels
    from eegbench.datasets import configure_download_provider
    from eegbench.specs import build_specs

    mne.set_log_level("ERROR")
    configure_download_provider("upstream")

    track = suite.get(args.track)
    dataset = getattr(md, suite.DATASETS[track.dataset])()
    if args.subjects:
        dataset.subject_list = dataset.subject_list[: args.subjects]

    available = dataset_channels(dataset, allow_download=True)
    specs = build_specs(available, track.ks, wearables=track.wearables, n_random=1)

    rows = []
    for spec in specs:
        present = [c for c in spec.channels if c in available]
        if len(present) < 2:
            continue
        print(f"[{spec.name}] {len(present)} ch", flush=True)

        per_subject = []
        for subject in dataset.subject_list:
            for raw in _raws_for(dataset, subject):
                names = raw.info["ch_names"]
                picks = [names.index(c) for c in present if c in names]
                if len(picks) < 2:
                    continue
                X = raw.get_data(picks=picks)
                per_subject.append(
                    signal_quality(
                        X, raw.info["sfreq"],
                        line_freq=args.line_freq, reject_uv=args.reject_uv,
                    )
                )

        if not per_subject:
            continue
        agg = pd.DataFrame(per_subject).mean(numeric_only=True)
        rows.append({
            "track": track.name,
            "subset": spec.name,
            "strategy": spec.strategy,
            "k": len(present),
            **{key: agg[key] for key in (
                "reject_rate", "line_noise_ratio",
                "effective_rank", "mean_abs_corr", "median_p2p_uv",
            )},
        })

    df = pd.DataFrame(rows).sort_values(["k", "strategy"])
    df.to_csv(args.out, index=False)
    with pd.option_context("display.width", 200):
        print(df.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
