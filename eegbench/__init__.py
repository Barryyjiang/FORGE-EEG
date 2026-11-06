"""Electrode-subset and wearable-EEG benchmarking on top of MOABB."""

from .paths import configure_data_home

# Must run before MOABB/MNE are imported anywhere, so downloads and caches stay
# inside ./data. Opt out with EEGBENCH_NO_DATA_REDIRECT=1.
configure_data_home()

from .benchmark import dataset_channels, subset_channels, summarise, sweep  # noqa: E402
from .montages import REGIONS, WEARABLES, Montage, montage  # noqa: E402
from .subsets import SubsetSpec, equal_n_specs, farthest_point_order  # noqa: E402

__all__ = [
    "REGIONS",
    "WEARABLES",
    "Montage",
    "SubsetSpec",
    "configure_data_home",
    "dataset_channels",
    "equal_n_specs",
    "farthest_point_order",
    "montage",
    "subset_channels",
    "summarise",
    "sweep",
]
