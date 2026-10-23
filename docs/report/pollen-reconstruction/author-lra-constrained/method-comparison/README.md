# Two preserved LOVE methods on matched English development folds

This retrospective comparison asks how stored pollen point scores differ between
the original uniform-start method and the separately executed fixed-start method.
The changed method combines the 32-start grid **and** the explicitly unrounded
`x/x.sum()` composition adapter; it does not isolate a causal starting-point effect.
All source sites and outcomes are previously exposed development evidence.

The original method scored 14 folds and refused BECKHAM. The fixed-start cohort
scored all 15 folds. The paired comparison therefore retains **14 matched folds
per baseline and 42 fold/baseline pairs**, alongside all 15 method dispositions.
The three new BECKHAM scores remain explicitly unpaired; the original refusal is
preserved without inventing an old score or replacing it with zero.

| Spatial baseline | Matched folds | Mean ΔTV | Median ΔTV | ΔTV range | TV worsened / reduced |
| --- | --- | --- | --- | --- | --- |
| training_mean | 14 | +1.52646e-06 | +1.74661e-06 | -1.46919e-06 to +4.0688e-06 | 11 / 3 |
| nearest_site | 14 | +2.35433e-06 | +2.27844e-07 | -1.51366e-05 to +3.69592e-05 | 8 / 6 |
| inverse_distance_squared | 14 | +2.71337e-06 | +1.60853e-06 | -1.15043e-05 to +2.80313e-05 | 10 / 4 |

All three mean total-variation differences are positive, about 1.53×10⁻⁶ to 2.71×10⁻⁶. Across the paired folds, the retained total-variation differences range from −1.51×10⁻⁵ to +3.70×10⁻⁵. These small descriptive joint-method differences provide no starting-point causal effect or superiority claim.

Each paired fold receives equal weight. The following differences are the
fixed-start/unrounded method minus the original uniform/host-rounded method.
Positive MAE, RMSE, total-variation or finite deviance changes mean worse measured
pollen mismatch on that pair. Signed bias differences have no universal better
or worse direction. Shared training, reused requests and common physical inputs
make these descriptive point differences dependent, without inferential intervals,
significance or a model-superiority claim.

| Native record | Baseline | Original TV | Cohort TV | ΔMAE | ΔRMSE | ΔTV | Δbias | Δdeviance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| author:GOURTEMIRES | training_mean | 0.292076 | 0.292078 | +1.61468e-07 | +3.70121e-07 | +2.42202e-06 | +1.56848e-18 | +0.0155349 |
| author:GOURTEMIRES | nearest_site | 0.137883 | 0.137882 | -9.60612e-08 | -2.09735e-07 | -1.44092e-06 | -4.55365e-18 | -0.00274169 |
| author:GOURTEMIRES | inverse_distance_squared | 0.141072 | 0.141071 | -7.48003e-08 | -1.62375e-07 | -1.12201e-06 | +1.24322e-17 | -0.0034809 |
| author:LONGBREACH | training_mean | 0.275022 | 0.275026 | +2.71254e-07 | +4.28085e-07 | +4.0688e-06 | -7.50268e-18 | +0.00577781 |
| author:LONGBREACH | nearest_site | 0.12525 | 0.125256 | +3.59243e-07 | +1.58194e-06 | +5.38865e-06 | -2.2696e-18 | +0.00505413 |
| author:LONGBREACH | inverse_distance_squared | 0.115579 | 0.115584 | +2.96118e-07 | +1.4885e-06 | +4.44178e-06 | -2.77556e-18 | +0.00429137 |
| author:CUTHILL2 | training_mean | 0.257496 | 0.257496 | -1.28687e-08 | -1.03323e-07 | -1.9303e-07 | -3.95372e-18 | -0.00337572 |
| author:CUTHILL2 | nearest_site | 0.2446 | 0.244602 | +1.2497e-07 | +9.41382e-08 | +1.87455e-06 | -3.87422e-18 | +0.0029094 |
| author:CUTHILL2 | inverse_distance_squared | 0.313936 | 0.313938 | +9.35711e-08 | +3.67685e-07 | +1.40357e-06 | +7.88576e-18 | +0.00697713 |
| author:HARESDOWN | training_mean | 0.47029 | 0.470294 | +2.44187e-07 | +4.73671e-07 | +3.66281e-06 | -3.9465e-18 | +0.0316619 |
| author:HARESDOWN | nearest_site | 0.213645 | 0.21363 | -1.00911e-06 | -2.25595e-06 | -1.51366e-05 | -4.27898e-18 | -0.0461285 |
| author:HARESDOWN | inverse_distance_squared | 0.193997 | 0.193986 | -7.66951e-07 | -1.93308e-06 | -1.15043e-05 | -4.10551e-18 | -0.0355697 |
| author:BROADOWN | training_mean | 0.338467 | 0.338466 | -9.79458e-08 | -2.81769e-07 | -1.46919e-06 | -4.19225e-18 | -0.0153251 |
| author:BROADOWN | nearest_site | 0.239006 | 0.239004 | -1.4597e-07 | -2.3278e-08 | -2.18955e-06 | +4.22116e-18 | +0.000543673 |
| author:BROADOWN | inverse_distance_squared | 0.262533 | 0.262531 | -1.3325e-07 | -5.74132e-08 | -1.99875e-06 | -2.51535e-18 | -0.00239831 |
| author:NTWITCHEN | training_mean | 0.3067 | 0.306703 | +2.24781e-07 | +3.37876e-07 | +3.37171e-06 | -2.65991e-18 | +0.0163452 |
| author:NTWITCHEN | nearest_site | 0.280598 | 0.280635 | +2.46395e-06 | +6.31797e-06 | +3.69592e-05 | +6.36065e-19 | +0.255717 |
| author:NTWITCHEN | inverse_distance_squared | 0.279206 | 0.279234 | +1.86875e-06 | +4.17645e-06 | +2.80313e-05 | +6.7076e-18 | +0.181687 |
| author:WINNEYS | training_mean | 0.499836 | 0.499835 | -6.34006e-08 | -1.67229e-07 | -9.51009e-07 | -3.06468e-18 | -0.00711322 |
| author:WINNEYS | nearest_site | 0.442712 | 0.442712 | -1.44729e-08 | -8.85407e-08 | -2.17093e-07 | -1.7275e-18 | -0.000371214 |
| author:WINNEYS | inverse_distance_squared | 0.441212 | 0.441213 | +8.73739e-09 | -1.00266e-07 | +1.31061e-07 | +2.61654e-18 | -0.000668423 |
| author:WINDMILL | training_mean | 0.355725 | 0.355726 | +8.22857e-08 | +4.69343e-07 | +1.23429e-06 | -6.57749e-18 | +0.0151413 |
| author:WINDMILL | nearest_site | 0.173178 | 0.173178 | +1.67046e-08 | -1.05869e-08 | +2.50568e-07 | +5.51498e-18 | -0.00230265 |
| author:WINDMILL | inverse_distance_squared | 0.193062 | 0.193063 | +1.20899e-07 | +4.37669e-07 | +1.81349e-06 | +9.68554e-19 | -0.00130115 |
| author:MOLECHAM | training_mean | 0.403739 | 0.403741 | +1.38984e-07 | +3.07046e-07 | +2.08477e-06 | -8.96274e-19 | +0.0188642 |
| author:MOLECHAM | nearest_site | 0.352927 | 0.352939 | +7.86246e-07 | +1.72676e-06 | +1.17937e-05 | +3.75857e-18 | +0.0669219 |
| author:MOLECHAM | inverse_distance_squared | 0.294722 | 0.294729 | +4.89991e-07 | +5.21371e-07 | +7.34986e-06 | -7.37257e-18 | +0.0168062 |
| author:COMERSLA | training_mean | 0.291903 | 0.291905 | +1.23055e-07 | +3.93491e-07 | +1.84583e-06 | -2.84784e-18 | +0.00125676 |
| author:COMERSLA | nearest_site | 0.2725 | 0.27251 | +7.20662e-07 | +2.19477e-06 | +1.08099e-05 | +8.29776e-18 | +0.00877769 |
| author:COMERSLA | inverse_distance_squared | 0.247009 | 0.247018 | +6.27146e-07 | +1.91292e-06 | +9.40719e-06 | +3.46945e-18 | +0.00668141 |
| author:LOBBSBOG | training_mean | 0.408244 | 0.408248 | +2.37511e-07 | +5.05265e-07 | +3.56266e-06 | -4.87891e-18 | +0.0319039 |
| author:LOBBSBOG | nearest_site | 0.164048 | 0.164034 | -9.43262e-07 | -5.90705e-07 | -1.41489e-05 | -4.97287e-18 | -0.0252866 |
| author:LOBBSBOG | inverse_distance_squared | 0.138418 | 0.138413 | -3.18264e-07 | -4.22561e-07 | -4.77396e-06 | -2.02384e-19 | -0.0157785 |
| author:LARKBARR | training_mean | 0.430712 | 0.430714 | +1.09826e-07 | +3.60937e-07 | +1.64739e-06 | -1.44127e-17 | +0.00453857 |
| author:LARKBARR | nearest_site | 0.305223 | 0.305219 | -2.52362e-07 | +5.32645e-07 | -3.78543e-06 | +2.15395e-18 | +0.00714584 |
| author:LARKBARR | inverse_distance_squared | 0.324384 | 0.324386 | +1.33854e-07 | +4.56327e-07 | +2.00781e-06 | -2.2696e-18 | +0.00528093 |
| author:HANGINGS | training_mean | 0.325351 | 0.325351 | +3.73929e-09 | +2.16722e-08 | +5.60893e-08 | -1.06975e-18 | -0.00107018 |
| author:HANGINGS | nearest_site | 0.665647 | 0.66565 | +1.73162e-07 | +6.33183e-07 | +2.59743e-06 | -6.3462e-18 | +0.0262295 |
| author:HANGINGS | inverse_distance_squared | 0.662499 | 0.662501 | +1.72638e-07 | +6.32768e-07 | +2.58957e-06 | -8.67362e-20 | +0.0259395 |
| author:WHH05 | training_mean | 0.861867 | 0.861867 | +1.82111e-09 | -5.28008e-08 | +2.73167e-08 | +5.69568e-18 | +0.000535014 |
| author:WHH05 | nearest_site | 0.820589 | 0.820589 | +1.36746e-08 | -9.95434e-09 | +2.05119e-07 | -4.27898e-18 | +0.00135072 |
| author:WHH05 | inverse_distance_squared | 0.820779 | 0.82078 | +1.40349e-08 | -9.63543e-09 | +2.10523e-07 | -7.86408e-18 | +0.00137731 |

| Native record | Original disposition | Original reason | Cohort disposition | Paired baseline rows |
| --- | --- | --- | --- | --- |
| author:GOURTEMIRES | predicted | — | predicted | 3 |
| author:LONGBREACH | predicted | — | predicted | 3 |
| author:CUTHILL2 | predicted | — | predicted | 3 |
| author:HARESDOWN | predicted | — | predicted | 3 |
| author:BROADOWN | predicted | — | predicted | 3 |
| author:NTWITCHEN | predicted | — | predicted | 3 |
| author:WINNEYS | predicted | — | predicted | 3 |
| author:WINDMILL | predicted | — | predicted | 3 |
| author:MOLECHAM | predicted | — | predicted | 3 |
| author:BECKHAM | refused | training_reconstruction_incomplete | predicted | 0 |
| author:COMERSLA | predicted | — | predicted | 3 |
| author:LOBBSBOG | predicted | — | predicted | 3 |
| author:LARKBARR | predicted | — | predicted | 3 |
| author:HANGINGS | predicted | — | predicted | 3 |
| author:WHH05 | predicted | — | predicted | 3 |

| Native record | Baseline | MAE | RMSE | TV | Bias | Deviance | Original disposition |
| --- | --- | --- | --- | --- | --- | --- | --- |
| author:BECKHAM | training_mean | 0.027368 | 0.0638813 | 0.410519 | 7.82071e-18 | 651.873 | refused: training_reconstruction_incomplete |
| author:BECKHAM | nearest_site | 0.0224929 | 0.0547431 | 0.337393 | 2.93457e-18 | 516.951 | refused: training_reconstruction_incomplete |
| author:BECKHAM | inverse_distance_squared | 0.0226671 | 0.0550258 | 0.340007 | -8.73144e-18 | 516.706 | refused: training_reconstruction_incomplete |

31 of 42 paired fold/baseline rows worsen at least one measured nonbias error metric. Every such row is retained below.

| Native record | Baseline | Worsened error metrics |
| --- | --- | --- |
| author:GOURTEMIRES | training_mean | mae_fraction, rmse_fraction, total_variation, count_conditioned_deviance |
| author:LONGBREACH | training_mean | mae_fraction, rmse_fraction, total_variation, count_conditioned_deviance |
| author:LONGBREACH | nearest_site | mae_fraction, rmse_fraction, total_variation, count_conditioned_deviance |
| author:LONGBREACH | inverse_distance_squared | mae_fraction, rmse_fraction, total_variation, count_conditioned_deviance |
| author:CUTHILL2 | nearest_site | mae_fraction, rmse_fraction, total_variation, count_conditioned_deviance |
| author:CUTHILL2 | inverse_distance_squared | mae_fraction, rmse_fraction, total_variation, count_conditioned_deviance |
| author:HARESDOWN | training_mean | mae_fraction, rmse_fraction, total_variation, count_conditioned_deviance |
| author:BROADOWN | nearest_site | count_conditioned_deviance |
| author:NTWITCHEN | training_mean | mae_fraction, rmse_fraction, total_variation, count_conditioned_deviance |
| author:NTWITCHEN | nearest_site | mae_fraction, rmse_fraction, total_variation, count_conditioned_deviance |
| author:NTWITCHEN | inverse_distance_squared | mae_fraction, rmse_fraction, total_variation, count_conditioned_deviance |
| author:WINNEYS | inverse_distance_squared | mae_fraction, total_variation |
| author:WINDMILL | training_mean | mae_fraction, rmse_fraction, total_variation, count_conditioned_deviance |
| author:WINDMILL | nearest_site | mae_fraction, total_variation |
| author:WINDMILL | inverse_distance_squared | mae_fraction, rmse_fraction, total_variation |
| author:MOLECHAM | training_mean | mae_fraction, rmse_fraction, total_variation, count_conditioned_deviance |
| author:MOLECHAM | nearest_site | mae_fraction, rmse_fraction, total_variation, count_conditioned_deviance |
| author:MOLECHAM | inverse_distance_squared | mae_fraction, rmse_fraction, total_variation, count_conditioned_deviance |
| author:COMERSLA | training_mean | mae_fraction, rmse_fraction, total_variation, count_conditioned_deviance |
| author:COMERSLA | nearest_site | mae_fraction, rmse_fraction, total_variation, count_conditioned_deviance |
| author:COMERSLA | inverse_distance_squared | mae_fraction, rmse_fraction, total_variation, count_conditioned_deviance |
| author:LOBBSBOG | training_mean | mae_fraction, rmse_fraction, total_variation, count_conditioned_deviance |
| author:LARKBARR | training_mean | mae_fraction, rmse_fraction, total_variation, count_conditioned_deviance |
| author:LARKBARR | nearest_site | rmse_fraction, count_conditioned_deviance |
| author:LARKBARR | inverse_distance_squared | mae_fraction, rmse_fraction, total_variation, count_conditioned_deviance |
| author:HANGINGS | training_mean | mae_fraction, rmse_fraction, total_variation |
| author:HANGINGS | nearest_site | mae_fraction, rmse_fraction, total_variation, count_conditioned_deviance |
| author:HANGINGS | inverse_distance_squared | mae_fraction, rmse_fraction, total_variation, count_conditioned_deviance |
| author:WHH05 | training_mean | mae_fraction, total_variation, count_conditioned_deviance |
| author:WHH05 | nearest_site | mae_fraction, total_variation, count_conditioned_deviance |
| author:WHH05 | inverse_distance_squared | mae_fraction, total_variation, count_conditioned_deviance |

All 210 retained paired metric comparisons are finite. There are no infinite-deviance transitions in these actual paired outputs; the protocol and report retain their explicit refusal/category rules.

Every compared pair joins the exact native fold, site, taxon axis, integer count
vector, chronology identifiers and geometry/kernel support. The retained window
is labelled calendar BP, 1,250–1,750 and centred at 1,500, without a separately
encoded BP reference epoch. No age conversion or calibration is performed.
Circular basins and homogeneous rings remain conditional transport assumptions,
not measured historical vegetation. Across all 15 source sites, the 30-taxon subcomposition retains the
original exclusion of 159 Filipendula grains from 20,732 source grains.

Null and infinite-deviance cases retain their explicit categories. A finite mean
or median uses only its stated finite paired denominator; excluded infinite cases
remain visible alongside it. No observation smoothing, pseudocount, refit,
rescoring or outcome-based method selection is introduced by this comparison.

The registered saved-result comparison ran on `b30acdff340aa36c9ab28974232f73badd53393d` under
[the frozen scientific protocol](protocol.json), designed on the separate
`bfee143ff2fc07624d931300f81dabda1f1dceea` source epoch. Its compact execution
authority binds the exact original and cohort products, native terminals,
resource observations and independent saved-output review:
[execution authority](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/author-love-matched-method-comparison.json).

[report.json](report.json) retains full support and descriptive summaries;
[paired-scores.csv](paired-scores.csv) retains every metric difference and
nonfinite category; [fold-dispositions.csv](fold-dispositions.csv) retains all
15 original/cohort dispositions. [sources.py](sources.py),
[comparison.py](comparison.py) and [replay.py](replay.py) retain the exact executed
custody/support, arithmetic and entry-point sources.

These already generated outcomes cannot supply untouched confirmation,
independent vegetation accuracy, calibrated uncertainty, original R optimizer
parity, source-rights admission, installed-distribution qualification or release
approval. The original studies and every unmet owner criterion remain separate.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Retrospective saved-score comparison of combined fixed-start/unrounded and uniform-start/host-rounded LOVE methods on14 matched exposed English folds; preserve all15 dispositions and separate unpaired BECKHAM outcomes.

**Supported claim.** Exact stored-result support joins and descriptive point-score differences for14 matched folds across three fixed spatial baselines; all15 method dispositions and three unpaired BECKHAM scores retained.

**Unsupported claim.** A causal starting-point effect, method superiority, independent or untouched ecological accuracy, calibrated uncertainty, optimizer global optimum, original R parity, physical cohort acceptance or release approval.

**Actual verification performed.** Actual saved-result stage, scientific runner and root-collected process exits0 on b30acdff340aa36c9ab28974232f73badd53393d; independent output review joins all210 paired metric cells,42 pairs,15 dispositions,three unpaired scores,three summaries,31 pairs worsening at least one nonbias error metric and both CSV projections. No new fits or pollen rescoring.

**Remaining input or review.** All outcomes are previously exposed development evidence. Independent compatible vegetation/support, prospectively untouched outcomes and qualified ecological review remain required for broader accuracy; method/uncertainty/release criteria remain open.

**Cause category.** algorithm/numerical | assumption | comparability | qualified review

**Consequence.** Treat the32-start grid and unrounded composition adapter as a combined method change; keep tiny positive and negative point differences, dependent equal-fold weighting, every refusal and unmatched outcome.

**Precise next acceptance route.** Review descriptive paired evidence without selecting or claiming superiority from it; prespecify an independently admitted physical-support and untouched-outcome protocol before confirmatory accuracy claims.

**Negative or refused result.** Original uniform method refused BECKHAM; no old score is invented.31 of42 paired rows worsen at least one nonbias metric; meanTV differences are positive for all three baselines. All210 actual paired metric comparisons are finite.

**Matched denominator.** 14 matched folds per baseline;42 paired rows and210 metric differences. All15 original/cohort dispositions and three separate unpaired cohort BECKHAM scores remain visible; no15-fold paired delta.

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/method-comparison/fold-dispositions.csv](fold-dispositions.csv) (SHA-256 `9293ffd67fc6feae262f53f64f83db4091d14cbbbabed42dabb5c8c1a55c25d0`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/method-comparison/paired-scores.csv](paired-scores.csv) (SHA-256 `9ad9a7c730ec479a3a779726c93a466964cf88287e6893288c8ab1b77523a890`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/method-comparison/report.json](report.json) (SHA-256 `27a3e26512acfee8142555c82425c8a3378ee50bae668585e2513e8c443ff4da`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/method-comparison/protocol.json](protocol.json) (SHA-256 `a53b0c1f8691b204d3cd19326f2055033740105a22efe57abab36025a3df25fd`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/method-comparison/comparison.py](comparison.py).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/method-comparison/replay.py](replay.py).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/method-comparison/sources.py](sources.py).

- [Retained qualification evidence: reports/science/source-cohorts/author-love-matched-method-comparison.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/author-love-matched-method-comparison.json) (SHA-256 `23a6d11f763c0e262a25b6f77dc2437bfaa9f7691ca8db7d2826e7566e2e22f1`).

- [Canonical scientific account: reports/science/english-lra-pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/english-lra-pollen-prediction.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
