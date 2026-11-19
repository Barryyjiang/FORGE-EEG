"""Build every paper figure.

    .\\.venv\\Scripts\\python.exe figures\\build_figures.py
    .\\.venv\\Scripts\\python.exe figures\\build_figures.py --only fig4

Each figure is written to ``docs/assets/figures/`` as PNG (for the page) and
PDF (vector, for print). The scripts read ``docs/data/benchmark.json`` and
``results/benchmark/*.csv`` only.
"""

from __future__ import annotations

import argparse
import importlib
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

MODULES = [
    "plot_fig1_overview",
    "plot_fig2_channel_budget",
    "plot_fig3_placement",
    "plot_fig4_wearable_gap",
    "plot_fig5_decoder",
    "plot_fig6_controls",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        action="append",
        default=None,
        help="build only figures whose module name contains this string "
        "(repeatable), e.g. --only fig4",
    )
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args(argv)

    selected = [
        name
        for name in MODULES
        if not args.only or any(token in name for token in args.only)
    ]
    if not selected:
        parser.error(f"no figure matches {args.only}")

    failures = 0
    for name in selected:
        module = importlib.import_module(name)
        start = time.perf_counter()
        try:
            paths = module.build(dpi=args.dpi)
        except Exception as exc:  # keep going: one bad figure is not fatal
            failures += 1
            print(f"FAILED {name}: {type(exc).__name__}: {exc}")
            continue
        elapsed = time.perf_counter() - start
        for path in paths:
            size = path.stat().st_size / 1024
            print(f"{path.relative_to(HERE.parent)}  ({size:.0f} KB)")
        print(f"  {name}: {elapsed:.1f}s")

    if failures:
        print(f"\n{failures} figure(s) failed")
        return 1
    print(f"\n{len(selected)} figure(s) rebuilt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
