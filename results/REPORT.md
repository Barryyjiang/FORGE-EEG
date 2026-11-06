# Benchmark report

Generated from `results/benchmark/`. Every number below is
reproducible with the commands in `README.md`.

## Validity checks

- _warn_ cvep_local / riemann_tslr: n=1 < 5; do not quote as a stable estimate

## Coverage

| track | protocol | pipeline | subsets | n |
|---|---|---|---|---|
| cvep_local | within_session | riemann_tslr | 1 | 1 |
| mi_leftright_22ch | cross_session | csp_lda | 16 | 18 |
| mi_leftright_22ch | cross_session | logvar_lda | 16 | 18 |
| mi_leftright_22ch | cross_session | riemann_tslr | 16 | 18 |
| mi_leftright_22ch | within_session | csp_lda | 16 | 18 |
| mi_leftright_22ch | within_session | logvar_lda | 16 | 18 |
| mi_leftright_22ch | within_session | riemann_tslr | 16 | 18 |
| motor_execution_ear_vs_scalp | within_session | csp_lda | 14 | 6 |
| motor_execution_ear_vs_scalp | within_session | logvar_lda | 14 | 6 |
| motor_execution_ear_vs_scalp | within_session | riemann_tslr | 14 | 6 |
| p300_8ch | within_session | logvar_lda | 5 | 8 |
| p300_8ch | within_session | xdawn_tslr | 5 | 8 |
| sleep_staging_local | within_session | bandpower_lda | 3 | 5 |
| ssvep_8ch | within_session | ssvep_cca | 5 | 10 |

## cvep_local

| protocol | pipeline | score_mean | score_sem | chance | itr_bpm |
|---|---|---|---|---|---|
| within_session | riemann_tslr | 0.400 | — | 0.250 | 2.342 |

| protocol | pipeline | subset | k | score_mean | score_sem | delta_vs_full | itr_bpm |
|---|---|---|---|---|---|---|---|

## mi_leftright_22ch

| protocol | pipeline | score_mean | score_sem | chance | itr_bpm |
|---|---|---|---|---|---|
| cross_session | csp_lda | 0.817 | 0.039 | 0.500 | — |
| cross_session | logvar_lda | 0.749 | 0.040 | 0.500 | — |
| cross_session | riemann_tslr | 0.860 | 0.031 | 0.500 | — |
| within_session | csp_lda | 0.829 | 0.037 | 0.500 | — |
| within_session | logvar_lda | 0.775 | 0.038 | 0.500 | — |
| within_session | riemann_tslr | 0.871 | 0.032 | 0.500 | — |

| protocol | pipeline | subset | k | score_mean | score_sem | delta_vs_full | itr_bpm |
|---|---|---|---|---|---|---|---|
| cross_session | riemann_tslr | random-s0_k16 | 16 | 0.843 | 0.032 | -0.017 | — |
| cross_session | riemann_tslr | random-s2_k16 | 16 | 0.839 | 0.032 | -0.021 | — |
| cross_session | riemann_tslr | random-s1_k16 | 16 | 0.830 | 0.034 | -0.031 | — |
| cross_session | csp_lda | random-s2_k16 | 16 | 0.827 | 0.034 | 0.010 | — |
| cross_session | csp_lda | random-s0_k16 | 16 | 0.819 | 0.036 | 0.003 | — |
| cross_session | riemann_tslr | distributed_k16 | 16 | 0.814 | 0.037 | -0.046 | — |
| cross_session | csp_lda | random-s1_k16 | 16 | 0.811 | 0.037 | -0.005 | — |
| cross_session | csp_lda | distributed_k16 | 16 | 0.799 | 0.040 | -0.018 | — |
| cross_session | riemann_tslr | region-sensorimotor_k8 | 8 | 0.786 | 0.040 | -0.074 | — |
| cross_session | riemann_tslr | distributed_k8 | 8 | 0.784 | 0.039 | -0.076 | — |
| cross_session | riemann_tslr | random-s1_k8 | 8 | 0.784 | 0.036 | -0.076 | — |
| cross_session | csp_lda | distributed_k8 | 8 | 0.778 | 0.040 | -0.039 | — |
| cross_session | riemann_tslr | random-s2_k8 | 8 | 0.774 | 0.039 | -0.086 | — |
| cross_session | csp_lda | region-sensorimotor_k8 | 8 | 0.773 | 0.044 | -0.044 | — |
| cross_session | csp_lda | random-s2_k8 | 8 | 0.764 | 0.041 | -0.052 | — |
| cross_session | csp_lda | random-s1_k8 | 8 | 0.761 | 0.040 | -0.055 | — |
| cross_session | riemann_tslr | random-s0_k8 | 8 | 0.752 | 0.039 | -0.109 | — |
| cross_session | riemann_tslr | region-sensorimotor_k4 | 4 | 0.751 | 0.036 | -0.110 | — |
| cross_session | csp_lda | region-sensorimotor_k4 | 4 | 0.746 | 0.035 | -0.071 | — |
| cross_session | logvar_lda | random-s0_k16 | 16 | 0.730 | 0.036 | -0.020 | — |
| cross_session | logvar_lda | random-s1_k16 | 16 | 0.727 | 0.039 | -0.023 | — |
| cross_session | csp_lda | random-s0_k8 | 8 | 0.726 | 0.044 | -0.091 | — |
| cross_session | riemann_tslr | distributed_k4 | 4 | 0.717 | 0.034 | -0.143 | — |
| cross_session | logvar_lda | random-s2_k16 | 16 | 0.713 | 0.032 | -0.037 | — |
| cross_session | csp_lda | distributed_k4 | 4 | 0.710 | 0.035 | -0.107 | — |
| cross_session | logvar_lda | distributed_k16 | 16 | 0.709 | 0.042 | -0.041 | — |
| cross_session | riemann_tslr | region-parietal_k4 | 4 | 0.699 | 0.033 | -0.161 | — |
| cross_session | riemann_tslr | random-s1_k4 | 4 | 0.699 | 0.034 | -0.161 | — |
| cross_session | logvar_lda | region-sensorimotor_k8 | 8 | 0.697 | 0.041 | -0.053 | — |
| cross_session | csp_lda | random-s1_k4 | 4 | 0.694 | 0.036 | -0.123 | — |
| cross_session | csp_lda | region-parietal_k4 | 4 | 0.683 | 0.036 | -0.134 | — |
| cross_session | logvar_lda | distributed_k8 | 8 | 0.680 | 0.028 | -0.069 | — |
| cross_session | riemann_tslr | random-s0_k4 | 4 | 0.677 | 0.032 | -0.183 | — |
| cross_session | riemann_tslr | random-s2_k4 | 4 | 0.667 | 0.025 | -0.193 | — |
| cross_session | csp_lda | random-s0_k4 | 4 | 0.663 | 0.034 | -0.154 | — |
| cross_session | logvar_lda | region-sensorimotor_k4 | 4 | 0.661 | 0.029 | -0.089 | — |
| cross_session | csp_lda | random-s2_k4 | 4 | 0.656 | 0.026 | -0.161 | — |
| cross_session | logvar_lda | random-s2_k8 | 8 | 0.655 | 0.028 | -0.094 | — |
| cross_session | logvar_lda | random-s1_k8 | 8 | 0.648 | 0.033 | -0.101 | — |
| cross_session | logvar_lda | random-s0_k8 | 8 | 0.641 | 0.028 | -0.109 | — |
| cross_session | logvar_lda | distributed_k4 | 4 | 0.611 | 0.022 | -0.138 | — |
| cross_session | logvar_lda | random-s1_k4 | 4 | 0.610 | 0.027 | -0.139 | — |
| cross_session | logvar_lda | region-parietal_k4 | 4 | 0.604 | 0.034 | -0.145 | — |
| cross_session | logvar_lda | random-s2_k4 | 4 | 0.592 | 0.018 | -0.158 | — |
| cross_session | logvar_lda | random-s0_k4 | 4 | 0.581 | 0.017 | -0.169 | — |
| within_session | riemann_tslr | random-s2_k16 | 16 | 0.855 | 0.033 | -0.016 | — |
| within_session | riemann_tslr | random-s0_k16 | 16 | 0.854 | 0.033 | -0.018 | — |
| within_session | csp_lda | random-s2_k16 | 16 | 0.836 | 0.035 | 0.007 | — |
| within_session | riemann_tslr | random-s1_k16 | 16 | 0.828 | 0.036 | -0.043 | — |
| within_session | csp_lda | random-s0_k16 | 16 | 0.827 | 0.035 | -0.002 | — |
| within_session | riemann_tslr | distributed_k16 | 16 | 0.817 | 0.039 | -0.055 | — |
| within_session | csp_lda | random-s1_k16 | 16 | 0.806 | 0.039 | -0.023 | — |
| within_session | riemann_tslr | region-sensorimotor_k8 | 8 | 0.794 | 0.040 | -0.077 | — |
| within_session | csp_lda | distributed_k16 | 16 | 0.790 | 0.041 | -0.039 | — |
| within_session | riemann_tslr | random-s1_k8 | 8 | 0.785 | 0.039 | -0.086 | — |
| within_session | csp_lda | region-sensorimotor_k8 | 8 | 0.781 | 0.045 | -0.048 | — |
| within_session | riemann_tslr | random-s2_k8 | 8 | 0.778 | 0.042 | -0.093 | — |
| within_session | csp_lda | random-s2_k8 | 8 | 0.777 | 0.040 | -0.052 | — |
| within_session | csp_lda | distributed_k8 | 8 | 0.773 | 0.044 | -0.055 | — |
| within_session | riemann_tslr | distributed_k8 | 8 | 0.773 | 0.044 | -0.098 | — |
| within_session | csp_lda | random-s1_k8 | 8 | 0.773 | 0.040 | -0.056 | — |
| within_session | riemann_tslr | random-s0_k8 | 8 | 0.766 | 0.040 | -0.105 | — |
| within_session | logvar_lda | random-s0_k16 | 16 | 0.749 | 0.035 | -0.026 | — |
| within_session | csp_lda | random-s0_k8 | 8 | 0.749 | 0.043 | -0.080 | — |
| within_session | logvar_lda | random-s1_k16 | 16 | 0.748 | 0.038 | -0.027 | — |
| within_session | logvar_lda | distributed_k16 | 16 | 0.744 | 0.036 | -0.031 | — |
| within_session | riemann_tslr | region-sensorimotor_k4 | 4 | 0.741 | 0.040 | -0.130 | — |
| within_session | logvar_lda | random-s2_k16 | 16 | 0.740 | 0.031 | -0.035 | — |
| within_session | csp_lda | region-sensorimotor_k4 | 4 | 0.735 | 0.042 | -0.094 | — |
| within_session | logvar_lda | region-sensorimotor_k8 | 8 | 0.734 | 0.035 | -0.041 | — |
| within_session | riemann_tslr | region-parietal_k4 | 4 | 0.725 | 0.033 | -0.147 | — |
| within_session | csp_lda | region-parietal_k4 | 4 | 0.723 | 0.033 | -0.105 | — |
| within_session | csp_lda | random-s1_k4 | 4 | 0.718 | 0.032 | -0.111 | — |
| within_session | riemann_tslr | random-s1_k4 | 4 | 0.713 | 0.032 | -0.159 | — |
| within_session | riemann_tslr | distributed_k4 | 4 | 0.705 | 0.040 | -0.167 | — |
| within_session | riemann_tslr | random-s0_k4 | 4 | 0.694 | 0.035 | -0.177 | — |
| within_session | csp_lda | random-s0_k4 | 4 | 0.693 | 0.035 | -0.136 | — |
| within_session | csp_lda | distributed_k4 | 4 | 0.690 | 0.041 | -0.139 | — |
| within_session | logvar_lda | random-s1_k8 | 8 | 0.680 | 0.033 | -0.095 | — |
| within_session | logvar_lda | region-sensorimotor_k4 | 4 | 0.668 | 0.033 | -0.107 | — |
| within_session | logvar_lda | distributed_k8 | 8 | 0.666 | 0.035 | -0.109 | — |
| within_session | logvar_lda | random-s2_k8 | 8 | 0.664 | 0.031 | -0.111 | — |
| within_session | logvar_lda | random-s0_k8 | 8 | 0.660 | 0.031 | -0.115 | — |
| within_session | logvar_lda | region-parietal_k4 | 4 | 0.649 | 0.028 | -0.126 | — |
| within_session | riemann_tslr | random-s2_k4 | 4 | 0.645 | 0.031 | -0.227 | — |
| within_session | csp_lda | random-s2_k4 | 4 | 0.635 | 0.033 | -0.194 | — |
| within_session | logvar_lda | random-s1_k4 | 4 | 0.621 | 0.027 | -0.154 | — |
| within_session | logvar_lda | distributed_k4 | 4 | 0.607 | 0.031 | -0.168 | — |
| within_session | logvar_lda | random-s0_k4 | 4 | 0.596 | 0.024 | -0.179 | — |
| within_session | logvar_lda | random-s2_k4 | 4 | 0.580 | 0.028 | -0.195 | — |

## motor_execution_ear_vs_scalp

| protocol | pipeline | score_mean | score_sem | chance | itr_bpm |
|---|---|---|---|---|---|
| within_session | csp_lda | 0.755 | 0.058 | 0.500 | — |
| within_session | logvar_lda | 0.651 | 0.053 | 0.500 | — |
| within_session | riemann_tslr | 0.775 | 0.072 | 0.500 | — |

| protocol | pipeline | subset | k | score_mean | score_sem | delta_vs_full | itr_bpm |
|---|---|---|---|---|---|---|---|
| within_session | riemann_tslr | region-sensorimotor_k8 | 8 | 0.739 | 0.062 | -0.036 | — |
| within_session | riemann_tslr | random-s1_k8 | 8 | 0.732 | 0.030 | -0.043 | — |
| within_session | csp_lda | region-sensorimotor_k8 | 8 | 0.695 | 0.053 | -0.059 | — |
| within_session | riemann_tslr | random-s0_k8 | 8 | 0.675 | 0.045 | -0.099 | — |
| within_session | riemann_tslr | distributed_k8 | 8 | 0.675 | 0.058 | -0.100 | — |
| within_session | logvar_lda | region-sensorimotor_k8 | 8 | 0.653 | 0.046 | 0.001 | — |
| within_session | riemann_tslr | random-s2_k8 | 8 | 0.648 | 0.063 | -0.126 | — |
| within_session | csp_lda | random-s1_k8 | 8 | 0.644 | 0.037 | -0.111 | — |
| within_session | logvar_lda | random-s0_k8 | 8 | 0.635 | 0.054 | -0.017 | — |
| within_session | csp_lda | distributed_k8 | 8 | 0.632 | 0.056 | -0.122 | — |
| within_session | logvar_lda | random-s1_k8 | 8 | 0.614 | 0.039 | -0.038 | — |
| within_session | logvar_lda | distributed_k8 | 8 | 0.614 | 0.038 | -0.038 | — |
| within_session | csp_lda | random-s2_k8 | 8 | 0.603 | 0.062 | -0.152 | — |
| within_session | csp_lda | random-s0_k8 | 8 | 0.594 | 0.055 | -0.161 | — |
| within_session | logvar_lda | random-s2_k8 | 8 | 0.590 | 0.050 | -0.062 | — |
| within_session | logvar_lda | region-frontal_k8 | 8 | 0.558 | 0.049 | -0.094 | — |
| within_session | csp_lda | thielen2021_k6 | 6 | 0.552 | 0.029 | -0.202 | — |
| within_session | logvar_lda | thielen2021_k6 | 6 | 0.549 | 0.042 | -0.102 | — |
| within_session | riemann_tslr | thielen2021_k6 | 6 | 0.547 | 0.034 | -0.228 | — |
| within_session | csp_lda | region-temporal_k8 | 8 | 0.546 | 0.029 | -0.209 | — |
| within_session | csp_lda | region-frontal_k8 | 8 | 0.545 | 0.024 | -0.210 | — |
| within_session | riemann_tslr | region-frontal_k8 | 8 | 0.544 | 0.036 | -0.231 | — |
| within_session | logvar_lda | region-temporal_k8 | 8 | 0.542 | 0.024 | -0.110 | — |
| within_session | logvar_lda | headband_proxy_k4 | 4 | 0.540 | 0.034 | -0.111 | — |
| within_session | csp_lda | headband_proxy_k4 | 4 | 0.529 | 0.032 | -0.226 | — |
| within_session | riemann_tslr | region-temporal_k8 | 8 | 0.525 | 0.038 | -0.249 | — |
| within_session | logvar_lda | earbud_proxy_k2 | 2 | 0.525 | 0.026 | -0.127 | — |
| within_session | riemann_tslr | headband_proxy_k4 | 4 | 0.516 | 0.039 | -0.259 | — |
| within_session | logvar_lda | muse2_k2 | 2 | 0.507 | 0.037 | -0.144 | — |
| within_session | riemann_tslr | earbud_proxy_k2 | 2 | 0.500 | 0.016 | -0.275 | — |
| within_session | csp_lda | muse2_k2 | 2 | 0.494 | 0.036 | -0.261 | — |
| within_session | csp_lda | earbud_proxy_k2 | 2 | 0.494 | 0.021 | -0.261 | — |
| within_session | riemann_tslr | muse2_k2 | 2 | 0.492 | 0.038 | -0.283 | — |
| within_session | riemann_tslr | ceegrid_proxy_k6 | 6 | 0.481 | 0.021 | -0.294 | — |
| within_session | logvar_lda | wu2020_inear_k8 | 8 | 0.481 | 0.010 | -0.171 | — |
| within_session | logvar_lda | ceegrid_proxy_k6 | 6 | 0.479 | 0.020 | -0.173 | — |
| within_session | csp_lda | ceegrid_proxy_k6 | 6 | 0.466 | 0.025 | -0.289 | — |
| within_session | csp_lda | wu2020_inear_k8 | 8 | 0.466 | 0.030 | -0.289 | — |
| within_session | riemann_tslr | wu2020_inear_k8 | 8 | 0.464 | 0.031 | -0.311 | — |

## p300_8ch

| protocol | pipeline | score_mean | score_sem | chance | itr_bpm |
|---|---|---|---|---|---|
| within_session | logvar_lda | 0.536 | 0.016 | 0.500 | — |
| within_session | xdawn_tslr | 0.858 | 0.016 | 0.500 | — |

| protocol | pipeline | subset | k | score_mean | score_sem | delta_vs_full | itr_bpm |
|---|---|---|---|---|---|---|---|
| within_session | xdawn_tslr | distributed_k4 | 4 | 0.812 | 0.022 | -0.046 | — |
| within_session | xdawn_tslr | random-s2_k4 | 4 | 0.801 | 0.024 | -0.057 | — |
| within_session | xdawn_tslr | random-s0_k4 | 4 | 0.784 | 0.026 | -0.074 | — |
| within_session | xdawn_tslr | random-s1_k4 | 4 | 0.754 | 0.022 | -0.103 | — |
| within_session | logvar_lda | distributed_k4 | 4 | 0.535 | 0.015 | -0.001 | — |
| within_session | logvar_lda | random-s1_k4 | 4 | 0.534 | 0.015 | -0.002 | — |
| within_session | logvar_lda | random-s0_k4 | 4 | 0.525 | 0.013 | -0.011 | — |
| within_session | logvar_lda | random-s2_k4 | 4 | 0.517 | 0.014 | -0.019 | — |

## sleep_staging_local

| protocol | pipeline | subset | k | score_mean | score_sem | delta_vs_full | itr_bpm |
|---|---|---|---|---|---|---|---|
| within_session | bandpower_lda | scalp_6_k6 | 6 | 0.519 | 0.087 | — | — |
| within_session | bandpower_lda | ear_13_k14 | 14 | 0.498 | 0.088 | — | — |
| within_session | bandpower_lda | ear_6_k6 | 6 | 0.473 | 0.093 | — | — |

## ssvep_8ch

| protocol | pipeline | score_mean | score_sem | chance | itr_bpm |
|---|---|---|---|---|---|
| within_session | ssvep_cca | 0.928 | 0.041 | 0.083 | 44.474 |

| protocol | pipeline | subset | k | score_mean | score_sem | delta_vs_full | itr_bpm |
|---|---|---|---|---|---|---|---|
| within_session | ssvep_cca | distributed_k4 | 4 | 0.914 | 0.046 | -0.014 | 43.013 |
| within_session | ssvep_cca | random-s2_k4 | 4 | 0.892 | 0.047 | -0.037 | 40.730 |
| within_session | ssvep_cca | random-s0_k4 | 4 | 0.875 | 0.050 | -0.053 | 39.135 |
| within_session | ssvep_cca | random-s1_k4 | 4 | 0.874 | 0.051 | -0.054 | 39.082 |

## Signal quality (raw data, per montage)

| track | subset | k | reject_rate | line_noise_ratio | effective_rank | mean_abs_corr |
|---|---|---|---|---|---|---|
| mi_leftright_22ch | distributed_k4 | 4 | 0.003 | 2.120 | 1.561 | 0.719 |
| mi_leftright_22ch | random-s0_k4 | 4 | 0.003 | 1.045 | 1.341 | 0.810 |
| mi_leftright_22ch | region-parietal_k4 | 4 | 0.001 | 0.847 | 1.081 | 0.949 |
| mi_leftright_22ch | region-sensorimotor_k4 | 4 | 0.003 | 1.984 | 1.368 | 0.798 |
| mi_leftright_22ch | distributed_k8 | 8 | 0.016 | 1.703 | 1.451 | 0.797 |
| mi_leftright_22ch | random-s0_k8 | 8 | 0.003 | 1.390 | 1.352 | 0.832 |
| mi_leftright_22ch | region-sensorimotor_k8 | 8 | 0.004 | 1.592 | 1.345 | 0.838 |
| mi_leftright_22ch | distributed_k16 | 16 | 0.016 | 1.460 | 1.363 | 0.841 |
| mi_leftright_22ch | random-s0_k16 | 16 | 0.003 | 1.553 | 1.301 | 0.864 |
| mi_leftright_22ch | full_k22 | 22 | 0.016 | 1.461 | 1.351 | 0.848 |

## Permutation control

Permuted-label AUC should sit at chance; a gap is the real effect.

| track | pipeline | real | perm_mean | gap |
|---|---|---|---|---|
| ear_vs_scalp_8ch | riemann_tslr | 0.963 | 0.519 | 0.444 |
| mi_leftright_22ch | riemann_tslr | 0.957 | 0.509 | 0.448 |
| motor_execution_ear_vs_scalp | riemann_tslr | 0.821 | 0.514 | 0.307 |
| p300_8ch | xdawn_tslr | 0.823 | 0.500 | 0.323 |
| sleep_staging_local | bandpower_lda | 0.748 | 0.031 | 0.717 |
| ssvep_8ch | ssvep_cca | 0.689 | 0.077 | 0.612 |
