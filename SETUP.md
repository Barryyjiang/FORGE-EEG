# Environment Notes

## Layout

```
CS 499 Brain/
├── .venv/              Python 3.13.11 virtualenv
├── data/               ALL downloads + caches (gitignored)
│   ├── mne_data/       datasets
│   ├── moabb/          MOABB HDF5 result cache
│   └── mne_home/       MNE config (~1 KB)
├── vendor/moabb/       NeuroTechX/moabb        branch: develop
├── vendor/braindecode/ braindecode/braindecode branch: master
├── eegbench/           this project (pip install -e .)
├── scripts/            smoke_test.py, run_sweep.py, install_data_hook.py
└── results/            CSV output
```

Repos live in `vendor/` deliberately: a top-level `moabb/` directory is importable
from the project root as a **namespace package** and shadows the installed one,
producing baffling partial-import failures (`moabb.pipelines` importing as empty).

## Pinned commits

| Repo        | Branch  | Commit                                     |
| ----------- | ------- | ------------------------------------------ |
| moabb       | develop | `bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5` |
| braindecode | master  | `d19b024aa37a334f783b4873285b1b52044721d5` |

Both move fast; `develop` can break. Record the hash with any result you publish.

## Verified versions

| Package     | Version          |
| ----------- | ---------------- |
| python      | 3.13.11          |
| moabb       | 1.8.0 (editable) |
| braindecode | 1.8.1 (editable) |
| mne         | 1.13.2           |
| torch       | 2.11.0+cu128     |

`torch.cuda.is_available()` → `True` (RTX 4070 Laptop, 8 GB).

## Interpreter

No `py` launcher on this machine. PowerShell execution policy blocks
`Activate.ps1`, so call the binary directly:

```powershell
.\.venv\Scripts\python.exe -V
```

From another directory, use the absolute path:
`"C:\Files\ComputerScience\CS 499 Brain\.venv\Scripts\python.exe"`.

## Install / upgrade

```powershell
.\.venv\Scripts\python.exe -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
.\.venv\Scripts\python.exe -m pip install -e vendor\moabb -e vendor\braindecode
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
.\.venv\Scripts\python.exe -m pip install curryreader --no-deps   # for Wu2020 (Curry .dat)
```

## One-time setup

Nothing may live outside the project folder, so the data redirect is installed as
a venv-wide `sitecustomize` hook (runs at interpreter startup, before user code):

```powershell
.\.venv\Scripts\python.exe scripts\install_data_hook.py
```

Re-run this after recreating or rebuilding `.venv`. Verify with a process that
does **not** import `eegbench`:

```powershell
.\.venv\Scripts\python.exe -c "import mne; print(mne.get_config('MNE_DATA'))"
# -> ...\CS 499 Brain\data\mne_data
```

Show locations and sizes: `.\\.venv\\Scripts\\python.exe scripts\\run_sweep.py --paths`

Opt out for one shell with `set EEGBENCH_NO_DATA_REDIRECT=1`.

## Download sizes (measured)

| Item | Size |
| ---- | ---- |
| `Thielen2021`, subject 1 | 58.6 MB (5 blocks x ~11.7 MB GDF) |
| `Thielen2021`, all 30 subjects | **~1.8 GB** |
| `BNCI2014_001`, per subject | ~125 MB (NEMAR) |
| `BNCI2014_001`, all 9 subjects | **~1.1 GB** |
| `Wu2020`, published per-subject ZIPs | 473 MB (s4) to 1.53 GB (s5), ~6.9 GB total (Zenodo 18961128) |
| `Wu2020`, all 6 subjects as fetched | **~21 GB** — NEMAR store (6.9 GB of ZIPs + 6.9 GB extracted) plus a second extracted copy |
| after pruning the NEMAR store | **8.9 GB total for the whole project** |

Storage note: **do not just delete the NEMAR store.** `get_data()` calls
`_prefetch_nemar_sourcedata()`, which re-creates it on the next load — deleting it
costs 3 GB of re-download per subject and leaves disk unchanged. The real fix is
to pin the provider, which makes the prefetch return immediately
(`base.py:1193`):

```python
from eegbench.datasets import configure_download_provider
configure_download_provider("upstream")   # persisted in data/mne_home
```

`run_sweep.py --download-provider upstream` is the default. Measured effect:
22,670 MB -> 8,065 MB, and it stays there because the prefetch is skipped rather
than defeated.
| observed duplication | MOABB fetches via both pooch and NEMAR, so 1 subject took 118 MB on disk |

`Lee2021Mobile` (50 ch, 23 subjects, 4 sessions) is the big one — expect single-digit GB.
Check a dataset's real size before pulling it, e.g.
`https://zenodo.org/api/records/<id>` lists per-file byte counts.

## Checks

```powershell
.\.venv\Scripts\python.exe scripts\smoke_test.py
.\.venv\Scripts\python.exe scripts\run_sweep.py --fake --ks 3,5
```

## API notes (verified against this checkout, not the docs)

The online docs are out of step with the source. These all cost time to discover:

- `Lee2021Mobile` is a **base class only**. Import `Lee2021Mobile_SSVEP` or
  `Lee2021Mobile_ERP`.
- `find_intersecting_channels` lives in `moabb.datasets.utils`, not `moabb.utils`.
  It calls `get_data([1])`, i.e. it **downloads** subject 1.
- `LogVariance` lives in `moabb.pipelines.features`.
- Braindecode's model is `EEGNet`, not `EEGNetv4`
  (`EEGNet(n_chans=8, n_outputs=2, n_times=256)` → 1,490 params).
- `mne.channels.make_standard_montage("standard_1005")` is deprecated in MNE
  1.13 → use `colin27_1005` (`montages.standard_positions()` handles both).
- All four paradigms (`SSVEP`, `P300`, `LeftRightImagery`, `CVEP`) accept
  `channels=`. That is the hook the whole sweep hangs on.
- **c-VEP is not classification-ready with `CVEP` + LogVar/LDA.**
  `Thielen2021.event_id == {'1.0': 101, '0.0': 100}` — those are stimulus
  *bit* on/off markers, not the 20 speller symbols. `CVEP` therefore produces a
  binary problem (`n_classes=2` in the results), and LogVar+LDA sits at ROC-AUC
  0.5 by construction. c-VEP needs template matching / CCA / reconvolution
  (the original paper's encoding model), or benchmark a different paradigm.
- **`Lee2021Mobile` channel names are only knowable after downloading.** It
  reads BrainVision files directly and does not rename channels; its metadata
  omits `sensors`. The ear electrodes are not 10-10 names, so they cannot enter
  `farthest_point_order` — define an explicit `Montage` from the dataset's own
  labels for the ear comparison.
- Datasets with non-scalp channels (EOG/ECG/ear) list them in metadata.
  `equal_n_specs` drops anything without a 10-10 position before doing geometry
  and prints what it dropped; `full_spec` should be built from the positioned
  channels only.
- **Wu2020 types its 8 in-ear electrodes as `misc`, not `eeg`.** MOABB's
  paradigm picker keeps only `eeg`, so they disappear silently and the ear
  montage yields zero channels. Fix with `--promote LF,LB,LOU,LOD,RF,RB,ROU,ROD`
  (`eegbench.datasets.promote_channels`), which re-types them before the
  paradigm sees the data. Re-typing is an explicit modelling choice, not a data
  change.
- Wu2020 also needs `curryreader` (optional MNE dependency) to read Curry `.dat`.
- Electrode-name matching is case-insensitive everywhere (`Ft7` == `FT7`);
  datasets do not agree. 115/122 Wu2020 scalp channels have a 1005 position; the
  rest are 10-5 names (`P11`, `POO11h`, `TPP5h`) that simply are not in the set.

## Datasets of interest (`vendor/moabb/moabb/datasets/`)

| File                | Why it matters |
| ------------------- | -------------- |
| `wu2020.py`         | 132 ch: 122 scalp + 8 in-ear, simultaneous. Validates an ear-EEG simulator. |
| `lee2021_mobile.py` | `Lee2021Mobile_SSVEP` / `_ERP`: 50 ch (32 scalp + 14 ear + EOG), standing/walking/running. |
| `thielen2021.py`    | Real 8-channel optimised montage (`Fpz Iz O1 O2 Oz POz T7 T8`). |
| `thielen2015.py`    | 64-channel c-VEP. Dense reference for the same lab and paradigm. |

## Open decisions

- [ ] Target paradigm — determines which "region" is the fair comparison.
- [ ] Whether to hold model capacity fixed across channel counts.
- [ ] Tier 2: forward model (MNE `simulate_raw` vs SimNIBS lead fields).
