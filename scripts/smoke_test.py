r"""Smoke test: verify the venv, CUDA, and the wearable datasets load.

Run with:
    .\.venv\Scripts\python.exe scripts\smoke_test.py

This does NOT download data. It only checks that the packages import and that
the dataset classes expose their montages.
"""

import sys

print(f"python      {sys.version.split()[0]}")

import braindecode  # noqa: E402
import mne  # noqa: E402
import moabb  # noqa: E402
import torch  # noqa: E402

print(f"moabb       {moabb.__version__}")
print(f"braindecode {braindecode.__version__}")
print(f"mne         {mne.__version__}")
print(f"torch       {torch.__version__}")
print(f"cuda avail  {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"cuda device {torch.cuda.get_device_name(0)}")

print()
print("-- wearable datasets --")

from moabb.datasets import Thielen2015, Thielen2021, Wu2020  # noqa: E402
from moabb.datasets import Lee2021Mobile_ERP, Lee2021Mobile_SSVEP  # noqa: E402

DATASETS = [Wu2020, Lee2021Mobile_SSVEP, Lee2021Mobile_ERP, Thielen2021, Thielen2015]

for cls in DATASETS:
    ds = cls()
    n_sub = len(getattr(ds, "subject_list", []))
    print(f"\n{cls.__name__}  subjects={n_sub}")

    # Channel names live in different places depending on the dataset class;
    # probe the common ones rather than assuming.
    names = None
    for attr in ("ch_names", "channel_names", "electrodes"):
        if hasattr(ds, attr):
            names = getattr(ds, attr)
            print(f"  via .{attr}: {len(names)} channels")
            break
    if names is None and hasattr(ds, "metadata"):
        meta = ds.metadata
        print(f"  metadata.acquisition.n_channels = "
              f"{getattr(meta.acquisition, 'n_channels', '?')}")
        sensors = getattr(meta.acquisition, "sensors", None)
        if sensors:
            print(f"  sensors: {sensors}")
    elif names is not None:
        shown = list(names)[:14]
        print(f"  {shown}{' ...' if len(names) > 14 else ''}")

print()
print("-- benchmark utilities --")
from moabb.datasets.utils import find_intersecting_channels  # noqa: E402

print(f"find_intersecting_channels: {find_intersecting_channels.__name__} OK")

# The channel-subset sweep depends on paradigms accepting a `channels=` filter.
import inspect  # noqa: E402

from moabb.paradigms import FixedIntervalWindowsProcessing, LeftRightImagery, P300, SSVEP  # noqa: E402

for par in (SSVEP, P300, LeftRightImagery, FixedIntervalWindowsProcessing):
    sig = inspect.signature(par.__init__)
    print(f"{par.__name__:32s} channels={'channels' in sig.parameters}")

from braindecode.models import EEGNet  # noqa: E402

net = EEGNet(n_chans=8, n_outputs=2, n_times=256)
n_params = sum(p.numel() for p in net.parameters())
print(f"EEGNet(8ch) params: {n_params:,}")
