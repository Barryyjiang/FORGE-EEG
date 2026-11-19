# Benchmark report

Generated from `results/benchmark/`. Every number below is
reproducible with the commands in `README.md`.

## Validity checks

All checks passed.

## Coverage

| track | protocol | pipeline | subsets | n |
|---|---|---|---|---|
| auditory_attention_earsaad | within_session | ridge_reconstruction | 5 | 15 |
| faced_emotion_123 | within_session | psd_lda | 15 | 123 |
| mi_4class_22ch | within_session | csp_lda | 16 | 18 |
| mi_4class_22ch | within_session | logvar_lda | 16 | 18 |
| mi_4class_22ch | within_session | riemann_tslr | 16 | 18 |
| mi_leftright_22ch | cross_session | csp_lda | 16 | 18 |
| mi_leftright_22ch | cross_session | logvar_lda | 16 | 18 |
| mi_leftright_22ch | cross_session | riemann_tslr | 16 | 18 |
| mi_leftright_22ch | within_session | csp_lda | 16 | 18 |
| mi_leftright_22ch | within_session | logvar_lda | 16 | 18 |
| mi_leftright_22ch | within_session | riemann_tslr | 16 | 18 |
| motor_execution_ear_vs_scalp | within_session | csp_lda | 9 | 6 |
| motor_execution_ear_vs_scalp | within_session | logvar_lda | 9 | 6 |
| motor_execution_ear_vs_scalp | within_session | riemann_tslr | 9 | 6 |
| p300_8ch | within_session | logvar_lda | 5 | 8 |
| p300_8ch | within_session | xdawn_tslr | 5 | 8 |
| sleep_staging_local | within_session | bandpower_lda | 3 | 9 |
| ssvep_8ch | within_session | ssvep_cca | 5 | 10 |
| stew_workload_14ch | cross_subject | psd_lda | 4 | 48 |
| stew_workload_14ch | within_session | psd_lda | 4 | 48 |

## auditory_attention_earsaad

| protocol | pipeline | score_mean | score_sem | chance | itr_bpm |
|---|---|---|---|---|---|
| within_session | ridge_reconstruction | 0.837 | 0.028 | 0.500 | — |

| protocol | pipeline | subset | k | score_mean | score_sem | delta_vs_reference | itr_bpm |
|---|---|---|---|---|---|---|---|
| within_session | ridge_reconstruction | scalp_19_k19 | 19 | 0.820 | 0.029 | -0.017 | — |
| within_session | ridge_reconstruction | scalp_12_k12 | 12 | 0.807 | 0.026 | -0.030 | — |
| within_session | ridge_reconstruction | around_ear_19_k19 | 19 | 0.689 | 0.027 | -0.148 | — |
| within_session | ridge_reconstruction | in_ear_12_k12 | 12 | 0.626 | 0.022 | -0.211 | — |

## faced_emotion_123

| protocol | pipeline | score_mean | score_sem | chance | itr_bpm |
|---|---|---|---|---|---|
| within_session | psd_lda | 0.570 | 0.008 | 0.500 | — |

| protocol | pipeline | subset | k | score_mean | score_sem | delta_vs_reference | itr_bpm |
|---|---|---|---|---|---|---|---|
| within_session | psd_lda | nested_k24 | 24 | 0.573 | 0.009 | 0.003 | — |
| within_session | psd_lda | random-s1_k4 | 4 | 0.568 | 0.009 | -0.002 | — |
| within_session | psd_lda | random-s0_k4 | 4 | 0.564 | 0.007 | -0.006 | — |
| within_session | psd_lda | posterior_4_k4 | 4 | 0.558 | 0.007 | -0.012 | — |
| within_session | psd_lda | glasses_4_k4 | 4 | 0.553 | 0.007 | -0.018 | — |
| within_session | psd_lda | nested_k4 | 4 | 0.553 | 0.007 | -0.018 | — |
| within_session | psd_lda | random-s2_k4 | 4 | 0.551 | 0.008 | -0.019 | — |
| within_session | psd_lda | nested_k20 | 20 | 0.551 | 0.008 | -0.019 | — |
| within_session | psd_lda | nested_k6 | 6 | 0.550 | 0.006 | -0.020 | — |
| within_session | psd_lda | nested_k12 | 12 | 0.550 | 0.008 | -0.020 | — |
| within_session | psd_lda | nested_k8 | 8 | 0.549 | 0.006 | -0.021 | — |
| within_session | psd_lda | nested_k16 | 16 | 0.549 | 0.007 | -0.021 | — |
| within_session | psd_lda | temporal_4_k4 | 4 | 0.540 | 0.007 | -0.030 | — |
| within_session | psd_lda | nested_k2 | 2 | 0.537 | 0.007 | -0.033 | — |

## mi_4class_22ch

| protocol | pipeline | score_mean | score_sem | chance | itr_bpm |
|---|---|---|---|---|---|
| within_session | csp_lda | 0.630 | 0.033 | 0.250 | 6.930 |
| within_session | logvar_lda | 0.592 | 0.033 | 0.250 | 5.663 |
| within_session | riemann_tslr | 0.722 | 0.036 | 0.250 | 10.586 |

| protocol | pipeline | subset | k | score_mean | score_sem | delta_vs_reference | itr_bpm |
|---|---|---|---|---|---|---|---|
| within_session | riemann_tslr | random-s0_k16 | 16 | 0.710 | 0.036 | -0.012 | 10.057 |
| within_session | riemann_tslr | random-s2_k16 | 16 | 0.696 | 0.034 | -0.026 | 9.482 |
| within_session | riemann_tslr | random-s1_k16 | 16 | 0.696 | 0.037 | -0.026 | 9.480 |
| within_session | riemann_tslr | distributed_k16 | 16 | 0.691 | 0.036 | -0.031 | 9.275 |
| within_session | csp_lda | random-s0_k16 | 16 | 0.626 | 0.035 | -0.003 | 6.815 |
| within_session | csp_lda | random-s2_k16 | 16 | 0.623 | 0.039 | -0.006 | 6.715 |
| within_session | csp_lda | random-s1_k16 | 16 | 0.614 | 0.037 | -0.016 | 6.392 |
| within_session | riemann_tslr | region-sensorimotor_k8 | 8 | 0.613 | 0.036 | -0.108 | 6.364 |
| within_session | csp_lda | distributed_k16 | 16 | 0.607 | 0.036 | -0.023 | 6.158 |
| within_session | riemann_tslr | random-s0_k8 | 8 | 0.606 | 0.039 | -0.116 | 6.125 |
| within_session | riemann_tslr | distributed_k8 | 8 | 0.599 | 0.034 | -0.123 | 5.897 |
| within_session | riemann_tslr | random-s1_k8 | 8 | 0.593 | 0.032 | -0.129 | 5.701 |
| within_session | csp_lda | random-s0_k8 | 8 | 0.576 | 0.037 | -0.053 | 5.181 |
| within_session | riemann_tslr | random-s2_k8 | 8 | 0.576 | 0.034 | -0.145 | 5.178 |
| within_session | csp_lda | region-sensorimotor_k8 | 8 | 0.575 | 0.036 | -0.055 | 5.129 |
| within_session | logvar_lda | random-s0_k16 | 16 | 0.574 | 0.031 | -0.018 | 5.111 |
| within_session | logvar_lda | distributed_k16 | 16 | 0.561 | 0.031 | -0.031 | 4.733 |
| within_session | logvar_lda | random-s1_k16 | 16 | 0.561 | 0.032 | -0.031 | 4.731 |
| within_session | csp_lda | random-s1_k8 | 8 | 0.550 | 0.032 | -0.080 | 4.399 |
| within_session | csp_lda | distributed_k8 | 8 | 0.546 | 0.034 | -0.083 | 4.309 |
| within_session | logvar_lda | random-s2_k16 | 16 | 0.540 | 0.030 | -0.052 | 4.138 |
| within_session | csp_lda | random-s2_k8 | 8 | 0.521 | 0.032 | -0.109 | 3.620 |
| within_session | riemann_tslr | region-sensorimotor_k4 | 4 | 0.508 | 0.025 | -0.213 | 3.312 |
| within_session | riemann_tslr | region-parietal_k4 | 4 | 0.497 | 0.033 | -0.225 | 3.032 |
| within_session | riemann_tslr | random-s0_k4 | 4 | 0.493 | 0.031 | -0.229 | 2.939 |
| within_session | logvar_lda | region-sensorimotor_k8 | 8 | 0.491 | 0.030 | -0.101 | 2.897 |
| within_session | riemann_tslr | random-s1_k4 | 4 | 0.485 | 0.026 | -0.237 | 2.763 |
| within_session | csp_lda | region-sensorimotor_k4 | 4 | 0.484 | 0.027 | -0.146 | 2.734 |
| within_session | csp_lda | random-s0_k4 | 4 | 0.483 | 0.030 | -0.147 | 2.717 |
| within_session | logvar_lda | random-s0_k8 | 8 | 0.478 | 0.028 | -0.114 | 2.606 |
| within_session | csp_lda | random-s1_k4 | 4 | 0.472 | 0.026 | -0.157 | 2.488 |
| within_session | csp_lda | region-parietal_k4 | 4 | 0.470 | 0.033 | -0.160 | 2.438 |
| within_session | riemann_tslr | distributed_k4 | 4 | 0.469 | 0.027 | -0.253 | 2.416 |
| within_session | logvar_lda | random-s1_k8 | 8 | 0.457 | 0.024 | -0.134 | 2.179 |
| within_session | logvar_lda | distributed_k8 | 8 | 0.450 | 0.026 | -0.141 | 2.040 |
| within_session | csp_lda | distributed_k4 | 4 | 0.446 | 0.025 | -0.184 | 1.950 |
| within_session | logvar_lda | region-parietal_k4 | 4 | 0.437 | 0.026 | -0.155 | 1.791 |
| within_session | logvar_lda | random-s2_k8 | 8 | 0.436 | 0.022 | -0.156 | 1.761 |
| within_session | riemann_tslr | random-s2_k4 | 4 | 0.431 | 0.025 | -0.291 | 1.671 |
| within_session | logvar_lda | region-sensorimotor_k4 | 4 | 0.420 | 0.023 | -0.172 | 1.483 |
| within_session | csp_lda | random-s2_k4 | 4 | 0.412 | 0.023 | -0.217 | 1.363 |
| within_session | logvar_lda | random-s0_k4 | 4 | 0.404 | 0.023 | -0.188 | 1.227 |
| within_session | logvar_lda | random-s1_k4 | 4 | 0.397 | 0.014 | -0.195 | 1.126 |
| within_session | logvar_lda | distributed_k4 | 4 | 0.392 | 0.019 | -0.200 | 1.056 |
| within_session | logvar_lda | random-s2_k4 | 4 | 0.366 | 0.016 | -0.226 | 0.713 |

## mi_leftright_22ch

| protocol | pipeline | score_mean | score_sem | chance | itr_bpm |
|---|---|---|---|---|---|
| cross_session | csp_lda | 0.817 | 0.039 | 0.500 | — |
| cross_session | logvar_lda | 0.749 | 0.040 | 0.500 | — |
| cross_session | riemann_tslr | 0.860 | 0.031 | 0.500 | — |
| within_session | csp_lda | 0.829 | 0.037 | 0.500 | — |
| within_session | logvar_lda | 0.775 | 0.038 | 0.500 | — |
| within_session | riemann_tslr | 0.871 | 0.032 | 0.500 | — |

| protocol | pipeline | subset | k | score_mean | score_sem | delta_vs_reference | itr_bpm |
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

| protocol | pipeline | subset | k | score_mean | score_sem | delta_vs_reference | itr_bpm |
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
| within_session | csp_lda | region-temporal_k8 | 8 | 0.546 | 0.029 | -0.209 | — |
| within_session | csp_lda | region-frontal_k8 | 8 | 0.545 | 0.024 | -0.210 | — |
| within_session | riemann_tslr | region-frontal_k8 | 8 | 0.544 | 0.036 | -0.231 | — |
| within_session | logvar_lda | region-temporal_k8 | 8 | 0.542 | 0.024 | -0.110 | — |
| within_session | riemann_tslr | region-temporal_k8 | 8 | 0.525 | 0.038 | -0.249 | — |
| within_session | logvar_lda | wu2020_inear_k8 | 8 | 0.481 | 0.010 | -0.171 | — |
| within_session | csp_lda | wu2020_inear_k8 | 8 | 0.466 | 0.030 | -0.289 | — |
| within_session | riemann_tslr | wu2020_inear_k8 | 8 | 0.464 | 0.031 | -0.311 | — |

## p300_8ch

| protocol | pipeline | score_mean | score_sem | chance | itr_bpm |
|---|---|---|---|---|---|
| within_session | logvar_lda | 0.536 | 0.016 | 0.500 | — |
| within_session | xdawn_tslr | 0.858 | 0.016 | 0.500 | — |

| protocol | pipeline | subset | k | score_mean | score_sem | delta_vs_reference | itr_bpm |
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

| protocol | pipeline | subset | k | score_mean | score_sem | delta_vs_reference | itr_bpm |
|---|---|---|---|---|---|---|---|
| within_session | bandpower_lda | scalp_6_k6 | 6 | 0.418 | 0.073 | 0.000 | — |
| within_session | bandpower_lda | ear_14_k14 | 14 | 0.388 | 0.077 | -0.030 | — |
| within_session | bandpower_lda | ear_6_k6 | 6 | 0.362 | 0.081 | -0.056 | — |

## ssvep_8ch

| protocol | pipeline | score_mean | score_sem | chance | itr_bpm |
|---|---|---|---|---|---|
| within_session | ssvep_cca | 0.928 | 0.041 | 0.083 | 44.474 |

| protocol | pipeline | subset | k | score_mean | score_sem | delta_vs_reference | itr_bpm |
|---|---|---|---|---|---|---|---|
| within_session | ssvep_cca | distributed_k4 | 4 | 0.914 | 0.046 | -0.014 | 43.013 |
| within_session | ssvep_cca | random-s2_k4 | 4 | 0.892 | 0.047 | -0.037 | 40.730 |
| within_session | ssvep_cca | random-s0_k4 | 4 | 0.875 | 0.050 | -0.053 | 39.135 |
| within_session | ssvep_cca | random-s1_k4 | 4 | 0.874 | 0.051 | -0.054 | 39.082 |

## stew_workload_14ch

| protocol | pipeline | score_mean | score_sem | chance | itr_bpm |
|---|---|---|---|---|---|
| cross_subject | psd_lda | 0.874 | 0.017 | 0.500 | — |
| within_session | psd_lda | 0.990 | 0.002 | 0.500 | — |

| protocol | pipeline | subset | k | score_mean | score_sem | delta_vs_reference | itr_bpm |
|---|---|---|---|---|---|---|---|
| cross_subject | psd_lda | glasses_4_k4 | 4 | 0.844 | 0.020 | -0.030 | — |
| cross_subject | psd_lda | posterior_4_k4 | 4 | 0.759 | 0.023 | -0.114 | — |
| cross_subject | psd_lda | forehead_2_k2 | 2 | 0.700 | 0.028 | -0.173 | — |
| within_session | psd_lda | glasses_4_k4 | 4 | 0.952 | 0.008 | -0.038 | — |
| within_session | psd_lda | posterior_4_k4 | 4 | 0.948 | 0.009 | -0.042 | — |
| within_session | psd_lda | forehead_2_k2 | 2 | 0.904 | 0.012 | -0.086 | — |

## Accuracy vs decision window

A task scored at several decision windows is reported at its headline window in the tables above; averaging across windows would produce a number that belongs to no window. This is the full curve. A lower signal-to-noise ratio shows up as a need for longer windows rather than as a hard ceiling, which is the difference between a wearable that cannot do a task and one that is merely slow.

### auditory_attention_earsaad

| subset | 1s | 5s | 10s | 30s | 60s | 120s | 300s | 600s |
|---|---|---|---|---|---|---|---|---|
| around_ear_19_k19 | 0.531 | 0.570 | 0.593 | 0.642 | 0.689 | 0.753 | 0.844 | 0.900 |
| in_ear_12_k12 | 0.519 | 0.540 | 0.550 | 0.603 | 0.626 | 0.656 | 0.744 | 0.844 |
| scalp_12_k12 | 0.548 | 0.604 | 0.643 | 0.729 | 0.807 | 0.875 | 0.911 | 0.967 |
| scalp_19_k19 | 0.555 | 0.615 | 0.663 | 0.751 | 0.820 | 0.883 | 0.922 | 0.967 |
| scalp_29_k29 | 0.562 | 0.633 | 0.673 | 0.784 | 0.837 | 0.917 | 0.944 | 0.967 |

## How many ear electrodes do you need?

The attention table above compares the three systems as they were built (29 / 19 / 12 electrodes). This sweeps the channel budget instead: at each *k*, the *k* most spatially spread electrodes within each array, against the *k* most spread scalp electrodes as a matched reference. Every point uses the same decoder, the same leave-one-trial-out protocol and the same 60 s decision window, so a point here is comparable to a row above.

| k | in_ear | around_ear | scalp |
|---|---|---|---|
| 2 | 0.553 | 0.664 | 0.653 |
| 4 | 0.617 | 0.678 | 0.731 |
| 8 | 0.619 | 0.674 | 0.810 |
| 12 | 0.626 | 0.681 | 0.805 |
| 19 | — | 0.689 | 0.817 |

If the ear and scalp curves are parallel, the ear costs a constant offset. If the ear curve flattens first, the ear runs out of information before it runs out of electrodes — which is the difference between adding electrodes and changing the site.

## Paired comparisons

Each row is a within-subject difference; the CI is a paired t interval. `same_sign` is how many pairs agree with the mean.

| comparison | n | delta | ci_low | ci_high | same_sign |
|---|---|---|---|---|---|
| MI: sensorimotor 8 − full 22 | 18 | -0.077 | -0.120 | -0.035 | 18 |
| MI 4-class: sensorimotor 8 − full 22 | 18 | -0.108 | -0.144 | -0.073 | 18 |
| MI 4-class: sensorimotor 4 − parietal 4 | 18 | 0.012 | -0.017 | 0.041 | 11 |
| P300: spread 4 − full 8 | 8 | -0.046 | -0.067 | -0.025 | 8 |
| SSVEP: spread 4 − full 8 | 10 | -0.014 | -0.052 | 0.024 | 5 |
| Motor: in-ear 8 − sensorimotor 8 | 6 | -0.275 | -0.378 | -0.173 | 6 |
| Sleep: ear 6 − scalp 6 | 9 | -0.056 | -0.104 | -0.009 | 9 |
| Workload: glasses 4 − full 14 | 48 | -0.030 | -0.059 | -0.001 | 30 |
| Workload: glasses 4 − posterior 4 | 48 | 0.084 | 0.037 | 0.132 | 37 |
| Attention: in-ear 12 − scalp 12 | 15 | -0.181 | -0.249 | -0.114 | 14 |
| Attention: around-ear 19 − scalp 19 | 15 | -0.131 | -0.200 | -0.062 | 13 |
| Attention: in-ear 12 − scalp 29 (as built) | 15 | -0.211 | -0.275 | -0.148 | 15 |
| Emotion: posterior 4 − full 30 | 123 | -0.012 | -0.030 | 0.006 | 55 |
| Emotion: glasses 4 − posterior 4 | 123 | -0.005 | -0.024 | 0.013 | 47 |

## What each reduction costs

A raw delta is not comparable across tasks whose chance levels differ, so each reduction is also given as the share of the above-chance margin it consumes. `bal_acc` is a binormal translation of ROC-AUC at the equal-error threshold: a *derived* reading aid on an operator's scale, not a scored value, and ITR is still never derived from an AUC. Sorted most- to least-costly.

| track | pipeline | subset | k | score_mean | delta_vs_reference | headroom_lost_pct | bal_acc | bal_acc_drop_pts | itr_pct_change |
|---|---|---|---|---|---|---|---|---|---|
| motor_execution_ear_vs_scalp | csp_lda | wu2020_inear_k8 | 8 | 0.466 | -0.289 | 113.4 | 0.476 | 21.1 | — |
| motor_execution_ear_vs_scalp | riemann_tslr | wu2020_inear_k8 | 8 | 0.464 | -0.311 | 113.3 | 0.474 | 22.9 | — |
| motor_execution_ear_vs_scalp | logvar_lda | wu2020_inear_k8 | 8 | 0.481 | -0.171 | 112.7 | 0.486 | 12.2 | — |
| motor_execution_ear_vs_scalp | riemann_tslr | region-temporal_k8 | 8 | 0.525 | -0.249 | 90.8 | 0.518 | 18.5 | — |
| motor_execution_ear_vs_scalp | riemann_tslr | region-frontal_k8 | 8 | 0.544 | -0.231 | 84.1 | 0.531 | 17.2 | — |
| motor_execution_ear_vs_scalp | csp_lda | region-frontal_k8 | 8 | 0.545 | -0.210 | 82.3 | 0.532 | 15.5 | — |
| motor_execution_ear_vs_scalp | csp_lda | region-temporal_k8 | 8 | 0.546 | -0.209 | 82.0 | 0.532 | 15.5 | — |
| motor_execution_ear_vs_scalp | logvar_lda | region-temporal_k8 | 8 | 0.542 | -0.110 | 72.5 | 0.529 | 7.9 | — |
| mi_leftright_22ch | logvar_lda | random-s2_k4 | 4 | 0.580 | -0.195 | 70.8 | 0.557 | 14.6 | — |
| mi_leftright_22ch | logvar_lda | random-s0_k4 | 4 | 0.581 | -0.169 | 67.7 | 0.557 | 12.6 | — |
| mi_4class_22ch | logvar_lda | random-s2_k4 | 4 | 0.366 | -0.226 | 66.1 | — | — | -87.4 |
| mi_leftright_22ch | logvar_lda | random-s0_k4 | 4 | 0.596 | -0.179 | 65.0 | 0.568 | 13.5 | — |
| mi_leftright_22ch | logvar_lda | random-s2_k4 | 4 | 0.592 | -0.158 | 63.3 | 0.565 | 11.8 | — |
| motor_execution_ear_vs_scalp | csp_lda | random-s0_k8 | 8 | 0.594 | -0.161 | 63.0 | 0.567 | 12.0 | — |
| auditory_attention_earsaad | ridge_reconstruction | in_ear_12_k12 | 12 | 0.626 | -0.211 | 62.6 | — | — | — |
| motor_execution_ear_vs_scalp | logvar_lda | region-frontal_k8 | 8 | 0.558 | -0.094 | 61.9 | 0.541 | 6.8 | — |
| mi_4class_22ch | riemann_tslr | random-s2_k4 | 4 | 0.431 | -0.291 | 61.7 | — | — | -84.2 |
| mi_leftright_22ch | logvar_lda | distributed_k4 | 4 | 0.607 | -0.168 | 61.2 | 0.576 | 12.7 | — |
| mi_leftright_22ch | riemann_tslr | random-s2_k4 | 4 | 0.645 | -0.227 | 61.0 | 0.604 | 18.5 | — |
| motor_execution_ear_vs_scalp | csp_lda | random-s2_k8 | 8 | 0.603 | -0.152 | 59.7 | 0.573 | 11.4 | — |
| mi_leftright_22ch | csp_lda | random-s2_k4 | 4 | 0.635 | -0.194 | 59.0 | 0.596 | 15.3 | — |
| mi_4class_22ch | logvar_lda | distributed_k4 | 4 | 0.392 | -0.200 | 58.4 | — | — | -81.3 |
| mi_leftright_22ch | logvar_lda | region-parietal_k4 | 4 | 0.604 | -0.145 | 58.1 | 0.574 | 10.9 | — |
| mi_4class_22ch | csp_lda | random-s2_k4 | 4 | 0.412 | -0.217 | 57.2 | — | — | -80.3 |
| mi_4class_22ch | logvar_lda | random-s1_k4 | 4 | 0.397 | -0.195 | 57.0 | — | — | -80.1 |
| mi_leftright_22ch | logvar_lda | random-s1_k4 | 4 | 0.621 | -0.154 | 56.1 | 0.586 | 11.7 | — |
| mi_leftright_22ch | logvar_lda | random-s1_k4 | 4 | 0.610 | -0.139 | 55.7 | 0.579 | 10.4 | — |
| mi_leftright_22ch | logvar_lda | distributed_k4 | 4 | 0.611 | -0.138 | 55.3 | 0.579 | 10.4 | — |
| mi_4class_22ch | logvar_lda | random-s0_k4 | 4 | 0.404 | -0.188 | 55.0 | — | — | -78.3 |
| mi_4class_22ch | riemann_tslr | distributed_k4 | 4 | 0.469 | -0.253 | 53.6 | — | — | -77.2 |
| mi_leftright_22ch | riemann_tslr | random-s2_k4 | 4 | 0.667 | -0.193 | 53.6 | 0.620 | 15.8 | — |
| p300_8ch | logvar_lda | random-s2_k4 | 4 | 0.517 | -0.019 | 52.8 | 0.512 | 1.341 | — |
| mi_leftright_22ch | csp_lda | random-s2_k4 | 4 | 0.656 | -0.161 | 50.8 | 0.611 | 12.7 | — |
| mi_leftright_22ch | riemann_tslr | random-s0_k4 | 4 | 0.677 | -0.183 | 50.8 | 0.628 | 15.0 | — |
| mi_4class_22ch | logvar_lda | region-sensorimotor_k4 | 4 | 0.420 | -0.172 | 50.4 | — | — | -73.8 |
| mi_4class_22ch | riemann_tslr | random-s1_k4 | 4 | 0.485 | -0.237 | 50.2 | — | — | -73.9 |
| mi_4class_22ch | riemann_tslr | random-s0_k4 | 4 | 0.493 | -0.229 | 48.6 | — | — | -72.2 |
| mi_leftright_22ch | csp_lda | random-s0_k4 | 4 | 0.663 | -0.154 | 48.5 | 0.617 | 12.1 | — |
| mi_4class_22ch | csp_lda | distributed_k4 | 4 | 0.446 | -0.184 | 48.4 | — | — | -71.9 |
| motor_execution_ear_vs_scalp | csp_lda | distributed_k8 | 8 | 0.632 | -0.122 | 48.0 | 0.594 | 9.3 | — |
| mi_4class_22ch | riemann_tslr | region-parietal_k4 | 4 | 0.497 | -0.225 | 47.7 | — | — | -71.4 |
| mi_leftright_22ch | riemann_tslr | random-s0_k4 | 4 | 0.694 | -0.177 | 47.7 | 0.640 | 14.8 | — |
| faced_emotion_123 | psd_lda | nested_k2 | 2 | 0.537 | -0.033 | 46.9 | — | — | — |
| stew_workload_14ch | psd_lda | forehead_2_k2 | 2 | 0.700 | -0.173 | 46.4 | 0.645 | 14.6 | — |
| motor_execution_ear_vs_scalp | riemann_tslr | random-s2_k8 | 8 | 0.648 | -0.126 | 46.0 | 0.606 | 9.7 | — |
| mi_leftright_22ch | logvar_lda | region-parietal_k4 | 4 | 0.649 | -0.126 | 45.8 | 0.607 | 9.7 | — |
| mi_4class_22ch | logvar_lda | random-s2_k8 | 8 | 0.436 | -0.156 | 45.7 | — | — | -68.9 |
| mi_4class_22ch | riemann_tslr | region-sensorimotor_k4 | 4 | 0.508 | -0.213 | 45.2 | — | — | -68.7 |
| mi_4class_22ch | logvar_lda | region-parietal_k4 | 4 | 0.437 | -0.155 | 45.2 | — | — | -68.4 |
| mi_leftright_22ch | riemann_tslr | distributed_k4 | 4 | 0.705 | -0.167 | 44.9 | 0.648 | 14.0 | — |
| mi_leftright_22ch | riemann_tslr | random-s1_k4 | 4 | 0.699 | -0.161 | 44.7 | 0.644 | 13.4 | — |
| mi_leftright_22ch | riemann_tslr | region-parietal_k4 | 4 | 0.699 | -0.161 | 44.6 | 0.644 | 13.3 | — |
| auditory_attention_earsaad | ridge_reconstruction | around_ear_19_k19 | 19 | 0.689 | -0.148 | 44.0 | — | — | — |
| mi_leftright_22ch | logvar_lda | random-s0_k8 | 8 | 0.641 | -0.109 | 43.5 | 0.601 | 8.2 | — |
| motor_execution_ear_vs_scalp | csp_lda | random-s1_k8 | 8 | 0.644 | -0.111 | 43.5 | 0.603 | 8.4 | — |
| faced_emotion_123 | psd_lda | temporal_4_k4 | 4 | 0.540 | -0.030 | 43.5 | — | — | — |
| mi_leftright_22ch | riemann_tslr | random-s1_k4 | 4 | 0.713 | -0.159 | 42.8 | 0.654 | 13.4 | — |
| mi_leftright_22ch | csp_lda | region-parietal_k4 | 4 | 0.683 | -0.134 | 42.2 | 0.632 | 10.7 | — |
| mi_leftright_22ch | csp_lda | distributed_k4 | 4 | 0.690 | -0.139 | 42.1 | 0.637 | 11.2 | — |
| mi_4class_22ch | csp_lda | region-parietal_k4 | 4 | 0.470 | -0.160 | 42.0 | — | — | -64.8 |
| mi_leftright_22ch | logvar_lda | random-s0_k8 | 8 | 0.660 | -0.115 | 41.9 | 0.615 | 8.9 | — |
| mi_4class_22ch | csp_lda | random-s1_k4 | 4 | 0.472 | -0.157 | 41.4 | — | — | -64.1 |
| mi_4class_22ch | logvar_lda | distributed_k8 | 8 | 0.450 | -0.141 | 41.4 | — | — | -64.0 |
| mi_leftright_22ch | csp_lda | random-s0_k4 | 4 | 0.693 | -0.136 | 41.4 | 0.639 | 11.0 | — |
| motor_execution_ear_vs_scalp | logvar_lda | random-s2_k8 | 8 | 0.590 | -0.062 | 40.7 | 0.564 | 4.5 | — |
| mi_leftright_22ch | logvar_lda | random-s1_k8 | 8 | 0.648 | -0.101 | 40.7 | 0.606 | 7.7 | — |
| mi_leftright_22ch | logvar_lda | random-s2_k8 | 8 | 0.664 | -0.111 | 40.2 | 0.618 | 8.5 | — |
| mi_leftright_22ch | logvar_lda | distributed_k8 | 8 | 0.666 | -0.109 | 39.7 | 0.619 | 8.4 | — |
| mi_leftright_22ch | riemann_tslr | distributed_k4 | 4 | 0.717 | -0.143 | 39.7 | 0.658 | 12.0 | — |
| mi_leftright_22ch | riemann_tslr | region-parietal_k4 | 4 | 0.725 | -0.147 | 39.5 | 0.663 | 12.5 | — |
| mi_4class_22ch | logvar_lda | random-s1_k8 | 8 | 0.457 | -0.134 | 39.3 | — | — | -61.5 |
| mi_leftright_22ch | csp_lda | random-s1_k4 | 4 | 0.694 | -0.123 | 38.9 | 0.640 | 9.9 | — |
| mi_leftright_22ch | logvar_lda | region-sensorimotor_k4 | 4 | 0.668 | -0.107 | 38.8 | 0.621 | 8.3 | — |
| mi_4class_22ch | csp_lda | random-s0_k4 | 4 | 0.483 | -0.147 | 38.7 | — | — | -60.8 |
| mi_4class_22ch | csp_lda | region-sensorimotor_k4 | 4 | 0.484 | -0.146 | 38.5 | — | — | -60.5 |
| mi_leftright_22ch | logvar_lda | random-s2_k8 | 8 | 0.655 | -0.094 | 37.9 | 0.611 | 7.2 | — |
| motor_execution_ear_vs_scalp | riemann_tslr | distributed_k8 | 8 | 0.675 | -0.100 | 36.3 | 0.626 | 7.7 | — |
| motor_execution_ear_vs_scalp | riemann_tslr | random-s0_k8 | 8 | 0.675 | -0.099 | 36.1 | 0.626 | 7.7 | — |
| mi_leftright_22ch | logvar_lda | region-sensorimotor_k4 | 4 | 0.661 | -0.089 | 35.5 | 0.615 | 6.7 | — |
| mi_leftright_22ch | riemann_tslr | region-sensorimotor_k4 | 4 | 0.741 | -0.130 | 35.1 | 0.676 | 11.2 | — |
| mi_leftright_22ch | logvar_lda | random-s1_k8 | 8 | 0.680 | -0.095 | 34.5 | 0.630 | 7.4 | — |
| mi_leftright_22ch | csp_lda | random-s1_k4 | 4 | 0.718 | -0.111 | 33.8 | 0.658 | 9.1 | — |
| mi_leftright_22ch | csp_lda | distributed_k4 | 4 | 0.710 | -0.107 | 33.7 | 0.652 | 8.6 | — |
| mi_4class_22ch | logvar_lda | random-s0_k8 | 8 | 0.478 | -0.114 | 33.4 | — | — | -54.0 |
| mi_leftright_22ch | csp_lda | region-parietal_k4 | 4 | 0.723 | -0.105 | 32.1 | 0.663 | 8.7 | — |
| p300_8ch | logvar_lda | random-s0_k4 | 4 | 0.525 | -0.011 | 30.9 | 0.518 | 0.786 | — |
| mi_4class_22ch | riemann_tslr | random-s2_k8 | 8 | 0.576 | -0.145 | 30.8 | — | — | -51.1 |
| stew_workload_14ch | psd_lda | posterior_4_k4 | 4 | 0.759 | -0.114 | 30.6 | 0.691 | 10.0 | — |
| faced_emotion_123 | psd_lda | nested_k16 | 16 | 0.549 | -0.021 | 30.4 | — | — | — |
| faced_emotion_123 | psd_lda | nested_k8 | 8 | 0.549 | -0.021 | 30.4 | — | — | — |
| mi_leftright_22ch | riemann_tslr | region-sensorimotor_k4 | 4 | 0.751 | -0.110 | 30.4 | 0.684 | 9.4 | — |
| mi_leftright_22ch | riemann_tslr | random-s0_k8 | 8 | 0.752 | -0.109 | 30.1 | 0.685 | 9.3 | — |
| mi_4class_22ch | logvar_lda | region-sensorimotor_k8 | 8 | 0.491 | -0.101 | 29.6 | — | — | -48.8 |
| p300_8ch | xdawn_tslr | random-s1_k4 | 4 | 0.754 | -0.103 | 28.9 | 0.687 | 8.9 | — |
| mi_4class_22ch | csp_lda | random-s2_k8 | 8 | 0.521 | -0.109 | 28.7 | — | — | -47.8 |
| mi_leftright_22ch | csp_lda | random-s0_k8 | 8 | 0.726 | -0.091 | 28.6 | 0.664 | 7.4 | — |
| mi_leftright_22ch | csp_lda | region-sensorimotor_k4 | 4 | 0.735 | -0.094 | 28.5 | 0.672 | 7.8 | — |
| faced_emotion_123 | psd_lda | nested_k12 | 12 | 0.550 | -0.020 | 28.5 | — | — | — |
| faced_emotion_123 | psd_lda | nested_k6 | 6 | 0.550 | -0.020 | 28.5 | — | — | — |
| mi_leftright_22ch | riemann_tslr | random-s0_k8 | 8 | 0.766 | -0.105 | 28.3 | 0.696 | 9.2 | — |
| mi_leftright_22ch | logvar_lda | distributed_k8 | 8 | 0.680 | -0.069 | 27.7 | 0.630 | 5.3 | — |
| mi_4class_22ch | riemann_tslr | random-s1_k8 | 8 | 0.593 | -0.129 | 27.3 | — | — | -46.1 |
| faced_emotion_123 | psd_lda | random-s2_k4 | 4 | 0.551 | -0.019 | 27.1 | — | — | — |
| faced_emotion_123 | psd_lda | nested_k20 | 20 | 0.551 | -0.019 | 27.1 | — | — | — |
| mi_leftright_22ch | riemann_tslr | distributed_k8 | 8 | 0.773 | -0.098 | 26.5 | 0.702 | 8.7 | — |
| mi_4class_22ch | riemann_tslr | distributed_k8 | 8 | 0.599 | -0.123 | 26.0 | — | — | -44.3 |
| mi_leftright_22ch | riemann_tslr | random-s2_k8 | 8 | 0.778 | -0.093 | 25.2 | 0.706 | 8.3 | — |
| faced_emotion_123 | psd_lda | nested_k4 | 4 | 0.553 | -0.018 | 25.1 | — | — | — |
| faced_emotion_123 | psd_lda | glasses_4_k4 | 4 | 0.553 | -0.018 | 25.1 | — | — | — |
| motor_execution_ear_vs_scalp | logvar_lda | distributed_k8 | 8 | 0.614 | -0.038 | 25.0 | 0.581 | 2.8 | — |
| motor_execution_ear_vs_scalp | logvar_lda | random-s1_k8 | 8 | 0.614 | -0.038 | 24.8 | 0.581 | 2.7 | — |
| mi_4class_22ch | riemann_tslr | random-s0_k8 | 8 | 0.606 | -0.116 | 24.5 | — | — | -42.1 |
| mi_leftright_22ch | csp_lda | random-s0_k8 | 8 | 0.749 | -0.080 | 24.4 | 0.682 | 6.7 | — |
| mi_leftright_22ch | riemann_tslr | random-s2_k8 | 8 | 0.774 | -0.086 | 23.9 | 0.703 | 7.5 | — |
| motor_execution_ear_vs_scalp | csp_lda | region-sensorimotor_k8 | 8 | 0.695 | -0.059 | 23.4 | 0.641 | 4.6 | — |
| mi_leftright_22ch | riemann_tslr | random-s1_k8 | 8 | 0.785 | -0.086 | 23.2 | 0.712 | 7.7 | — |
| mi_4class_22ch | riemann_tslr | region-sensorimotor_k8 | 8 | 0.613 | -0.108 | 23.0 | — | — | -39.9 |
| mi_leftright_22ch | csp_lda | region-sensorimotor_k4 | 4 | 0.746 | -0.071 | 22.3 | 0.680 | 5.8 | — |
| mi_4class_22ch | csp_lda | distributed_k8 | 8 | 0.546 | -0.083 | 21.9 | — | — | -37.8 |
| mi_leftright_22ch | riemann_tslr | random-s1_k8 | 8 | 0.784 | -0.076 | 21.2 | 0.711 | 6.7 | — |
| mi_leftright_22ch | logvar_lda | region-sensorimotor_k8 | 8 | 0.697 | -0.053 | 21.2 | 0.642 | 4.1 | — |
| mi_4class_22ch | csp_lda | random-s1_k8 | 8 | 0.550 | -0.080 | 21.1 | — | — | -36.5 |
| mi_leftright_22ch | riemann_tslr | distributed_k8 | 8 | 0.784 | -0.076 | 21.1 | 0.711 | 6.7 | — |
| mi_leftright_22ch | riemann_tslr | region-sensorimotor_k8 | 8 | 0.794 | -0.077 | 20.8 | 0.719 | 6.9 | — |
| p300_8ch | xdawn_tslr | random-s0_k4 | 4 | 0.784 | -0.074 | 20.7 | 0.711 | 6.5 | — |
| mi_leftright_22ch | riemann_tslr | region-sensorimotor_k8 | 8 | 0.786 | -0.074 | 20.4 | 0.713 | 6.5 | — |
| stew_workload_14ch | psd_lda | forehead_2_k2 | 2 | 0.904 | -0.086 | 17.6 | 0.822 | 12.9 | — |
| mi_leftright_22ch | csp_lda | random-s1_k8 | 8 | 0.761 | -0.055 | 17.4 | 0.692 | 4.6 | — |
| faced_emotion_123 | psd_lda | posterior_4_k4 | 4 | 0.558 | -0.012 | 17.4 | — | — | — |
| mi_leftright_22ch | csp_lda | random-s1_k8 | 8 | 0.773 | -0.056 | 16.9 | 0.702 | 4.7 | — |
| mi_leftright_22ch | csp_lda | distributed_k8 | 8 | 0.773 | -0.055 | 16.9 | 0.702 | 4.7 | — |
| mi_leftright_22ch | csp_lda | random-s2_k8 | 8 | 0.764 | -0.052 | 16.5 | 0.695 | 4.3 | — |
| mi_leftright_22ch | logvar_lda | distributed_k16 | 16 | 0.709 | -0.041 | 16.3 | 0.651 | 3.2 | — |
| p300_8ch | xdawn_tslr | random-s2_k4 | 4 | 0.801 | -0.057 | 15.9 | 0.725 | 5.1 | — |
| mi_leftright_22ch | csp_lda | random-s2_k8 | 8 | 0.777 | -0.052 | 15.7 | 0.705 | 4.4 | — |
| motor_execution_ear_vs_scalp | riemann_tslr | random-s1_k8 | 8 | 0.732 | -0.043 | 15.5 | 0.669 | 3.4 | — |
| mi_4class_22ch | logvar_lda | random-s2_k16 | 16 | 0.540 | -0.052 | 15.1 | — | — | -26.9 |
| mi_leftright_22ch | logvar_lda | region-sensorimotor_k8 | 8 | 0.734 | -0.041 | 14.9 | 0.671 | 3.3 | — |
| mi_leftright_22ch | riemann_tslr | distributed_k16 | 16 | 0.817 | -0.055 | 14.7 | 0.738 | 5.0 | — |
| mi_leftright_22ch | logvar_lda | random-s2_k16 | 16 | 0.713 | -0.037 | 14.7 | 0.654 | 2.9 | — |
| mi_leftright_22ch | csp_lda | region-sensorimotor_k8 | 8 | 0.781 | -0.048 | 14.6 | 0.708 | 4.1 | — |
| mi_4class_22ch | csp_lda | region-sensorimotor_k8 | 8 | 0.575 | -0.055 | 14.5 | — | — | -26.0 |
| mi_4class_22ch | csp_lda | random-s0_k8 | 8 | 0.576 | -0.053 | 14.0 | — | — | -25.2 |
| mi_leftright_22ch | csp_lda | region-sensorimotor_k8 | 8 | 0.773 | -0.044 | 13.9 | 0.701 | 3.7 | — |
| sleep_staging_local | bandpower_lda | ear_6_k6 | 6 | 0.362 | -0.056 | 13.5 | — | — | — |
| motor_execution_ear_vs_scalp | riemann_tslr | region-sensorimotor_k8 | 8 | 0.739 | -0.036 | 13.0 | 0.675 | 2.8 | — |
| p300_8ch | xdawn_tslr | distributed_k4 | 4 | 0.812 | -0.046 | 12.9 | 0.734 | 4.1 | — |
| mi_leftright_22ch | logvar_lda | random-s2_k16 | 16 | 0.740 | -0.035 | 12.8 | 0.675 | 2.8 | — |
| mi_leftright_22ch | riemann_tslr | distributed_k16 | 16 | 0.814 | -0.046 | 12.8 | 0.736 | 4.2 | — |
| mi_leftright_22ch | csp_lda | distributed_k8 | 8 | 0.778 | -0.039 | 12.3 | 0.706 | 3.3 | — |
| mi_leftright_22ch | csp_lda | distributed_k16 | 16 | 0.790 | -0.039 | 11.9 | 0.715 | 3.4 | — |
| mi_leftright_22ch | riemann_tslr | random-s1_k16 | 16 | 0.828 | -0.043 | 11.6 | 0.749 | 4.0 | — |
| mi_leftright_22ch | logvar_lda | distributed_k16 | 16 | 0.744 | -0.031 | 11.3 | 0.679 | 2.5 | — |
| motor_execution_ear_vs_scalp | logvar_lda | random-s0_k8 | 8 | 0.635 | -0.017 | 11.0 | 0.596 | 1.218 | — |
| mi_leftright_22ch | logvar_lda | random-s1_k16 | 16 | 0.748 | -0.027 | 9.7 | 0.682 | 2.1 | — |
| mi_leftright_22ch | logvar_lda | random-s0_k16 | 16 | 0.749 | -0.026 | 9.3 | 0.683 | 2.0 | — |
| mi_leftright_22ch | logvar_lda | random-s1_k16 | 16 | 0.727 | -0.023 | 9.2 | 0.665 | 1.8 | — |
| mi_4class_22ch | logvar_lda | random-s1_k16 | 16 | 0.561 | -0.031 | 9.0 | — | — | -16.5 |
| mi_4class_22ch | logvar_lda | distributed_k16 | 16 | 0.561 | -0.031 | 8.9 | — | — | -16.4 |
| auditory_attention_earsaad | ridge_reconstruction | scalp_12_k12 | 12 | 0.807 | -0.030 | 8.8 | — | — | — |
| stew_workload_14ch | psd_lda | posterior_4_k4 | 4 | 0.948 | -0.042 | 8.6 | 0.875 | 7.6 | — |
| mi_leftright_22ch | riemann_tslr | random-s1_k16 | 16 | 0.830 | -0.031 | 8.5 | 0.750 | 2.8 | — |
| faced_emotion_123 | psd_lda | random-s0_k4 | 4 | 0.564 | -0.006 | 8.2 | — | — | — |
| stew_workload_14ch | psd_lda | glasses_4_k4 | 4 | 0.844 | -0.030 | 8.0 | 0.762 | 2.8 | — |
| mi_leftright_22ch | logvar_lda | random-s0_k16 | 16 | 0.730 | -0.020 | 7.9 | 0.667 | 1.5 | — |
| stew_workload_14ch | psd_lda | glasses_4_k4 | 4 | 0.952 | -0.038 | 7.8 | 0.881 | 7.0 | — |
| sleep_staging_local | bandpower_lda | ear_14_k14 | 14 | 0.388 | -0.030 | 7.2 | — | — | — |
| mi_leftright_22ch | csp_lda | random-s1_k16 | 16 | 0.806 | -0.023 | 7.1 | 0.729 | 2.0 | — |
| p300_8ch | logvar_lda | random-s1_k4 | 4 | 0.534 | -0.002 | 6.6 | 0.524 | 0.168 | — |
| mi_4class_22ch | riemann_tslr | distributed_k16 | 16 | 0.691 | -0.031 | 6.5 | — | — | -12.4 |
| ssvep_8ch | ssvep_cca | random-s1_k4 | 4 | 0.874 | -0.054 | 6.4 | — | — | -12.1 |
| ssvep_8ch | ssvep_cca | random-s0_k4 | 4 | 0.875 | -0.053 | 6.3 | — | — | -12.0 |
| mi_4class_22ch | csp_lda | distributed_k16 | 16 | 0.607 | -0.023 | 5.9 | — | — | -11.1 |
| mi_leftright_22ch | riemann_tslr | random-s2_k16 | 16 | 0.839 | -0.021 | 5.8 | 0.758 | 1.9 | — |
| mi_leftright_22ch | csp_lda | distributed_k16 | 16 | 0.799 | -0.018 | 5.5 | 0.723 | 1.500 | — |
| mi_4class_22ch | riemann_tslr | random-s1_k16 | 16 | 0.696 | -0.026 | 5.4 | — | — | -10.4 |
| mi_4class_22ch | riemann_tslr | random-s2_k16 | 16 | 0.696 | -0.026 | 5.4 | — | — | -10.4 |
| mi_4class_22ch | logvar_lda | random-s0_k16 | 16 | 0.574 | -0.018 | 5.2 | — | — | -9.7 |
| auditory_attention_earsaad | ridge_reconstruction | scalp_19_k19 | 19 | 0.820 | -0.017 | 5.1 | — | — | — |
| mi_leftright_22ch | riemann_tslr | random-s0_k16 | 16 | 0.854 | -0.018 | 4.8 | 0.772 | 1.7 | — |
| mi_leftright_22ch | riemann_tslr | random-s0_k16 | 16 | 0.843 | -0.017 | 4.6 | 0.762 | 1.5 | — |
| mi_leftright_22ch | riemann_tslr | random-s2_k16 | 16 | 0.855 | -0.016 | 4.4 | 0.773 | 1.6 | — |
| ssvep_8ch | ssvep_cca | random-s2_k4 | 4 | 0.892 | -0.037 | 4.3 | — | — | -8.4 |
| mi_4class_22ch | csp_lda | random-s1_k16 | 16 | 0.614 | -0.016 | 4.1 | — | — | -7.8 |
| faced_emotion_123 | psd_lda | random-s1_k4 | 4 | 0.568 | -0.002 | 3.4 | — | — | — |
| p300_8ch | logvar_lda | distributed_k4 | 4 | 0.535 | -0.001 | 3.1 | 0.525 | 0.079 | — |
| mi_4class_22ch | riemann_tslr | random-s0_k16 | 16 | 0.710 | -0.012 | 2.6 | — | — | -5.0 |
| ssvep_8ch | ssvep_cca | distributed_k4 | 4 | 0.914 | -0.014 | 1.6 | — | — | -3.3 |
| mi_leftright_22ch | csp_lda | random-s1_k16 | 16 | 0.811 | -0.005 | 1.6 | 0.734 | 0.447 | — |
| mi_4class_22ch | csp_lda | random-s2_k16 | 16 | 0.623 | -0.006 | 1.6 | — | — | -3.1 |
| mi_4class_22ch | csp_lda | random-s0_k16 | 16 | 0.626 | -0.003 | 0.858 | — | — | -1.6 |
| mi_leftright_22ch | csp_lda | random-s0_k16 | 16 | 0.827 | -0.002 | 0.538 | 0.747 | 0.156 | — |
| sleep_staging_local | bandpower_lda | scalp_6_k6 | 6 | 0.418 | 0.000 | 0.000 | — | — | — |
| motor_execution_ear_vs_scalp | logvar_lda | region-sensorimotor_k8 | 8 | 0.653 | 0.001 | -0.679 | 0.609 | -0.076 | — |
| mi_leftright_22ch | csp_lda | random-s0_k16 | 16 | 0.819 | 0.003 | -0.884 | 0.741 | -0.243 | — |
| mi_leftright_22ch | csp_lda | random-s2_k16 | 16 | 0.836 | 0.007 | -2.1 | 0.755 | -0.604 | — |
| mi_leftright_22ch | csp_lda | random-s2_k16 | 16 | 0.827 | 0.010 | -3.2 | 0.747 | -0.900 | — |
| faced_emotion_123 | psd_lda | nested_k24 | 24 | 0.573 | 0.003 | -4.3 | — | — | — |

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

Each control re-runs the exact decoder on shuffled labels. The null should sit at chance (AUC 0.5, accuracy 1/n, κ 0).

Controls cover the whole cohort of their track, under the control's own stratified 5-fold CV, so a `real` here is close to, but not identical with, the score in the tables above. The sleep track permutes whole 20-epoch blocks: a circular shift is not a valid null there, because it preserves the stage runs and the band-power drift and leaves the null near κ 0.13 rather than 0.

| track | subset | pipeline | real | perm_mean | chance | gap |
|---|---|---|---|---|---|---|
| auditory_attention_earsaad | around_ear_19_k19 | ridge_reconstruction | 0.689 | 0.506 | 0.500 | 0.183 |
| auditory_attention_earsaad | in_ear_12_k12 | ridge_reconstruction | 0.626 | 0.501 | 0.500 | 0.125 |
| auditory_attention_earsaad | scalp_12_k12 | ridge_reconstruction | 0.807 | 0.516 | 0.500 | 0.291 |
| auditory_attention_earsaad | scalp_19_k19 | ridge_reconstruction | 0.820 | 0.506 | 0.500 | 0.314 |
| auditory_attention_earsaad | scalp_29_k29 | ridge_reconstruction | 0.837 | 0.494 | 0.500 | 0.343 |
| faced_emotion_123 | glasses_4_k4 | psd_lda | 0.553 | 0.500 | 0.500 | 0.053 |
| faced_emotion_123 | posterior_4_k4 | psd_lda | 0.558 | 0.500 | 0.500 | 0.058 |
| mi_4class_22ch | region-sensorimotor_k8 | riemann_tslr | 0.626 | 0.252 | 0.250 | 0.374 |
| mi_leftright_22ch | region-sensorimotor_k8 | riemann_tslr | 0.801 | 0.501 | 0.500 | 0.300 |
| motor_execution_ear_vs_scalp | wu2020_inear_k8 | riemann_tslr | 0.468 | 0.504 | 0.500 | -0.036 |
| p300_8ch | distributed_k4 | xdawn_tslr | 0.811 | 0.498 | 0.500 | 0.313 |
| sleep_staging_local | ear_14_k14 | bandpower_lda | 0.388 | 0.004 | 0.000 | 0.385 |
| sleep_staging_local | ear_6_k6 | bandpower_lda | 0.362 | -0.002 | 0.000 | 0.364 |
| sleep_staging_local | scalp_6_k6 | bandpower_lda | 0.418 | 0.001 | 0.000 | 0.417 |
| ssvep_8ch | distributed_k4 | ssvep_cca | 0.914 | 0.083 | 0.083 | 0.831 |
| stew_workload_14ch | forehead_2_k2 | psd_lda | 0.700 | 0.506 | 0.500 | 0.194 |
| stew_workload_14ch | full_14_k14 | psd_lda | 0.874 | 0.508 | 0.500 | 0.365 |
| stew_workload_14ch | glasses_4_k4 | psd_lda | 0.844 | 0.501 | 0.500 | 0.342 |
| stew_workload_14ch | posterior_4_k4 | psd_lda | 0.759 | 0.497 | 0.500 | 0.262 |

## Confound and reproduction checks

### STEW: is rest-vs-task partly just time-in-session?

Rest was always recorded before the multitasking test, so the two conditions sit on opposite sides of a session boundary. This control uses no task labels at all: it asks whether a decoder can tell the first half of a recording from its second half, and compares that against randomly assigned halves.

| layout | real_half_accuracy | null_mean | gap |
|---|---|---|---|
| full_14 | 0.613 | 0.501 | 0.112 |
| posterior_4 | 0.575 | 0.499 | 0.076 |
| glasses_4 | 0.578 | 0.503 | 0.076 |
| forehead_2 | 0.567 | 0.497 | 0.070 |

Chance is 0.50. A gap above zero means the recording drifts, so the rest-vs-task result is partly "which half of the session". The released data cannot separate the two, which is why the workload track is reported as rest-vs-SIMKAP *condition recognition* and never as a validated mental-workload score.

### FACED: does this benchmark agree with the team's own run?

The emotion track re-derives everything from the per-participant feature caches rather than copying a spreadsheet. This compares the result with the predictions the team's FACED notebook saved. The window metadata is identical between the two, and the score is stable to about 0.001 across fold assignments, so a gap larger than that means the cached features were regenerated after those predictions were written — a version difference, not a disagreement about the conclusion.

| montage | ours | reference | delta | n_trials |
|---|---|---|---|---|
| Full 30 ch | 0.570 | 0.563 | 0.007 | 2952 |
| Glasses-like 4 ch | 0.552 | 0.548 | 0.005 | 2952 |

### Ear-SAAD: does the release already include artifact removal?

The paper reports its 60 s accuracies twice: with the full preprocessing pipeline, and after omitting EOG regression, bad-channel removal, ASR and high-power artifact rejection. The released `preprocessedData.zip` is the output of the authors' own `preprocessFromBIDS.m`, which runs `clean_channels_nolocs` at 0.45 and `clean_asr` at cutoff 5 before saving, so a correct reproduction must land on the *with-ASR* column. It does, which retires the worry that the ear numbers here are an un-cleaned upper bound.

| setup | ours_pct | paper_full_pct | paper_no_cleanup_pct | delta_vs_full | delta_vs_no_cleanup | closer_to |
|---|---|---|---|---|---|---|
| scalp_29 | 83.700 | 83.440 | 86.110 | 0.260 | -2.410 | full |
| around_ear_19 | 68.890 | 67.220 | 64.890 | 1.670 | 4.000 | full |
| in_ear_12 | 62.590 | 61.110 | 58.780 | 1.480 | 3.810 | full |
