# What the current pollen prediction studies show

We report prior-exposed development results on observed pollen and English
LRA forward pollen. We keep them separate from independent vegetation
accuracy and a complete Nordic LRA reconstruction.

## Four Nordic countries on the author taxon axis

In our [four-country study](nordic-pollen-study.md), we excluded Denmark,
Finland, Norway or Sweden from its corresponding training set. We retained
source counts, exclusions, predictions before outcome access, scores and
country-specific support. We scored a closed 31-author-target pollen
subcomposition. We do not compare its error numerically with the separate
16-literal-label result because the denominators differ. Denmark has one
captured target site, and we refused 94 Norwegian bins without eligible
training support. We report observed-pollen transfer, not a vegetation
estimate or confirmatory country skill: we had inspected outer outcomes
before this design.

## Swedish training scope on matched targets

In our [Swedish training-scope comparison](sweden-training-scope.md), we
asked whether adding 81 DK/FI/NO sites to two Swedish training sites changed
prediction at the third Swedish site. We retained 117 paired score rows for
three fixed methods on 39 bins shared by both scopes. Inverse-distance-squared equal-site pollen MAE is
0.032846 with Sweden-only training and 0.023226 with four-country training.
Sweden-only training refused 15 of 54 candidate bins; four-country training
predicted all 54. Most of the mean IDW advantage comes from Abborrtjärnen;
we have only three previously exposed Swedish sites. We compare observed
pollen here, not LRA-derived vegetation or independent ecological truth. We
do not infer population-level spatial generalization from this study.

We then used the same four-country source-excluded folds for an
[age and distance sensitivity](sweden-spatiotemporal-sensitivity.md). Shifting
the training source by one nominal 500-year bin, capping its nearest sites at
five, and excluding source centers within 100 km yields 486 attempted
site-bin/policy queries, 473 predictions and 13 refusals. On 52 bins paired
to the unshifted all-site reference, the 100-km exclusion raises IDW equal-site
MAE from 0.023151 to 0.029171; the shift and nearest-five effects are smaller
and differ between sites. We report a three-site development sensitivity,
not an age-model uncertainty estimate or independent spatial validation.

## A newly evaluated Swedish physical site on the literal-label axis

We applied three fixed predictors to [Lake Sämbosjön](sambosjon-direct-pollen.md),
which was absent from the earlier target studies. All 22 candidate bins were
predicted and scored; inverse-distance-squared equal-bin MAE was 0.022991.
The 16 exact source labels contain 224,291 of 393,822 native pollen counts.
This closed response differs from the 31-author-target studies above, so we do
not compare their error magnitudes. Aggregate target count support was screened
before prediction, and aggregate scores were inspected before a later protocol
annotation correction; the frozen prediction bytes and fixed methods did not
change. This is one-site descriptive development evidence, not independent
confirmation, an LRA reconstruction or a vegetation score. A separate
[source age-bound screen](sambosjon-direct-pollen.md) finds 58 of 111 selected
sample intervals crossing a nominal bin boundary, with at least one crossing
in every scored bin. It does not reassign pollen or estimate a new score.

We separately froze and scored [Lilla Gloppsjön](lilla-gloppsjon-direct-pollen.md),
another physical site excluded from the 84-site training set. All 23 bins
produced three fixed scores. The prespecified inverse-distance-squared
method's equal-bin MAE is 0.017295, while training mean has lower MAE
(0.016272) and nearest site has lower Hellinger distance (0.228724 versus
0.237576). Its 16 literal labels cover 55,638 of 127,027 native pollen
counts; two source samples are refused from calibrated-age bins. A prior
source-validation screen parsed the target partition, so the result is
descriptive development, not untouched independent confirmation. We keep
the two lakes separate because site histories and age support differ.

## Matched English direct pollen and LRA forward pollen

In our [constrained LOVE source study](english-lra-pollen-prediction.md), we
used 15 English author examples in one 1250–1750 BP window. We excluded
`Filipendula` from the declared 30-taxon composition because its published
fall speed lies outside the selected optimized transport contract. We kept
target pollen out of whole-site training reconstructions and regional inputs.
Fourteen folds published predictions; we refused BECKHAM because three
training LOVE fits did not converge. We paired the 42 scored site-method
rows with fixed direct observed-pollen baselines on the exact target support.

| Method | Direct pollen MAE | LRA forward pollen MAE | Direct Hellinger | LRA Hellinger |
| --- | ---: | ---: | ---: | ---: |
| Training mean | 0.020496 | 0.026273 | 0.282082 | 0.360671 |
| Nearest site | 0.019552 | 0.021132 | 0.255767 | 0.286001 |
| Inverse-distance-squared | 0.018579 | 0.021088 | 0.243673 | 0.285415 |

We calculated MAE as mean absolute fraction error over 30 named taxa,
averaged equally across 14 scored sites. We calculated Hellinger as the
site-macro distance between closed compositions; smaller values favor the
prediction. Our
[Hellinger source rows](../../docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/paired-hellinger.json),
[paired MAE rows](../../docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/matched-scores.csv)
and [site sensitivity](../../docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/site-sensitivity.json)
retain all methods and source identities. Direct prediction used all 14
training pollen sites; LRA used one regional anchor and 13 local
reconstruction predictors. Their training information therefore differs.
We froze both prediction sets before scoring target outcomes.

We also varied each English target lake's assumed radius by 20% in the
actual LRA forward consumer while keeping reconstructed vegetation fixed.
Our [radius sensitivity](english-lra-pollen-prediction.md#basin-radius-in-the-forward-consumer)
replayed all 42 original pollen fractions exactly and scored 126 projections.
For inverse-distance-squared vegetation, site-macro pollen MAE is 0.021032,
0.021088 and 0.021457 at 80%, 100% and 120% of the assumed radius. We use
this as a forward-transport diagnostic, not a calibrated radius or Swedish
LRA admission.

We observed lower mean pollen error for the fixed direct methods on this
matched English development support. We do not infer that LRA is ecologically
inferior, that its vegetation reconstruction is inaccurate, or which method
would win on new Nordic sites. We scored no independent vegetation observation.

In our [Hellinger site-influence calculation](../../docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/paired-hellinger-sensitivity.json),
we omitted each scored site in turn. The mean direct-minus-LRA Hellinger difference
stays below zero for every omission and all three methods. The nearest-site
method favors direct at only seven of 14 individual sites, however, so the
mean direction is not unanimous site behavior. We do not derive a sampling
interval or independent spatial confirmation from these correlated,
previously explored sites.

## Model use and open inputs

In our [bounded development search](nordic-pollen-study.md), we selected a
CLR/WGS84 RBF-ridge candidate on one prior-exposed author comparison. It
lowered common-support MAE relative to inverse-distance-squared but covered
fewer predictions. We limit that selection to its declared search, response,
metric and cohort. We held published PPE and fall speeds fixed in the English
LRA run; its constrained SLSQP LOVE backend had three training
nonconvergences even under a higher-budget check. Neither result identifies
universal LRA parameters. We list unresolved Swedish/Nordic basin geometry,
selected chronology, PPE/taxon denominator, independent vegetation pairs and
HYDE semantics in our research-needs register.


## Development evaluator split and target isolation

Our [constructed development intake witness](../../docs/report/synthetic-validation/site-leakage/development-input-isolation.json)
checks five direct experiment APIs: split files are flushed before reconstruction,
verified cached-result consumption and spatial fitting, and checked again before
publication. A known nine-record graph forms four site/core/publication/alias
and derived-product groups; missing derived ownership is refused.

For one withheld constructed target, changing valid raw pollen counts from
`[600,400]` to `[100,900]` and changing the separately scored synthetic cover
labels preserves all three baseline and both fitted-family training/prediction
fingerprints. Its training-mean pollen MAE changes from `0.002610865` to
`0.502610865`; fitted CLR/WGS84 RBF-ridge changes from `0.002610715` to
`0.502610715`. The altered record becomes training data in three other folds,
where negative-composition refusals remain explicit: baseline predictions
12→3 of 12 and fitted predictions 8→2 of 8, with 30 failed-prediction score rows.
The separate source account retains all actual metrics, 16 exact reconstruction
cache hits, five spatial fits, failed whole-job receipts and independent checks.

The verification-only consumer passes 57 focused guards and 676 independent
checks, including 50 Decimal50 MAE comparisons within `8.5e-17`. This is an
inspected constructed software contract, with no measured vegetation reference,
qualified real-source alias graph or untouched confirmation. It does not change
the source/population limits of the empirical development studies above.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Aggregate development account separates 31-author, 16-literal and English forward-pollen scores. Separately, five development experiment entry points persist and guard split custody before fitting; an explicit nine-record/four-group constructed graph and held-out input perturbation preserve fitted target inputs and predictions.

**Unsupported claim.** General model ranking, Nordic vegetation accuracy or untouched confirmation.

**Actual verification performed.** Retained country, Swedish site and English fold receipts are synthesized; index did not rerun studies. A distinct source-bound development-input isolation consumer completed with native exit 0, 57 focused guards and 676 independent checks, including 50 Decimal score checks; retained failures and zero new basin inversions are explicit.

**Remaining input or review.** Observed-pollen and English LRA-forward scores are development results on different axes and exposed sites; no admitted Nordic LRA core or independent measured-cover pair supports vegetation accuracy. Resolver: Independent cohort and vegetation-reference owners with qualified science reviewer Reopen when: A fresh grouped cohort and source-qualified same-estimand vegetation pair are frozen, predicted and scored.

**Cause category.** data|comparability|qualified review

**Consequence.** Do not average unlike score axes or convert a failed fit into zero accuracy.

**Precise next acceptance route.** A fresh grouped cohort and source-qualified same-estimand vegetation pair are frozen, predicted and scored. Then update reports/science/model-use.md.

**Negative or refused result.** 94 NO country bins, 15 Sweden-only bins and one English outer fold refused in their respective studies; no measured vegetation score. In the separate constructed perturbation, three other folds legitimately refuse because the perturbed record enters training; three alternative-dataset folds refuse and perform no inversion.

**Matched denominator.** Separate 31-, 16- and 30-target axes; English 14 paired target sites after one refusal; country/lake denominators remain separate. Distinct constructed intake population: nine identity records/four groups; reference predictions 12 to 3 and fitted predictions 8 to 2 after target-source perturbation; 80 score rows comprise 50 scored and 30 prediction_failed, five unchanged target method predictions, 16 retained request hits and five spatial fits.

Retained evidence: [reports/science/nordic-observed-pollen-transfer.md](nordic-observed-pollen-transfer.md), [reports/science/english-lra-pollen-prediction.md](english-lra-pollen-prediction.md), [docs/report/synthetic-validation/site-leakage/development-input-isolation.json](../../docs/report/synthetic-validation/site-leakage/development-input-isolation.json), [docs/report/synthetic-validation/site-leakage/development-input-isolation-source-account.json](../../docs/report/synthetic-validation/site-leakage/development-input-isolation-source-account.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
