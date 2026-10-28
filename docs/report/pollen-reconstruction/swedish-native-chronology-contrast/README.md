# Native chronology contrasts on five Swedish pollen cores

The same native pollen datasets give different conditional Betula/Poaceae panel estimates when two recorded calibrated-BP chronology profiles allocate them to different declared windows. This retained-output comparison covers every existing same-dataset chronology pair in the Swedish common-panel result. It evaluates all 125 pair/window slots without refitting ages or rerunning reconstruction or physical transport.

## Same-core comparison and sample membership

Each pair shares its exact native dataset and collection unit, the original two literal parameter-selection tokens, PPE, static receiving-basin scenario, 100 km regional extent and 3 m/s wind. Both age models retain their native calibrated-BP scale and the documented Neotoma AD 1950 datum. First and second refer to their retained producer order; they indicate no preference or greater chronology accuracy. Publication and collection years do not reset BP zero.

| Native site / dataset | CalBP chronology IDs, first → second | Selected samples, first / second | Samples changing windows | Matched windows | Largest absolute Betula panel change |
| --- | --- | ---: | ---: | ---: | ---: |
| Lake Flarken / 4042 | 25402 → 25404 | 111 / 111 | 14 | 24 | 5.985 percentage points |
| Klotjärnen / 19909 | 11514 → 11513 | 101 / 100 | 17 | 20 | 9.493 percentage points |
| Holtjärnen / 21790 | 12503 → 12504 | 101 / 100 | 9 | 23 | 14.395 percentage points |
| Vuoskkujávri / 45311 | 29525 → 29524 | 65 / 65 | 22 | 22 | 11.586 percentage points |
| Alanen Laanijärvi / 45314 | 29528 → 29529 | 54 / 53 | 14 | 17 | 7.488 percentage points |

Across 449 source samples, 76 change windows while remaining selected in both models. Three more are retained only by the first model because their alternative point ages lie outside the declared window domain. Klotjärnen, Holtjärnen and Alanen therefore have different selected sample cohorts; equal or nearly equal sample totals do not establish identical membership. Seventeen source samples remain outside both selected cohorts under their point-window or literal-panel refusals. Raw ages, missing bounds, signed values and all excluded observations remain unchanged in private source support.

## Full window domain and contrasts

Of the 125 declared pair/window slots, 106 have both source-supported saved outputs, five have only the first, four have only the second, and ten have neither. All 19 unpaired slots retain null contrasts. Window-specific one-sided support can arise from different allocation of samples that remain present in both global cohorts; it does not imply a missing physical core. Missing windows are not filled with zero pollen or vegetation.

The reported change is second minus first in conditional composition within the Betula/Poaceae panel. Flarken’s and Holtjärnen’s largest Betula changes are decreases; the other three largest changes are increases. These extrema describe this finite fixed-parameter scenario and its different pooled counts. They are not measured vegetation change, whole-landscape cover, a historical LandClim replay, or evidence that either chronology is more accurate.

## Uncertainty and numerical verification

The original counting and shared-PPE marginal covariance remains its recorded authority. In the original [retained-output report](report.json), all 125 paired standard-error fields remain null: its pooled-window marginal errors do not supply cross-chronology covariance. The separate per-aliquot scenario below declares and evaluates a joint model; it does not replace those original errors or supply a chronology probability allocation, age-error posterior or empirical uncertainty coverage.

The actual bounded reader reconciled every selected native sample identity and pooled count to its saved numerical window. A separate Decimal50 implementation checked all 898 sample-side age memberships, 663 pooled support-count cells, 442 retained cover cells and 212 paired contrast cells. Its largest absolute discrepancy was below 2.04 × 10⁻¹⁶ against the unchanged 2 × 10⁻¹³ tolerance. It reused the previously qualified physical factors; no new physical quadrature, source acquisition, calibration or model reconstruction occurred.

## Declared per-sample counting and shared-PPE uncertainty

A separate [qualified joint scenario](paired-uncertainty.json) reuses the same ten retained source files, fixed point-age memberships, literal Betula/Poaceae counts, static radii and deposition factors. Its 432 selected counted samples are distinct primitive counting observations drawn from the original 449 source samples. Each sample has a fixed two-taxon panel total and a plug-in multinomial count covariance. Counts outside that panel are excluded from this denominator. The same counted sample is reused as one latent observation wherever either chronology assigns it; alternate profiles are not independent replicate cores.

One global PPE vector, Betula 5.106 and Poaceae 1, spans all cores, profiles and windows, with retained input SD magnitudes 0.303 and 0 and a declared diagonal taxon covariance. Distinct samples have independent conditional counting error, and counts and PPE have zero cross-covariance under this scenario. These are working assumptions, not observed environmental independence or newly estimated PPE correlations. Cross-core shared-PPE covariance remains even when count supports are disjoint.

The actual public API produced 221 occupied profile/window compositions, a joint covariance on 442 taxon axes and paired contrasts on 212 axes across the 106 matched slots. All 19 unpaired slots remain refused. The 76 window migrations, three cohort losses and 17 samples refused by both selections are unchanged. Point estimates match the retained originals within 1.85 × 10⁻¹⁶. An independent Decimal50 implementation checked 1,105,676 scalar values, including all 720,924 counting/PPE/total joint and contrast covariance cells. Its largest covariance discrepancy was below 1.15 × 10⁻¹⁸ under the frozen scale-aware tolerances. The focused 83-test run also preserved the old pooled API's overlap refusals and qualified source identity, zero-count and extreme-arithmetic boundaries.

| Native dataset | Matched slots | Largest conditional paired Betula SE, percentage points | Identical support and response slots with exact-zero contrasts |
| --- | ---: | ---: | ---: |
| 4042 | 24 | 3.264 | 4 |
| 19909 | 20 | 2.544 | 2 |
| 21790 | 23 | 4.471 | 12 |
| 45311 | 22 | 4.284 | 1 |
| 45314 | 17 | 4.705 | 3 |

These standard errors are conditional first-order delta quantities on fixed chronology selections. Twenty-two matched slots reuse identical sample support and response and have exact-zero contrasts and paired variance; identical support with a changed response does not generally cancel. Assuming independent profile errors fails the shared-source controls. No selected sample in this fixture has a measured zero on either panel axis, and no primitive count covariance or occupied marginal variance is degenerate. General taxon-zero plug-in cases can nevertheless understate finite-sample uncertainty; the focused controls retain that boundary.

This model conditions on each sample's observed composition, while the earlier counting model conditions on one pooled-window composition. The pooled count covariance minus the sum of per-sample count covariances equals the positive semidefinite weighted between-sample composition term. The actual new marginal counting variances therefore do not exceed the original pooled marginals; the largest decrease is 3.706 × 10⁻⁵ in squared cover-fraction units. Shared-PPE marginals retain numerical parity. The smaller counting variance follows the changed conditioning assumption and establishes no accuracy or interval-coverage gain. Neither scenario models age-error distributions, dating/calibration uncertainty, historical basin change, site bootstrap, ecological dependence or measured whole-vegetation accuracy.

The [source and execution account](paired-uncertainty-source.json) binds the actual producer/API/independent-oracle code, source and protocol identities and successful native receipt, while retaining the earlier typing failure. The maintained [joint consumer](../../../../reports/science/swedish-native-chronology-contrast/paired_uncertainty.py) and [frozen aliquot protocol](../../../../reports/science/swedish-native-chronology-contrast/aliquot-protocol.json) reproduce these derived aggregates from the same qualified private packet. Full sample associations, Jacobians and covariance matrices remain private. No source acquisition, physical quadrature, age fit or historical/rights admission was performed.

## Source attribution and retained evidence

The [common-panel source attribution](../swedish-observed-common-panel/attribution.json) retains native dataset DOIs, original investigator and EPD credit, and source publication relationships for these exact datasets. Current public analytical-use attribution remains distinct from historical/private-author-copy permissions and redistribution decisions. This account publishes aggregate derived comparisons; it does not redistribute individual source sample/depth/age associations or original archives.

The [aggregate report](report.json) retains every pair/window slot, model identity, source-custody hashes, cohort/refusal totals and scientific limitations. The maintained [source reader](../../../../reports/science/swedish-native-chronology-contrast/qualify.py) and [frozen comparison protocol](../../../../reports/science/swedish-native-chronology-contrast/protocol.json) consume the exact retained source packet to reproduce the aggregate. The completed [Tibetanus TP/native sensitivity](../tibetanus-point-age-sensitivity/README.md) is a separate study and was not rerun here.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-bound conditional reconstruction or exposed pollen development wrapper; own source assumptions and exact scored/refused populations must be preserved alongside account links.

**Supported claim.** The original deterministic comparison retains all 125 chronology/window combinations. A separate model of counting error per aliquot and shared PPE uncertainty now gives conditional joint covariance on 442 axes and 212 matched contrast axes. Its point estimates agree with the retained comparison.

**Unsupported claim.** An age-model probability distribution, better chronology or vegetation accuracy, environmental independence, calibrated interval coverage, historical LandClim reproduction or empirically estimated shared-PPE covariance. The new counting model does not replace the original pooled-window marginal errors.

**Actual verification performed.** The public API and maintained consumer passed 83 focused tests, strict typing, lint and format checks. An independent Decimal50 calculation checked 1,105,676 scalar values, including 720,924 covariance cells. All 28,456 source and runtime pins stayed unchanged. Point differences were below 1.85 × 10⁻¹⁶; joint and contrast covariance errors were below 1.15 × 10⁻¹⁸ and satisfied the frozen scale-aware bounds. No new source capture, quadrature, calibration or age fit was performed.

**Remaining input or review.** Raw age bounds remain unknown. Cross-profile covariance is conditional on plug-in multinomial counts for each aliquot and one global diagonal PPE covariance; it is not a source age posterior. Historical geometry and selection, biological and environmental dependence, independent chronology and vegetation accuracy, qualified review and rights decisions remain open.

**Cause category.** data | assumption | comparability | access/rights | qualified review

**Consequence.** Preserve the original 125 null paired standard errors and pooled marginals. All 19 unpaired combinations also remain null in the new scenario. Identical membership and response can cancel to exact zero contrast covariance; narrower conditional variance does not establish improved accuracy.

**Precise next acceptance route.** Qualify a source age and membership probability model before describing chronology-distribution uncertainty. Obtain external chronology and matched vegetation evidence for accuracy. Qualify sample dependence and PPE uncertainty empirically before interpreting conditional delta standard errors as calibrated intervals.

**Negative or refused result.** The 19 unpaired combinations comprise five reference-only, four alternative-only and ten empty combinations. Three samples leave the second cohort and 17 are refused by both. Identical support and response produce 44 exact zero contrast variances in 22 combinations. No zero taxon axis or degenerate primitive covariance occurs among the 432 selected samples. Generic taxon-zero plug-in undercoverage remains a limitation; the existing pooled-overlap and extreme-arithmetic refusals are preserved.

**Matched denominator.** 449 source samples supply 432 selected counting primitives across five native same-dataset chronology pairs and 25 windows: 125 combinations, 106 matched and 19 unpaired. The 221 occupied profile windows produce 442 joint axes and 212 matched contrast axes. Of the shared selected samples, 76 migrate windows. Each sample uses a fixed total over two literal taxa; unparameterized NISP is excluded.

- [Retained qualification evidence: docs/report/pollen-reconstruction/swedish-native-chronology-contrast/report.json](report.json) (SHA-256 `27ab3800dce9f9a620e0ed0b0ed99cf2c2e5781330f2dae0a631c2082e95254a`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/swedish-observed-common-panel/attribution.json](../swedish-observed-common-panel/attribution.json) (SHA-256 `b760890e945c1efdbd3a7c5a81f986d50da762945f8220136da7a4953d34ea58`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/swedish-native-chronology-contrast/paired-uncertainty.json](paired-uncertainty.json) (SHA-256 `248c94af458b2f941426ef518b4a2493b772bcd3501b6208eb3106049cb8c5a4`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/swedish-native-chronology-contrast/paired-uncertainty-source.json](paired-uncertainty-source.json) (SHA-256 `a68a0568f8298f78d394c015ce4f951a208d81ebd327b7e12a33c6ec08559a72`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
