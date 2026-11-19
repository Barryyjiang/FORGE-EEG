# The Electrode Budget

**How much EEG accuracy survives when a lab cap becomes a wearable?**

A lab EEG cap has 64–128 electrodes. A consumer wearable has two to eight. This
benchmark holds the channel budget and the decoder fixed, then changes *where*
the electrodes sit. It answers two questions with the same rows:

1. **How many** electrodes do you need?
2. **Where** do they have to be?

Eight public datasets, nine tasks, one fixed classical pipeline per task. Where
a dataset has wearable electrodes they were physically recorded alongside a
scalp cap; where it does not, the reduced montage is a scalp proxy and is
labelled as one rather than passed off as a device.

**Website:** two static pages under `docs/`. The paper page is generated from
the results; the explorer is hand-written HTML around a generated data bundle.

- `/` — the **paper page**: title, abstract, six figures, six tables, citation.
  Prose lives in `paper/paper.html`; tables, figures and every inline number are
  written by `scripts/build_paper.py` and `figures/build_figures.py`.
- `/explore/` — the **interactive explorer**: every montage, per decoder, with
  head maps. Its numbers come from `scripts/build_site.py`.

Deployment and editing instructions are in [`SITE.md`](SITE.md).

---

## Results at a glance

All deltas are paired within subject; brackets are 95% confidence intervals.
Full task details and per-decoder tables are in [`results/REPORT.md`](results/REPORT.md).

| task | dataset | n | metric | reference | best reduced montage | delta |
|---|---|---|---|---|---|---|
| Motor imagery | BNCI 2014-001 | 9 × 2 sessions | ROC-AUC | **0.871** (22 ch) | 0.794 (sensorimotor 8) | −0.077 [−0.120, −0.035] |
| Motor imagery, 4 classes | BNCI 2014-001 | 9 × 2 sessions | accuracy | **0.722** (22 ch) | 0.613 (sensorimotor 8) | −0.108 [−0.144, −0.073] |
| P300 speller | BNCI 2014-008 | 8 | ROC-AUC | **0.858** (8 ch) | 0.812 (spread 4) | −0.046 [−0.067, −0.025] |
| SSVEP | Nakanishi 2015 | 10 | accuracy | **0.928** (8 ch) | 0.914 (spread 4) | −0.014 [−0.052, +0.024] |
| Motor execution | Wu 2020 | 6 | ROC-AUC | **0.775** (115 ch) | 0.739 (sensorimotor 8) | −0.036 [−0.144, +0.073] |
| Sleep staging | OpenNeuro ds004348 | 9 nights | Cohen’s κ | **0.418** (scalp 6) | 0.362 (ear 6) | −0.056 [−0.104, −0.009] |
| Cognitive workload | STEW | 48 | ROC-AUC | **0.874** (14 ch) | 0.844 (glasses-like 4) | −0.030 [−0.059, −0.001] |
| Auditory attention | Ear-SAAD | 15 | accuracy | **0.807** (scalp 12) | 0.626 (in-ear 12) | −0.181 [−0.249, −0.114] |
| Emotion recognition | FACED | 123 | balanced acc. | **0.570** (30 ch) | 0.558 (posterior 4) | −0.012 [−0.030, +0.006] |

For SSVEP, information transfer rate is 44.5 bits/min at the full 8-channel cap
and 43.0 bits/min with four occipital electrodes. The sleep reference is the
matched six-channel scalp montage because that dataset has no dense cap.

### Wearable comparison

Wu 2020 records a 115-channel scalp cap and eight in-ear electrodes at the same
time. At the same eight channels, in the same session, and with the same decoder:

| montage | ROC-AUC |
|---|---|
| sensorimotor scalp, 8 ch | **0.739** |
| in-ear, 8 ch | **0.464** |

Paired difference **−0.275 AUC, 95% CI [−0.378, −0.173]**, negative in **6/6**
subjects. The ear is not missing channels; it is missing the focal sensorimotor
source.

The sleep track inverts the result. With six ear electrodes against six scalp
electrodes, across nine nights:

| montage | Cohen’s κ |
|---|---|
| scalp, 6 ch | **0.418** |
| ear, 6 ch | **0.362** |
| ear, all 14 ch | 0.388 |

Paired difference **−0.056 κ, 95% CI [−0.104, −0.009]**, negative in **9/9**
nights. Extra ear channels close part of the gap but do not erase it.

**The wearable cost is task-dependent.** Broad, slow sleep activity reaches the
ear; a focal sensorimotor rhythm does not.

### Class count is a hidden variable

The same nine people and the same 22-channel cap, cued for four classes instead
of two (left hand, right hand, feet, tongue), reach 0.722 accuracy at the full
montage and 0.613 at the same eight sensorimotor electrodes: **85.0% retained,
against 91.1% for two classes**. The paired loss grows from 0.077 to 0.108
(95% CI [−0.144, −0.073], negative in 18/18 subject-sessions).

The reason is spatial: feet and tongue are represented near the midline, while
the sensorimotor patch is lateralised over C3 and C4. Asking a lateralised
montage for two more classes costs more than the electrode count alone suggests,
so "eight electrodes are enough" is a claim about a task, not about a head.

### The ear runs out of electrodes before the scalp does

Sweeping the channel budget at a fixed 60 s decision window, with the *k* most
spatially spread electrodes inside each array and *k* spread scalp electrodes as
a matched reference:

| k | in-ear | around-ear | scalp |
|---|---|---|---|
| 2 | 0.553 | **0.664** | 0.653 |
| 4 | **0.617** | 0.678 | 0.731 |
| 8 | 0.619 | 0.674 | 0.810 |
| 12 | 0.626 | 0.681 | 0.805 |
| 19 | — | 0.689 | 0.817 |

Four in-ear electrodes already reach 0.617 of a twelve-electrode ceiling of
0.626 — eight more electrodes buy **0.009**. The around-ear array is flat from
two electrodes on. The scalp reference over the same budgets climbs from 0.653 to
0.817. Adding ear electrodes is not a route to better decoding; changing the site
is.

One caveat that matters at low *k*: M1 and M2 are mastoid references sitting a
couple of centimetres from the ear arrays. Including them lifts the two-electrode
scalp score from 0.653 to 0.731, which is larger than the whole scalp-vs-ear gap
at that budget, so the curve excludes them. At k≥12 the difference is 0.002.

### The three new paradigms

**Cognitive workload (STEW).** 48 participants, a 14-channel Emotiv headset, a
150-second rest recording and a 150-second SIMKAP multitasking recording. Scored
with the decoder never seeing the test person: the full 14 channels reach 0.874
AUC, a four-electrode frontal “glasses-like” subset keeps 96.6% of that, and
those same four electrodes beat a four-electrode posterior subset by +0.084 AUC
(95% CI [+0.037, +0.132]). They also sit at the 90th percentile of 100 random
four-electrode draws. Here the useful site is the front of the head, not the
back.

The task carries a confound that no analysis removes: rest was always recorded
before the task, so the conditions sit on opposite sides of a session boundary.
A label-free control asked only “first half or second half of this recording?”
and scored 0.613 against a shuffled-halves null of 0.501. The result is reported
as rest-versus-SIMKAP **condition recognition**, never as a validated workload
score. That it transfers to an unseen person at all is evidence that much of what
it reads is gross and universal rather than neural.

**Auditory attention (Ear-SAAD).** The only public dataset that records 29 scalp,
19 around-ear and 12 in-ear electrodes simultaneously while a participant follows
one of two talkers. At the paper’s 60-second decision window, twelve in-ear
electrodes decode at 0.626 against 0.807 for the twelve most spread scalp
electrodes — a paired loss of 0.181 (95% CI [0.114, 0.249], negative in 14/15).
At nineteen electrodes the around-ear array loses 0.131 against a matched scalp
nineteen. This is the largest wearable cost in the benchmark, and the one that
matters most, because attention decoding is why ear-EEG exists.

It is a latency cost rather than a wall: twelve in-ear electrodes climb from
0.519 at a one-second window to 0.626 at sixty seconds and 0.844 at ten minutes,
while the matched scalp twelve goes from 0.548 to 0.807 and 0.967. The ear does
not fail to carry the signal; it needs longer to decide.

The released preprocessedData.zip already contains the authors’ full
preprocessing pipeline, ASR included. `scripts/earsaad_paper_check.py` confirms it
numerically: our 60-second accuracies land on the paper’s with-ASR column
(83.44 / 67.22 / 61.11) rather than its no-artifact-removal ablation
(86.11 / 64.89 / 58.78). There is nothing to re-run, and re-running ASR on 20 Hz
data would be wrong.

---

## Three findings

1. **Placement is the main effect.** At a fixed eight channels in motor
   execution, sensorimotor scalp scores 0.739, frontal 0.544, temporal 0.525,
   and in-ear 0.464. In motor imagery, eight sensorimotor electrodes keep 91% of
   the 22-channel score *on average* — but that mean hides a range of 70–100%
   across the 18 subject-sessions, so for some participants the reduction costs
   far more than the headline. Count matters, but only after the electrodes are
   over the right source.

2. **Decoder choice rivals montage choice.** The same eight P300 channels score
   0.536 with a generic log-variance decoder and 0.858 with xDAWN. SSVEP has the
   same structure: covariance and band-power are not the right tool; CCA is. A
   benchmark without the paradigm’s standard decoder measures decoder mismatch.

3. **Wearables are task-dependent.** The same ear site loses 0.275 AUC on motor
   execution and 0.056 κ on sleep. The difference is the signal, not the
   electrode: sleep is broad and slow, motor execution is focal and fast.

**Emotion (FACED).** The largest cohort in the benchmark: 123 participants,
30 scalp electrodes, videos chosen to elicit a particular emotion. Binary
valence decodes at **0.570** balanced accuracy against 0.5 chance — a real
effect, significant across participants (t = +8.6, p < 10⁻¹²), but a small
one. Four posterior electrodes reach 0.558, a paired loss of 0.012
(95% CI [−0.030, +0.006]) that includes zero.

The placement result points the opposite way from workload. A glasses-like
frontal four scores 0.553, below the posterior four, and sits only at the
**65th percentile** of twenty random four-electrode draws while the posterior
four sits at the 80th. Frontal electrodes are where a glasses frame would put
them, and for this task they are the wrong choice.

Read the retention against the margin: 98% of a score that is only seven
points above chance is not the same claim as 98% of 0.928. A task whose whole
effect is small supports a weak statement about what a wearable preserves, not
a strong one.

---

## Validity

Every number on the site is regenerated from the CSVs in `results/benchmark/`.
The design rules that make the comparisons interpretable:

- **Matched channel counts.** Region, spread, random, and wearable comparisons
  use exactly *k* electrodes on both sides. A difference is placement, not count.
- **Paired by subject.** Deltas pair each participant with themselves. The
  confidence intervals above are paired t intervals.
- **Permutation controls.** Each task’s headline decoder and channel subset is
  re-run on shuffled labels: 100 shuffles for MI, SSVEP and motor execution, 20
  for P300 (its null SD is small), and 200 block permutations for sleep, on
  every night. A circular shift is not a valid sleep null — it preserves the
  stage runs and the band-power drift, leaving the null at κ≈0.13 instead of 0
  — so whole 20-epoch blocks are permuted. Every null is within 0.05 of chance,
  checked per control row rather than on an average. The report refuses to
  write if a control exceeds its tolerance.
- **Measured wearables first, proxies labelled.** The in-ear montage is Wu 2020’s
  eight physical in-ear electrodes; the sleep ear montage is ds004348’s 14
  physical ear electrodes; the Ear-SAAD arrays are 19 around-ear and 12 in-ear
  electrodes recorded at the same time as the cap. The workload headset has no ear
  recording, so its frontal sets are scalp proxies and carry `fidelity: proxy` in
  every result file and in the explorer. No nearest-neighbour stand-in for a
  commercial device is scored anywhere.
- **Full cohorts.** 9, 8, 10, 6, 9, 48 and 15 subjects/nights — the complete
  public datasets used here, not a convenient subset. Two are small (6 and 9),
  and their intervals are reported rather than hidden.
- **Confounds are measured, not argued away.** STEW recorded rest before the
  task, so the workload track ships a label-free drift control alongside its
  score; the number is reported as condition recognition, not workload.
- **Reproduction is checked against the source.** `scripts/earsaad_paper_check.py`
  compares the attention track against both columns the original paper publishes,
  which is how the “the release is already artifact-cleaned” claim is settled.
- **Fixed pipelines.** One standard decoder per task, chosen before the montage
  results and never tuned per montage. The sleep track is the one exception to
  the decoder registry: its band-power + LDA lives in
  [`scripts/sleep_track.py`](scripts/sleep_track.py), because it is the only
  task that is not a MOABB paradigm.

---

## Reproduce

```powershell
# whole suite: benchmark, sleep, controls, quality, report
.\.venv\Scripts\python.exe scripts\run_all.py

# fast path: skip the two ear datasets
.\.venv\Scripts\python.exe scripts\run_all.py --skip-heavy

# one task
.\.venv\Scripts\python.exe scripts\run_benchmark.py --suite mi_leftright_22ch

# rebuild the site data (no raw datasets needed)
.\.venv\Scripts\python.exe scripts\build_site.py

# rebuild the paper figures (PNG for the page, PDF for print)
.\.venv\Scripts\python.exe figures\build_figures.py

# rebuild the paper page itself
.\.venv\Scripts\python.exe scripts\build_paper.py

# the two paradigm-level extensions, and their controls
.\.venv\Scripts\python.exe scripts\stew_raw_track.py
.\.venv\Scripts\python.exe scripts\stew_drift_control.py
.\.venv\Scripts\python.exe scripts\auditory_attention_track.py --subjects all
.\.venv\Scripts\python.exe scripts\auditory_attention_control.py
.\.venv\Scripts\python.exe scripts\earsaad_paper_check.py

# emotion: extract per-participant features once from the FACED BIDS
# release, then run the track from the cache
.\.venv\Scripts\python.exe scripts\faced_extract_features.py
.\.venv\Scripts\python.exe scripts\faced_emotion_track.py

# regenerate the real-data illustrations (needs the raw datasets)
.\.venv\Scripts\python.exe scripts\build_site_signals.py

# check that every quoted number still traces to a CSV, and that the
# generated pages carry no unresolved placeholder
.\.venv\Scripts\python.exe scripts\verify.py

# preview
.\.venv\Scripts\python.exe -m http.server 8000 --directory docs
```

`run_all.py` uses 100 shuffles for MI/SSVEP/motor, 20 for P300, and 200 block
permutations for sleep. The first full run downloads the public datasets and takes
hours; later runs reuse the cache.

---

## Repository layout

```
eegbench/
├── suite.py        task definitions (dataset, paradigm, protocol, ks)
├── montages.py     scalp regions + measured wearable layouts
├── subsets.py      farthest-point / random orderings, equal-N specs
├── benchmark.py    MOABB sweep driver
├── pipelines.py    decoder registry
└── leaderboard.py  chance-aware aggregation
scripts/
├── run_all.py      one entry point
├── run_benchmark.py
├── sleep_track.py  BIDS sleep adapter
├── stew_raw_track.py           cognitive workload (raw IEEE DataPort release)
├── stew_drift_control.py       label-free session-drift control for STEW
├── auditory_attention_track.py auditory attention (Ear-SAAD)
├── auditory_attention_control.py  trial-shuffle control for the AAD track
├── earsaad_paper_check.py      reproduction check against the paper
├── permutation_control.py
├── report.py
├── build_site.py   explorer data bundle
├── build_paper.py  renders docs/index.html from paper/paper.html
└── build_site_signals.py
figures/            publication figures (matplotlib, PNG + PDF)
paper/              paper page template (prose + placeholders)
docs/               static GitHub Pages site: paper at /, explorer at /explore/
results/            derived CSVs and REPORT.md
```

---

## Scope

This is an **electrode-subset benchmark**, not a simulation of a specific
product. It measures how much decodable signal is present at a site with a fixed
classical pipeline. It does not model a particular wearable’s amplifier,
reference scheme, impedance, or motion artifact; those are hardware questions,
and the right next step is a forward-model study validated against the
simultaneous scalp-and-ear recordings used here.

The decoders are deliberately classical and trained from scratch inside every
fold. No pretrained weights, no fine-tuning, and no per-montage hyperparameter
search. The point is to compare electrode layouts on equal terms, not to win a
leaderboard.

---

## Data sources

| dataset | task | participants | channels |
|---|---|---|---|
| [BNCI 2014-001](http://bnci-horizon-2020.eu/database/data-sets) | motor imagery | 9 × 2 sessions | 22 EEG |
| [BNCI 2014-008](http://bnci-horizon-2020.eu/database/data-sets) | P300 speller | 8 | 8 EEG |
| [Nakanishi 2015](https://doi.org/10.1371/journal.pone.0114853) | SSVEP | 10 | 8 occipital |
| [Wu 2020](https://doi.org/10.1088/1741-2552/abc1b6) | motor execution | 6 | 122 scalp (115 with a 10-5 position) + 8 in-ear |
| [OpenNeuro ds004348](https://doi.org/10.18112/openneuro.ds004348.v1.0.5) | sleep staging | 9 nights | 6 scalp + 14 ear |
| [STEW](https://doi.org/10.21227/44r8-ya50) | cognitive workload | 48 | 14 (Emotiv EPOC) |
| [Ear-SAAD](https://zenodo.org/records/16536441) | auditory attention | 15 | 29 scalp + 19 around-ear + 12 in-ear |
| [FACED](https://nemar.org/dataexplorer/detail?dataset_id=nm000112) | emotion recognition | 123 | 30 scalp |

All datasets are public and permissively licensed. `SETUP.md` records the
environment and dataset commits; `SITE.md` documents the static site.

The Wu 2020 "full cap" reference is the **115 scalp channels that have a 10-5
position**, because geometric subsetting needs coordinates. Its other 7 scalp
channels are never part of a subset comparison, so `full_k115` is one channel
short of the dataset's 122-channel scalp montage.
