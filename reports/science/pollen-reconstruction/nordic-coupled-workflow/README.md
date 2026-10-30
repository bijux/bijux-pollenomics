# Conditional Nordic coupled pollen predictions

This development experiment asks whether the maintained regional-to-local
reconstruction and forward-pollen workflow can produce source-driven
withheld-place predictions for three named places on the same two-taxon
panel. It keeps reconstruction, saved prediction reopening and pollen
scoring separate. It does not evaluate independent vegetation accuracy.

The source panel is **Betula/Ulmus** at Bökesjön (BOKE), Bussjösjön (BUS)
and Solsø 83 (SOLSOE83). BOKE's measured Fraxinus counts are explicitly
excluded from this panel and its denominator is reclosed; an excluded or
unmeasured taxon is not an observed zero. Six separate 500-year CalBP bins
span 2700–5700 CalBP. Repeated bins do not create additional physical sites.

## What was reconstructed and withheld

Each bin has three leave-one-place-out folds. The target place is excluded
from the regional anchor and local training reconstruction. One training
place supplies the declared regional proxy and the other supplies the local
reconstruction; the frozen priority rotates with the held-out place.
These are small-lake development proxies, not independently qualified
regional REVEALS observations. The published training tables retain the
native groups, source references, dependency closure and actual fold roles.

The declared static geometry uses separate inversion and forward supports,
two local rings and a 100 km regional extent. Bin stationarity, circular
geometry, transport settings and parameter transfer are conditional
assumptions in the [source protocol](../../../../docs/report/pollen-reconstruction/nordic-coupled-workflow/assumptions/protocol.json).
They are not source-supported historical basin reconstructions or calibrated
chronology uncertainty. The original source epochs remain in the native
tables and [publication map](publication.json).

Training mean, nearest site and inverse-distance-squared interpolation all
have one remaining local predictor in each fold. Their names therefore do
not represent three independent information sources or a meaningful search
over richer spatial models. The forward step retains the separate regional
background and the target's declared geometry.

## Complete prediction and refusal population

There are 18 requested place-bin folds and 54 method dispositions. The saved
prediction tables retain 30 predicted and 24 refused dispositions. A refusal
is neither a zero prediction nor a missing row. The linked failures preserve
their original reason codes and details; this account does not independently
certify their physical cause.

| CalBP bin | Predicted / refused method dispositions | Frozen scientific tables |
| --- | ---: | --- |
| 2700–3200 | 9 / 0 | [Training](cal-bp-2700-3200/training.json), [predictions](cal-bp-2700-3200/predictions.json), [failures](cal-bp-2700-3200/failures.json), [pollen scores](cal-bp-2700-3200/scores.json) |
| 3200–3700 | 3 / 6 | [Training](cal-bp-3200-3700/training.json), [predictions](cal-bp-3200-3700/predictions.json), [failures](cal-bp-3200-3700/failures.json), [pollen scores](cal-bp-3200-3700/scores.json) |
| 3700–4200 | 3 / 6 | [Training](cal-bp-3700-4200/training.json), [predictions](cal-bp-3700-4200/predictions.json), [failures](cal-bp-3700-4200/failures.json), [pollen scores](cal-bp-3700-4200/scores.json) |
| 4200–4700 | 3 / 6 | [Training](cal-bp-4200-4700/training.json), [predictions](cal-bp-4200-4700/predictions.json), [failures](cal-bp-4200-4700/failures.json), [pollen scores](cal-bp-4200-4700/scores.json) |
| 4700–5200 | 3 / 6 | [Training](cal-bp-4700-5200/training.json), [predictions](cal-bp-4700-5200/predictions.json), [failures](cal-bp-4700-5200/failures.json), [pollen scores](cal-bp-4700-5200/scores.json) |
| 5200–5700 | 9 / 0 | [Training](cal-bp-5200-5700/training.json), [predictions](cal-bp-5200-5700/predictions.json), [failures](cal-bp-5200-5700/failures.json), [pollen scores](cal-bp-5200-5700/scores.json) |

The [prediction batch](prediction-batch.json) and [score batch](score-batch.json)
retain the complete bin accounting. Scores are computed only after the saved
predictions have been authenticated. All signed errors, denominators and
score refusals remain at their original machine precision in the six native
score tables. No vegetation outcome is inferred from a pollen score.

For every bin, the accompanying `folds.json` retains all requested outer folds,
including failed folds. `preparations.json` retains the successfully prepared
regional cover, target rings, kernel support and regional source identities;
`operations.json` retains the corresponding native batch and request lineage.
These successful-fold tables do not imply that refused folds completed.
The [composition-refusal finding](composition-refusals.json) preserves the
eight selected negative LOVE vectors and their exact source identities and
limited arithmetic diagnosis, without reproducing the whole numerical cache.
Each bin's `projection.json` retains its original panel count, projected
Betula/Ulmus count, excluded count and source references. These files keep
source-count projection distinct from model success or scientific admission.

## Native pollen-error summaries

The table copies each native summary, with six decimals for display. Each
entry is a mean over the actually scored outer place groups within that bin,
not a mean over all requested groups or an estimate of independent accuracy.
All three methods have the same value because only one local predictor
remains; the JSON retains all three rows and full precision. No new pooled
mean or matched direct-pollen superiority claim is calculated here.

| CalBP bin | Scored groups / requested, per method | Native mean MAE, pollen fraction | Source |
| --- | ---: | ---: | --- |
| 2700–3200 | 3 / 3 | 0.096611 | [Summary](cal-bp-2700-3200/summaries.json) |
| 3200–3700 | 1 / 3 | 0.147177 | [Summary](cal-bp-3200-3700/summaries.json) |
| 3700–4200 | 1 / 3 | 0.373859 | [Summary](cal-bp-3700-4200/summaries.json) |
| 4200–4700 | 1 / 3 | 0.393054 | [Summary](cal-bp-4200-4700/summaries.json) |
| 4700–5200 | 1 / 3 | 0.493522 | [Summary](cal-bp-4700-5200/summaries.json) |
| 5200–5700 | 3 / 3 | 0.020523 | [Summary](cal-bp-5200-5700/summaries.json) |

## Stored coupled and direct pollen errors on matched support

The completed [comparison](comparison.json) authenticates target identity,
window, two-taxon counts and panel denominator, source count fingerprints,
training-place eligibility and source roles before joining stored errors.
It contains 36 dispositions: 16 paired rows and 20 unmatched rows. The pairs
repeat **eight unique Swedish target windows**, two at BOKE and six at BUS,
under two direct-training scopes; they are not 16 independent targets.
The unmatched population retains eight BOKE scope rows with unavailable
current predictions and 12 Solsø scope rows with no earlier Swedish-target
direct counterpart. Neither becomes a zero score.

| Target | CalBP window | Coupled MAE | Swedish-only direct MAE | Pooled-eligible direct MAE |
| --- | --- | ---: | ---: | ---: |
| BOKE | 2700–3200 | 0.105945 | 0.101614 | 0.105596 |
| BOKE | 5200–5700 | 0.015550 | 0.026664 | 0.004425 |
| BUS | 2700–3200 | 0.097256 | 0.101614 | 0.046824 |
| BUS | 3200–3700 | 0.147177 | 0.143542 | 0.143039 |
| BUS | 3700–4200 | 0.373859 | 0.369787 | 0.421463 |
| BUS | 4200–4700 | 0.393054 | 0.388567 | 0.416262 |
| BUS | 4700–5200 | 0.493522 | 0.489147 | 0.515229 |
| BUS | 5200–5700 | 0.030320 | 0.026664 | 0.035572 |

These cells copy stored errors and display six decimals; the JSON retains
full precision. MAE and total variation coincide on the two complementary
taxa here and are not independent metrics. No new mean, metric or difference
is calculated for this table. Lower error is not uniform: both BOKE windows
are poorer than the pooled direct comparator, and BUS at 2700–3200 CalBP is
also poorer than that comparator. The table also retains the poorer
Swedish-only comparisons, including BUS from 3200–5700 CalBP and BOKE at
2700–3200 CalBP. Other windows differ by comparator scope.
This table does not establish general model superiority.

For these BOKE/BUS targets, the coupled physical route uses Solsø 83 as
the regional proxy and one Swedish place as the local predictor. The pooled
direct comparator averages count-panel fractions from both training places;
the Swedish-only direct comparator uses only that Swedish local source.
Matched support means exact target, window, taxa, counts, panel denominator,
source-support fingerprints and declared training eligibility and role
lineage. It does not mean identical model information, independent accuracy
or a source-qualified regional vegetation estimate. The three coupled interpolation labels still share
one local predictor; the comparison uses only their training-mean row.

The read-only comparison completed with native and outer exit zero at
`e0597c47fc1a3316875cfd4e0dacf2929dfd04ca`, with all 6,894 registered
pins unchanged. It reused the original input epoch
`efac2696d313d551cd4422164461bfc0591d1da8`, prediction epoch
`964baa9418e0e22a43cdb971fdd67518b000b62f`, scoring epoch
`560abd7c16a17a38f1836fd0c1f638193ca03fcd` and earlier direct-study epoch
`a890b5e433fd2679768b588bae2774aa3d382e17`. It did not fit a model,
recompute scores or change the original prediction job exit one.
The [comparison publication map](comparison-publication.json) retains the
exact result and separate execution identities.

## Execution and evidence boundary

The original prediction computation used source epoch
`964baa9418e0e22a43cdb971fdd67518b000b62f`. It generated all six bins, then
the isolated source executor refused the artifact driver's multiprocessing
import origin. The original native and outer exits remain **one**.
A later maintained reader at source epoch
`560abd7c16a17a38f1836fd0c1f638193ca03fcd` authenticated all six products
and 517 native members with exit zero, without repeating fitting or kernels.
That reader result does not change the original job's terminal status.

The separate scoring run completed with native and outer exit zero at source
epoch `560abd7c16a17a38f1836fd0c1f638193ca03fcd`. All six bins were
accounted for: 30 method rows scored and 24 retained prediction failures.
All 7,263 registered input pins agreed before and after scoring. This metric
pass read the frozen predictions; it did not repeat fitting or kernels.

The native training, prediction, failure and score JSON files are published
byte for byte. Their run-local references remain literal; the publication
map binds them to these public paths. No source code, installed packages,
runtime inventories or numerical caches are copied into this account.

This is previously exposed conditional development evidence. It does not
establish untouched testing, independent vegetation accuracy, predictive
interval calibration, historical paper reproduction, a source-qualified
regional basin, four-country target coverage, source-use permission or
qualified scientific approval. The complete source-driven prediction and source-core
admission requirements remain open. The completed stored-score comparison now establishes exact matched target
and training support for the eight Swedish windows above. Its remaining
unmatched cases, conditional geometry and source-specific rights and review
limits remain explicit; no broader scientific acceptance follows.


## Deterministic PPE endpoint sensitivity

The [frozen PPE protocol](../../../../docs/report/pollen-reconstruction/nordic-coupled-workflow/assumptions/ppe-sensitivity.json) changes one taxon at a time. Betula PPE is 4.803 or 5.409 around nominal 5.106 (declared SD 0.303); Ulmus PPE is 1.22 or 1.32 around nominal 1.27 (declared SD 0.05). These are literal decimal domain endpoints, not draws from a probability law. Counts, fallspeeds, geometry, three physical places, six separate bins and withheld-place roles are unchanged.

At source epoch `381d1db3cafc18decf6c70f8cc044acf37c6e3ac`, all four prediction and all four separate scoring jobs completed with native and outer exit zero. Each scenario retains 18 requested folds and 54 dependent method dispositions: 30 scored and 24 prediction_failed. The eight refused place-bin folds per scenario remain explicit; they are neither clipped nor assigned zero error. These are separate deterministic parameter experiments, not 72 independent sites. The three spatial labels still share one local predictor.

The table copies the `training_mean` baseline's stored MAE fractions for the ten nominal scored target windows. Every endpoint cell is scored and paired by the publication binder using the exact full count/source observation, withheld target, training exclusions, regional anchor and local training roles. No score, difference, pooled mean or uncertainty interval is calculated for this table.

| Target record | Bin (CalBP, half-open) | Nominal | Betula 4.803 | Betula 5.409 | Ulmus 1.22 | Ulmus 1.32 |
| --- | --- | --- | --- | --- | --- | --- |
| neotoma-54001-39241-cal-bp-2700-3200 | cal-bp-2700-3200 | 0.10594470028404825 | 0.10595459827157884 | 0.10593510407273526 | 0.10593785070714906 | 0.10595119610008152 |
| neotoma-53995-39238-cal-bp-2700-3200 | cal-bp-2700-3200 | 0.0972556223925084 | 0.0969658081971529 | 0.09754447441758711 | 0.09745523354635163 | 0.09707071868741782 |
| neotoma-4446-4304-cal-bp-2700-3200 | cal-bp-2700-3200 | 0.08663289784109177 | 0.08663340745142133 | 0.08663534068277387 | 0.0866343131156916 | 0.08663278742740668 |
| neotoma-53995-39238-cal-bp-3200-3700 | cal-bp-3200-3700 | 0.14717742560405592 | 0.1471823601447159 | 0.14717259922343431 | 0.14717403497039366 | 0.14718057422233832 |
| neotoma-53995-39238-cal-bp-3700-4200 | cal-bp-3700-4200 | 0.3738588957857718 | 0.37417757169180077 | 0.37354419974630537 | 0.373641123585268 | 0.3740618369287361 |
| neotoma-53995-39238-cal-bp-4200-4700 | cal-bp-4200-4700 | 0.3930539449549848 | 0.3931852950628214 | 0.3929246441602681 | 0.3929644259970372 | 0.3931375251576579 |
| neotoma-53995-39238-cal-bp-4700-5200 | cal-bp-4700-5200 | 0.4935222128574675 | 0.4936389249816105 | 0.4934071587383887 | 0.4934425774948825 | 0.4935965235737195 |
| neotoma-54001-39241-cal-bp-5200-5700 | cal-bp-5200-5700 | 0.015550414177189262 | 0.015513174841214464 | 0.015587273885294066 | 0.015575982861764398 | 0.015526663255121961 |
| neotoma-53995-39238-cal-bp-5200-5700 | cal-bp-5200-5700 | 0.030319504412371863 | 0.030354297914605338 | 0.0302853973750802 | 0.030295882055932304 | 0.030341631697293835 |
| neotoma-4446-4304-cal-bp-5200-5700 | cal-bp-5200-5700 | 0.015700504311890105 | 0.015739211965021576 | 0.015663405055543134 | 0.01567461424759092 | 0.01572483310967269 |

All requested folds, failures, full training roles and exact stored point values are retained in [the PPE sensitivity account](ppe-sensitivity.json); [its publication map](ppe-sensitivity-publication.json) binds the completed native jobs and the source epochs. The nominal prediction and score products and their older failed prediction terminal remain unchanged. Endpoint sensitivity is not proof of ecological accuracy, robust model superiority, count/PPE covariance, joint chronology/geometry uncertainty, calibrated coverage, a qualified regional basin, source-use permission or qualified human review. Previously exposed development data and the original source/rights limitations remain in force. These results establish conditional parameter sensitivity; full scientific validation and release readiness remain open.


## Fixed-input LOVE composition admissibility

The original eight signed LOVE estimates are retained diagnostic information, not clipped compositions. Analytical LOVE is permitted to return values outside `[0,1]`; the downstream prediction consumer separately refuses such values as physical cover. The new optional diagnostic asks only whether this fixed count/PPE/background/deposition packet has a nonnegative local-cover solution under the maintained affine equation.

For local counts `n`, PPE means `a`, saved regional cover fractions `c`, and saved selected-ring factors `Kloc` and `Kreg`, set `q = normalize(n/a)`, `D = sum(c*Kloc)` and `T = D + sum(c*Kreg)`. The equation is `L_i = (T*q_i - c_i*Kreg_i)/D`. With the diagnosed nonnegative factors and `D > 0`, `0 <= L_i <= 1` is equivalent to `c_i*Kreg_i/T <= q_i <= (D+c_i*Kreg_i)/T`. This is a conditional algebraic bound, not an extra restriction on the estimator's mathematical output.

The maintained diagnostic source is committed at `69b29274207da0094f857ef2a68a96d52fa9d4ce`; the original input/native-prediction epoch remains `964baa9418e0e22a43cdb971fdd67518b000b62f`. The new diagnostic job's native and outer exits, exact current source and rerun argv are bound in [its publication map](admissibility-publication.json). It only reopens the original eight cache packets; there is no refit, kernel evaluation, prediction or metric calculation.

The table shows the below-lower-bound taxon in each original refused fold. Ratios are copied exactly as numerator/denominator text from the completed diagnostic; negative margins retain their sign. The companion above-upper-bound component, both native signed fractions, all interval quantities and every signed native-minus-rational residual remain in [the complete eight-case result](admissibility.json).

| Bin (CalBP) | Withheld record | Local predictor | Taxon below its conditional lower bound | PPE-adjusted local q | Required lower bound | Signed lower margin | Native signed cover | Native minus rational cover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3200-3700 | neotoma-54001-39241-cal-bp-3200-3700 | neotoma-53995-39238-cal-bp-3200-3700 | Betula | 95885/200558 | 18164635186429716442/36470251824595611155 | -146112807518620894577461/7314400765437246582024490 | -0.05475759019264426 | 6089445383485208968647009/66708928846474507770875350000000000000000 |
| 3200-3700 | neotoma-4446-4304-cal-bp-3200-3700 | neotoma-54001-39241-cal-bp-3200-3700 | Ulmus | 5957/25642 | 16580341544525117833/52524370270000477444 | -56132722093160113669939/673414951231676121309524 | -0.23208866347263946 | -2624063694828053208739937/60464739265235068057533450000000000000000 |
| 3700-4200 | neotoma-4446-4304-cal-bp-3700-4200 | neotoma-54001-39241-cal-bp-3700-4200 | Ulmus | 107226/233591 | 98671987406993562107/194339256791302797476 | -2210667061682799403974661/45395901333137211765216316 | -0.13046631266939213 | 59855162760290900541015961/1210310821923343387849280300000000000000000 |
| 3700-4200 | neotoma-54001-39241-cal-bp-3700-4200 | neotoma-53995-39238-cal-bp-3700-4200 | Betula | 75565/438091 | 2325910309649175034/4668487035396277385 | -666186150634797039222569/2045222153823790555872035 | -0.8928999482135171 | -23122833290258156078247/932615899418068820285570000000000000000 |
| 4200-4700 | neotoma-54001-39241-cal-bp-4200-4700 | neotoma-53995-39238-cal-bp-4200-4700 | Betula | 92710/478213 | 12450461069298525182/24433500686592500255 | -3688742490678464924218716/11684417663837459324444315 | -0.8673810326940689 | -5278773246980098907303989/63791039087308059571297010000000000000000 |
| 4200-4700 | neotoma-4446-4304-cal-bp-4200-4700 | neotoma-54001-39241-cal-bp-4200-4700 | Ulmus | 81696/230921 | 4826954668845348433/9768910253916666244 | -316564306980460740026969/2255846524744690485730724 | -0.3769720352889244 | 1370580802417401372350241/10496942655767383437618422500000000000000 |
| 4700-5200 | neotoma-54001-39241-cal-bp-4700-5200 | neotoma-53995-39238-cal-bp-4700-5200 | Betula | 13081/92224 | 305289812373433067698/588685896167369251445 | -20454447448562134057228307/54290968088139461845263680 | -1.037024124771285 | -1593994578637291841803/7704756662586589902315800000000000000 |
| 4700-5200 | neotoma-4446-4304-cal-bp-4700-5200 | neotoma-54001-39241-cal-bp-4700-5200 | Ulmus | 61272/182557 | 33899302793688542743/64288436182056422324 | -2249473958360438188897723/11736304044087674290202468 | -0.5115315035062445 | -9829008964890680525534561/131925831133075745438286898000000000000000 |

The algebra interprets the printed decimal input cells as exact rationals. It is not an exact replay of native float64 arithmetic; the full residuals remain visible without a new equality tolerance. A violated bound identifies incompatibility of this particular fixed input/background/K tuple with nonnegative cover. It does not distinguish an inappropriate regional proxy, geometry, chronology/taxon transfer, PPE, transport assumptions or source observations, and does not establish a field cause or an algorithm defect. Original signed estimates, refusal guards, epochs and the 24 dependent refused method dispositions remain unchanged. No clipping, reclosure, threshold relaxation, corrected prediction, ecological accuracy, probability law, confidence interval, calibrated coverage, source-rights permission or qualified human approval follows.

A local rerun uses the maintained module with the retained, hash-identified eight-cache contract and a fresh output under `artifacts/`:

```sh
python -m bijux_pollenomics_dev.essd_reproduction.nordic_coupled.admissibility \
  --contract <retained-input-contract.json> \
  --contract-sha256 beecdd97445f141661c8080c041d81599822066fc2101f44d08ab2a79068afa2 \
  --output <fresh-artifacts-diagnostic.json>
```

The actual registered source executor, runtime, complete input pins and argv are retained in the publication map. This optional diagnostic does not discharge whole source-driven prediction or uncertainty acceptance.


## FLINK native source panels, separate from reconstruction

A separately registered source-only projection uses FLINK's literal Neotoma dataset 54024, collection unit 39258, site 28889 and default chronology 38438. Its maintained source is committed at `9937173f9be978d7a72110672b636ea892e299a2`. The [native panel account](flink-source-panels.json) preserves all 109 sample identities, typed ages, native bounds/depths and literal count-row states; the three negative native ages (samples 552982, 552983 and 552996) remain in the account, separately from the 106 nonnegative-age selection. No negative sample becomes ecological absence.

Chronology uses the source-default **Calibrated radiocarbon years BP** label and the explicitly declared AD1950 BP reference. Native model interpolation and chronology endpoints are metadata, not per-sample confidence bounds. The adapter performs no recalibration, interpolation or calendar conversion, and it does not correct the historical workbook's separate age representation.

The six-window table is copied from the completed source projection. Membership is by the native point age in each half-open `[younger, older)` interval. Counts are pooled only when every member has complete literal Betula/Ulmus observations; missing, duplicate or incompatible rows are retained separately from measured zero. Empty or refused windows remain visible. `Pollen N` includes literal pollen/NISP rows (element and elementtype pollen, context null), not a source-qualified terrestrial LRA denominator. Excluded pollen is literal nonpanel mass, not a taxon-synonym assignment. No geometry or PPE input participates in this projection.

| Native point-age window (CalBP, half-open) | Member samples | Betula NISP | Ulmus NISP | Panel N | Pollen N | Excluded pollen N | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [2700, 3200) | 3 | 916 | 33 | 949 | 3272 | 2323 | projected |
| [3200, 3700) | 4 | 1149 | 58 | 1207 | 4410 | 3203 | projected |
| [3700, 4200) | 4 | 1084 | 70 | 1154 | 4325 | 3171 | projected |
| [4200, 4700) | 4 | 1099 | 63 | 1162 | 4315 | 3153 | projected |
| [4700, 5200) | 4 | 1059 | 69 | 1128 | 4356 | 3228 | projected |
| [5200, 5700) | 5 | 1258 | 76 | 1334 | 5395 | 4061 | projected |

**Existing geometry metadata is a separate lead.** LandClim II's `LANDCLIMII metadata file!D989` supplies a static site-radius token **98**, with the meters unit stated by `readme!A6:B6`. LandClim I's `SiteData!G102` is the literal area `3.00*`, under `G1` `Area of site (ha) (*Actual size)`. The area star is not the distinct date-column “includes top” convention. These are source-provided metadata; no radius was derived from area. Neotoma's `area:null` applies only to that site object and is not global absence of LandClim radius/area metadata. The selected cells do not establish a measurement date/method/uncertainty, dated basin trajectory or transfer to the exact core and all six windows. The LandClim/Neotoma point discrepancy remains unresolved. Any future use of a static radius requires a separate conditional protocol and source/core/time admission.

[The publication map](flink-source-publication.json) binds the actual native manifest, source/protocol identities, completed native/outer execution and rerun argv. This is **no fourth-place LRA run**: the original three-place/six-bin/54-method results, their epochs and all refused cases remain unchanged. There is no reconstruction, prediction, kernel evaluation, scoring, new geometry/parameter assignment, source-use grant, qualified human approval, independent vegetation accuracy or whole scientific acceptance.


## Four-place conditional pollen predictions

This separate development cohort adds FLINK to BOKE, BUS and Solsø 83. It retains six separate 500-year CalBP experiments, 24 requested whole-place holdouts and 72 dependent method dispositions. Each fold has three training places: one declared regional proxy and two local predictors. The training-mean, nearest-site and inverse-distance-squared labels may yield different predictions; they remain dependent methods sharing fitted physical inputs. Refused folds, unavailable scores and unrun outcomes are retained rather than set to zero. The completed run produced 33 scored method dispositions and 39 prediction failures across the 24 folds; all 13 refused folds retain their original invalid_composition reason.

The source protocol and workflow were committed at `e50ea3ecb9a9ade4512451993dc80fc6a326ca2b`; the original 117-member input delivery is from `a1f4412e333964d7408937045faa8b4a0289af83`. The two new JSON accounts record the actual prediction and score execution epoch, native/outer statuses, exact frozen products and rerun commands. The following table copies stored per-target method MAE fractions and total variation; it calculates no new metric, aggregate mean or model.

| Window | Target | Baseline | Status | Stored MAE fraction | Stored TV |
| --- | --- | --- | --- | --- | --- |
| cal-bp-2700-3200 | neotoma-54024-39258-cal-bp-2700-3200 | training_mean | scored | 0.04714850777089169 | 0.04714850777089169 |
| cal-bp-2700-3200 | neotoma-54024-39258-cal-bp-2700-3200 | nearest_site | scored | 0.08840719906483681 | 0.08840719906483681 |
| cal-bp-2700-3200 | neotoma-54024-39258-cal-bp-2700-3200 | inverse_distance_squared | scored | 0.05511047709506792 | 0.05511047709506792 |
| cal-bp-2700-3200 | neotoma-54001-39241-cal-bp-2700-3200 | training_mean | scored | 0.11451280223859847 | 0.11451280223859847 |
| cal-bp-2700-3200 | neotoma-54001-39241-cal-bp-2700-3200 | nearest_site | scored | 0.10594470028404825 | 0.10594470028404825 |
| cal-bp-2700-3200 | neotoma-54001-39241-cal-bp-2700-3200 | inverse_distance_squared | scored | 0.10785920826119749 | 0.10785920826119749 |
| cal-bp-2700-3200 | neotoma-53995-39238-cal-bp-2700-3200 | training_mean | scored | 0.028437090476459995 | 0.028437090476459995 |
| cal-bp-2700-3200 | neotoma-53995-39238-cal-bp-2700-3200 | nearest_site | scored | 0.0972556223925084 | 0.0972556223925084 |
| cal-bp-2700-3200 | neotoma-53995-39238-cal-bp-2700-3200 | inverse_distance_squared | scored | 0.08544775515306853 | 0.08544775515306853 |
| cal-bp-2700-3200 | neotoma-4446-4304-cal-bp-2700-3200 | training_mean | scored | 0.030519892134545402 | 0.030519892134545402 |
| cal-bp-2700-3200 | neotoma-4446-4304-cal-bp-2700-3200 | nearest_site | scored | 0.012231170448298315 | 0.012231170448298315 |
| cal-bp-2700-3200 | neotoma-4446-4304-cal-bp-2700-3200 | inverse_distance_squared | scored | 0.02720824112774209 | 0.02720824112774209 |
| cal-bp-3200-3700 | neotoma-54024-39258-cal-bp-3200-3700 | training_mean | prediction_failed | unavailable | unavailable |
| cal-bp-3200-3700 | neotoma-54024-39258-cal-bp-3200-3700 | nearest_site | prediction_failed | unavailable | unavailable |
| cal-bp-3200-3700 | neotoma-54024-39258-cal-bp-3200-3700 | inverse_distance_squared | prediction_failed | unavailable | unavailable |
| cal-bp-3200-3700 | neotoma-54001-39241-cal-bp-3200-3700 | training_mean | prediction_failed | unavailable | unavailable |
| cal-bp-3200-3700 | neotoma-54001-39241-cal-bp-3200-3700 | nearest_site | prediction_failed | unavailable | unavailable |
| cal-bp-3200-3700 | neotoma-54001-39241-cal-bp-3200-3700 | inverse_distance_squared | prediction_failed | unavailable | unavailable |
| cal-bp-3200-3700 | neotoma-53995-39238-cal-bp-3200-3700 | training_mean | scored | 0.15873222247006918 | 0.15873222247006918 |
| cal-bp-3200-3700 | neotoma-53995-39238-cal-bp-3200-3700 | nearest_site | scored | 0.14717742560405592 | 0.14717742560405592 |
| cal-bp-3200-3700 | neotoma-53995-39238-cal-bp-3200-3700 | inverse_distance_squared | scored | 0.14894305750569828 | 0.14894305750569828 |
| cal-bp-3200-3700 | neotoma-4446-4304-cal-bp-3200-3700 | training_mean | prediction_failed | unavailable | unavailable |
| cal-bp-3200-3700 | neotoma-4446-4304-cal-bp-3200-3700 | nearest_site | prediction_failed | unavailable | unavailable |
| cal-bp-3200-3700 | neotoma-4446-4304-cal-bp-3200-3700 | inverse_distance_squared | prediction_failed | unavailable | unavailable |
| cal-bp-3700-4200 | neotoma-53995-39238-cal-bp-3700-4200 | training_mean | scored | 0.4384535388778275 | 0.4384535388778275 |
| cal-bp-3700-4200 | neotoma-53995-39238-cal-bp-3700-4200 | nearest_site | scored | 0.3738588957857718 | 0.3738588957857718 |
| cal-bp-3700-4200 | neotoma-53995-39238-cal-bp-3700-4200 | inverse_distance_squared | scored | 0.38477166617747793 | 0.38477166617747793 |
| cal-bp-3700-4200 | neotoma-4446-4304-cal-bp-3700-4200 | training_mean | prediction_failed | unavailable | unavailable |
| cal-bp-3700-4200 | neotoma-4446-4304-cal-bp-3700-4200 | nearest_site | prediction_failed | unavailable | unavailable |
| cal-bp-3700-4200 | neotoma-4446-4304-cal-bp-3700-4200 | inverse_distance_squared | prediction_failed | unavailable | unavailable |
| cal-bp-3700-4200 | neotoma-54024-39258-cal-bp-3700-4200 | training_mean | prediction_failed | unavailable | unavailable |
| cal-bp-3700-4200 | neotoma-54024-39258-cal-bp-3700-4200 | nearest_site | prediction_failed | unavailable | unavailable |
| cal-bp-3700-4200 | neotoma-54024-39258-cal-bp-3700-4200 | inverse_distance_squared | prediction_failed | unavailable | unavailable |
| cal-bp-3700-4200 | neotoma-54001-39241-cal-bp-3700-4200 | training_mean | prediction_failed | unavailable | unavailable |
| cal-bp-3700-4200 | neotoma-54001-39241-cal-bp-3700-4200 | nearest_site | prediction_failed | unavailable | unavailable |
| cal-bp-3700-4200 | neotoma-54001-39241-cal-bp-3700-4200 | inverse_distance_squared | prediction_failed | unavailable | unavailable |
| cal-bp-4200-4700 | neotoma-54001-39241-cal-bp-4200-4700 | training_mean | prediction_failed | unavailable | unavailable |
| cal-bp-4200-4700 | neotoma-54001-39241-cal-bp-4200-4700 | nearest_site | prediction_failed | unavailable | unavailable |
| cal-bp-4200-4700 | neotoma-54001-39241-cal-bp-4200-4700 | inverse_distance_squared | prediction_failed | unavailable | unavailable |
| cal-bp-4200-4700 | neotoma-53995-39238-cal-bp-4200-4700 | training_mean | scored | 0.4280967258428796 | 0.4280967258428796 |
| cal-bp-4200-4700 | neotoma-53995-39238-cal-bp-4200-4700 | nearest_site | scored | 0.3930539449549848 | 0.3930539449549848 |
| cal-bp-4200-4700 | neotoma-53995-39238-cal-bp-4200-4700 | inverse_distance_squared | scored | 0.398677922926151 | 0.398677922926151 |
| cal-bp-4200-4700 | neotoma-4446-4304-cal-bp-4200-4700 | training_mean | prediction_failed | unavailable | unavailable |
| cal-bp-4200-4700 | neotoma-4446-4304-cal-bp-4200-4700 | nearest_site | prediction_failed | unavailable | unavailable |
| cal-bp-4200-4700 | neotoma-4446-4304-cal-bp-4200-4700 | inverse_distance_squared | prediction_failed | unavailable | unavailable |
| cal-bp-4200-4700 | neotoma-54024-39258-cal-bp-4200-4700 | training_mean | prediction_failed | unavailable | unavailable |
| cal-bp-4200-4700 | neotoma-54024-39258-cal-bp-4200-4700 | nearest_site | prediction_failed | unavailable | unavailable |
| cal-bp-4200-4700 | neotoma-54024-39258-cal-bp-4200-4700 | inverse_distance_squared | prediction_failed | unavailable | unavailable |
| cal-bp-4700-5200 | neotoma-54001-39241-cal-bp-4700-5200 | training_mean | prediction_failed | unavailable | unavailable |
| cal-bp-4700-5200 | neotoma-54001-39241-cal-bp-4700-5200 | nearest_site | prediction_failed | unavailable | unavailable |
| cal-bp-4700-5200 | neotoma-54001-39241-cal-bp-4700-5200 | inverse_distance_squared | prediction_failed | unavailable | unavailable |
| cal-bp-4700-5200 | neotoma-53995-39238-cal-bp-4700-5200 | training_mean | scored | 0.5194497195053145 | 0.5194497195053145 |
| cal-bp-4700-5200 | neotoma-53995-39238-cal-bp-4700-5200 | nearest_site | scored | 0.4935222128574675 | 0.4935222128574675 |
| cal-bp-4700-5200 | neotoma-53995-39238-cal-bp-4700-5200 | inverse_distance_squared | scored | 0.49760282080739626 | 0.49760282080739626 |
| cal-bp-4700-5200 | neotoma-4446-4304-cal-bp-4700-5200 | training_mean | prediction_failed | unavailable | unavailable |
| cal-bp-4700-5200 | neotoma-4446-4304-cal-bp-4700-5200 | nearest_site | prediction_failed | unavailable | unavailable |
| cal-bp-4700-5200 | neotoma-4446-4304-cal-bp-4700-5200 | inverse_distance_squared | prediction_failed | unavailable | unavailable |
| cal-bp-4700-5200 | neotoma-54024-39258-cal-bp-4700-5200 | training_mean | prediction_failed | unavailable | unavailable |
| cal-bp-4700-5200 | neotoma-54024-39258-cal-bp-4700-5200 | nearest_site | prediction_failed | unavailable | unavailable |
| cal-bp-4700-5200 | neotoma-54024-39258-cal-bp-4700-5200 | inverse_distance_squared | prediction_failed | unavailable | unavailable |
| cal-bp-5200-5700 | neotoma-54001-39241-cal-bp-5200-5700 | training_mean | scored | 0.004155318144303241 | 0.004155318144303241 |
| cal-bp-5200-5700 | neotoma-54001-39241-cal-bp-5200-5700 | nearest_site | scored | 0.015550414177189262 | 0.015550414177189262 |
| cal-bp-5200-5700 | neotoma-54001-39241-cal-bp-5200-5700 | inverse_distance_squared | scored | 0.011051024241206596 | 0.011051024241206596 |
| cal-bp-5200-5700 | neotoma-54024-39258-cal-bp-5200-5700 | training_mean | scored | 0.019384491769813907 | 0.019384491769813907 |
| cal-bp-5200-5700 | neotoma-54024-39258-cal-bp-5200-5700 | nearest_site | scored | 0.0106630655073694 | 0.0106630655073694 |
| cal-bp-5200-5700 | neotoma-54024-39258-cal-bp-5200-5700 | inverse_distance_squared | scored | 0.017514666877217904 | 0.017514666877217904 |
| cal-bp-5200-5700 | neotoma-53995-39238-cal-bp-5200-5700 | training_mean | scored | 0.039503472944246096 | 0.039503472944246096 |
| cal-bp-5200-5700 | neotoma-53995-39238-cal-bp-5200-5700 | nearest_site | scored | 0.030319504412371863 | 0.030319504412371863 |
| cal-bp-5200-5700 | neotoma-53995-39238-cal-bp-5200-5700 | inverse_distance_squared | scored | 0.031714090235093216 | 0.031714090235093216 |
| cal-bp-5200-5700 | neotoma-4446-4304-cal-bp-5200-5700 | training_mean | prediction_failed | unavailable | unavailable |
| cal-bp-5200-5700 | neotoma-4446-4304-cal-bp-5200-5700 | nearest_site | prediction_failed | unavailable | unavailable |
| cal-bp-5200-5700 | neotoma-4446-4304-cal-bp-5200-5700 | inverse_distance_squared | prediction_failed | unavailable | unavailable |

[Complete dispositions and stored scores](flink-nordic.json) · [Execution/source identities and rerun map](flink-nordic-publication.json).

This is a prior-exposed, conditional source-pollen comparison. The older three-place nominal, PPE endpoint, affine diagnostic and source-only FLINK accounts remain unchanged and retain their original epochs/refusals. The training populations differ, so this extension does not establish comparative gain. Static FLINK geometry and transferred parameters remain declared assumptions, not dated core/window geometry admission. No independent vegetation accuracy, untouched validation, historical reproduction, calibrated uncertainty, probability law, source-specific analytical rights, qualified human review or whole scientific acceptance follows.


## Conditional counting sets for the retained LOVE refusals

This separate calculation examines the **eight previously selected place-bin
contexts**, not eight independent sites. They are the same requests whose
analytical LOVE estimates and 24 dependent method refusals remain in the
[original admissibility account](admissibility.json). Selection followed
inspection of those failures; this calculation does not replace an analytical
estimate, repair a refusal or add a successful prediction or pollen score.

The [counting protocol](../../../../docs/report/pollen-reconstruction/nordic-coupled-workflow/assumptions/love-counting-uncertainty.json)
freezes a nominal 95% marginal confidence level for one homogeneous,
two-taxon, fixed-background counting law. Each local Betula/Ulmus panel is
treated as one fixed-effort binomial observation, with its denominator equal
to the sum of those two measured integer counts. This is not an all-pollen
or terrestrial-pollen denominator. Constant within-panel probability and
exchangeable, independent counts are assumptions; pooling samples across a
500-year bin does not establish them empirically.

For Betula cover `v` and complementary Ulmus cover `1-v`, the conditional law
is `p(v) = (a_B*v + b_B) / (a_B*v + a_U*(1-v) + b_B + b_U)`.
The coefficients use the saved regional fractions `c`, the selected local
and regional responses and the transferred PPE values:
`D = sum(c_i*Kloc_i)`, `a_i = PPE_i*D`, and
`b_i = PPE_i*c_i*Kreg_i`. The common `D` is not a taxon-specific `Kloc`.
Saved decimal coefficients are formed as exact rationals, then each is
rounded once to binary64; the numerical API conditions on those supplied
binary64 coefficients. This is not replay of the old native arithmetic.

The maintained API intersects its certified binomial confidence interval
with the fixed model's feasible pollen range and inverts the monotone law.
Outward bounds describe one dependent two-taxon cover set, not two
independent taxon intervals. An empty set retains null cover bounds. The
constrained binomial point MLE is a separate quantity, including when the
confidence set is empty; it never replaces the original analytical LOVE
point. Numerical refusals, fatal failures and later unrun requests remain
distinct from both empty and nonempty sets.

The actual calculation completed with native and outer exit zero at `a10f24735712dab1dbc66aeb12fe7b7cc3f25a93`: all eight requests were computed, with three nonempty sets and five empty sets; zero requests were refused, fatal or unrun. The original eight fold refusals and 24 dependent method failures remain unchanged.

| Retained context | Consumer status | Confidence-set status | Betula bounds | Ulmus bounds | Constrained binomial point (Betula, Ulmus) | Original analytical LOVE point / refusal |
| --- | --- | --- | --- | --- | --- | --- |
| 3200-3700; withheld neotoma-54001-39241-cal-bp-3200-3700; local predictor neotoma-53995-39238-cal-bp-3200-3700 | computed | nonempty | [0.0, 0.19807918595263377] | [0.8019208140473661, 1.0] | [0.0, 1.0] | {"Betula": "-0.05475759019264426", "Ulmus": "1.0547575901926443"}; original range refusal retained |
| 3200-3700; withheld neotoma-4446-4304-cal-bp-3200-3700; local predictor neotoma-54001-39241-cal-bp-3200-3700 | computed | nonempty | [0.7834725925332543, 1.0] | [0.0, 0.21652740746674562] | [1.0, 0.0] | {"Betula": "1.2320886634726391", "Ulmus": "-0.23208866347263946"}; original range refusal retained |
| 3700-4200; withheld neotoma-4446-4304-cal-bp-3700-4200; local predictor neotoma-54001-39241-cal-bp-3700-4200 | computed | nonempty | [0.9052837268348708, 1.0] | [0.0, 0.09471627316512912] | [1.0, 0.0] | {"Betula": "1.1304663126693923", "Ulmus": "-0.13046631266939213"}; original range refusal retained |
| 3700-4200; withheld neotoma-54001-39241-cal-bp-3700-4200; local predictor neotoma-53995-39238-cal-bp-3700-4200 | computed | empty | null (empty) | null (empty) | [0.0, 1.0] | {"Betula": "-0.8928999482135171", "Ulmus": "1.8928999482135174"}; original range refusal retained |
| 4200-4700; withheld neotoma-54001-39241-cal-bp-4200-4700; local predictor neotoma-53995-39238-cal-bp-4200-4700 | computed | empty | null (empty) | null (empty) | [0.0, 1.0] | {"Betula": "-0.8673810326940689", "Ulmus": "1.867381032694069"}; original range refusal retained |
| 4200-4700; withheld neotoma-4446-4304-cal-bp-4200-4700; local predictor neotoma-54001-39241-cal-bp-4200-4700 | computed | empty | null (empty) | null (empty) | [1.0, 0.0] | {"Betula": "1.376972035288925", "Ulmus": "-0.3769720352889244"}; original range refusal retained |
| 4700-5200; withheld neotoma-54001-39241-cal-bp-4700-5200; local predictor neotoma-53995-39238-cal-bp-4700-5200 | computed | empty | null (empty) | null (empty) | [0.0, 1.0] | {"Betula": "-1.037024124771285", "Ulmus": "2.037024124771285"}; original range refusal retained |
| 4700-5200; withheld neotoma-4446-4304-cal-bp-4700-5200; local predictor neotoma-54001-39241-cal-bp-4700-5200 | computed | empty | null (empty) | null (empty) | [1.0, 0.0] | {"Betula": "1.5115315035062442", "Ulmus": "-0.5115315035062445"}; original range refusal retained |

The table copies stored values and classifications only. Full machine
precision, original signed points, numerical diagnostics and all eight
dispositions remain in [the exact result](love-counting-uncertainty.json).
The [publication map](love-counting-uncertainty-publication.json) preserves
the actual source epoch, five execution records and unchanged original
native identities. No new mean, error metric or fit is calculated here.

The nominal coverage statement is conditional on fixed PPE, regional
reconstruction/background, K, selected ring and basin geometry, chronology,
taxon support, pooling and sampling design. It is not coverage conditional
on selecting these eight observed failures, a simultaneous eight-request
guarantee, or joint propagation of count and parameter uncertainty. It is
not a probability that the historical model is correct. Neither an empty
nor a nonempty set establishes a field cause or an estimator defect.
Independent vegetation accuracy, untouched validation, calibrated field
uncertainty, historical reproduction, source-specific analytical rights and
qualified human review remain unresolved under their original criteria.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Maintained source-driven coupled regional/local reconstruction and forward-pollen development preserves all six bins, 18 requested place-bin folds and 54 method dispositions; independently reopened frozen products are scored separately. A read-only stored-score comparison establishes 16 paired scope rows over eight unique Swedish target windows, retaining all 20 unmatched rows. Four deterministic one-taxon PPE endpoint experiments preserve complete fold/refusal accounting and exact shared-support stored MAE comparisons for ten nominal scored target windows. An optional saved-intermediate affine diagnostic identifies the exact conditional nonnegative-cover bounds and signed margins for the eight original refused local LOVE tuples, without changing the estimator or its downstream refusal. A separate FLINK literal source projection retains all 109 native samples, three negative ages, count-row missingness states and six prospective point-age window dispositions. It does not add a fourth-place reconstruction or scored result. A separately executed conditional four-place FLINK–Nordic cohort retains all six bins, 24 requested whole-place folds and 72 dependent method dispositions; each fold uses one regional anchor and two local training places. All new outcomes and exact stored scores remain separate from the three-place accounts. A separate conditional counting calculation retains the eight previously selected signed LOVE requests and all dispositions. It reports a nominal 95% marginal two-taxon fixed-background cover set; empty/null sets, constrained binomial points and numerical refusals remain distinct. None replaces an original analytical estimate or refusal.

**Unsupported claim.** Untouched testing, independent vegetation or field accuracy, calibrated uncertainty, a qualified regional basin, historical reproduction, four-country target generalization, source-rights or complete source-driven prediction acceptance.

**Actual verification performed.** Original prediction execution at 964baa9418e0e22a43cdb971fdd67518b000b62f generated all six bins with 30 predicted and 24 refused method dispositions, then ended with native and outer exit one at a final import-origin guard. The maintained reader at 560abd7c16a17a38f1836fd0c1f638193ca03fcd reopened all six products and 517 native members with exit zero without refitting. Separate scoring at that later source epoch completed with native and outer exit zero: 30 scored rows and 24 prediction failures, with all 7,263 pins unchanged. Native tables and all eight selected out-of-range LOVE vectors are retained literally. The separate comparison completed with native and outer exit zero at e0597c47fc1a3316875cfd4e0dacf2929dfd04ca, with all 6,894 pins unchanged; it authenticates exact stored target/training inputs before joining errors and performs no fitting or rescoring. Four endpoint prediction jobs and four separate scoring jobs completed with native and outer exit zero at source epoch 381d1db3cafc18decf6c70f8cc044acf37c6e3ac; each has 30 scored and 24 prediction_failed method dispositions. The publication binder authenticates exact observation and fold-role identity before copying the stored endpoint and nominal MAE fractions; no new metric is calculated. The separately completed diagnostic at source epoch 69b29274207da0094f857ef2a68a96d52fa9d4ce reopens the original eight deterministic cache packets and preserves all exact rational bounds and signed native-minus-rational residuals; the publication map records its actual native/outer exits and source/input identities. It performs no refit, kernel evaluation, prediction or scoring. The separately completed source-only job at 9937173f9be978d7a72110672b636ea892e299a2 authenticates the exact retained raw buffer and default-chronology protocol, then publishes literal panel observations and only admissible window aggregates; its actual native/outer exits and manifest are retained in the FLINK publication map. No LRA/model/metric call occurs. The separate four-place prediction and pure-score jobs are admitted here only after their actual native and outer exits are zero, all source/input pins remain unchanged, and exact frozen product readers join the stored score rows to every available prediction. The publication records both actual execution identities and calculates no metric or fit. The separate counting job completed with native and outer exit zero at source epoch a10f24735712dab1dbc66aeb12fe7b7cc3f25a93, with all 6,751 registered input pins unchanged. The publication copies the exact result and stored classifications without recomputing bounds, fits, kernels, predictions or metrics. Five execution records and current source/input identities remain distinct from the original failed prediction job.

**Remaining input or review.** Static circular geometry, bin stationarity, source-taxonomy/PPE transfer and small-lake regional proxies are declared development assumptions; no independent measured vegetation or calibrated interval is available. Source-specific use and qualified review remain separate. Resolver: Physical source, chronology and parameter custodians and qualified ecological reviewer Reopen when: Freeze compatible source-supported basin/regional/chronology/taxon inputs and an independent vegetation reference for the intended inference; resolve source-specific analytical use and qualified review.

**Cause category.** data|assumption|comparability|access/rights|qualified review

**Consequence.** Retain poorer or refused cases and limit the reported error to the actually scored two-taxon support; neither repeated method labels nor bins increase the number of independent sites.

**Precise next acceptance route.** A broader scientific prediction claim requires a source-qualified regional and local geometry/parameter packet on compatible time/taxon support, independent measured vegetation for vegetation accuracy, and the original source-specific rights and qualified review decisions. Exact matched target and training support is now established for these eight Swedish windows; extending that comparison requires independently compatible support for the remaining cases, without dropping their recorded refusals.

**Negative or refused result.** Eight place-bin folds yield 24 refused method dispositions: saved local LOVE fractions fall outside [0,1] and the exact range guard refuses before closure. All 24 remain prediction_failed in scoring. The original prediction job also retains its distinct final source-origin guard failure. Physical causality is unresolved; no clipping, renormalization or tolerance change is justified. The comparison retains 20 unmatched rows: eight BOKE scope rows lack current predictions and 12 Solsø scope rows lack an earlier Swedish-target counterpart. Both BOKE windows and BUS at 2700–3200 CalBP are poorer than the pooled direct comparator; no general superiority is inferred. Each PPE endpoint retains eight refused folds and 24 prediction_failed method rows; no clipping or zero substitution is admitted. Deterministic SD endpoints do not establish a probability law, covariance, confidence interval, calibration or robustness across other assumptions. The diagnostic leaves original signed LOVE values and range refusals unchanged. Printed-decimal rational interpretation is not exact native float64 replay. Conditional tuple incompatibility does not identify a field cause, faulty source or algorithm defect; no tolerance, clipping or reclosure is introduced. FLINK negative native ages and missing/duplicate/incompatible literal count rows stay distinct from measured zero; empty/refused window states are preserved. Existing static LandClim radius/area metadata does not establish dated core/window geometry or resolve source-specific use and qualified review. Four-place refusals and unavailable scores remain explicit. No prediction or scoring success is inferred from the requested population. Different training populations prohibit a general gain claim; dependent method labels do not create independent models or sites. The actual eight requests yield three nonempty and five empty sets, with zero numerical refusals, fatal failures or unrun requests; empty-set cover bounds remain null. Original eight fold refusals and 24 dependent method failures remain unchanged. Failure-based selection does not acquire post-selection or simultaneous coverage. Fixed nuisance quantities and pooled-count assumptions remain unvalidated; neither an empty nor a nonempty set identifies a field cause or estimator defect.

**Matched denominator.** Three native physical places (BOKE, BUS, SOLSOE83), six separate 500-year CalBP bins, two measured taxa, 18 requested place-bin folds and three method labels produce 54 dispositions: 30 scored and 24 prediction_failed. The three spatial labels share one local predictor and are not independent models. Native within-bin means use only 3, 1, 1, 1, 1 and 3 scored outer groups per method; no new pooled mean is inferred. The separate comparison has 36 dispositions: 16 paired scope rows over eight unique Swedish windows (BOKE two, BUS six) and 20 unmatched rows; repeated scopes are not independent targets. For BOKE/BUS, coupled reconstruction uses Solsø 83 as regional proxy plus one Swedish local predictor; pooled direct averages both training panels, Swedish-only direct uses the local Swedish source alone. Exact support/eligibility/role lineage does not make model information identical. PPE endpoint delivery uses four separate one-taxon domain experiments on the same three places and six bins: 18 requested folds and 54 dependent method dispositions per scenario. The readable table has ten exact shared-support scored nominal target windows, each repeated across four endpoints; these are not independent sites or methods. The affine diagnostic covers exactly the eight originally refused place-bin folds at their saved second local ring, with two ordered taxa per tuple. This is an optional algebraic feasibility check, not a new independent cohort or a constraint imposed on analytical LOVE estimates. FLINK source-only delivery covers all 109 native samples (106 nonnegative and three negative-age samples), two literal pollen labels and six separately declared half-open point-age windows; actual membership, panel counts, full pollen N and excluded literal pollen mass are retained per window. It creates no fourth-place model denominator or independent scored target. The distinct four-place extension requests six separate bins, 24 whole-place folds and 72 dependent method dispositions with three training places per fold: one regional anchor and two locals. Actual scored support and all missing/refused outcomes are retained literally, without pooling into the earlier three-place denominator. The completed run retains 33 scored and 39 prediction_failed method dispositions; these are outcomes, not additional independent targets. This counting calculation covers eight selected place-bin contexts on the literal Betula/Ulmus panel, not eight independent sites. Each panel denominator is its two measured integer counts. All eight requests were computed: three nonempty and five empty sets, with no dropped or unrun context. Complementary cover bounds form one dependent set; no pooled uncertainty, new scored cohort or extra independent model follows.

Retained evidence: [reports/science/pollen-reconstruction/nordic-coupled-workflow/prediction-batch.json](prediction-batch.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/score-batch.json](score-batch.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/composition-refusals.json](composition-refusals.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/publication.json](publication.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-2700-3200/training.json](cal-bp-2700-3200/training.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-2700-3200/preparations.json](cal-bp-2700-3200/preparations.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-2700-3200/operations.json](cal-bp-2700-3200/operations.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-2700-3200/folds.json](cal-bp-2700-3200/folds.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-2700-3200/predictions.json](cal-bp-2700-3200/predictions.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-2700-3200/failures.json](cal-bp-2700-3200/failures.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-2700-3200/scores.json](cal-bp-2700-3200/scores.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-2700-3200/summaries.json](cal-bp-2700-3200/summaries.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-2700-3200/projection.json](cal-bp-2700-3200/projection.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-3200-3700/training.json](cal-bp-3200-3700/training.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-3200-3700/preparations.json](cal-bp-3200-3700/preparations.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-3200-3700/operations.json](cal-bp-3200-3700/operations.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-3200-3700/folds.json](cal-bp-3200-3700/folds.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-3200-3700/predictions.json](cal-bp-3200-3700/predictions.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-3200-3700/failures.json](cal-bp-3200-3700/failures.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-3200-3700/scores.json](cal-bp-3200-3700/scores.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-3200-3700/summaries.json](cal-bp-3200-3700/summaries.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-3200-3700/projection.json](cal-bp-3200-3700/projection.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-3700-4200/training.json](cal-bp-3700-4200/training.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-3700-4200/preparations.json](cal-bp-3700-4200/preparations.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-3700-4200/operations.json](cal-bp-3700-4200/operations.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-3700-4200/folds.json](cal-bp-3700-4200/folds.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-3700-4200/predictions.json](cal-bp-3700-4200/predictions.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-3700-4200/failures.json](cal-bp-3700-4200/failures.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-3700-4200/scores.json](cal-bp-3700-4200/scores.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-3700-4200/summaries.json](cal-bp-3700-4200/summaries.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-3700-4200/projection.json](cal-bp-3700-4200/projection.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-4200-4700/training.json](cal-bp-4200-4700/training.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-4200-4700/preparations.json](cal-bp-4200-4700/preparations.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-4200-4700/operations.json](cal-bp-4200-4700/operations.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-4200-4700/folds.json](cal-bp-4200-4700/folds.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-4200-4700/predictions.json](cal-bp-4200-4700/predictions.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-4200-4700/failures.json](cal-bp-4200-4700/failures.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-4200-4700/scores.json](cal-bp-4200-4700/scores.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-4200-4700/summaries.json](cal-bp-4200-4700/summaries.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-4200-4700/projection.json](cal-bp-4200-4700/projection.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-4700-5200/training.json](cal-bp-4700-5200/training.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-4700-5200/preparations.json](cal-bp-4700-5200/preparations.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-4700-5200/operations.json](cal-bp-4700-5200/operations.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-4700-5200/folds.json](cal-bp-4700-5200/folds.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-4700-5200/predictions.json](cal-bp-4700-5200/predictions.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-4700-5200/failures.json](cal-bp-4700-5200/failures.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-4700-5200/scores.json](cal-bp-4700-5200/scores.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-4700-5200/summaries.json](cal-bp-4700-5200/summaries.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-4700-5200/projection.json](cal-bp-4700-5200/projection.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-5200-5700/training.json](cal-bp-5200-5700/training.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-5200-5700/preparations.json](cal-bp-5200-5700/preparations.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-5200-5700/operations.json](cal-bp-5200-5700/operations.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-5200-5700/folds.json](cal-bp-5200-5700/folds.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-5200-5700/predictions.json](cal-bp-5200-5700/predictions.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-5200-5700/failures.json](cal-bp-5200-5700/failures.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-5200-5700/scores.json](cal-bp-5200-5700/scores.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-5200-5700/summaries.json](cal-bp-5200-5700/summaries.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/cal-bp-5200-5700/projection.json](cal-bp-5200-5700/projection.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/comparison.json](comparison.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/comparison-publication.json](comparison-publication.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/ppe-sensitivity.json](ppe-sensitivity.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/ppe-sensitivity-publication.json](ppe-sensitivity-publication.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/admissibility.json](admissibility.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/admissibility-publication.json](admissibility-publication.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/flink-source-panels.json](flink-source-panels.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/flink-source-publication.json](flink-source-publication.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/flink-nordic.json](flink-nordic.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/flink-nordic-publication.json](flink-nordic-publication.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/love-counting-uncertainty.json](love-counting-uncertainty.json), [reports/science/pollen-reconstruction/nordic-coupled-workflow/love-counting-uncertainty-publication.json](love-counting-uncertainty-publication.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
