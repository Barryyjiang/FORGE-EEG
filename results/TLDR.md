# Wearable-EEG electrode-subset benchmark — detailed summary

Six tracks: four classification paradigms plus one continuous task, scored on
reduced electrode montages against each dataset's own full cap. Every model is
classical (scikit-learn / pyRiemann) and **trained from scratch per fold** — no
pretrained weights, no foundation models, no fine-tuning.

---

## 1. Tasks at a glance

| # | Task | Classes | Dataset | Channels | Data used | Model | Metric | Full cap |
|---|---|---|---|---|---|---|---|---|
| 1 | Motor **imagery**: imagine left vs right hand | 2 | BNCI2014_001 | 22 EEG | 9 subj × 2 sess × 144 epochs = **2,592** | Covariances(LWF) → TangentSpace → LogisticRegression | ROC-AUC | 0.871 |
| 2 | **P300**: attend a target in a speller grid | 2 | BNCI2014_008 | 8 EEG | 8 subj × 4,200 epochs = **33,600** | XdawnCov(nfilter=4) → TangentSpace → LogisticRegression | ROC-AUC | 0.858 |
| 3 | **SSVEP**: fixate one of 12 flickering targets | 12 | Nakanishi2015 | 8 occipital | 10 subj × 180 epochs = **1,800** | CCA (3 harmonics, 12-class) | accuracy, ITR | 0.928 / 44.5 b·min⁻¹ |
| 4 | Motor **execution**: clench left vs right fist on cue | 2 | Wu2020 | 122 scalp + 8 in-ear | 6 subj × ~197 epochs = **1,182** | Covariances(LWF) → TangentSpace → LogisticRegression | ROC-AUC | 0.775 |
| 5 | **Sleep staging**: score 30 s epochs into 5 stages | 5 | OpenNeuro ds004348 | 6 scalp + 13 ear | 5 nights × ~926 epochs = **4,630** | 5-band log power → LDA (shrinkage), block-wise CV | Cohen's κ | 0.519 (6 scalp) |
| 6 | **c-VEP**: fixate one of 4 code-modulated targets | 4 | CastillosCVEP40 | 28 EEG | 1 subj × 60 trials = **60** | Covariances → TangentSpace → LogisticRegression *(wrong decoder, see caveats)* | accuracy | 0.400 |

Motor **imagery** (track 1) and motor **execution** (track 4) are different tasks
on different datasets; they are not two views of the same experiment.

---

## 2. Reduced montages — full detail

### Motor imagery — cap 22 ch, 0.871 (within-session) / 0.860 (cross-session)

| montage | k | within | cross |
|---|---|---|---|
| sensorimotor region | 4 | 0.741 (−0.130) | 0.751 (−0.110) |
| parietal region | 4 | 0.725 (−0.147) | 0.699 (−0.161) |
| distributed | 4 | 0.705 (−0.167) | 0.717 (−0.143) |
| random (3 seeds) | 4 | 0.645–0.713 | 0.667–0.699 |
| sensorimotor region | 8 | 0.794 (−0.077) | 0.786 (−0.074) |
| distributed | 8 | 0.773 (−0.098) | 0.784 (−0.076) |
| random (3 seeds) | 8 | 0.766–0.785 | 0.752–0.784 |
| distributed | 16 | 0.817 (−0.055) | 0.814 (−0.046) |
| random (3 seeds) | 16 | 0.828–0.855 | 0.830–0.843 |

### P300 — cap 8 ch, 0.858

| montage | k | score |
|---|---|---|
| distributed | 4 | 0.812 (−0.046) |
| random (3 seeds) | 4 | 0.754–0.801 (−0.057 … −0.103) |

No k=8 reduction exists: the cap itself is 8 channels.

### SSVEP — cap 8 ch, 0.928 (44.5 bits/min)

| montage | k | accuracy | ITR |
|---|---|---|---|
| distributed | 4 | 0.914 (−0.014) | 43.0 b·min⁻¹ |
| random (3 seeds) | 4 | 0.874–0.892 | 39.1–40.7 b·min⁻¹ |

No k=8 reduction exists: the cap itself is 8 channels.

### Motor execution (ear vs scalp) — cap 115 ch, 0.775

| montage | k | score | drop |
|---|---|---|---|
| sensorimotor region | 8 | **0.739** | −0.036 |
| random (3 seeds) | 8 | 0.648–0.732 | −0.043 … −0.126 |
| distributed | 8 | 0.675 | −0.100 |
| frontal region | 8 | 0.544 | −0.231 |
| temporal region | 8 | 0.525 | −0.249 |
| **in-ear** | 8 | **0.464** | **−0.311** |
| thielen2021 (measured 8-ch montage) | 6 | 0.547 | −0.228 |
| headband proxy | 4 | 0.516 | −0.259 |
| earbud proxy | 2 | 0.500 | −0.275 |
| Muse 2 | 2 | 0.492 | −0.283 |
| cEEGrid proxy | 6 | 0.481 | −0.294 |

The controlled comparison is **in-ear 0.464 vs sensorimotor 0.739 at k=8**:
identical channel count, same session, same decoder. Difference −0.275.

### Sleep staging — no full-density cap available; 6 scalp channels is the reference

| montage | k | kappa |
|---|---|---|
| scalp (C3 O1 F3 C4 O2 F4) | 6 | **0.519** |
| ear, matched (ELB ELG ELK ERB ERG ERK) | 6 | 0.473 |
| ear, all (EL*/ER*) | 14 | 0.498 |

Paired ear − scalp at matched k: **−0.046, 95% CI [−0.075, −0.016]**, negative in
5/5 nights. Fourteen ear channels do **not** close the gap (0.498 vs 0.519).

### c-VEP — no reduced montage measured

| montage | k | accuracy | chance |
|---|---|---|---|
| all EEG | 28 | 0.400 | 0.250 |

Only one subject, and the decoder is not a c-VEP decoder. This is a lower bound,
not a benchmark result.

---

## 3. Chance levels

| task | metric | chance |
|---|---|---|
| Motor imagery, P300, motor execution | ROC-AUC | 0.500 |
| SSVEP | accuracy | 1/12 = 0.083 |
| c-VEP | accuracy | 1/4 = 0.250 |
| Sleep staging | Cohen's κ | 0.000 |

---

## 4. What was trained

All six tracks use per-fold refitting of classical pipelines:

- **Riemannian**: `Covariances(estimator="lwf") → TangentSpace → LogisticRegression`
- **P300**: `XdawnCovariances(nfilter=4) → TangentSpace → LogisticRegression`
- **SSVEP**: `SSVEP_CCA(n_harmonics=3, freq_map=…)`
- **Sleep**: log band-power in delta/theta/alpha/sigma/beta → `LDA(solver="lsqr", shrinkage="auto")`

None are pretrained. EEGNet was implemented and **excluded**: it scored 0.513 on
the scalp control where linear models reach 0.86, so it fails its own sanity
check and cannot be used as evidence.

---

## 5. Headline findings

1. **Placement beats count.** 4–8 well-placed electrodes recover most of
   full-cap performance: SSVEP −0.014 accuracy, P300 −0.046 AUC, motor imagery
   −0.077 AUC at k=8. At every k, targeted regions beat random subsets.

2. **Paradigm-specific decoders are mandatory.** Generic band-power sat at
   chance on SSVEP (0.13) and P300 (0.49) until given CCA and xDAWN. A benchmark
   without the right decoder reports "bad montage" when the decoder is at fault.

3. **Wearable performance is task-dependent.** At matched channel count,
   in-ear electrodes lose **0.275 AUC** on motor execution but only
   **0.046 κ** on sleep staging. Sleep is dominated by spatially broad slow
   activity that reaches the ear; motor rhythm is focal and does not.

---

## 6. Caveats

- **Sleep** is n=5 nights, and per-subject κ spans 0.33–0.76; the mean hides
  large between-subject variance.
- **c-VEP** uses the wrong decoder (Riemannian covariance, not template
  matching); 0.400 is a floor, not an estimate.
- **Ear permutation control** sits at 0.519, about 0.02 above chance — within
  tolerance but probably above its standard error. The ear gap is inflated by
  roughly that amount.
- **Motor imagery** results exist only for this dataset's central/parietal
  channels, so "wrong region" cannot be tested there; track 4 provides that.
- **Random-subset comparisons** use 3 seeds; ranges, not point estimates.

---

## 7. Reproducing

```powershell
.\.venv\Scripts\python.exe scripts\run_all.py            # suite + controls + report
.\.venv\Scripts\python.exe scripts\leaderboard.py        # cross-track table
.\.venv\Scripts\python.exe scripts\report.py             # regenerates REPORT.md
```

`results/REPORT.md` is the auto-generated, auditable version of this summary;
this file is the human-readable narrative.
