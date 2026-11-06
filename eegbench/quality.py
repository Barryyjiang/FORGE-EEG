"""Signal-quality axis.

Wearables are defined as much by their noise floor as by their electrode
positions. A montage that decodes badly could be badly *placed* or badly
*measured*, and accuracy alone cannot distinguish those.

**These must be computed on raw, unfiltered data.** An earlier version used the
paradigm's epochs, which are band-passed to the decoding band; that silently
removed the mains frequency (making ``line_noise_ratio`` meaningless) and
flattened amplitude (making artefact rejection find nothing). A quality metric
that cannot fail is worse than none.

Metrics:

- ``reject_rate``      fraction of 2 s windows whose peak-to-peak exceeds a
                       threshold. Standard artefact proxy.
- ``line_noise_ratio`` power at mains frequency vs its shoulders. Dry and
                       wearable electrodes are the ones that suffer here.
- ``effective_rank``   participation ratio of the *correlation* matrix
                       eigenvalues. Scale-free, so one loud electrode cannot
                       masquerade as many independent dimensions.
- ``mean_abs_corr``    average absolute inter-channel correlation: redundancy
                       from volume conduction.
"""

from __future__ import annotations

import numpy as np


def _participation_ratio(matrix: np.ndarray) -> float:
    eig = np.linalg.eigvalsh(np.atleast_2d(matrix))
    eig = np.clip(eig, 0, None)
    denom = (eig**2).sum()
    return float((eig.sum() ** 2) / denom) if denom > 0 else float("nan")


def signal_quality(
    X: np.ndarray,
    sfreq: float,
    *,
    line_freq: float = 50.0,
    reject_uv: float = 150.0,
    window_seconds: float = 2.0,
) -> dict[str, float]:
    """Quality metrics for one montage of continuous data.

    ``X`` is ``(n_chans, n_times)`` in **volts** at ``sfreq``.
    """
    if X.ndim != 2:
        raise ValueError(f"expected (chans, times), got {X.shape}")

    n_chans, n_times = X.shape

    # --- artefact proxy: peak-to-peak in short windows -----------------------
    win = max(int(window_seconds * sfreq), 2)
    n_windows = n_times // win
    if n_windows >= 1:
        windows = X[:, : n_windows * win].reshape(n_chans, n_windows, win)
        p2p_uv = np.ptp(windows, axis=-1) * 1e6  # (chans, windows)
        reject_rate = float((p2p_uv > reject_uv).any(axis=0).mean())
        median_p2p = float(np.median(p2p_uv))
    else:
        reject_rate = float("nan")
        median_p2p = float(np.ptp(X, axis=-1).mean() * 1e6)

    # --- line noise from the full segment -----------------------------------
    freqs = np.fft.rfftfreq(n_times, d=1.0 / sfreq)
    psd = (np.abs(np.fft.rfft(X, axis=-1)) ** 2).mean(axis=0)
    at_line = np.abs(freqs - line_freq) <= 0.5
    shoulder = (np.abs(freqs - line_freq) > 1.0) & (np.abs(freqs - line_freq) <= 5.0)
    if at_line.any() and shoulder.any() and psd[shoulder].mean() > 0:
        line_noise_ratio = float(psd[at_line].mean() / psd[shoulder].mean())
    else:
        line_noise_ratio = float("nan")

    # --- dimensionality and redundancy --------------------------------------
    centred = X - X.mean(axis=1, keepdims=True)
    cov = np.cov(centred)
    std = np.sqrt(np.clip(np.diag(cov), 1e-30, None))
    corr = cov / np.outer(std, std)
    effective_rank = _participation_ratio(corr)

    if n_chans > 1:
        off = corr[~np.eye(n_chans, dtype=bool)]
        mean_abs_corr = float(np.mean(np.abs(off)))
    else:
        mean_abs_corr = float("nan")

    return {
        "n_channels": int(n_chans),
        "n_times": int(n_times),
        "reject_rate": reject_rate,
        "line_noise_ratio": line_noise_ratio,
        "effective_rank": effective_rank,
        "mean_abs_corr": mean_abs_corr,
        "median_p2p_uv": median_p2p,
    }
