# What the current pollen prediction studies show

We report prior-exposed development results on observed pollen, English LRA
forward pollen and conditional physical-forward studies at Swedish and Danish
targets. We keep these distinct from independent vegetation accuracy
and a source-complete Nordic LRA reconstruction.

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

## Retained buffered results and historical replay

The retained [buffered author-pollen results](../../docs/report/pollen-reconstruction/author-buffered-pollen/README.md)
remain checked against their frozen outputs, ten exact numerical/replay sources
and two authenticated historical reader-code witnesses. Current account routes,
all nine scientific fields and their structured evidence are checked separately.
This readback does not admit a new execution of the historical model. The full
producer requires all twelve declared source hashes to match the current
software and refuses the changed reader implementations. Its recorded source
revision remains historical; its execution ancestry has not been reconstructed.
No model or original R rerun forms part of this readback.

## Matched conditional physical forwarding at Swedish targets

Our [matched physical-forward comparison](pollen-reconstruction/matched-pollen-forward/README.md)
asks a different, explicitly conditional question from the 31-author, 16-label
and English studies. It uses saved counts and transport factors from eight
cores at seven physical places, with four Swedish target cores and 77 literal
source windows. Swedish-only and pooled eligible Nordic training give 154
contexts; physical inverse-to-forward and direct panel-mean prediction give
308 family outcomes, of which 200 scored and 108 refused for lack of an
eligible source. Both families use the same whole-target-place exclusion,
explicit taxon panel, exact window, positive projected counts and PPE-transfer
eligibility. No new kernel, fit, optimizer or R calculation was run.

The physical family averages training-source conditional cover equally by
physical place, then forwards it through the target's saved K and PPE on one
homogeneous annulus with zero separate background. The baseline averages
count-panel fractions on the same sources. BOKE is explicitly projected from
Betula/Fraxinus/Ulmus onto Betula/Ulmus; the other scored panels also have two
taxa. A missing taxon is refused, not assigned zero. These two-taxon MAE and
TV fractions cannot be compared with the broader axes above.

Only 26 windows at BOKE and BUS, 13 each, score both families in both scopes.
Windows receive equal weight within target, then the two physical targets
receive equal weight. The full-precision values and every refusal remain in
the [saved report](pollen-reconstruction/matched-pollen-forward/report.json).

| Training scope | Family | BOKE MAE / TV | BUS MAE / TV | Two-target mean |
| --- | --- | ---: | ---: | ---: |
| Swedish-only | Direct panel mean | 0.149995 | 0.149995 | 0.149995 |
| Swedish-only | Physical forward | 0.149644 | 0.149967 | 0.149805 |
| Pooled eligible Nordic | Direct panel mean | 0.087016 | 0.154539 | 0.120778 |
| Pooled eligible Nordic | Physical forward | 0.061348 | 0.154732 | 0.108040 |

The pooled physical mean is lower, but BUS is poorer than its direct baseline
and its Swedish-only physical result. The only additional source on the joint
matched support is Danish SOLSOE83 in 12 pooled contexts; SOLSOE81 and SOLSOE83
remain one place. Finnish and Norwegian cores exist in the pool and contribute
to other Swedish contexts, but their axes are ineligible for this jointly
matched Betula/Ulmus comparison. No Danish, Finnish or Norwegian target was
scored by this consumer.

The independent 50-digit Decimal check matched 1,424 values within the frozen
1e-12 absolute tolerance, with maximum residual
1.9653480873864026090362878350698437E-16. This checks conditional point algebra,
not field truth or uncertainty. Input counts were parsed before prediction;
the complete prediction freeze precedes scoring, not prior outcome exposure.
Historical basin/source admission, independent vegetation and calibrated
uncertainty remain separate. Neither a four-country accuracy result nor an
untouched model ranking follows.

## Three-place physical predictions and a fixed regional background

The [spatial-field study](pollen-reconstruction/spatial-field-forward/README.md)
matches direct pollen IDW, homogeneous centre-cover forwarding and spatial
cover-field forwarding at BOKE, BUS and SOLSOE83. Each family uses the same
two training places in six fixed windows: 18 held-place/window contexts and
54 scored outcomes, with no refused context. The Betula/Ulmus response is
projected from each source's admitted panel; it is not a verified whole
terrestrial pollen denominator. Equal-place MAE/TV is 0.220493174 for direct
pollen, 0.205958107 for centre-cover and 0.204875686 for spatial forwarding.
The original eight-ring diagnostics leave the centre-versus-spatial
difference numerically unresolved.

A separate 128-ring refinement treats all 768 returned positive binary64
masses as exact conditional constants. Its complementary-coefficient and
score certificates give spatial equal-place MAE/TV in approximately
[0.204811632, 0.204937641] and centre-minus-spatial in
[0.001020466, 0.001146475]. This separates the aggregate scores within that
finite-mass model. Spatial forwarding is still poorer than centre forwarding
at BUS and SOLSOE83; BOKE supplies the aggregate improvement. The exact sum
of the refined masses is distinct from the old saved total. These bounds
do not certify quadrature error or the underlying continuous integrals, and
do not resolve the original diagnostic in its own context.

The [fixed-KRAG study](pollen-reconstruction/krageholm-regional-coupled/README.md)
asks a different conditional question. KRAGMJNY remains regional-only while
each of BOKE, BUS and SOLSOE83 is withheld in turn, leaving two local training
places. All 18 folds and 54 method dispositions remain present. Only
2700–3200 cal BP supports the nine scored outcomes; all 45 method slots in
the five older windows refuse because at least one required local analytical
LOVE composition lies outside the nonnegative closed domain. Signed outputs
remain visible, without clipping or a single-predictor fallback. On the three
scored targets, training-mean, nearest-site and inverse-square MAE/TV are
0.062165, 0.096838 and 0.082295. These one-window errors cannot be ranked
against the six-window spatial-field errors. Compared with the earlier
small-proxy regional study, both regional input and local predictor information
change; the result does not isolate a basin-size effect.

The separate [actual continuous-receiver calculation](pollen-reconstruction/spatial-field-forward/README.md#actual-continuous-study-complete-coverage-unresolved-precision)
retains all six place/taxon cases and their complete integration domains.
It fixes the saved radii and projected anchors with a newly captured native
survival coefficient; it does not authenticate historical floating arithmetic.
Within the unchanged 180-second, 768-MiB and 5-MB limits, neither producer nor
independent fixed-leaf replay meets any of the 18 K/B1/B2 full-width targets
of 1e-9. No usable positive lower bounds support normalized forecasts. The
producer exits zero with numerical refusal; the observer verifies accounting
but exits one for unresolved precision. This is a retained negative numerical
result, not a new forecast or a replacement for the finite-mass certificates.

These are previously exposed development studies with fixed geometry and
transport assumptions. Their independent arithmetic checks are conditional
on their declared kernels or continuous law. None scores measured vegetation,
propagates the full chronology/PPE/geometry uncertainty, or supplies untouched
confirmation or historical field acceptance.

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

**Supported claim.** Aggregate development account separates 31-author, 16-literal and English forward-pollen scores from the separate conditional two-taxon physical-forward comparison at Swedish targets. Separately, five development experiment entry points persist and guard split custody before fitting; an explicit nine-record/four-group constructed graph and held-out input perturbation preserve fitted target inputs and predictions. Additional synthesis retains the distinct three-place six-window spatial development comparison, conditional finite-mass envelope, fixed-KRAG one-window scored subset and actual continuous precision refusal.

**Unsupported claim.** General model ranking, Nordic vegetation accuracy or untouched confirmation.

**Actual verification performed.** Retained country, Swedish site and English fold receipts are synthesized; index did not rerun studies. A distinct source-bound development-input isolation consumer completed with native exit 0, 57 focused guards and 676 independent checks, including 50 Decimal score checks; retained failures and zero new basin inversions are explicit. The distinct conditional physical-forward producer completed at a890b5e433fd2679768b588bae2774aa3d382e17 with native/collector exit zero and all 6,668 pins unchanged. Its independent Decimal50 check matched 1,424 values at absolute tolerance 1e-12, maximum residual 1.9653480873864026090362878350698437E-16. These saved results are synthesized without repeating prediction or scoring. The existing spatial-field18contexts/54scores, finite-mass18contexts/54scores, fixedKRAG18folds/54slots (9scored/45refused) and actualcontinuous6case/18coefficient-width refusal are synthesized from their owning qualified accounts. No new prediction/scoring/model or integration ran for this synthesis; the report renderer and 27 local links pass.

**Remaining input or review.** Observed-pollen, English LRA-forward and conditional Swedish physical-forward scores are prior-exposed development results on different axes and supports. The conditional saved metadata geometry does not provide a source-complete historical Nordic reconstruction, independent measured-cover pair or calibrated uncertainty. Resolver: Independent cohort and vegetation-reference owners with qualified science reviewer Reopen when: A fresh grouped cohort and source-qualified same-estimand vegetation pair are frozen, predicted and scored.

**Cause category.** data|assumption|comparability|qualified review

**Consequence.** Do not average unlike score axes or convert a failed fit into zero accuracy.

**Precise next acceptance route.** A fresh grouped cohort and source-qualified same-estimand vegetation pair are frozen, predicted and scored. Then update reports/science/model-use.md.

**Negative or refused result.** 94 NO country bins, 15 Sweden-only bins and one English outer fold refused in their respective studies; no measured vegetation score. In the separate constructed perturbation, three other folds legitimately refuse because the perturbed record enters training; three alternative-dataset folds refuse and perform no inversion. The conditional physical-forward comparison retains 108 no-eligible-source family refusals; pooled BUS MAE/TV is poorer than direct (0.154732 versus 0.154539). Three-place original centre-versus-spatial comparison remains numerically unresolved; finite-mass separation is conditional and spatial remains poorer atBUS/SOLSOE83. FixedKRAG retains45negative/nonclosed-LOVE method refusals. Actualcontinuousproducer+independentobserver refuseall18widths despite verifiedaccounting.

**Matched denominator.** Separate 31-, 16- and 30-target axes; English 14 paired target sites after one refusal; country/lake denominators remain separate. Distinct constructed intake population: nine identity records/four groups; reference predictions 12 to 3 and fitted predictions 8 to 2 after target-source perturbation; 80 score rows comprise 50 scored and 30 prediction_failed, five unchanged target method predictions, 16 retained request hits and five spatial fits. Separate conditional physical-forward support: eight source cores/seven places, four Swedish targets/77 windows, 154 contexts/308 family outcomes, 200 scored/108 refused; only 26 jointly matched windows at BOKE/BUS, 13 each, enter the two-target comparison. All scored panels have two taxa. SOLSOE83 adds source support on 12 joint pooled contexts; no DK/FI/NO target score. Separate three-place spatial comparison:147native/59selectedsamples,18contexts/54scores. FixedKRAG:18folds/54slots,9scored in2700–3200BP and45refused acrossfiveolderwindows. Continuousnumerics:6geometryowners/18failedwidthtargets, no newforecast slots. These populations are not pooled.

Retained evidence: [reports/science/nordic-observed-pollen-transfer.md](nordic-observed-pollen-transfer.md), [reports/science/english-lra-pollen-prediction.md](english-lra-pollen-prediction.md), [docs/report/synthetic-validation/site-leakage/development-input-isolation.json](../../docs/report/synthetic-validation/site-leakage/development-input-isolation.json), [docs/report/synthetic-validation/site-leakage/development-input-isolation-source-account.json](../../docs/report/synthetic-validation/site-leakage/development-input-isolation-source-account.json), [reports/science/pollen-reconstruction/matched-pollen-forward/README.md](pollen-reconstruction/matched-pollen-forward/README.md), [reports/science/pollen-reconstruction/matched-pollen-forward/report.json](pollen-reconstruction/matched-pollen-forward/report.json), [reports/science/pollen-reconstruction/matched-pollen-forward/decimal-comparison.json](pollen-reconstruction/matched-pollen-forward/decimal-comparison.json), [reports/science/pollen-reconstruction/matched-pollen-forward/publication.json](pollen-reconstruction/matched-pollen-forward/publication.json), [reports/science/pollen-reconstruction/spatial-field-forward/README.md](pollen-reconstruction/spatial-field-forward/README.md), [reports/science/pollen-reconstruction/krageholm-regional-coupled/README.md](pollen-reconstruction/krageholm-regional-coupled/README.md).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
