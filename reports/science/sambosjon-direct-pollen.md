# What a newly evaluated Swedish lake showed for observed-pollen prediction

We evaluated the fixed 16-label observed-pollen predictors at [Lake
Sämbosjön](../../docs/report/regions/nordic/sambosjon-direct-pollen/README.md),
a Swedish Neotoma/EPD physical site absent from the earlier Swedish and Nordic
target studies. The entire site and its core were excluded from 84 training
physical sites. We froze 66 predictions for 22 age bins before target scoring.
No bin was refused or failed.

The primary fixed inverse-distance-squared predictor had equal-bin pollen
fraction MAE **0.022991** and Hellinger distance **0.184176**. The fixed
nearest-site comparator had MAE 0.026202, and the training mean had 0.037466,
on the same 22 bins. These are descriptive results for one site, not evidence
of a general method ranking across Sweden. The 16 exact source labels account
for 224,291 of 393,822 native pollen NISP counts (56.95%); these scores
describe that closed subcomposition, not all pollen or vegetation.

Sämbosjön contributes 111 distinct core samples. Each has a source-default
comparable calibrated age from the Neotoma MADCAP chronology; temporal bins
did not propagate its age uncertainty. Our separate
[source age-bound screen](../../docs/report/regions/nordic/sambosjon-direct-pollen/age-bounds/README.md)
finds that 58 of 111 reported sample intervals cross a nominal 500-year bin
boundary; every scored bin contains at least one crossing sample. The source
does not state a confidence level for these bounds or provide a joint age
posterior. Our [contained-age sensitivity](../../docs/report/regions/nordic/sambosjon-direct-pollen/interval-support/README.md)
keeps 53 samples in 21 bins. Primary MAE is **0.023054**, compared with
**0.022881** for the original counts on those same bins; Hellinger distance
is 0.185741 versus 0.183698. Bin 1 has no contained sample and retains null
refused scores. The 185,150 retained native counts include 108,163 counts on
the closed axis. This is a marginal-bound sensitivity using unchanged frozen
predictions, rather than an age posterior or confidence interval. A nearby
LandClim `SAM` point is
3.316459 km away and remains an explicitly refused identity join. The source
names Gunnar Digerfeldt and a 1982 primary report; the Neotoma dataset DOI is
[`10.21233/53ys-nt12`](https://doi.org/10.21233/53ys-nt12). Neotoma's
[data policy](https://www.neotomadb.org/data/data-use-and-embargo-policy)
governs reuse and attribution.

The site is newly scored, with prior aggregate count-mass and positive-bin
exposure disclosed in the [protocol and governed evidence](../../docs/report/regions/nordic/sambosjon-direct-pollen/README.md).
The shared source screen parsed target rows during preparation but discarded
them before predictor inputs. Aggregate scores were inspected after a
pre-score prediction freeze and before a later annotation correction; fixed
prediction bytes did not change. This is descriptive development evidence,
not independent confirmation. One site supplies no between-site uncertainty
estimate. The result does not admit LRA reconstruction or validate predictions
against measured vegetation.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Frozen 16-label direct-pollen result for one Swedish core and completed interval-contained sensitivity are reported.

**Unsupported claim.** Untouched general Swedish skill or age-posterior/vegetation accuracy.

**Actual verification performed.** Retained frozen 66 predictions, point-age scoring, age-bound and completed contained-age rescoring receipts are cited; index did not rerun.

**Remaining input or review.** One-site 16-label pollen score uses nominal ages; 58/111 intervals cross a bin, bound confidence and joint posterior are unknown, and prior source exposure prevents untouched confirmation. Resolver: Core chronology custodian and independent cohort/vegetation reviewer Reopen when: Selected joint chronology and a new cohort or measured-cover pair are qualified before stronger temporal/ecological claims.

**Cause category.** assumption|comparability|qualified review

**Consequence.** Keep 0.022991 IDW point-bin MAE, 0.023054 contained-bin MAE and 0.022881 original-count matched-bin MAE in their distinct supports.

**Precise next acceptance route.** If a source-qualified joint age posterior becomes available, rerun age-aware scoring against the unchanged prediction freeze and preserve the 22-bin nominal and 21-bin contained baselines; require a fresh qualified cohort or measured cover separately before broader skill or ecology claims.

**Negative or refused result.** One of 22 nominal bins lacks contained-age support; 58/111 source age intervals cross nominal bin edges; zero LRA admission.

**Matched denominator.** One site, 111 samples, 22/22 nominal point-age bins; 224,291/393,822 native NISP on 16 labels; 53/111 samples in 21/22 contained-age bins, 21 scored and one refused.

Retained evidence: [docs/report/regions/nordic/sambosjon-direct-pollen/age-bounds/README.md](../../docs/report/regions/nordic/sambosjon-direct-pollen/age-bounds/README.md), [docs/report/regions/nordic/sambosjon-direct-pollen/interval-support/README.md](../../docs/report/regions/nordic/sambosjon-direct-pollen/interval-support/README.md).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-claim-semantic-sha256: e4c9e4f0b1e68ec9cf404b599bfdb55f0d715537644395baa672f0387eed2f0a -->
<!-- scientific-authored-source-sha256: d606179c2a6d67c91aa7355c814873306175a9fc25c280a32def53325a1ebe4e -->
<!-- scientific-verification-and-limits:end -->
