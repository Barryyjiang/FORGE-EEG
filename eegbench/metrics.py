"""Metrics beyond accuracy.

Two reasons this module exists rather than using MOABB's scorer strings:

1. **ITR.** For visual paradigms the field reports information transfer rate
   (bits/min), not AUC. A montage that is accurate but slow loses to one that is
   slightly less accurate and much faster, and AUC cannot express that.
2. **Continuous tasks.** Sleep staging and auditory attention are regression /
   sequence problems with kappa and correlation as the natural scores. The
   benchmark must be able to name a metric that is not classification accuracy.

All functions take plain arrays so they can be used as MOABB scorers or computed
post hoc from a results table.
"""

from __future__ import annotations

import numpy as np


def itr_bits_per_min(
    accuracy: float,
    n_classes: int,
    trial_seconds: float,
) -> float:
    """Wolpaw information transfer rate, bits per minute.

    .. math::
        \\mathrm{ITR} = \\frac{60}{T}
        \\left[ \\log_2 N + P\\log_2 P + (1-P)\\log_2\\frac{1-P}{N-1} \\right]

    ``accuracy`` is the probability that a selection is correct. For a 2-class
    ROC-AUC this formula does not apply directly — convert to accuracy first or
    report AUC and skip ITR.
    """
    if n_classes < 2 or not np.isfinite(accuracy) or trial_seconds <= 0:
        return float("nan")

    p = float(np.clip(accuracy, 1e-6, 1 - 1e-6))
    bits = (
        np.log2(n_classes)
        + p * np.log2(p)
        + (1 - p) * np.log2((1 - p) / (n_classes - 1))
    )
    return float(max(bits, 0.0) * 60.0 / trial_seconds)


def cohens_kappa(y_true, y_pred, *, n_classes: int | None = None) -> float:
    """Chance-corrected agreement. Standard for sleep staging."""
    from sklearn.metrics import cohen_kappa_score

    return float(cohen_kappa_score(y_true, y_pred))


def auc_to_balanced_accuracy(auc: float) -> float:
    """Balanced accuracy implied by an ROC-AUC, under a stated assumption.

    Assumes two equal-variance Gaussian score distributions (the binormal
    model) and an operating point at the equal-error threshold. Then
    ``AUC = Phi(d / sqrt(2))`` and ``balanced accuracy = Phi(d / 2)`` for a
    separation ``d``, so ``balanced accuracy = Phi(Phi^-1(AUC) / sqrt(2))``.

    This is a **translation, not a measurement**. AUC tracks are never scored
    with accuracy here, and ITR is still never derived from an AUC (see
    :func:`eegbench.leaderboard._add_itr`); the number exists only so a delta
    can be judged on the scale an operator experiences. It is wrong if the
    two classes have different variances or the threshold is not at the
    equal-error point.
    """
    from scipy.stats import norm

    a = float(np.clip(auc, 1e-6, 1 - 1e-6))
    return float(norm.cdf(norm.ppf(a) / np.sqrt(2.0)))


def headroom_lost(score: float, reference: float, chance: float) -> float:
    """Share of the above-chance margin a reduction gives up.

    ``(reference - score) / (reference - chance)``. Unlike a raw delta this is
    comparable across tasks whose chance levels differ (AUC 0.5, accuracy 1/n,
    kappa 0), which is what makes "how bad is 5 points?" answerable. Returns
    NaN when the reference has no headroom to lose.
    """
    span = float(reference) - float(chance)
    if not np.isfinite(span) or span <= 0:
        return float("nan")
    return (float(reference) - float(score)) / span


def pearson_r(y_true, y_pred) -> float:
    """Correlation. Standard for auditory attention / stimulus reconstruction."""
    from scipy.stats import pearsonr

    if len(y_true) < 3:
        return float("nan")
    return float(pearsonr(np.asarray(y_true).ravel(), np.asarray(y_pred).ravel())[0])


#: metric name -> (higher_is_better, needs_probabilities)
#:
#: ``needs_probabilities`` tells the runner whether a classifier's
#: ``predict_proba`` or its ``predict`` is the thing to score.
METRICS: dict[str, dict] = {
    "roc_auc": {"higher_is_better": True, "needs_probabilities": True},
    "accuracy": {"higher_is_better": True, "needs_probabilities": False},
    "kappa": {"higher_is_better": True, "needs_probabilities": False},
    "pearson": {"higher_is_better": True, "needs_probabilities": False},
}

#: Metrics that are only meaningful for multi-class classification.
CLASSIFICATION_ONLY = {"roc_auc", "accuracy"}


def chance_level(metric: str, n_classes: int) -> float:
    """Chance performance for a metric.

    ROC-AUC is 0.5 regardless of class count; accuracy and balanced accuracy are
    1/n; kappa and correlation are 0. Getting this wrong silently rescales an
    entire leaderboard, so it lives here rather than inline.

    Balanced accuracy is kept distinct from accuracy on purpose: it is the metric
    the FACED emotion track reports, and calling it "accuracy" in the CSV would
    mislabel a class-balanced score as a raw one.
    """
    if metric == "roc_auc":
        return 0.5
    if metric in ("accuracy", "balanced_accuracy"):
        return 1.0 / max(n_classes, 1)
    return 0.0


def is_itr_eligible(metric: str, n_classes: int, trial_seconds: float | None) -> bool:
    """ITR needs accuracy (not AUC), >=2 classes, and a known trial duration."""
    return (
        metric == "accuracy"
        and n_classes >= 2
        and trial_seconds is not None
        and trial_seconds > 0
    )
