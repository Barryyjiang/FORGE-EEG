# EEG Electrode-Subset / Wearable Benchmark

Question: **how much classification accuracy do you lose when you go from a full
EEG cap to a region, to a wearable montage?**

This repo is the Tier-1 benchmark: it takes existing dense recordings, evaluates
matched-size electrode subsets, and reports the accuracy cost of channel count
and channel *placement*. It does **not** yet simulate wearable hardware
(Tier 2) — see "What this is not" below.

## Website

The results are also a static GitHub Pages site under `docs/`, aimed at people
outside EEG: task explainers with real signals, an interactive montage explorer
with electrode maps, and a validity section. Preview it locally with:

```powershell
.\.venv\Scripts\python.exe -m http.server 8000 --directory docs
```

The site data is generated from `results/benchmark/*.csv` by
`scripts/build_site.py`; the real-data illustrations by
`scripts/build_site_signals.py`. Publishing instructions, query parameters and
editing notes are in [`SITE.md`](SITE.md).

## Quickstart

```powershell
# offline self-test, no downloads (~1 min)
.\.venv\Scripts\python.exe scripts\run_sweep.py --fake --ks 3,5 --out results\fake.csv

# real data
.\.venv\Scripts\python.exe scripts\run_sweep.py --dataset thielen2015 --ks 4,8,16 --subjects 3 --allow-download --out results\thielen2015.csv

# list the montages
.\.venv\Scripts\python.exe scripts\run_sweep.py --list

# where data/caches live and how big they are
.\.venv\Scripts\python.exe scripts\run_sweep.py --paths
```

## Benchmark architecture

The benchmark is a cross-product of five axes, each defined declaratively:

| axis | defined in | values |
| --- | --- | --- |
| dataset | `eegbench/suite.py` | BNCI2014_001, Wu2020, Lee2021Mobile ×2, Thielen ×2 |
| paradigm | `eegbench/suite.py` | MI (left/right), P300, SSVEP, c-VEP |
| protocol | `eegbench/suite.py` | within-session, cross-session, cross-subject |
| montage | `eegbench/specs.py` | equal-N region, distributed, random, full cap, wearables |
| decoder | `eegbench/pipelines.py` | LogVar+LDA, CSP+LDA, Riemannian TSLR, Riemannian MDM, CSP+TSLR |

A **track** is one (dataset, paradigm, protocol) with its montage sizes and
decoders. Tracks carry a status so the suite stays honest about what has
actually been run:

```
[ready]           mi_leftright_22ch, motor_execution_ear_vs_scalp
[needs_download]  ssvep_mobile_ear, p300_mobile_ear
[excluded]        cvep_dense_vs_lowchannel, cvep_lowchannel
```

`excluded` tracks stay in the file with their reason, so nobody re-adds the
c-VEP datasets and rediscovers that their event markers are stimulus bits.

### Running it

```powershell
# show the matrix
.\.venv\Scripts\python.exe scripts\run_benchmark.py --list

# one track, quick
.\.venv\Scripts\python.exe scripts\run_benchmark.py --suite mi_leftright_22ch --subjects 2

# everything currently ready (resumable; skips existing outputs)
.\.venv\Scripts\python.exe scripts\run_benchmark.py --suite all

# aggregate every track into one table
.\.venv\Scripts\python.exe scripts\leaderboard.py --dir results/benchmark
```

### What makes it "comprehensive"

- **Chance level is per row.** MOABB reports ROC-AUC for 2-class and accuracy
  for multi-class; the leaderboard derives the correct chance level from
  `n_classes` so tracks are comparable.
- **Deltas are against the full cap**, so every montage is reported as a loss,
  not an absolute number that cannot be compared across datasets.
- **Random-subset controls** are built into every equal-N condition. Without
  them a "region" result is unfalsifiable.
- **Resumable output.** One CSV per (track, protocol); re-running skips
  completed files, so a multi-day sweep can be stopped and restarted.
- **Decoders are opt-in.** The three cheap classical baselines are the default.
  Deep models are deliberately not in the default set: EEGNet needed two
  silent fixes (label encoding, microvolt scaling) before its numbers meant
  anything at all, and it is still unstable.

### Protocol axis: two corrections worth keeping

**1. A false alarm.** An early comparison showed 0.965 within-session vs 0.793
cross-session, which looked like trial-block leakage. It was subject
composition: the first number came from one subject, the second from two.

With 9 subjects and n=18 per cell, the protocol effect on BNCI2014_001 is
**~0.01** — full cap 0.869 (within) vs 0.860 (cross). Within-session evaluation
is not inflated here. Protocol still changes the *question* (same session vs new
session), and it must be reported, but it is not a source of bias in this track.

**2. A real contamination bug.** MOABB keeps an on-disk result cache keyed by
pipeline. A run that reused entries written by an earlier script returned rows
labelled `CSP+LDA` while the new run called the same estimator `csp_lda` — one
result file contained two naming schemes, which silently split every group in
the leaderboard. `run_benchmark.py` now forces `overwrite=True` on the
evaluation unless `--reuse-cache` is passed explicitly.

Both are recorded because a benchmark is only as trustworthy as its known
failure modes:

- never compare protocols across different subject sets;
- a single subject can move an AUC by 0.15, so n<5 cannot rank montages;
- cached results are keyed by name, and names drift between scripts.

### Powered benchmark result — `mi_leftright_22ch`

9 subjects, n=18 per cell, ROC-AUC. Every number below is regenerable with
`run_benchmark.py` and carries the same schema, chance level and full-cap
reference.

**Decoder axis (full cap, k=22):**

| decoder | within-session | cross-session |
|---|---|---|
| `riemann_tslr` | **0.871** | **0.860** |
| `csp_lda` | 0.829 | 0.817 |
| `logvar_lda` | 0.775 | 0.749 |

Decoder ranking is stable across protocols, which is what makes the decoder
axis usable as a benchmark dimension rather than noise.

**Montage axis (Riemannian):**

| k | montage | within | cross |
|---|---|---|---|
| 4 | sensorimotor region | 0.741 | 0.751 |
| 4 | random (3 seeds) | 0.645–0.713 | 0.667–0.699 |
| 8 | sensorimotor | 0.794 | 0.786 |
| 8 | random | 0.766–0.785 | 0.752–0.784 |
| 16 | distributed | 0.817 | 0.814 |
| 16 | random | 0.828–0.855 | 0.830–0.843 |
| 22 | full cap | 0.871 | 0.860 |

The placement effect is real at k=4 (+0.04 to +0.07 for the sensorimotor region
over random subsets), gone by k=8, and slightly negative at k=16 where random
subsets match the cap. Protocol shifts each cell by ~0.01 — smaller than the
k=4 placement effect, so the montage conclusion is not a protocol artefact.

### Axis status

| axis | state | evidence |
| --- | --- | --- |
| paradigms | MI, SSVEP, P300 live; c-VEP excluded after verification | P300 0.858 (n=8), SSVEP 0.772 (n=1) |
| decoders | 8 registered, 3 default | `ssvep_cca`, `xdawn_tslr`, `bandpower_ridge` added |
| ITR | live for accuracy-scored tracks | 30.3 bits/min at 4 occipital electrodes |
| signal quality | live, computed on raw data | rejection 2–6%, line-noise 0.98–3.5 |
| continuous tasks | **live** — sleep staging runs | ear κ=0.755 vs scalp κ=0.754 (chance 0) |

**Paradigm-specific decoders are not optional.** Both new tracks sat at chance
with the generic decoders and only became meaningful with the field's standard
method:

| track | generic decoder | correct decoder |
| --- | --- | --- |
| SSVEP | 0.133 (LogVar) | **0.772** (`ssvep_cca`) |
| P300 | 0.487 (LogVar) | **0.831** (`xdawn_tslr`) |

A benchmark that reports near-chance on a well-known paradigm is measuring
decoder mismatch, not montage quality. `PARADIGM_SPECIFIC` in `pipelines.py`
records which decoders belong to which paradigm so this cannot be silently
crossed again.


**ITR is not cosmetic.** On `ssvep_8ch`, four well-spread occipital electrodes score
0.772 accuracy (30.3 bits/min) against 0.689 for the full 8-channel cap (24.2
bits/min). Ranking by AUC would have missed a result where fewer electrodes win.

**Two bugs this axis exposed, both silent:**

- The full cap was being dropped by de-duplication on 8-electrode datasets,
  because full and distributed subsets are then the same channel set — every
  delta would have been measured against a missing reference.
- Quality metrics were first computed on the paradigm's 8–32 Hz epochs, which
  removed the 50 Hz line noise and flattened amplitude: `line_noise_ratio` was
  0.966 for every montage and `reject_rate` was exactly 0.000. A metric that
  cannot vary is not measuring anything.

### Sleep staging: the ear is close, not equal

The canonical wearable continuous task, on OpenNeuro ds004348 (ear-EEG), scored
with Cohen's kappa (chance 0, block-wise CV over 20-epoch blocks so adjacent
30 s windows cannot leak).

**Matched 6-vs-6, 5 subject-nights:**

| montage | channels | kappa |
|---|---|---|
| scalp (C3 O1 F3 C4 O2 F4) | 6 | 0.519 mean over subjects |
| ear (ELB ELG ELK ERB ERG ERK) | 6 | 0.473 |

Paired difference **−0.046, 95% CI [−0.075, −0.016]**, negative in **5/5**
subjects.

**Correction to an earlier version of this section.** On subject 1 alone, 14
ear channels looked equal to 6 scalp (0.755 vs 0.754). Across all five nights
the 14-channel ear averages **0.498** against **0.519** for 6 scalp channels —
so extra channels did not close the gap; subject 1 was the exception. At
matched count the ear is consistently behind.

The substantive point survives and sharpens: compared with motor execution,
where in-ear electrodes sit at chance (0.464 AUC vs 0.739 scalp), sleep staging
from the ear reaches kappa ≈ 0.47–0.73. **The ear deficit is task-dependent**,
and at equal channel count it costs about 0.05 kappa for sleep — not the
collapse seen in motor tasks.

```powershell
.\.venv\Scripts\python.exe scripts\sleep_track.py --subjects 001,002,003,004,005
```

### Adding a dataset or decoder

A new track is one entry in `SUITE`; a new decoder is one entry in `REGISTRY`.
Nothing else changes — the runner and leaderboard pick both up automatically.

## Analysis workflow

Three scripts, in order:

| script | purpose |
| --- | --- |
| `run_sweep.py` | evaluate every subset, write per-trial CSV |
| `plot_sweep.py` | accuracy-vs-k figure with SEM error bars |
| `compare.py` | **paired** delta vs the full cap, with 95% CI and Wilcoxon p |

```powershell
.\.venv\Scripts\python.exe scripts\run_sweep.py --dataset bnci2014_001 --ks 4,8,16 --subjects 9 --out results\bnci_s9.csv
.\.venv\Scripts\python.exe scripts\plot_sweep.py results\bnci_s9.csv
.\.venv\Scripts\python.exe scripts\compare.py results\bnci_s9.csv --pipeline "CSP+LDA"
```

`compare.py` pairs on subject-session, so between-subject variance cancels. That
matters more than it sounds: at n=4 the unpaired SEM is larger than every
between-strategy difference, so an unpaired report would be meaningless.


## Design

### Equal-N comparison

The question "is a region better than a subset?" is only meaningful at fixed
channel count. Asking it with a 9-electrode region against a 4-electrode subset
measures count, not placement.

`eegbench.subsets.equal_n_specs(available, k)` therefore emits, all with exactly
`k` channels:

| strategy      | what it is                                           |
| ------------- | ---------------------------------------------------- |
| `full`        | the whole cap (ceiling)                              |
| `distributed` | greedy farthest-point spread across the head         |
| `region-*`    | one per 10-10 region, truncated to `k` by spread     |
| `random-*`    | chance-level control, `n` seeds                      |
| wearable montages | real or proxy device layouts                     |

`farthest_point_order` produces a *nested* ordering, so prefixes of length
`k = 2..N` give a monotone accuracy-vs-k curve from a single selection pass.

### Fidelity labels

Every montage carries a `fidelity` field, and it is not decoration:

- `measured` — a real device's documented electrode positions
  (`muse2`, `thielen2021`).
- `proxy` — the nearest standard 10-10 ring standing in for a device whose
  electrodes are not in the nomenclature (`ceegrid_proxy`, `earbud_proxy`).
  Reasonable geometry, **not** a claim about that device's accuracy.
- `synthetic` — ablation only.

Do not report a `proxy` result as "accuracy of device X".

### What is held constant

Model capacity is **not** held constant by default, because that is not what a
wearable deployment does — a 4-channel product would not ship a 64-channel
model. If you want the "electrode count alone" effect, you must additionally
sweep model capacity and report both. Keep this in mind when reading the curves:
part of the 4-channel drop is genuinely fewer electrodes, part is less overfitting.

## What this is not

Deleting channels from a dense cap is **not** a wearable simulation. It ignores:

- the **reference** (wearables use a local/contralateral reference; average
  reference over 4 channels is a completely different signal)
- **volume conduction** through skull and CSF at the wearable's positions
- the wearable's **noise floor**, motion artifact, and electrode impedance
- the fact that an in-ear electrode sees a different **mixture**, not a cleaner
  scalp channel

Tier 2 (forward-model simulation with `mne.simulation` / SimNIBS lead fields) is
what addresses those. Validate any Tier-2 simulator against datasets that
record scalp and ear electrodes **simultaneously** — `Wu2020` (122 scalp + 8
in-ear) and `Lee2021Mobile_SSVEP` / `_ERP` (32 scalp + 14 ear) — before trusting
it on data where you only have scalp.

## Layout

```
eegbench/
├── names.py       channel-name normalisation (Cz vs CZ, EEG prefix)
├── montages.py    scalp regions + wearable layouts, fidelity labels
├── subsets.py     farthest-point / random orderings, equal-N specs
└── benchmark.py   MOABB sweep driver + summarise()
scripts/
├── smoke_test.py  environment check
└── run_sweep.py   CLI
vendor/            moabb, braindecode (editable clones)
```

`vendor/` exists so the repo directories cannot shadow the installed packages as
namespace packages when you run from the project root.

## Known limitations

- **The c-VEP pairing does not work with a generic pipeline.** `Thielen2015` /
  `Thielen2021` expose stimulus *bit* events (`1.0`/`0.0`), not the 20 speller
  symbols, so `CVEP` + `LogVar+LDA` produces a 2-class problem that sits at
  ROC-AUC 0.5 by construction. c-VEP needs template matching / CCA /
  reconvolution. Pick `SSVEP`, `P300` or motor imagery for a first real result.
- Model capacity is not held constant (see above).
- Proxy montages are geometry only.

## First result — `BNCI2014_001`, left vs right hand

9 subjects × 2 sessions = 18 paired observations, ROC-AUC, CSP+LDA, full cap
(22 ch) = **0.825**.

| k | subset | score | Δ vs full | 95% CI | p |
|---|---|---|---|---|---|
| 4 | sensorimotor region | 0.744 | −0.082 | [−0.144, −0.019] | 0.003 |
| 4 | parietal region | 0.722 | −0.103 | [−0.154, −0.052] | 0.001 |
| 4 | distributed (farthest-point) | 0.697 | −0.128 | [−0.181, −0.076] | <0.001 |
| 8 | sensorimotor region | 0.780 | −0.045 | [−0.091, 0.000] | 0.012 |
| 8 | distributed | 0.776 | −0.049 | [−0.106, 0.008] | 0.081 |
| 16 | distributed | 0.788 | −0.038 | [−0.082, 0.007] | 0.049 |

Two findings:

1. **At k=4, placement dominates count.** The sensorimotor region beats the
   spatially spread subset by +0.047 (pairwise Wilcoxon p = 0.0013). Spreading
   electrodes to maximise coverage is the wrong objective for a focal source.
2. **At k=8 that advantage disappears** (+0.004, p = 0.93), and by k=16 the loss
   versus the full cap is inside the noise band. Eight electrodes in the right
   region recover ~95% of full-cap accuracy here.

Caveat: `BNCI2014_001` contains only central/parietal channels — no frontal,
occipital or temporal electrodes. It can test *focal vs spread*, but it cannot
test *wrong region*, which is the more interesting question for wearables.

Reproduce:

```powershell
.\.venv\Scripts\python.exe scripts\run_sweep.py --dataset bnci2014_001 --ks 4,8,16 --subjects 9 --random-seeds 3 --out results\bnci2014_001_s9.csv
.\.venv\Scripts\python.exe scripts\compare.py results\bnci2014_001_s9.csv --pipeline "CSP+LDA"
```

## Second result — `Wu2020` in-ear vs scalp

This is the question scalp-only data cannot answer. `Wu2020` records a
122-channel cap **and** 8 in-ear electrodes on the same head, same session.
Motor execution (left/right fist), 6 subjects, CSP+LDA, ROC-AUC, full cap
(115 positioned channels) = **0.741**.

Paired against the full cap:

| k | subset | score | Δ vs full | 95% CI | p |
|---|---|---|---|---|---|
| 8 | **sensorimotor region** | 0.717 | −0.024 | [−0.107, +0.059] | 0.56 |
| 8 | distributed | 0.660 | −0.081 | [−0.228, +0.066] | 0.31 |
| 8 | region frontal | 0.558 | −0.183 | [−0.338, −0.028] | 0.06 |
| 8 | region temporal | 0.517 | −0.224 | [−0.393, −0.055] | 0.06 |
| 6 | `ceegrid_proxy` | 0.498 | −0.243 | [−0.372, −0.114] | 0.03 |
| 8 | **`wu2020_inear`** | 0.457 | −0.284 | [−0.460, −0.108] | 0.06 |

Against the sensorimotor montage **at matched k=8**:

| subset | Δ vs sensorimotor | 95% CI | p |
|---|---|---|---|
| `wu2020_inear` | −0.259 | [−0.369, −0.150] | 0.031 |
| region temporal | −0.200 | [−0.340, −0.060] | 0.031 |
| region frontal | −0.159 | [−0.285, −0.033] | 0.031 |
| random scalp | −0.082 | [−0.115, −0.049] | 0.031 |
| distributed | −0.057 | [−0.127, +0.013] | 0.156 |

**Finding: the loss is placement, not count.** Eight scalp electrodes over the
right cortex are statistically indistinguishable from the 115-channel cap
(−0.024, CI spans 0). Eight in-ear electrodes at the *same count* sit at
chance. Count is not the binding constraint; position is.

Caveats, in order of importance:

1. This **contradicts the published result** for this dataset. Wu et al. report
   above-chance in-ear classification with methods designed for it. Our
   CSP+LDA is a motor-cortex pipeline applied to ear data, so "ear is at chance"
   is at least partly a pipeline limitation, not proof that ear-EEG is
   uninformative. Reproduce with the paper's approach before writing this up.
2. n=6, and 0.031 is the Wilcoxon floor at n=6 (all six subjects agree in sign).
   "p = 0.031" means "unanimous", not "highly significant".
3. `muse2`, `ceegrid_proxy`, `earbud_proxy`, `headband_proxy` are **scalp
   approximations** of where those devices sit. Their scores (0.47–0.55) say
   nothing about the real products.
4. Motor *execution*, not imagery.

Reproduce:

```powershell
.\.venv\Scripts\python.exe scripts\run_sweep.py --dataset wu2020 --ks 8 --mode both --promote LF,LB,LOU,LOD,RF,RB,ROU,ROD --allow-download --random-seeds 2 --pipelines csp,logvar --out results\wu2020_all6.csv
.\.venv\Scripts\python.exe scripts\compare.py results\wu2020_all6.csv --pipeline "CSP+LDA" --baseline region-sensorimotor
```

### Why the ear montage is at chance

Is it the decoder, or is the signal absent? Single-channel test: beta band
(13–30 Hz) log-power, one feature per electrode, LDA, 5-fold CV, per subject.

| channel | mean AUC | |
|---|---|---|
| CP1 | 0.590 | scalp |
| CPP4h | 0.581 | scalp |
| CCP4h | 0.579 | scalp |
| CP4 | 0.566 | scalp |
| RB | 0.486 | **ear** |
| RF | 0.482 | **ear** |
| ROD | 0.477 | **ear** |
| LOU | 0.464 | **ear** |

No single ear electrode carries linearly-decodable beta information, so CSP
collapsing to chance is consistent rather than a decoder bug. Note the ceiling
is low overall (best scalp channel 0.590) — this is a hard, weakly-localised
task even on the cap.

This narrows the question but does not close it: it tests one band and one
feature family. The published ear-EEG result may rely on temporal ERD
time-courses rather than band-power, which this does not evaluate.

### Feature representation does not rescue the ear

Same 8 channels, same CV folds (5-fold × 3 repeats), only the features change.
`temporal` = log band-power in 8 consecutive windows (ERD time course);
`bandpower` = one value per channel per band.

| model | montage | mean AUC | sd |
|---|---|---|---|
| bandpower | scalp sensorimotor | **0.702** | 0.101 |
| temporal | scalp sensorimotor | 0.666 | 0.120 |
| temporal | **ear** | 0.503 | 0.069 |
| bandpower | **ear** | 0.456 | 0.040 |

Two observations:

1. Ear rises to **exactly chance** (0.503) — it does not become decodable.
2. Temporal features *hurt* the scalp montage (0.702 → 0.666), so they are not
   a better representation for this task at all; they add variance without
   adding discriminability.

Per-subject, scalp minus ear is positive in **12/12** cells, from +0.075 to
+0.373. The gap narrows (0.246 → 0.163) but never closes.

```powershell
.\.venv\Scripts\python.exe scripts\temporal_ear_test.py --subjects 6 --models bandpower,temporal
```

### EEGNet: inconclusive, not a null result

| model | scalp sensorimotor | ear |
|---|---|---|
| EEGNet | **0.513** ± 0.020 | 0.497 ± 0.042 |

This must not be read as evidence that the ear is uninformative. Two problems:

1. **It fails on the control.** 0.513 on the scalp montage that linear models
   decode at 0.702. A decoder that cannot learn the positive control cannot
   testify about the target.
2. **It is unstable.** Subject 1 scored 0.601 in a single-subject run and 0.513
   in the full run — same data, same folds, same CV seed. Only network weight
   initialisation differed. 40 epochs with no seeding does not converge
   reliably.

Two earlier failure modes were also silent and worth recording, because both
produced plausible-looking chance results:

- string labels (`left_hand`) crash skorch — fixed with a `LabelEncoder`;
- EEG in **volts** (~1e-5) leaves the first convolution with unworkable
  gradients, so EEGNet sits at chance on every montage. Converting to
  microvolts moved the scalp control 0.456 → 0.601.

Before this becomes a usable replication it needs seeded initialisation, early
stopping, and probably augmentation. **Until the scalp control clears ~0.65,
ear numbers from EEGNet are uninterpretable.**



```powershell
.\.venv\Scripts\python.exe scripts\channel_diagnostics.py --dataset wu2020 --subjects 6 --band 13,30
```




