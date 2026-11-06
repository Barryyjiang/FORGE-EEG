"""Decoder registry.

A benchmark is only comprehensive if the decoder axis is systematic. Every
pipeline here is a *standard* method from the BCI literature, chosen so results
can be compared against published work rather than against our own inventions.

Adding a decoder means adding one entry to ``REGISTRY``. Everything downstream
(sweep, leaderboard) picks it up automatically.
"""

from __future__ import annotations

from typing import Callable

Pipelines = dict[str, object]


def _logvar_lda():
    """Band-power + LDA. The cheapest credible baseline."""
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
    from sklearn.pipeline import make_pipeline

    from moabb.pipelines.features import LogVariance

    return make_pipeline(LogVariance(), LDA())


def _csp_lda():
    """Common Spatial Patterns + LDA. Field standard for motor imagery."""
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
    from sklearn.pipeline import make_pipeline

    from mne.decoding import CSP

    return make_pipeline(CSP(n_components=4, log=True), LDA())


def _riemann_tslr():
    """Covariance + tangent space + logistic regression.

    The strongest classical method for MI/SSVEP in most MOABB comparisons.
    Operates on 3-D epochs (n_trials, n_chans, n_times), which is what MOABB
    paradigms return when ``return_epochs=False``.
    """
    from pyriemann.estimation import Covariances
    from pyriemann.tangentspace import TangentSpace
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline

    return make_pipeline(
        Covariances(estimator="lwf"),
        TangentSpace(),
        LogisticRegression(max_iter=1000),
    )


def _riemann_mdm():
    """Covariance + minimum distance to mean. No hyperparameters to tune."""
    from pyriemann.classification import MDM
    from pyriemann.estimation import Covariances
    from sklearn.pipeline import make_pipeline

    return make_pipeline(Covariances(estimator="lwf"), MDM())


def _csp_tslr():
    """CSP filters + Riemannian tangent space. A common strong hybrid."""
    from mne.decoding import CSP
    from pyriemann.estimation import Covariances
    from pyriemann.tangentspace import TangentSpace
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline

    return make_pipeline(
        CSP(n_components=8, log=False),
        Covariances(estimator="lwf"),
        TangentSpace(),
        LogisticRegression(max_iter=1000),
    )


def _bandpower_ridge():
    """Band-power + ridge regression.

    The regression counterpart to ``logvar_lda``. Needed for continuous tasks
    (sleep staging, auditory attention) where the target is a value or a
    sequence rather than a class. Declared here so the decoder axis is ready
    when a continuous dataset adapter exists; see ``suite`` for status.
    """
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    from moabb.pipelines.features import LogVariance

    return make_pipeline(LogVariance(), StandardScaler(), Ridge(alpha=1.0))


_SSVEP_FREQ_MAP: dict[int, float] | None = None


def set_ssvep_frequencies(labels) -> dict[int, float]:
    """Register the class-label -> stimulus-frequency map for ``ssvep_cca``.

    MOABB's evaluator encodes string labels (``'9.25'``) to ordinals before
    ``fit``, so CCA cannot recover the physical frequency on its own. The map is
    built from the dataset's event ids in sorted order, which is the ordering
    sklearn's ``LabelEncoder`` produces.

    Assumption is explicit and checkable: if the CCA result sits at chance on a
    montage that should work, suspect this mapping before concluding the montage
    is bad.
    """
    global _SSVEP_FREQ_MAP
    _SSVEP_FREQ_MAP = {
        i: float(label) for i, label in enumerate(sorted(labels))
    }
    return _SSVEP_FREQ_MAP


def _ssvep_cca():
    """Canonical correlation analysis for SSVEP.

    SSVEP is fundamentally a frequency-detection problem; band-power and
    covariance methods sit near chance on it. Without this decoder the SSVEP
    track measures decoder mismatch instead of montage quality.
    """
    from moabb.pipelines.classification import SSVEP_CCA

    return SSVEP_CCA(n_harmonics=3, freq_map=_SSVEP_FREQ_MAP)


def _xdawn_tslr():
    """xDAWN spatial filtering + tangent space + logistic regression.

    The field standard for single-trial ERP/P300. Without it a P300 track sits
    at chance, exactly as an SSVEP track does without CCA — and the resulting
    "no signal" conclusion would be about the decoder, not the montage.
    """
    from pyriemann.estimation import XdawnCovariances
    from pyriemann.tangentspace import TangentSpace
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline

    return make_pipeline(
        XdawnCovariances(nfilter=4, estimator="lwf"),
        TangentSpace(),
        LogisticRegression(max_iter=1000),
    )


#: name -> factory. Factories return a *fresh* unfitted pipeline each call,
#: because sklearn estimators are stateful and MOABB reuses them across folds.
REGISTRY: dict[str, Callable[[], object]] = {
    "logvar_lda": _logvar_lda,
    "csp_lda": _csp_lda,
    "riemann_tslr": _riemann_tslr,
    "riemann_mdm": _riemann_mdm,
    "csp_tslr": _csp_tslr,
    "bandpower_ridge": _bandpower_ridge,
    "ssvep_cca": _ssvep_cca,
    "xdawn_tslr": _xdawn_tslr,
}

#: Decoders that only make sense for one paradigm. They are never in DEFAULT.
PARADIGM_SPECIFIC: dict[str, str] = {
    "ssvep_cca": "ssvep",
    "xdawn_tslr": "p300",
}

#: Decoders that predict a continuous target rather than a class label.
REGRESSION: frozenset[str] = frozenset({"bandpower_ridge"})

#: Every decoder the benchmark runs by default. Deep models are opt-in: they
#: need tuning before their numbers mean anything (see README).
DEFAULT: tuple[str, ...] = ("logvar_lda", "csp_lda", "riemann_tslr")


def available() -> list[str]:
    return sorted(REGISTRY)


def build(names=None) -> Pipelines:
    """Instantiate pipelines by name. ``None`` -> :data:`DEFAULT`."""
    names = DEFAULT if names is None else names
    unknown = [n for n in names if n not in REGISTRY]
    if unknown:
        raise KeyError(f"unknown pipeline(s) {unknown}; available: {available()}")
    out: Pipelines = {}
    for name in names:
        try:
            out[name] = REGISTRY[name]()
        except Exception as exc:  # a missing optional dependency must not be silent
            raise RuntimeError(f"could not build pipeline {name!r}: {exc}") from exc
    return out
