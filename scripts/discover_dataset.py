"""Inspect a MOABB dataset's real channel names and types.

Needed because several datasets leave ``metadata.acquisition.sensors`` empty,
so channel names are only knowable after downloading. Also reports which
channels have standard 10-10 positions, which determines whether they can
enter geometric subsetting.

Usage::

    .\\.venv\\Scripts\\python.exe scripts\\discover_dataset.py Wu2020 --subject 4
    .\\.venv\\Scripts\\python.exe scripts\\discover_dataset.py Lee2021Mobile_SSVEP --subject 1
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter

from eegbench.montages import positions_for


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("dataset", help="class name in moabb.datasets")
    p.add_argument("--subject", type=int, default=None,
                   help="subject to read (downloads data); defaults to subject_list[0]")
    p.add_argument("--max-print", type=int, default=200)
    args = p.parse_args()

    import moabb.datasets as ds

    if not hasattr(ds, args.dataset):
        print(f"no such dataset: {args.dataset}", file=sys.stderr)
        return 1

    dataset = getattr(ds, args.dataset)()
    subject = args.subject or dataset.subject_list[0]

    print(f"dataset  : {args.dataset}")
    print(f"subjects : {len(dataset.subject_list)} -> {dataset.subject_list}")
    print(f"events   : {dataset.event_id}")
    print(f"reading  : subject {subject} (downloads if absent)")

    data = dataset.get_data([subject])
    sessions = data[subject]
    session_id = next(iter(sessions))
    raw = next(iter(sessions[session_id].values()))

    names = raw.info["ch_names"]
    types = raw.get_channel_types()
    print(f"\nsession  : {session_id}")
    print(f"sfreq    : {raw.info['sfreq']} Hz")
    print(f"channels : {len(names)}")
    print(f"types    : {dict(Counter(types))}")

    print("\nchannels by type:")
    for ch_type in sorted(set(types)):
        group = [n for n, t in zip(names, types) if t == ch_type]
        shown = group[: args.max_print]
        suffix = "" if len(group) <= args.max_print else f" ... (+{len(group) - len(args.max_print)})"
        print(f"  {ch_type:6s} n={len(group):3d}: {', '.join(shown)}{suffix}")

    positioned = positions_for(names)
    eeg = [n for n, t in zip(names, types) if t == "eeg"]
    eeg_pos = [n for n in eeg if n in positioned]
    print(f"\n10-10 positions: {len(eeg_pos)}/{len(eeg)} EEG channels")
    missing = [n for n in eeg if n not in positioned]
    if missing:
        print(f"  no position ({len(missing)}): {', '.join(missing[:60])}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
