# Swedish forward-pollen development comparison

The actual source-group-withheld consumer predicts literal Betula/Poaceae pollen fractions from other collection units under fixed static-circle and point-age scenarios. All five declared profiles and both publication grouping rules were run. The complete 4,750-attempt ledger is retained, including failed support and unavailable target outcomes.

The scored evidence consists of **21 distinct target windows from three native collection units**, all in declared grid context 779. Five profiles and two grouping rules reuse those outcomes, producing 210 scored records; they are not 210 independent observations. Their total literal two-taxon count denominator is 37,300, rather than whole-sample NISP.

| Native dataset | Native collection unit | Core handle | Named chronology | Scored window indices |
| --- | --- | --- | --- | --- |
| 23013 | 16622 | KRAGMJNY | 13366 | 1, 2, 3, 4, 5, 6, 7 |
| 53999 | 39240 | BJARE | 38421 | 1, 2, 3, 4, 5, 6, 7 |
| 54001 | 39241 | BOKE | 38422 | 1, 2, 3, 4, 5, 6, 7 |

Each grouping rule declares 2,375 attempts: 135 predictions, 105 scored records, 30 predictions with no literal target panel and 2,240 source-support refusals. Across both rules there are 270 predictions, 210 scored records, 60 unavailable target outcomes and 4,480 source-support refusals. The two grouping rules happen to yield identical full prediction and score ledgers on these captured inputs. Future source relations may change that equivalence.

Source-support refusals require fewer than two allowed dependency groups in all 2,240 refused attempts per rule. Missing primary publications contribute to 375 of those attempts and alternate datasets from an already represented collection unit to 125. These cause counts overlap. Target values were opened for scoring after predictions and their hash were frozen; missing target panels do not alter training, predictions or profile choices.

Errors remain large. Equal-window macro mean L1 error is 0.7181 for count-pooled pollen and 0.8021 for the equal-source pollen mean. The fixed forward profiles produce 0.6399–0.6699. On this closed two-taxon panel, mean per-taxon absolute error is half the L1 error: about **32.0–33.5 percentage points**. The nominal wind-3 profile gives 33.0 percentage points. These are modest development differences alongside substantial prediction error. No profile is chosen from these outcomes.

The table reports every profile on the same 21 scored windows. Negative differences mean lower error than the matched baseline; the two grouping rules give the same numerical table. Means give each target window equal weight, not each pollen count.

| Declared profile | Mean L1 error | Mean per-taxon error (percentage points) | L1 difference from pooled | L1 difference from equal-source | Lower/higher than pooled | Lower/higher than equal-source |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| double_metadata_radius_wind_3 | 0.65424061 | 32.712 | -0.06384402 | -0.14789016 | 18/3 | 12/9 |
| half_metadata_radius_wind_3 | 0.66514054 | 33.257 | -0.05294409 | -0.13699022 | 18/3 | 12/9 |
| metadata_radius_wind_2 | 0.63992912 | 31.996 | -0.07815551 | -0.16220165 | 18/3 | 12/9 |
| metadata_radius_wind_3 | 0.66002499 | 33.001 | -0.05805964 | -0.14210578 | 18/3 | 12/9 |
| metadata_radius_wind_4 | 0.66988181 | 33.494 | -0.04820282 | -0.13224896 | 18/3 | 12/9 |

The forward model has higher L1 error than the pooled baseline in three of the 21 windows and higher error than the equal-source mean in nine. The saved summary also retains all matched squared-error and multinomial negative-log-likelihood differences. All 1,890 saved score values were independently checked using Decimal50 composition arithmetic and an exact-integer binomial-coefficient route; maximum absolute discrepancy was 1.1833×10⁻¹¹ under 2×10⁻⁹ absolute plus 2×10⁻¹⁰ relative tolerance. Each actual prediction additionally passed a separate Decimal count/K then target-K equation route. Those checks establish implementation arithmetic on these inputs.

The regional consumer first pools **unclosed** inverse terms across allowed training sources: Wᵢ = Σₛ nₛᵢ/(Kₛᵢ pᵢ), where nₛᵢ is that source's pooled literal taxon count in the fixed window and Kₛᵢ its declared deposition response. Each source has coefficient one in this sum; its count total therefore affects its contribution. It closes only this pooled vector, cᵢ = Wᵢ/ΣⱼWⱼ, rather than averaging separately closed per-core cover vectors. The target prediction then closes Kₜᵢ pᵢ cᵢ. Cancelling the common closure and shared positive PPE gives qₜᵢ = Kₜᵢ Σₛ(nₛᵢ/Kₛᵢ) / Σⱼ[Kₜⱼ Σₛ(nₛⱼ/Kₛⱼ)]. PPE remains in the intermediate conditional cover cᵢ but cancels from the final pollen prediction under this particular pooling rule. Equal training and target responses reduce that prediction to count-pooled pollen. An average of individually closed source covers would have a different, potentially PPE-dependent equation. These comparisons cannot identify PPE. Training and prediction use the frozen source exclusions, exact named chronologies, fixed point-age windows, literal two-taxon counts and representative source-location/static-circle assumptions. Native unit IDs authenticate deduplication; they do not prove environmental independence.

The targets were already exposed during source work. This remains development evidence without untouched confirmation, independent vegetation accuracy, empirical interval coverage, historical LandClim reproduction or validation of basin/chronology/PPE transfer assumptions. Chronology intervals and uncertain basin geometry are not fitted or scored here. The retained negative outcomes remain part of the scientific result.

The compact writer authenticates the complete original external prediction,
score, preflight, protocol, terminal and independent-review records. It retains
all 4,750 attempt identities/statuses and every scored fold/profile/baseline
comparison, including worse results. The original count-bearing ledgers remain
external; public products contain no raw target taxon-count vectors or native
samples. Source qualification establishes identity rather than permission or
new scientific acceptance.

`report.json` records the complete compact ledger, paired losses and macro
comparisons; `source-proof.json` records the source/producer identities.
The writer performs no new physical integration, R run, prediction or scoring.
A saved-result aggregation is distinct from the original scientific execution.
No configured-owner or installed-product qualification is inferred from that
original execution.

To aggregate an explicitly provisioned immutable external snapshot:

```sh
python -m bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_grouped_forward \
  --repository . \
  --source-root /path/to/qualified-source-store \
  --output artifacts/jobs/swedish-grouped-forward-account
```


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-bound conditional reconstruction or exposed pollen development wrapper; own source assumptions and exact scored/refused populations must be preserved alongside account links.

**Supported claim.** Five fixed physical profiles and two source-publication grouping rules predict a literal Betula/Poaceae pollen response on identical matched support. Complete attempt statuses and all poorer physical contrasts remain part of an exposed development comparison.

**Unsupported claim.** Independent 210-observation evidence, identified PPE, independent vegetation accuracy, calibrated interval coverage, historical LandClim reproduction, untouched confirmation or validated basin/chronology/parameter transfer.

**Actual verification performed.** Two actual ordinary maintained source-account publishers returned zero. All reported scores, attempt/refusal counts and captured source values remain byte-exact; only three current writer-module SHA strings changed in the source proof, matching physical producer.py, sources.py and summary.py. Old tracked-byte checkers refused that metadata change. Original independent review of 1,890 score values and count/K then target-K routes retains its own scope. No fresh fit, physical integration, prediction, scoring or untouched evaluation was run.

**Remaining input or review.** Only 21 distinct target windows from 3 native units are scored, all in declared grid 779. Most declared attempts lack 2 permitted dependency groups, source chronologies/geometry are fixed, targets were already exposed and native deduplication is not empirical independence. Shared PPE cancels from final pollen prediction under this pooling rule.

**Cause category.** data | assumption | comparability | access/rights | qualified review

**Consequence.** Keep large absolute errors and coverage refusal visible alongside modest relative improvements. Repeated profiles/grouping rules do not create independent outcomes, and lower pollen error cannot identify PPE or validate vegetation.

**Precise next acceptance route.** Qualify additional independent source groups, full taxon/age/geometry support and source-use scope; freeze new profile/model selection before unexposed outcomes. Supply an explicit predictive uncertainty model and independent matched vegetation before coverage or ecological accuracy claims.

**Negative or refused result.** Across both rules 4,480 support refusals and 60 unavailable target outcomes remain. Every profile is poorer than pooled pollen in 3/21 windows and equal-source pollen in 9/21. Fixed-profile mean per-taxon error remains about 32.0–33.5 percentage points; no profile is selected. Missing-publication/alternate-unit diagnostic cause counts overlap.

**Matched denominator.** 4,750 total attempts;270 predictions;210 scored records =21 distinct windows ×5 profiles ×2 grouping rules;60 predicted records lack target panels. Unique paired literal-panel counts 37,300. Each grouping rule has 2,375 attempts,135 predictions,105 scores,30 target absences and 2,240 support refusals; they yield identical captured ledgers on these inputs.

Qualified authored reader SHA-256: `23398a214715e620c8d0eb780c1939b5d4de0acde49ec69fb525f01e01a776b1`.

- [Retained qualification evidence: docs/report/pollen-reconstruction/swedish-grouped-forward-development/report.json](report.json) (SHA-256 `a87afba1ba06736efdc8d7f1d9b8212acf6aaaa634c9a56435f2889e081c6439`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/swedish-grouped-forward-development/source-proof.json](source-proof.json) (SHA-256 `b2ff8e0b3f8d27e8abedb644b338e6238a8534bdad220270c2808e5d7f527559`).

- [Canonical scientific account: reports/science/pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/pollen-prediction.md) (source SHA-256 `2f61fcbbf6fb36a075790199e81d834dbf8225e426aa7d92dc1ba4cbfb19f1f0`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
