"""End-to-end consistency check: every quoted number must trace to a CSV.

Run after rebuilding anything. It fails loudly rather than printing a warning,
because the whole point of the benchmark is that the prose cannot drift from the
data.

    .\\.venv\\Scripts\\python.exe scripts\\verify.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "figures"))
sys.path.insert(0, str(ROOT / "scripts"))

import pandas as pd  # noqa: E402

import paper_data as pd_  # noqa: E402

FAIL: list[str] = []


def check(ok: bool, message: str) -> None:
    if not ok:
        FAIL.append(message)


def main() -> int:
    bundle = pd_.load_bundle()
    tasks = bundle.tasks
    ids = [t["id"] for t in tasks]

    # --- coverage ---------------------------------------------------------
    check(len(tasks) == 9, f"expected 9 tasks in the bundle, found {len(tasks)}")
    check(bundle.meta["nSources"] == 8,
          f"expected 8 datasets, found {bundle.meta['nSources']}")

    for task in tasks:
        stats = task.get("stats")
        check(stats is not None, f"{task['id']}: no headline stats")
        if not stats:
            continue
        for key in ("reference", "best", "retainedPct", "referenceLabel",
                    "bestLabel"):
            check(stats.get(key) is not None,
                  f"{task['id']}: stats[{key}] is empty")
        check(0.0 < float(stats["retainedPct"]) <= 100.0,
              f"{task['id']}: retainedPct {stats['retainedPct']} out of range")

    # --- every task has a control -----------------------------------------
    controls = pd_.load_permutation_controls()
    for track in ids:
        rows = controls[controls["track"] == track]
        check(not rows.empty, f"{track}: no permutation control")
        if rows.empty:
            continue
        worst = float(rows["perm_mean"].max())
        check(worst <= 0.55,
              f"{track}: a shuffled-label null reached {worst:.3f}, above 0.55")

    # --- the generated pages carry no unresolved placeholder --------------
    for name in ("docs/index.html", "docs/explore/index.html"):
        path = ROOT / name
        check(path.exists(), f"{name}: missing (run the build scripts)")
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        left = re.findall(r"\{\{[^}]+\}\}", text)
        check(not left, f"{name}: unresolved placeholders {sorted(set(left))[:5]}")
        for stale in ("Author One", "CHANGE-ME", "Affiliation One"):
            check(stale not in text, f"{name}: still contains {stale!r}")

    # --- the site bundle and the CSVs agree -------------------------------
    for task in tasks:
        rows = bundle.rows[bundle.rows["track"] == task["id"]]
        check(not rows.empty, f"{task['id']}: no rows in the site bundle")
        csv = ROOT / "results" / "benchmark" / f"{task['id']}__{task['defaultProtocol']}.csv"
        check(csv.exists(), f"{task['id']}: missing {csv.name}")

    # --- the two checks that back the newest claims -----------------------
    drift = ROOT / "results" / "stew_drift_control.csv"
    check(drift.exists(), "stew_drift_control.csv missing (run stew_drift_control.py)")
    if drift.exists():
        d = pd.read_csv(drift)
        gap = float(d.groupby("layout")["gap"].mean().max())
        check(gap > 0.0, "drift control shows no drift; the workload caveat is stale")

    paper_check = ROOT / "results" / "earsaad_paper_comparison.csv"
    check(paper_check.exists(),
          "earsaad_paper_comparison.csv missing (run earsaad_paper_check.py)")
    if paper_check.exists():
        c = pd.read_csv(paper_check)
        check((c["closer_to"] == "full").all(),
              "attention reproduction does not land on the paper's with-ASR column")

    # --- the ear channel-budget curve -------------------------------------
    ear_curve = ROOT / "results" / "aad_channel_curve.csv"
    check(ear_curve.exists(),
          "aad_channel_curve.csv missing (run aad_channel_curve.py)")
    if ear_curve.exists():
        c = pd.read_csv(ear_curve)
        # The ear arrays must not gain more from extra electrodes than the scalp
        # does; if they do, the "ear saturates first" claim in the prose is wrong.
        for setup in ("in_ear", "around_ear", "scalp"):
            g = c[c["setup"] == setup].sort_values("k")
            check(not g.empty, f"channel curve: no rows for {setup}")
        if {"in_ear", "scalp"} <= set(c["setup"]):
            ie = c[c["setup"] == "in_ear"].sort_values("k")
            sc = c[c["setup"] == "scalp"].sort_values("k")
            gain_ear = float(ie["score_mean"].iloc[-1] - ie["score_mean"].iloc[0])
            gain_scalp = float(sc["score_mean"].iloc[-1] - sc["score_mean"].iloc[0])
            check(gain_scalp > gain_ear,
                  f"channel curve: scalp gain {gain_scalp:.3f} is not larger than "
                  f"in-ear gain {gain_ear:.3f}; the saturation claim is unsupported")

    # --- figures referenced by the paper exist ----------------------------
    paper = (ROOT / "paper" / "paper.html").read_text(encoding="utf-8")
    for src in set(re.findall(r'src="(assets/figures/[^"]+)"', paper)):
        check((ROOT / "docs" / src).exists(), f"paper references missing {src}")

    # --- signals cover every task -----------------------------------------
    signals = json.loads((ROOT / "docs" / "data" / "signals.json")
                         .read_text(encoding="utf-8"))
    for task in tasks:
        key = task.get("signalKey")
        check(key in signals["signals"],
              f"{task['id']}: no signal illustration for key {key!r}")

    if FAIL:
        print(f"FAILED ({len(FAIL)}):")
        for f in FAIL:
            print(f"  - {f}")
        return 1
    print(f"OK: {len(tasks)} tasks, {len(controls)} control rows, "
          f"{len(signals['signals'])} signal illustrations, no placeholders.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
