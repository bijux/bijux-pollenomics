# What changes when we shift age support or remove nearby training sites?

We tested how three fixed observed-pollen predictors respond when their training
pollen comes from an adjacent 500-year source bin or from a restricted spatial
neighborhood. We used the same three Swedish whole-site targets and closed
31-author-taxon composition as our [training-scope study](sweden-training-scope.md).
Each target physical site remained absent from all predictor inputs. We used
the **four-country training scope** throughout this sensitivity run: the other
two Swedish sites plus 81 Denmark, Finland and Norway sites. This is a
previously exposed development cohort, not an independent confirmation.

## What we chose before scoring this run

The [prepared receipt](../../docs/report/regions/nordic/swedish-support-sensitivity/prepared/prepare.json)
binds the three existing target-excluded predictor folds and sealed Swedish
outcome identity. For each target bin, we asked for pollen from the same
source bin, the adjacent **younger** bin (`shift_bins=-1`) or the adjacent
**older** bin (`shift_bins=+1`). A bin shift is nominally 500 calibrated years
BP. We did not move the target observation or infer an age-model posterior;
different cores can have different chronology uncertainty.

At each age support, we tried all eligible source sites, the nearest five
eligible physical sites, and sites whose centers are at least 100 km from the
target center. The five-site cap probes concentration of nearby observations;
it is not a density correction. The 100 km rule probes a more distant source
set using site centers, not historical basin edges. Each policy requires two
positive-count training groups. We retained every refusal, with no nearest-bin
fallback. Training mean, nearest site and inverse-distance-squared use the
same closed target axis and fixed method definitions.

We wrote [1,419 method predictions](../../docs/report/regions/nordic/swedish-support-sensitivity/frozen/freeze.json)
across 473 supported site-bin/policy queries before opening the target counts.
The freeze SHA-256 is
`db5bd39b7e9630b48def3ea5082ad1d93358e1e2de75c297b75933584c8a08ed`.
There were 486 attempted queries and **13 refusals** for too few eligible
groups. The [coverage table](../../docs/report/regions/nordic/swedish-support-sensitivity/coverage.csv)
retains every site, shift and spatial policy; [scores](../../docs/report/regions/nordic/swedish-support-sensitivity/scores.csv)
and [paired rows](../../docs/report/regions/nordic/swedish-support-sensitivity/paired-scores.csv)
retain the scored denominator and nearest source distance.

## What we found on matched bins

The table compares inverse-distance-squared pollen MAE with the unshifted,
all-site reference **on the exact bins shared by each comparison**. We first
average bins within each site, then the three sites equally. Smaller MAE is
better; values are fractions of the closed 31-taxon composition.

| Source age and site rule | Shared bins | Reference MAE | Sensitivity MAE | Difference |
| --- | ---: | ---: | ---: | ---: |
| Adjacent younger bin, all sites | 51 | 0.022824 | 0.023812 | +0.000988 |
| Adjacent older bin, all sites | 54 | 0.023647 | 0.023743 | +0.000096 |
| Same bin, nearest five sites | 54 | 0.023647 | 0.023695 | +0.000048 |
| Same bin, sites at least 100 km away | 52 | 0.023151 | 0.029171 | +0.006020 |

The unshifted all-site result exactly reproduces all 162 method-score rows of
the previous four-country Swedish scope. We checked this row by row, including
Hellinger distance. The 100 km rule removes the near Swedish training site
for Bussjösjön and Bökesjön; it does not change Abborrtjärnen's same-bin IDW
prediction. On its 52 paired bins, both southern sites have higher mean error
under the distance exclusion (about +0.008372 and +0.009688), while the
three-site mean rises by +0.006020. The younger/older and five-site effects
are smaller and change sign between sites. Weighting bins by their target
sample counts changes the aggregate magnitude: on the same 52 paired bins,
the 100 km rule raises IDW MAE from 0.021666 to 0.025977; on 54 same-bin
pairs, the nearest-five cap changes it from 0.022012 to 0.022535. Sample
weights describe this retained sampling density, not independent replication.
The [machine report](../../docs/report/regions/nordic/swedish-support-sensitivity/report.json)
retains each policy's coverage, equal-site and sample-weighted scores,
matched macro scores and nearest-distance strata; unmatched policy means
are not paired effects.

We infer only that this **specific** observed-pollen development cohort is
sensitive to removing a nearby Swedish training site. Three correlated,
previously explored lakes do not quantify population spatial skill, country
effects or chronology uncertainty. A 500-year source-bin shift is a nominal
support probe; it is not a validated prediction at an independently dated
future or past time. We did not reconstruct LRA vegetation or compare against
measured vegetation.

## How we reproduced it

The producer is
`bijux_pollenomics_dev.source_completion.swedish_support_sensitivity`. It reads
the retained target-excluded four-country fold files and writes new outputs
under absent `artifacts/` destinations. From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_support_sensitivity prepare \
  --repository . --output artifacts/jobs/swedish-support-inputs-replay
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_support_sensitivity predict \
  --repository . --prepared artifacts/jobs/swedish-support-inputs-replay \
  --output artifacts/jobs/swedish-support-predictions-replay
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_support_sensitivity score \
  --repository . --prepared artifacts/jobs/swedish-support-inputs-replay \
  --frozen artifacts/jobs/swedish-support-predictions-replay \
  --freeze-sha256 db5bd39b7e9630b48def3ea5082ad1d93358e1e2de75c297b75933584c8a08ed \
  --output artifacts/jobs/swedish-support-scores-replay
```

The literal freeze digest applies to the retained inputs and producer. If
they change, inspect and retain the new predictions before scoring. Compare
replayed result bytes to the governed files cited above. We still need
source-qualified age-model ensembles, independent spatial groups and real
Nordic LRA inputs before making stronger temporal or ecological claims.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Frozen adjacent-bin and distance-support pollen comparisons are scored on matched bins.

**Unsupported claim.** Independent temporal or spatial skill and historical basin-radius calibration.

**Actual verification performed.** Retained prepare, freeze, coverage and paired-score receipts are cited; index did not rerun.

**Remaining input or review.** Adjacent-bin and 100-km center rules are nominal probes on three exposed correlated sites; age uncertainty, historical basin distances and independent time/spatial generalization are untested. Resolver: Core chronology/basin source owner and independent spatial-temporal reviewer Reopen when: Joint age support and new grouped spatial/temporal targets are source-qualified before predeclared prediction.

**Cause category.** assumption|comparability|qualified review

**Consequence.** Keep +0.006020 IDW MAE change as this cohort’s support sensitivity, not causal distance law.

**Precise next acceptance route.** Joint age support and new grouped spatial/temporal targets are source-qualified before predeclared prediction. Then update reports/science/pollen-prediction.md.

**Negative or refused result.** 13 of 486 site-bin/policy queries refused for insufficient groups.

**Matched denominator.** Three exposed sites; 473/486 supported queries, 1,419 method predictions; 52 matched bins for 100-km exclusion.

Retained evidence: [docs/report/regions/nordic/swedish-support-sensitivity/report.json](../../docs/report/regions/nordic/swedish-support-sensitivity/report.json), [docs/report/regions/nordic/swedish-support-sensitivity/coverage.csv](../../docs/report/regions/nordic/swedish-support-sensitivity/coverage.csv).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-claim-semantic-sha256: cc0b4bb6be6cca6c6c9718579312c5bc97a97969b580243d47ecafb6e15f8b8c -->
<!-- scientific-authored-source-sha256: 8f6dccebd81af82bfedea3e9ae3ddaea75a3999a59bfd1119046d947c43980de -->
<!-- scientific-verification-and-limits:end -->
