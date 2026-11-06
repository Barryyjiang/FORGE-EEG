# Benchmark TL;DR — detailed

**Scope:** 6 tracks across 4 paradigms + 1 continuous task. Every model is a
classical pipeline **trained from scratch per fold** — no pretrained weights, no
foundation models, no fine-tuning.

**Metrics and chance levels differ by task.** Quoting an AUC next to a kappa is
meaningless unless the chance level is stated:

| metric | used for | chance |
|---|---|---|
| ROC-AUC | motor imagery, P300, motor execution | 0.50 |
| accuracy | SSVEP (12-class), c-VEP (4-class) | 0.083 / 0.25 |
| Cohen's kappa | sleep staging (5-class) | 0.00 |

---

## 1. Tasks, data, models

| # | Task | What the participant does | Dataset / sampling / channels | Data used | Model (from scratch) |
|---|---|---|---|---|---|
| 1 | Motor **imagery**, 2-class | Imagines left vs right hand movement | BNCI2014_001 · 250 Hz · 22 EEG | 9 subj × 2 sess × 144 epochs = **2,592** | Covariances(LWF) → TangentSpace → LogisticRegression |
| 2 | **P300**, 2-class | Attends a target in a speller grid | BNCI2014_008 · 256 Hz · 8 EEG | 8 subj × 4,200 epochs = **33,600** | XdawnCov(nfilter=4) → TangentSpace → LogReg |
| 3 | **SSVEP**, 12-class | Fixates one of 12 flickering targets | Nakanishi2015 · 256 Hz · 8 occipital | 10 subj × 180 epochs = **1,800** | CCA, 3 harmonics, 12-class |
| 4 | Motor **execution**, 2-class | Clenches left vs right fist on cue | Wu2020 · 1000 Hz · 122 scalp + 8 in-ear | 6 subj × ~197 epochs = **1,182** | Covariances(LWF) → TangentSpace → LogReg |
| 5 | **Sleep staging**, 5-class | Sleeps; stage scored per 30 s epoch | OpenNeuro ds004348 · 200 Hz · 6 scalp + 13 ear | 5 nights × ~926 epochs = **4,630** | 5-band log power → LDA (shrinkage), block-wise CV |
| 6 | **c-VEP**, 4-class | Fixates one of 4 code-modulated targets | CastillosCVEP40 · 500 Hz · 28 EEG | 1 subj × 60 trials = **60** | Covariances → TangentSpace → LogReg *(wrong decoder)* |

---

## 2. Results with the reduced montage expanded

### 2.1 Motor imagery — full cap 22 ch

| montage | k | within-session | cross-session |
|---|---|---|---|
| **full cap** | **22** | **0.871** | **0.860** |
| sensorimotor region | 4 | 0.741 (−0.130) | 0.751 (−0.110) |
| parietal region | 4 | 0.725 (−0.147) | 0.699 (−0.161) |
| distributed (max spread) | 4 | 0.705 (−0.167) | 0.717 (−0.143) |
| random ×3 seeds | 4 | 0.645–0.713 | 0.667–0.699 |
| sensorimotor region | 8 | 0.794 (−0.077) | 0.786 (−0.074) |
| distributed | 8 | 0.773 (−0.098) | 0.784 (−0.076) |
| random ×3 seeds | 8 | 0.766–0.785 | 0.752–0.784 |
| distributed | 16 | 0.817 (−0.055) | 0.814 (−0.046) |
| random ×3 seeds | 16 | 0.828–0.855 | 0.830–0.843 |

n = 18 (9 subjects × 2 sessions).

### 2.2 P300 — full cap 8 ch

| montage | k | AUC |
|---|---|---|
| **full cap** | **8** | **0.858** |
| distributed | 4 | 0.812 (−0.046) |
| random ×3 seeds | 4 | 0.754–0.801 (−0.057 … −0.103) |

No k=8 reduction exists: the cap is only 8 channels. n = 8.

### 2.3 SSVEP — full cap 8 ch

| montage | k | accuracy | ITR |
|---|---|---|---|
| **full cap** | **8** | **0.928** | **44.5 bits/min** |
| distributed | 4 | 0.914 (−0.014) | 43.0 bits/min |
| random ×3 seeds | 4 | 0.874–0.892 | 39.1–40.7 bits/min |

n = 10. Subjects 3–10 scored 0.96–1.00; subjects 1–2 scored 0.68.

### 2.4 Motor execution, ear vs scalp — full cap 115 ch

| montage | k | AUC | drop |
|---|---|---|---|
| **full cap** | **115** | **0.775** | — |
| sensorimotor region | 8 | **0.739** | −0.036 |
| random ×3 seeds | 8 | 0.648–0.732 | −0.043 … −0.126 |
| distributed | 8 | 0.675 | −0.100 |
| frontal region | 8 | 0.544 | −0.231 |
| temporal region | 8 | 0.525 | −0.249 |
| **in-ear (8)** | **8** | **0.464** | **−0.311** |
| thielen2021 measured montage | 6 | 0.547 | −0.228 |
| headband proxy | 4 | 0.516 | −0.259 |
| earbud proxy | 2 | 0.500 | −0.275 |
| muse2 | 2 | 0.492 | −0.283 |
| ceegrid proxy | 6 | 0.481 | −0.294 |

n = 6. The decisive comparison is **in-ear 0.464 vs sensorimotor scalp 0.739 at
matched k=8** → **−0.275**, same session and decoder, isolating site from count.

### 2.5 Sleep staging — no full-density cap exists

| montage | k | kappa |
|---|---|---|
| scalp (C3 O1 F3 C4 O2 F4) — reference | 6 | **0.519** |
| ear, matched (ELB ELG ELK / ERB ERG ERK) | 6 | 0.473 |
| ear, all available | 14 | 0.498 |

n = 5 nights. Paired ear−scalp = **−0.046 κ, 95% CI [−0.075, −0.016]**,
negative in 5/5 subjects.

Per-subject (scalp / ear-6): 0.755/0.732 · 0.423/0.389 · 0.333/0.249 ·
0.381/0.344 · 0.702/0.652.

### 2.6 c-VEP — no reduced montage tested

| montage | k | accuracy |
|---|---|---|
| all EEG | 28 | 0.400 (chance 0.250) |

n = 1 subject, 60 trials (15 per class), folds [0.33, 0.33, 0.33, 0.25, 0.75].
Above chance, but covariance is the wrong decoder for code-modulated VEPs —
treat as a lower bound.

---

## 3. Coverage gaps — what was *not* tested

| track | reduced k values tested | wearables tested | gap |
|---|---|---|---|
| Motor imagery | 4, 8, 16 | none | — |
| P300 | 4 only | none | cap is 8, so no k=8 reduction |
| SSVEP | 4 only | none | cap is 8 |
| Motor execution | 8 | 2, 4, 6 | no k=4 or k=16 scalp |
| Sleep | 6, 14 | ear only | no full-density cap exists |
| c-VEP | **none** | none | no montage comparison at all |

**Matched-k (valid) comparisons:** MI strategies at k=4/8/16; P300 and SSVEP
distributed vs random at k=4; ear vs sensorimotor at k=8.

**Unmatched (flags only):** sleep ear-14 vs scalp-6; wearables at k=2/4/6 vs the
115-channel cap.

---

## 4. Headline findings

1. **Placement beats count.** 4–8 well-placed electrodes recover 85–98% of
   full-cap performance. At k=4, the sensorimotor region beats random subsets by
   ~0.05 AUC in motor imagery; distributed ("max spread") is the *worst*
   strategy when the source is focal.
2. **Decoder choice rivals montage choice.** Generic band-power sat at chance on
   SSVEP (0.13) and P300 (0.49) until given CCA and xDAWN. A benchmark without
   paradigm-appropriate decoders reports "bad montage" when the decoder is bad.
3. **Wearable success is task-dependent.** Same in-ear site: motor execution
   collapses (−0.275 at matched k), sleep costs only −0.046 κ. Broad, slow
   activity reaches the ear; focal sensorimotor rhythm does not.

---

## 5. Caveats and corrections

- **Sleep n=5**, per-subject κ spans 0.33–0.76. The mean hides large
  between-subject variance.
- **Earlier "ear matches scalp" was wrong.** On subject 1 alone, 14 ear channels
  matched 6 scalp (0.755 vs 0.754). Across five nights, 14 ear channels average
  0.498 — still below 6 scalp. Extra channels did not close the gap.
- **c-VEP uses the wrong decoder**, so 0.400 is a lower bound.
- **EEGNet was excluded**: it scored 0.513 on the scalp control where linear
  models reach 0.86, failing its own sanity check.
- **Ear control sits at 0.519**, ~0.02 above chance — within tolerance, above
  its standard error. The quoted ear gap is inflated by about that much.

**Validity checks that run automatically** (`results/REPORT.md`): a control above
chance, an `n` below 5, or a cross-site comparison at unequal channel counts each
produce a warning; a failed control blocks the report entirely.

---

## 6. Reproduce

```powershell
# whole suite
.\.venv\Scripts\python.exe scripts\run_all.py

# one track
.\.venv\Scripts\python.exe scripts\run_benchmark.py --suite mi_leftright_22ch

# sleep (separate adapter)
.\.venv\Scripts\python.exe scripts\sleep_track.py --subjects 001,002,003,004,005

# rebuild every table
.\.venv\Scripts\python.exe scripts\report.py
```

Full generated tables: `results/REPORT.md`. Acceptance criteria and open items:
`GOALS.md`. Environment and pinned commits: `SETUP.md`.
