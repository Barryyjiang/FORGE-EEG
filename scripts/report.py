"""Generate a single markdown report from benchmark outputs.

One command regenerates every number quoted in the README, which is what makes
the results auditable rather than transcribed.

    .\\.venv\\Scripts\\python.exe scripts\\report.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from eegbench.leaderboard import leaderboard

FLOAT = lambda v: f"{v:.3f}" if pd.notna(v) else "—"  # noqa: E731


def validate(table: pd.DataFrame, *, min_n: int = 5,
             perm_tol: float = 0.05) -> tuple[list[str], list[str]]:
    """Check the results against the benchmark's own validity rules.

    Returns ``(failures, warnings)``. Failures mean the report must not be
    published; warnings mean a number is weaker than it looks.

    The three rules exist because each of them caught a real error:
    - a control above chance means leakage (or a broken control);
    - an ``n`` that is too small produced three separate wrong conclusions in
      this project, always by comparing a subset mean to a full-set mean;
    - cross-site comparisons at unequal channel counts confound site with count.
    """
    failures: list[str] = []
    warnings: list[str] = []

    # --- controls ---------------------------------------------------------
    for path in sorted(Path("results").glob("perm_control_*.csv")):
        df = pd.read_csv(path)
        if "perm_mean" not in df.columns:
            failures.append(f"{path.name}: missing perm_mean column")
            continue
        metric = str(df["metric"].iloc[0]) if "metric" in df.columns else "roc_auc"
        n_cls = int(df["n_classes"].iloc[0]) if "n_classes" in df.columns else 2
        chance = 0.5 if metric == "roc_auc" else 1.0 / max(n_cls, 1)
        perm = float(df["perm_mean"].mean())
        tol = max(perm_tol, 2 * float(df.get("perm_sd", pd.Series([0])).mean()))
        if perm > chance + tol:
            failures.append(
                f"{path.name}: permuted score {perm:.3f} exceeds chance "
                f"{chance:.3f} + {tol:.3f} — treat results as leaked"
            )

    # --- sample size ------------------------------------------------------
    if "n" in table.columns:
        low = table[table["n"] < min_n]
        for _, r in low.drop_duplicates(["track", "pipeline"]).iterrows():
            warnings.append(
                f"{r['track']} / {r['pipeline']}: n={int(r['n'])} < {min_n}; "
                "do not quote as a stable estimate"
            )

    # --- matched channel counts ------------------------------------------
    for (track, protocol), g in table.groupby(["track", "protocol"]):
        wearable = g[g["strategy"] == "wearable"]
        other = g[g["strategy"] != "wearable"]
        if wearable.empty or other.empty:
            continue
        wk = set(wearable["k"].astype(int))
        ok = set(other["k"].astype(int))
        if wk and ok and not (wk & ok):
            warnings.append(
                f"{track} / {protocol}: wearable channels {sorted(wk)} vs "
                f"comparison {sorted(ok)} — site and count are confounded"
            )

    return failures, warnings



def _md(df: pd.DataFrame, cols: list[str], floatfmt=FLOAT) -> str:
    cols = [c for c in cols if c in df.columns]
    out = ["| " + " | ".join(cols) + " |",
           "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, row in df.iterrows():
        cells = []
        for c in cols:
            v = row[c]
            if isinstance(v, float):
                cells.append(floatfmt(v))
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dir", type=Path, default=Path("results/benchmark"))
    p.add_argument("--quality-glob", default="results/signal_quality_*.csv")
    p.add_argument("--out", type=Path, default=Path("results/REPORT.md"))
    p.add_argument("--force", action="store_true",
                   help="write the report even if validity checks fail")
    args = p.parse_args()

    table = leaderboard(args.dir)

    failures, warns = validate(table)
    if failures:
        print("REFUSING to write report — validity checks failed:")
        for f in failures:
            print(f"  FAIL  {f}")
        for w in warns:
            print(f"  warn  {w}")
        if not args.force:
            return 1
        print("\n--force given: writing anyway (numbers are not trustworthy)")

    lines = ["# Benchmark report", "",
             "Generated from `results/benchmark/`. Every number below is",
             "reproducible with the commands in `README.md`.", ""]

    # --- coverage ---------------------------------------------------------
    lines += ["## Validity checks", ""]
    if warns:
        lines += [f"- _warn_ {w}" for w in warns]
    else:
        lines += ["All checks passed."]
    lines += [""]

    lines += ["## Coverage", ""]
    cov = (
        table.groupby(["track", "protocol", "pipeline"])
        .agg(subsets=("subset", "nunique"), n=("n", "max"))
        .reset_index()
        .sort_values(["track", "protocol", "pipeline"])
    )
    lines += [_md(cov, ["track", "protocol", "pipeline", "subsets", "n"]), ""]

    # --- per track --------------------------------------------------------
    for track in sorted(table["track"].unique()):
        sub = table[table["track"] == track]
        lines += [f"## {track}", ""]

        full = sub[sub["strategy"] == "full"]
        if not full.empty:
            lines += [_md(full, ["protocol", "pipeline", "score_mean",
                                 "score_sem", "chance", "itr_bpm"]), ""]

        montage = sub[sub["strategy"] != "full"].sort_values(
            ["protocol", "score_mean"], ascending=[True, False]
        )
        lines += [_md(montage, ["protocol", "pipeline", "subset", "k",
                                "score_mean", "score_sem", "delta_vs_full",
                                "itr_bpm"]), ""]

    # --- signal quality ---------------------------------------------------
    quality_files = sorted(Path(".").glob(args.quality_glob))
    if quality_files:
        lines += ["## Signal quality (raw data, per montage)", ""]
        q = pd.concat([pd.read_csv(f) for f in quality_files], ignore_index=True)
        lines += [_md(q.sort_values(["track", "k", "strategy"]),
                      ["track", "subset", "k", "reject_rate",
                       "line_noise_ratio", "effective_rank", "mean_abs_corr"]),
                  ""]
    else:
        lines += ["## Signal quality", "",
                  "_not computed for any track yet_", ""]

    # --- permutation control ---------------------------------------------
    perm_files = sorted(Path("results").glob("perm_control_*.csv"))
    if perm_files:
        lines += ["## Permutation control", "",
                  "Permuted-label AUC should sit at chance; a gap is the real effect.",
                  ""]
        perm = pd.concat([pd.read_csv(f) for f in perm_files], ignore_index=True)
        perm = perm.groupby(["track", "pipeline"], as_index=False)[
            ["real", "perm_mean", "gap"]].mean()
        lines += [_md(perm.sort_values("track"),
                      ["track", "pipeline", "real", "perm_mean", "gap"]), ""]
    else:
        lines += ["## Permutation control", "", "_not run yet_", ""]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.out} ({len(lines)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
