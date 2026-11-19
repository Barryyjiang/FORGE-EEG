"""Generate a single markdown report from benchmark outputs.

One command regenerates every number quoted in the README, which is what makes
the results auditable rather than transcribed.

    .\\.venv\\Scripts\\python.exe scripts\\report.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from eegbench.leaderboard import leaderboard, window_curve

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
        chance = (
            0.5 if metric == "roc_auc"
            else 0.0 if metric == "kappa"
            else 1.0 / max(n_cls, 1)
        )
        # A fixed tolerance is the rule the site states. Scaling by the
        # permutation SD made a noisy control easier to pass, which is the
        # opposite of what a validity guard should do.
        #
        # Checked PER ROW, not on the file mean: averaging the null across
        # montages let the worst single control slip through (sleep scalp_6
        # had perm_mean 0.052 against a 0.05 rule, but the file mean was 0.037
        # and the guard passed it).
        for _, row in df.iterrows():
            perm = float(row["perm_mean"])
            if perm <= chance + perm_tol:
                continue
            where = "full"
            for key in ("subset", "montage"):
                if key in row and pd.notna(row[key]):
                    where = str(row[key])
                    break
            failures.append(
                f"{path.name} [{where}]: permuted score {perm:.3f} exceeds "
                f"chance {chance:.3f} + {perm_tol:.3f} — treat results as leaked"
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


def _consequence(table: pd.DataFrame) -> pd.DataFrame:
    """Cost of each reduction on scales that are comparable across tasks.

    A raw delta is not comparable between a task whose chance is 0.5 and one
    whose chance is 0.083, so every reduction is also expressed as the share
    of the above-chance margin it consumes. ROC-AUC rows additionally carry a
    *derived* balanced accuracy (binormal, equal-error threshold) so the cost
    can be read on the scale an operator experiences. That column is a
    translation, not a measurement; ITR is still never derived from an AUC.
    """
    from eegbench.metrics import auc_to_balanced_accuracy, headroom_lost

    keep = ["track", "protocol", "pipeline", "subset", "k", "score_mean",
            "delta_vs_reference", "chance", "full_score", "metric",
            "n_classes", "itr_bpm"]
    df = table[table["strategy"] != "full"].copy()
    df = df[[c for c in keep if c in df.columns]]
    if df.empty:
        return df
    df = df.drop_duplicates(["track", "protocol", "pipeline", "subset"])

    if "full_score" in df.columns and "chance" in df.columns:
        df["headroom_lost_pct"] = [
            100.0 * headroom_lost(s, f, c) if pd.notna(f) and pd.notna(c)
            else float("nan")
            for s, f, c in zip(df["score_mean"], df["full_score"], df["chance"])
        ]

    # Same metric inference as leaderboard.add_chance: files written before the
    # metric column existed (the motor-imagery CSVs) carry none.
    metric = (df["metric"].astype(str) if "metric" in df.columns
              else pd.Series("", index=df.index))
    known = {"roc_auc", "accuracy", "balanced_accuracy", "kappa", "pearson"}
    if "n_classes" in df.columns:
        n = pd.to_numeric(df["n_classes"], errors="coerce")
        metric = pd.Series(
            [m if m in known else ("roc_auc" if pd.notna(c) and c <= 2 else "accuracy")
             for m, c in zip(metric, n)],
            index=df.index,
        )
    is_auc = metric.eq("roc_auc")
    if is_auc.any():
        df["bal_acc"] = [
            auc_to_balanced_accuracy(s) if a else float("nan")
            for s, a in zip(df["score_mean"], is_auc)
        ]
        df["bal_acc_ref"] = [
            auc_to_balanced_accuracy(f) if a and pd.notna(f) else float("nan")
            for f, a in zip(df.get("full_score", pd.Series(index=df.index)), is_auc)
        ]
        df["bal_acc_drop_pts"] = 100.0 * (df["bal_acc_ref"] - df["bal_acc"])

    if "itr_bpm" in df.columns:
        ref = (
            table[table["strategy"] == "full"]
            .drop_duplicates(["track", "protocol", "pipeline"])
            .set_index(["track", "protocol", "pipeline"])["itr_bpm"]
        )
        idx = pd.MultiIndex.from_frame(df[["track", "protocol", "pipeline"]])
        itr_ref = list(ref.reindex(idx))
        df["itr_pct_change"] = [
            (100.0 * (v - r) / r) if pd.notna(v) and pd.notna(r) and r
            else float("nan")
            for v, r in zip(df["itr_bpm"], itr_ref)
        ]
        df = df.drop(columns=["itr_bpm"])

    sort = ("headroom_lost_pct" if "headroom_lost_pct" in df.columns
            else "delta_vs_reference")
    return df.sort_values(sort, ascending=False)


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
                                "score_mean", "score_sem", "delta_vs_reference",
                                "itr_bpm"]), ""]

    # --- accuracy vs decision window -------------------------------------
    curve = window_curve(args.dir)
    if not curve.empty:
        lines += [
            "## Accuracy vs decision window",
            "",
            "A task scored at several decision windows is reported at its headline "
            "window in the tables above; averaging across windows would produce a "
            "number that belongs to no window. This is the full curve. A lower "
            "signal-to-noise ratio shows up as a need for longer windows rather than "
            "as a hard ceiling, which is the difference between a wearable that "
            "cannot do a task and one that is merely slow.",
            "",
        ]
        for track in sorted(curve["track"].unique()):
            sub = curve[curve["track"] == track]
            piv = sub.pivot_table(index="subset", columns="trial_seconds",
                                  values="score_mean").round(3)
            piv.columns = [f"{int(c)}s" for c in piv.columns]
            curve_table = piv.reset_index()
            lines += [f"### {track}", "",
                      _md(curve_table, ["subset"] + list(piv.columns)), ""]

    # --- how many ear electrodes do you need? ----------------------------
    ear_curve_path = Path("results/aad_channel_curve.csv")
    if ear_curve_path.exists():
        ear_curve = pd.read_csv(ear_curve_path)
        piv = (ear_curve.pivot_table(index="k", columns="setup",
                                     values="score_mean").round(3))
        cols = [c for c in ("in_ear", "around_ear", "scalp") if c in piv.columns]
        piv = piv[cols]
        piv.index = piv.index.astype(int)
        piv.index.name = "k"
        # ``_md`` walks rows with ``iterrows``, which upcasts a mixed row to one
        # dtype and would print the channel count as "2.000". Format it first.
        curve_table = piv.reset_index()
        curve_table["k"] = curve_table["k"].map(lambda v: str(int(v)))
        lines += [
            "## How many ear electrodes do you need?",
            "",
            "The attention table above compares the three systems as they were "
            "built (29 / 19 / 12 electrodes). This sweeps the channel budget "
            "instead: at each *k*, the *k* most spatially spread electrodes within "
            "each array, against the *k* most spread scalp electrodes as a matched "
            "reference. Every point uses the same decoder, the same "
            "leave-one-trial-out protocol and the same 60 s decision window, so a "
            "point here is comparable to a row above.",
            "",
            _md(curve_table, ["k"] + cols),
            "",
            "If the ear and scalp curves are parallel, the ear costs a constant "
            "offset. If the ear curve flattens first, the ear runs out of "
            "information before it runs out of electrodes \u2014 which is the "
            "difference between adding electrodes and changing the site.",
            "",
        ]

    # --- paired comparisons ----------------------------------------------
    def _paired(track, pipeline, a, b, label, *, by_session=False,
                protocol="within_session", trial_seconds=None):
        path = Path(args.dir) / f"{track}__{protocol}.csv"
        if not path.exists():
            return None
        df = pd.read_csv(path)
        sub = df[(df["pipeline"] == pipeline) & (df["subset"].isin([a, b]))]
        if trial_seconds is not None and "trial_seconds" in sub.columns:
            # Tasks scored at several decision windows have one row per subject
            # per window; without this filter the pivot would silently average
            # across windows and compare the wrong numbers.
            sub = sub[sub["trial_seconds"] == trial_seconds]
        index = ["subject", "session"] if by_session else ["subject"]
        pivot = sub.pivot_table(index=index, columns="subset", values="score")
        if not {a, b}.issubset(pivot.columns):
            return None
        delta = (pivot[b] - pivot[a]).dropna()
        n = len(delta)
        if n < 2:
            return None
        from scipy import stats

        mean = float(delta.mean())
        sem = float(delta.std(ddof=1)) / (n ** 0.5)
        half = float(stats.t.ppf(0.975, n - 1)) * sem
        return {
            "comparison": label,
            "n": n,
            "delta": mean,
            "ci_low": mean - half,
            "ci_high": mean + half,
            "same_sign": int((delta < 0).sum()) if mean < 0 else int((delta > 0).sum()),
        }

    pairs = [
        _paired("mi_leftright_22ch", "riemann_tslr", "full_k22",
                "region-sensorimotor_k8", "MI: sensorimotor 8 − full 22",
                by_session=True),
        _paired("mi_4class_22ch", "riemann_tslr", "full_k22",
                "region-sensorimotor_k8", "MI 4-class: sensorimotor 8 − full 22",
                by_session=True),
        _paired("mi_4class_22ch", "riemann_tslr", "region-parietal_k4",
                "region-sensorimotor_k4", "MI 4-class: sensorimotor 4 − parietal 4",
                by_session=True),
        _paired("p300_8ch", "xdawn_tslr", "full_k8", "distributed_k4",
                "P300: spread 4 − full 8"),
        _paired("ssvep_8ch", "ssvep_cca", "full_k8", "distributed_k4",
                "SSVEP: spread 4 − full 8"),
        _paired("motor_execution_ear_vs_scalp", "riemann_tslr",
                "region-sensorimotor_k8", "wu2020_inear_k8",
                "Motor: in-ear 8 − sensorimotor 8"),
        _paired("sleep_staging_local", "bandpower_lda", "scalp_6_k6",
                "ear_6_k6", "Sleep: ear 6 − scalp 6"),
        _paired("stew_workload_14ch", "psd_lda", "full_14_k14",
                "glasses_4_k4", "Workload: glasses 4 − full 14",
                protocol="cross_subject"),        _paired("stew_workload_14ch", "psd_lda", "posterior_4_k4",
                "glasses_4_k4", "Workload: glasses 4 − posterior 4",
                protocol="cross_subject"),
        _paired("auditory_attention_earsaad", "ridge_reconstruction",
                "scalp_12_k12", "in_ear_12_k12",
                "Attention: in-ear 12 − scalp 12", trial_seconds=60.0),
        _paired("auditory_attention_earsaad", "ridge_reconstruction",
                "scalp_19_k19", "around_ear_19_k19",
                "Attention: around-ear 19 − scalp 19", trial_seconds=60.0),
        _paired("auditory_attention_earsaad", "ridge_reconstruction",
                "scalp_29_k29", "in_ear_12_k12",
                "Attention: in-ear 12 − scalp 29 (as built)", trial_seconds=60.0),
        _paired("faced_emotion_123", "psd_lda", "full_k30", "posterior_4_k4",
                "Emotion: posterior 4 − full 30"),
        _paired("faced_emotion_123", "psd_lda", "posterior_4_k4",
                "glasses_4_k4", "Emotion: glasses 4 − posterior 4"),
    ]
    pairs = [p for p in pairs if p is not None]
    if pairs:
        lines += ["## Paired comparisons", "",
                  "Each row is a within-subject difference; the CI is a paired "
                  "t interval. `same_sign` is how many pairs agree with the "
                  "mean.",
                  ""]
        lines += [_md(pd.DataFrame(pairs),
                      ["comparison", "n", "delta", "ci_low", "ci_high",
                       "same_sign"]), ""]

    # --- what each reduction costs ---------------------------------------
    cons = _consequence(table)
    if not cons.empty:
        lines += ["## What each reduction costs", "",
                  "A raw delta is not comparable across tasks whose chance "
                  "levels differ, so each reduction is also given as the share "
                  "of the above-chance margin it consumes. `bal_acc` is a "
                  "binormal translation of ROC-AUC at the equal-error "
                  "threshold: a *derived* reading aid on an operator's scale, "
                  "not a scored value, and ITR is still never derived from an "
                  "AUC. Sorted most- to least-costly.", ""]

        def _scale(v):
            if pd.isna(v):
                return "—"
            return f"{v:.1f}" if abs(v) > 1.5 else f"{v:.3f}"

        lines += [_md(cons, ["track", "pipeline", "subset", "k", "score_mean",
                             "delta_vs_reference", "headroom_lost_pct",
                             "bal_acc", "bal_acc_drop_pts", "itr_pct_change"],
                      floatfmt=_scale), ""]

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
                  "Each control re-runs the exact decoder on shuffled labels. The "
                  "null should sit at chance (AUC 0.5, accuracy 1/n, κ 0).",
                  "",
                  "Controls cover the whole cohort of their track, under the "
                  "control's own stratified 5-fold CV, so a `real` here is close "
                  "to, but not identical with, the score in the tables above. The "
                  "sleep track permutes whole 20-epoch blocks: a circular shift is "
                  "not a valid null there, because it preserves the stage runs and "
                  "the band-power drift and leaves the null near κ 0.13 rather "
                  "than 0.",
                  ""]
        perm = pd.concat([pd.read_csv(f) for f in perm_files], ignore_index=True)
        if "subset" not in perm.columns:
            perm["subset"] = "full"
        perm["subset"] = perm["subset"].fillna("full")
        if "chance" not in perm.columns:
            perm["chance"] = float("nan")

        def _chance(row):
            metric = str(row.get("metric", "roc_auc"))
            n_cls = int(row.get("n_classes", 2) or 2)
            if metric == "roc_auc":
                return 0.5
            if metric == "kappa":
                return 0.0
            return 1.0 / max(n_cls, 1)

        missing_chance = perm["chance"].isna()
        if missing_chance.any():
            perm.loc[missing_chance, "chance"] = perm[missing_chance].apply(
                _chance, axis=1
            )
        group = ["track", "pipeline"]
        if "subset" in perm.columns:
            group.insert(1, "subset")
        perm = perm.groupby(group, as_index=False)[
            ["real", "perm_mean", "chance", "gap"]].mean()
        cols = ["track"] + (["subset"] if "subset" in perm.columns else []) + [
            "pipeline", "real", "perm_mean", "chance", "gap"
        ]
        lines += [_md(perm.sort_values(cols[:2]), cols), ""]
    else:
        lines += ["## Permutation control", "", "_not run yet_", ""]

    # --- confound and reproduction checks --------------------------------
    drift_path = Path("results/stew_drift_control.csv")
    paper_check_path = Path("results/earsaad_paper_comparison.csv")
    if drift_path.exists() or paper_check_path.exists():
        lines += ["## Confound and reproduction checks", ""]

    if drift_path.exists():
        drift = pd.read_csv(drift_path)
        agg = (
            drift.groupby("layout")[
                ["real_half_accuracy", "null_mean", "gap"]]
            .mean().reset_index().sort_values("gap", ascending=False)
        )
        lines += [
            "### STEW: is rest-vs-task partly just time-in-session?",
            "",
            "Rest was always recorded before the multitasking test, so the two "
            "conditions sit on opposite sides of a session boundary. This "
            "control uses no task labels at all: it asks whether a decoder can "
            "tell the first half of a recording from its second half, and "
            "compares that against randomly assigned halves.",
            "",
            _md(agg, ["layout", "real_half_accuracy", "null_mean", "gap"]),
            "",
            "Chance is 0.50. A gap above zero means the recording drifts, so the "
            "rest-vs-task result is partly \"which half of the session\". The "
            "released data cannot separate the two, which is why the workload "
            "track is reported as rest-vs-SIMKAP *condition recognition* and "
            "never as a validated mental-workload score.",
            "",
        ]

    faced_check_path = Path("results/faced_reference_comparison.csv")
    if faced_check_path.exists():
        faced = pd.read_csv(faced_check_path)
        if faced["reference"].notna().any():
            lines += [
                "### FACED: does this benchmark agree with the team's own run?",
                "",
                "The emotion track re-derives everything from the per-participant "
                "feature caches rather than copying a spreadsheet. This compares "
                "the result with the predictions the team's FACED notebook saved. "
                "The window metadata is identical between the two, and the score "
                "is stable to about 0.001 across fold assignments, so a gap larger "
                "than that means the cached features were regenerated after those "
                "predictions were written \u2014 a version difference, not a "
                "disagreement about the conclusion.",
                "",
                _md(faced, ["montage", "ours", "reference", "delta", "n_trials"]),
                "",
            ]

    if paper_check_path.exists():
        check = pd.read_csv(paper_check_path)
        lines += [
            "### Ear-SAAD: does the release already include artifact removal?",
            "",
            "The paper reports its 60 s accuracies twice: with the full "
            "preprocessing pipeline, and after omitting EOG regression, "
            "bad-channel removal, ASR and high-power artifact rejection. The "
            "released `preprocessedData.zip` is the output of the authors' own "
            "`preprocessFromBIDS.m`, which runs `clean_channels_nolocs` at 0.45 "
            "and `clean_asr` at cutoff 5 before saving, so a correct "
            "reproduction must land on the *with-ASR* column. It does, which "
            "retires the worry that the ear numbers here are an un-cleaned "
            "upper bound.",
            "",
            _md(check, ["setup", "ours_pct", "paper_full_pct",
                        "paper_no_cleanup_pct", "delta_vs_full",
                        "delta_vs_no_cleanup", "closer_to"]),
            "",
        ]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.out} ({len(lines)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
