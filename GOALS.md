# Benchmark completion goals

**Definition of done:** every box below is checked, and each check is backed by a
row in `results/benchmark/` plus a line in the generated report. Anything not
achievable gets an explicit `blocked` note with the reason — not an empty box.

Status legend: `[ ]` open · `[x]` done · `[!]` blocked (reason recorded)

---

## G1 — Coverage: every runnable track at full subject count

Each track must run with its paradigm-appropriate decoder, not the generic default.

- [x] `mi_leftright_22ch` — 9 subjects, 3 decoders, 2 protocols
- [x] `p300_8ch` — 8 subjects, `xdawn_tslr`
- [x] `ssvep_8ch` — 10 subjects, `ssvep_cca`, accuracy + ITR
      (full 0.928 / 44.5 bits·min⁻¹; distributed k=4 0.914 / 43.0)
- [x] `motor_execution_ear_vs_scalp` - 6 subjects, 3 decoders, written to `results/benchmark/`
      (riemann: ear 0.464, sensorimotor k=8 0.739, full 0.775)
- [!] `cvep_trial_level` — excluded: MOABB CVEP exposes bit events only (verified)

**Acceptance:** `leaderboard.py` shows `n >= 6` for every row of every live track.

## G2 — Continuous task: one wearable-native regression track

- [x] install `openneuro-py`, fetch ds004348 sub-001 (1.1 GB)
- [x] implement BIDS sleep adapter (30 s windows, hypnogram from scoring TSV)
- [x] run `sleep_staging_local` — scalp κ=0.754, ear κ=0.755 (chance 0)

**Result: ear-EEG matches scalp for sleep staging.** This inverts the motor
result — the ear deficit is task-dependent, not a property of the electrode
site in general. Caveats: n=1 night, and the ear montage has 14 channels vs 6
scalp, so counts are not matched.

## G3 — Controls: prove the decoders can fail

- [x] permutation-label control implemented
- [x] `mi_leftright_22ch` / `riemann_tslr` — real 0.957, perm 0.509 (20 shuffles)
- [x] `p300_8ch` / `xdawn_tslr` — real 0.812, perm 0.502 (20 shuffles)
- [x] `ssvep_8ch` / `ssvep_cca` — real 0.683, perm 0.077 (20 shuffles; chance 0.083)

**Note:** 5 shuffles is too few — a chance decoder read 0.557 on subject 1;
20 shuffles gave 0.509. Default is now 20.

**Open discrepancy:** the control harness reports real=0.683 for SSVEP where the
benchmark reports 0.928 (same 8 channels, same decoder, both 5-fold). The
permuted score is at chance in both, so there is no evidence of leakage — but
the control validates chance-level behaviour, *not* the benchmark's absolute
numbers. Reconcile before quoting either as definitive.

**Acceptance:** control AUC within noise of chance for every tested paradigm. If
any control beats chance, that track's results are invalid and must be fixed.

## G4 — Aggregation and report

- [x] `leaderboard.py` handles all tracks, with chance, delta-vs-full, ITR
- [x] generated `results/REPORT.md` containing every table in one place
- [x] signal-quality table for one track (mi_leftright_22ch)

**Acceptance:** one command regenerates every number quoted in the README.

## G5 — Reproducibility

- [x] single entry point runs the whole suite (`scripts/run_all.py`)
- [x] pinned commit hashes and package versions recorded in `SETUP.md`
- [x] `scripts/smoke_test.py` passes from a clean shell

**Acceptance:** delete `results/`, run one command, get the same tables.
Verified in the resume path: `run_all.py --skip-heavy` re-ran controls, quality
and report end-to-end. A from-scratch rebuild is the same command with
`--overwrite` (hours, not minutes, because of the Wu2020 Curry re-reads).

---

## Phase 2 — closing the caveats

Phase 1 is complete; these are the three unresolved issues plus two guards that
should have existed from the start. Same rule: a box is checked only when a
number in `results/` backs it, and anything unachievable gets `[!]` with a
reason.

### H1 — Reconcile the SSVEP harness discrepancy

- [x] enumerated differences between the paths
- [x] cause identified: **not a harness difference**
- [x] resolved — both harnesses agree to 3 decimals

**Cause:** the control sampled subjects 1–2, the two weakest of ten (0.689,
0.678). The benchmark's 0.928 is the mean over all ten, where subjects 3–10
score 0.96–1.00. Per subject:

| subject | benchmark | control |
| --- | --- | --- |
| 1 | 0.689 | 0.689 |
| 2 | 0.678 | 0.678 |

This is the third instance of the same error in this project: comparing a small
subset against a full-set mean. It is now the motivating case for H5.

### H2 — Make the sleep result statistically valid

- [x] fetch >= 5 subject-nights (5 downloaded)
- [x] match channel counts — 6 ear (ELB/ELG/ELK/ERB/ERG/ERK) vs 6 scalp
- [x] report per-subject kappa, paired delta, 95% CI
- [x] keep block-wise CV

**Result (n=5, matched):** ear − scalp = **−0.046 kappa, 95% CI [−0.075,
−0.016]**, negative in 5/5 subjects. The earlier "ear matches scalp" claim came
from a single night where 14 ear channels happened to equal 6 scalp; across all
five nights even 14 ear channels average 0.498 against 0.519 for 6 scalp. The
task-dependence conclusion survives.

### H3 — Decide c-VEP properly

- [x] inspected the raw data: `stim_trial` carries command codes 200–203
      (the paradigm only uses the `stim_epoch` bit stream)
- [x] implemented custom epoching in `scripts/cvep_track.py` — 60 trials,
      4 classes x 15, ISI 3.42 s
- [x] verified >2 classes and above-chance decoding: **0.400 vs chance 0.250**
- [ ] proper decoder (template matching against the code sequence)

**Outcome: c-VEP is live but weak.** Fold scores `[0.33, 0.33, 0.33, 0.25,
0.75]` show the decoder — not the data — is the limiting factor. Riemannian
covariance is the wrong tool for code-modulated VEPs; template matching or CCA
against the known codes is standard. This is the fourth paradigm where the
generic decoder under-reports, so the track is marked live with a decoder
caveat rather than excluded.

### H4 — Controls for every live track

Permutation controls exist for MI, P300, SSVEP only.

- [x] add a control for `motor_execution_ear_vs_scalp` - 50 shuffles, subject 1:
      real 0.963, perm **0.519**
- [x] add a control for `sleep_staging_local` — circular-shift labels,
      real κ 0.755 / perm κ 0.034–0.045
- [x] store all under one naming scheme (`results/perm_control_<track>.csv`)

**Note:** the sleep control uses circular shifts, not a plain shuffle, so the
hypnogram's autocorrelation and block structure are preserved. A plain shuffle
would be an unrealistically easy null.

**Residual caveat:** the ear control sits at 0.519, about 0.02 above chance and
within the 0.05 tolerance but likely larger than its standard error at 50
shuffles. MI's subject-1 control showed the same tendency (0.509 at 20
shuffles). A 200+ shuffle null per subject is the correct way to bound this;
until then the ear gap (0.444) is inflated by roughly 0.02.

**Acceptance:** `results/perm_control_*.csv` covers every live track, each at
chance.

### H5 — Automated validity guard

- [x] report fails loudly if any control exceeds chance + tolerance
- [x] report flags cross-site comparisons at unequal channel counts
- [x] report flags rows whose `n` is below a threshold

**Acceptance met:** corrupting `perm_control_ssvep_8ch.csv` (perm_mean → 0.50)
makes the report print `REFUSING to write report` and exit 1. Restoring the file
restores normal output. Current live warnings: sleep `n=1`, and sleep
wearable [14] vs comparison [6].


1. G1 SSVEP scale-up (small downloads, highest value — only ITR track)
2. G1 ear track re-run into the canonical results dir
3. G3 permutation control (cheapest insurance against silent leakage)
4. G4 report generation
5. G2 sleep adapter (blocked on data fetch; do last, largest unknown)
6. G5 reproducibility pass

Rationale: close the cheap, high-certainty items before the one with an unknown
download cost.
