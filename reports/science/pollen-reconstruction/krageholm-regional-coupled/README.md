# Fixed Krageholm background with two local training sites

## Published PPE reference added

The [Wieczorek and Herzschuh (2020) paper](https://essd.copernicus.org/articles/12/3515/2020/)
and [PANGAEA.922661 data](https://doi.org/10.1594/PANGAEA.922661) are now explicitly
consumed as an attributed European parameter reference. The
[110-row reference and source account](../../../../data/validation/pollen-productivity/wieczorek-herzschuh-2020/README.md)
retain both author datasets, original cell locators, missing values and CC BY 4.0
attribution. [The exact comparison](nonnegative-cover/ppe-source-comparison.json)
binds the deposited values to the separately sourced executed inputs.

| Parameter source | Betula RPP | Uncertainty as reported | Ulmus RPP |
| --- | ---: | --- | ---: |
| Executed LANDCLIM working profile | 5.106 | SD label 0.303 | 1.27 (SD label 0.05) |
| 2020 Europe v1 | 5.6725 | SE 0.33503914 | Missing; n = 0 |
| 2020 Europe v2 | 4.94 | SE 0.44296664 | Missing; n = 0 |

The deposited European sets provide both taxa's fall speeds, but not Ulmus RPP
or SE. Their SE values describe compiled means and do not supply a population SD
or cross-taxon covariance matrix. Original-study metadata supports a more precise
local source/model choice; the harmonised Northern Hemisphere mean cannot silently
replace the missing local entry. The data source is useful without claiming that
it completes this two-taxon parameter configuration.

The completed 54-score and 55,296-slot results below retain their original
LANDCLIM/PANGAEA.937075 working parameters. No parameter substitution or new
model execution is claimed for this intake. It narrows the remaining PPE work
to source/model applicability, a justified Ulmus choice and the uncertainty law.

## Complete six-window comparison and uncertainty

The corrected analysis was executed at clean source
`dbcc4c3435da29d4e066fc34774d3118c46eaf32` on 14 November 2026. It
uses the same previously exposed BOKE, BUS and SOLSOE83 targets in six windows,
with KRAG regional-only. Every local analytical draw uses the declared
`clip-and-renormalize` rule before spatial transfer; raw signed diagnostics remain
available. All-zero/all-negative surviving mass fails explicitly. Missing support
is never turned into zero.

All **54 requested nominal method cells are predicted and scored**, with zero
refusals. Predictions are frozen and read back before exposed target counts are
opened for score diagnostics. The direct counterpart uses the same two training
places, taxon axis and spatial weights. These are 18 target–period folds at
**three physical places**, not 18 independent sites.

The [complete machine account](nonnegative-cover/development-result.json),
[all 54 matched score rows](nonnegative-cover/matched-scores.json) and
[independent verification](nonnegative-cover/independent-verification.json)
retain method/window/target denominators, predictions, observations, MAE, total
variation and Hellinger loss. The table uses percentage-point MAE; for this
closed two-taxon axis it equals percentage-point total variation. A positive gain
means lower LRA error.

| Transfer rule | LRA error (pp) | Matched direct error (pp) | Gain (pp) |
| --- | ---: | ---: | ---: |
| Equal weights | 14.6893 | 18.1907 | 3.5014 |
| Nearest site | 16.4734 | 18.7664 | 2.2929 |
| Inverse squared distance | 17.7880 | 22.0492 | 4.2613 |

The mean gain does not apply to every window or method/target combination.
Each cell below is LRA / matched direct MAE in percentage points:

| Window (cal BP) | Equal weights | Nearest site | Inverse squared distance |
| --- | ---: | ---: | ---: |
| 2700–3200 | 6.2165 / 7.0397 | 9.6838 / 10.4269 | 8.2295 / 8.8497 |
| 3200–3700 | 8.5600 / 9.5359 | 9.2395 / 9.6030 | 10.6809 / 11.6976 |
| 3700–4200 | 21.9309 / 28.0976 | 24.1163 / 28.0976 | 26.7621 / 33.6625 |
| 4200–4700 | 20.3827 / 27.7508 | 22.1592 / 27.7508 | 24.4850 / 33.6003 |
| 4700–5200 | 26.1494 / 34.3486 | 28.7455 / 34.3486 | 31.6740 / 41.7129 |
| 5200–5700 | 4.8963 / 2.3715 | 4.8963 / 2.3715 | 4.8963 / 2.7723 |

In particular, **5200–5700 cal BP is worse for all three methods**. Nearest-site
Solsø is also worse when averaged over the six windows: 6.8520 pp for LRA versus
5.6551 pp for matched direct pollen. All these negative results remain in the
complete comparison; no model is selected using a hidden successful subset.

### Uncertainty across every eligible fold

The [executed all-window protocol](nonnegative-cover/all-window-uncertainty-protocol.json)
extends the original conditional law to all 18 folds. It shares 24 owner/window
count streams and one productivity vector per replicate, preserving cross-fold
and cross-window dependence. All **18 × 3 × 1,024 = 55,296 method/draw slots**
are defined; every method has all 18 folds jointly available in all 1,024 draws.
No failed replicate is dropped or imputed. Historical signed refusals remain
separate rather than being rewritten as successes.

Scores are evaluated within each draw, then averaged equally over all 18 folds.
The central 95% ranges below are empirical ranges of paired gains under the
specified count/PPE working law, **not field confidence intervals**, independent
site/block uncertainty, posterior intervals or calibrated coverage.

| Transfer rule | Mean LRA error (pp) | Mean direct error (pp) | Mean gain (pp) | Central 95% paired-gain range (pp) |
| --- | ---: | ---: | ---: | ---: |
| Equal weights | 14.6761 | 18.2079 | 3.5317 | 2.5929–4.4047 |
| Nearest site | 16.4445 | 18.8749 | 2.4304 | 1.3868–3.3898 |
| Inverse squared distance | 17.7390 | 22.0509 | 4.3119 | 2.9889–5.5644 |

The producer completed in 37.00 s with 479,461,376-byte peak RSS and
42,171,533 output bytes; the maintained observer completed in 15.62 s. Both stay
within the prespecified 600 s / 1.5 GiB / 96 MiB limits. The observer binds 221
source files, 24 owners and all 54 nominal references. A separate fresh
Fraction/scalar/RNG/covariance/quantile audit verifies every replicate slot;
its maximum absolute discrepancy is 8.55 × 10⁻¹⁵. Exact original identities,
complete inputs, draws, predictions, summaries and failed attempts are retained
through the existing scientific recovery archive.

The maintained producer can reproduce the declared calculation after the exact
pinned original and adjusted-reference inputs are recovered. Use the recorded
calculation source and a fresh owning `artifacts/` destination, then run the
maintained `predictive_uncertainty.study` and `predictive_uncertainty.observation`
modules with the same protocol path. The protocol keeps the original artifact
input identities; changing its path for a fresh run creates a new receipt rather
than relabeling this execution. The observer requires the producer and checking
source epoch to agree.

### Installed behavior and remaining scientific scope

[Fresh wheel/sdist verification](nonnegative-cover/installed-verification.json)
passes at the same source. All eight archives have version `0.1.9.dev2958`.
Four isolated environments cover wheel/sdist × base/optional LRA, with confined
noneditable imports, source payload/RECORD/legal checks, both requested clipping
examples, zero-mass refusals, explicit-policy LOVE execution, raw diagnostics,
saved contracts, synthetic host execution/reopening and both CLI entry points.
Base installs preserve the missing-engine refusal. This is installed software
qualification, not a new native R or physical-field execution.

The conditional count/PPE model still fixes the two-taxon denominator, point
chronologies, saved finite kernels, static basins and parameter transfer. BOKE
with KRAG background is a source candidate; its core/basin crosswalk, justified
physical/time support and source-specific denominator/parameter-use decisions
remain outstanding. No compatible independent measured-vegetation pair or
unexposed confirmation cohort is newly admitted. Final accuracy criteria must be
reviewed and frozen before new outcomes. Original historical-paper reproduction
and qualified scientific acceptance remain open wherever their inputs or verdicts
are absent. The calculations above do not close those separate scientific claims.

## Full pilot source assessment

The [Bökesjön/Krageholm pilot assessment](../bokesjon-pilot/README.md) now checks
the full native taxon panels, public core/chronology/rights metadata, parameter
coverage and independent-reference availability for 2700–3200 cal BP. It preserves
explicit workbook zeros, sparse native omissions and distinct source denominators.
The two-taxon calculation above is unchanged; a full forest/open/cereal profile,
qualified physical decisions and measured vegetation accuracy remain unadmitted.

## Initial nonnegative-cover comparison

The explicit `clip-and-renormalize` assumption sets negative LOVE cover to zero
and closes the surviving cover to one before spatial averaging or uncertainty
summaries. An all-zero or all-negative result fails because it has no positive
mass to normalize. Signed equation outputs and outlier diagnostics remain
available. Clipping does not establish true taxon absence.

The [adjusted comparison](nonnegative-cover/result.json), executed at source
`1f25f44fc6dfab882e2bbac9b7e707a6402b7469` on 14 November 2026, reuses the
authenticated original exposed inputs. Each derived experiment explicitly sets
`request_template.configuration.love.analytical_cover_policy` to
`clip-and-renormalize` and calls the maintained
`prepare_experiment_predictions` API. The captured experiment files, counts,
original protocol and historical results are unchanged. No scores were opened
for this nominal comparison.

| Estimator | Held-place folds | Predictions | Failed method slots |
| --- | ---: | ---: | ---: |
| Historical signed source output | 18 | 9 | 45 |
| Explicit clipping and normalization | 18 | 54 | 0 |

All six windows now yield nine predictions each. Independent byte/role and
scalar checks verify target exclusion, the bound assumption, all 36 native
cover rows in 18 reused native products, spatial averaging and forward pollen.
Maximum closure difference is `1.11e-16`; no adjusted row is missing. Raw
negative cover remains visible in 28 native rows, including 12 products at
the selected ring. These are three places across six windows, not 18 independent
sites or an accuracy evaluation. The original 45 refusals remain historical
evidence of the signed estimator.

A separate count/PPE bootstrap applies the assumption to each local draw before
averaging. It retains its original three nominally eligible folds in
2700–3200 cal BP; it does not resample all 18 nominal folds. All 1,024 draws
are now defined for each of those three targets and each of the three methods:
9,216 defined method-replicate slots, with all 1,024 replicate identities jointly
defined. The historical signed bootstrap below had 525 jointly defined draws.
Independent source binding verifies 141 files and 24 owner/windows; the rational
observer verifies all 9,216 slots, shared draws, summaries and loss accounting.
Its post-freeze diagnostics concern already exposed outcomes and do not supply
field accuracy, calibrated coverage or untouched confirmation.

The [uncertainty reproduction protocol](nonnegative-cover/uncertainty-protocol.json)
has the exact bytes used in the recorded artifact protocol. With the retained
source files available and unchanged, run the maintained producer and observer
in an artifact-owned environment, directing products and verification to fresh
root `artifacts/` paths. The comparison records the executed protocol, result,
verification and source-input identities. Scripts calling the nominal API must
use `if __name__ == "__main__"` on spawn platforms.

Fixed chronology, prescribed static basins, the two-taxon denominator,
regional representativeness and parameter transfer remain conditional. This
calculation changes no physical-core admission or qualified scientific verdict.
The original account below records source-raw calculations; its negative-cover
refusals describe that retained estimator.

## Historical signed-cover calculation

A permanently regional Krageholm source permits nine conditional held-place
pollen predictions in the **2700–3200 cal BP** window. The other five windows
retain all **45** failed method dispositions: at least one required local
analytical LOVE result is outside the nonnegative closed-composition domain.
The result supports this declared calculation, not field accuracy or a
reproduced historical reconstruction. [Compact result](result.json).

The [prospective protocol](protocol.json) fixes Betula/Ulmus, six half-open
500-year windows, three target places and three spatial baselines. KRAGMJNY
(dataset 23013 / collection unit 16622) stays regional-only in every fold. BOKE, BUS and
SOLSOE83 each become the excluded target once per window, leaving **two** local
training places. Complete transitive identity families are formed before role
selection; cross-role families are refused. KRAG has no invented local rings,
local-predictor role or target score.

The [closed KRAG source audit](../krageholm-regional-source-support/README.md)
binds all 96 original owners, 19 selected owners and the explicit calibrated
chronology 13366. Collection reference 13365 and both native default flags remain
separate. Five missing Ulmus entries outside the requested windows remain
missing. Small-core integer counts and exact source-window fingerprints reuse
qualified source epochs 1988f522 / 33d45ecf, with measured support counts BOKE 20,
BUS 21 and SOLSOE83 18. That is 59 saved qualified supports, not a fresh literal
small-core owner-ID reconciliation. The two-taxon panel is not a verified full
terrestrial pollen denominator.

KRAG's 837 m static radius is a declared regional geometry hypothesis; the separate
186 ha statement is not harmonized with it. The small-site radii 80 / 69 / 89 m,
source-compatible analytical GPM-neutral operator, 3 m/s wind and fixed PPE/fall
speeds remain prescribed. All land beyond the modeled shore is assumed
terrestrial. Abundance normalization and regional representativeness remain
assumptions; closed pollen does not identify the regional/local abundance-density
ratio. Chronology, geometry, PPE covariance and model uncertainty are not
propagated here. Historical NR/R markers and current local analytical use do not
supply new redistribution rights, dated shoreline evidence or field permission.

Preparation closes and authenticates all six prediction products before any
score API opens its outcome inventory. Shared native evidence carries fixed
identities and assumptions; quantitative all-source projections stay in separate
accounting. Per-fold source admission and quantitative ancestry are checked,
with guarded I/O software controls. This is previously exposed development,
without OS-enforced isolation or independent dynamic filesystem tracing.

| Window, cal BP | Scored method dispositions | Failed method dispositions |
| --- | ---: | ---: |
| 2700–3200 | 9 | 0 |
| 3200–3700 | 0 | 9 |
| 3700–4200 | 0 | 9 |
| 4200–4700 | 0 | 9 |
| 4700–5200 | 0 | 9 |
| 5200–5700 | 0 | 9 |

No clipping or single-predictor fallback rescues the 15 failed target folds.
All 36 native fit references to 18 distinct requests remain inspectable,
including 24 negative final-cover occurrences among those references. Those
occurrences are not 24 independent fits. Both signed local-ring outputs and
refusal reasons survive.

The three methods now differ because two local predictors are available.
Mean absolute fraction error over the three scored targets is shown below;
with two taxa this equals total variation. These values describe one window
and do not establish a general method ranking.

| Method | Mean error on three scored targets |
| --- | ---: |
| Training mean | 0.062165 |
| Nearest site | 0.096838 |
| Inverse squared distance | 0.082295 |

The [earlier small-proxy study](../nordic-coupled-workflow/README.md) retained
30 scored / 24 failed method slots and one local predictor per fold. Regional input
and available local information change together in this new study. Comparing
these different scored populations cannot isolate a basin-size effect or show
a general improvement. Neither study measures vegetation accuracy.

The maintained command owner is
`bijux_pollenomics_dev.essd_reproduction.nordic_coupled.cohorts.krageholm_regional`,
with separate `materialize`, `prepare` and `score` operations. All three ran once
at source 43995b359425da99ce602e820b0ee2b7e1319e76, using the shared environment,
`-B`, bytecode suppression and all five numerical thread settings at one. Actual
commands, terminal status and resource facts are retained under
`artifacts/physical-core/krageholm-regional-coupled/native-execution/`.

| Operation | Process seconds | Peak RSS, bytes |
| --- | ---: | ---: |
| Source projection | 0.85 | 76,087,296 |
| Prediction preparation | 33.92 | 187,940,864 |
| Scoring | 1.33 | 75,235,328 |
| Independent observation | 0.590 | 31,506,432 |

All prospective resource limits pass. The independent observer at
a98bc99a0d43fba700b42475f8f6aa40ca06039c rechecks source membership, roles,
REVEALS rounding, signed LOVE, both training predictors, interpolation, forward
pollen and MAE/total variation for all 54 outcomes. Its maximum scalar difference
is 1.1102230246251565e-16, **conditional on saved native kernels and distances**.
It makes zero engine calls or fits, and does not independently certify the
continuous kernel, geodesy or physical truth. Raw products and the 2290-byte
independent check remain under their owning `artifacts/` paths in result.json.

Three earlier observer attempts stopped on incorrect metadata assumptions:
a relative artifact locator, independently sorted fold partitions and sorted
alias lists. Their literal failures remain preserved. Narrow committed repairs
retain the original producer bytes, parameters and numerical tolerances, with
separate producer/observer identities and unchanged-production Git checks.
An independent 8,322-leaf metadata comparison found no further mismatch. Final
qualification includes 151 independent controls, 86 affected host controls,
16 producer controls, the existing artificial default-profile fixture, and
configured Ruff/format/strict types. Earlier controlled scratch/import failures
remain distinct from scientific findings.

Regional representativeness, historical geometry/core equivalence, justified
parameter transfer, full uncertainty, measured vegetation and genuinely untouched
confirmation remain separate acceptance questions. This result closes neither
those questions nor the broader physical-validation outcome.


## Conditional count and PPE prediction uncertainty

The separate [prospective bootstrap protocol](predictive-uncertainty/protocol.json)
propagates the original fixed-total multinomial count law and whole-vector
nonnegative normal PPE draws through these saved finite kernels. It uses 1,024
replicates, seed 20261027, independent physical owner/window count streams and
one shared Betula/Ulmus PPE vector per replicate. The same allowed training
draws feed regional REVEALS, both signed local LOVE rings, interpolation and
forward pollen. Each fold excludes its target's counts and quantitative ancestry;
changing those counts leaves its predictions and allowed-input identities exact.
The two-taxon panel, source point ages, static geometry, distances and kernels
remain fixed. Source compatibility specifies a working law, not field calibration.

Only the nine originally successful method slots enter propagation; all 45 older
nominal refusals remain unchanged. Local final-ring domain failures are retained
for every replicate, without clipping or replacing a missing predictor. The
number of defined replicates is identical across the three spatial methods
because each still requires both local training compositions.

| Held target | Defined / 1,024 | Undefined fraction |
| --- | ---: | ---: |
| BOKE | 544 | 0.468750 |
| BUS | 594 | 0.419922 |
| SOLSOE83 | 860 | 0.160156 |
| All three targets jointly | 525 | 0.487305 |

All unconditional physical composition summaries therefore refuse. Saved
conditional means, population covariance and empirical 2.5/50/97.5 percentiles
summarize only the defined subset. The separately reported Monte Carlo standard
error estimates the conditional working-law expectation; it is neither the
finite ensemble spread nor uncertainty in field accuracy. Local signed covers
and both ring diagnostics remain available, including invalid unselected rings.

The direct counterpart uses the same two training count compositions and spatial
weights, without KRAG or PPE. Comparisons below use exactly the 525 common-defined
replicate IDs and equal weights across the three previously exposed targets.
MAE equals total variation on this two-component panel. The empirical ranges
are conditional training/working-model diagnostics, not predictive coverage,
credible intervals or evidence of general method superiority.

| Method | Physical mean MAE | Matched direct mean MAE | Physical minus direct MAE, mean | Empirical 2.5–97.5% contrast |
| --- | ---: | ---: | ---: | --- |
| Training mean | 0.062380 | 0.070176 | −0.007796 | [−0.010759, −0.005156] |
| Nearest site | 0.095547 | 0.102889 | −0.007342 | [−0.009359, −0.005318] |
| Inverse squared distance | 0.081528 | 0.087655 | −0.006128 | [−0.007994, −0.004343] |

The maintained producer ran once at
`d8886b48eb550282aa339c8a46d965bb12cac579`:

```bash
python -B -m bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty.study \
  --repository "$PWD" \
  --protocol "$PWD/reports/science/pollen-reconstruction/krageholm-regional-coupled/predictive-uncertainty/protocol.json" \
  --output "$PWD/artifacts/physical-core/krageholm-regional-coupled/predictive-uncertainty"
```

It used the shared environment, bytecode suppression and all five numerical
thread limits at one. Prediction members and their manifest were serialized,
authenticated and reopened before outcome diagnostics. Process time was 6.14 s,
peak RSS 195,379,200 bytes and all products/logs totaled 6,673,042 bytes, within
180 s / 768 MiB / 16 MiB. All nine nominal vectors matched the original absolute
1e-12 bound; 141 scientific files and 4,473 first-party Python/protocol files,
HEAD and raw index remained stable through the original producer/observer pair.

The first independent observer stopped solely on uppercase `Previously` versus
its lowercase diagnostic-scope label. Its literal failure is retained. A second
readback at the same committed source authenticated every original serialized
member, normalized that presentation string in memory only, and ran independent
`verification.sources.bind_sources` and `verification.audit`. It passed all
141 source bindings, 24 owners, three saved-kernel folds, nine nominal references
and 9,216 method-replicate slots, including RNG replay, scalar reconstruction,
admission, covariance, Monte Carlo errors, matched losses and complete population
accounting. Absolute 1e-13 / relative 1e-10 tolerances were unchanged. It took
2.28 s with RSS 81,461,248 bytes; the observer directory including its failed
attempt and successful logs/report totals 6,533 bytes. No predictions, draws,
source files or saved products were regenerated or edited. Subsequent source
normalizes the producer label to the observer's established lowercase spelling.

Raw products remain under
`artifacts/physical-core/krageholm-regional-coupled/predictive-uncertainty/`;
the independent result and both attempts remain under
`artifacts/verification/krageholm-predictive-uncertainty/`.
The producer result is 1,476 bytes, SHA256
`cb0e9db1f106296b8a29a72ef3d1ea1b585aeb42604b432111b02ee997e8584b`;
its 142,305-byte summary has SHA256
`185c89be761f081b70dbc51e8c582c6200fe09e6768fc0f4e84d4f1a34ae8ea2`.
The qualified nominal input reading still reuses the saved 59 small-core supports;
this study is not a fresh native-owner census. It does not propagate chronology,
basin history, kernel integration error, regional representativeness or an
empirically calibrated model-discrepancy law. It supplies no measured vegetation,
untouched confirmation or full physical-validation acceptance.


## Geographic Hellinger transfer with retained count and PPE uncertainty

The [geographic-transfer protocol](geographic-transfer/protocol.json) asks a new
question: can the Swedish BOKE/BUS local LOVE reconstructions and KRAG regional source
support a pollen prediction across the geographic gap to Danish SOLSOE83?
The partition holds the Swedish cluster together, including source-only KRAG,
and assigns Solsø to the other block. Every forecast requires its original
regional source and both original local sources. BOKE and BUS are refused
because their required sources include members of their held Swedish block;
no source is removed and no single-predictor fallback is introduced.

Solsø is admitted under the declared finite-footprint scenario: a 100 km source
extent, 1 km target extent, 20 km buffer and zero coordinate-error allowance.
The allowance is an optimistic diagnostic assumption, not measured positional
precision or a claim about empirical pollen source area. Both regional and local
sources face the same geographic check. An independent exact-rational WGS84
metric/path envelope certifies the admission and both refusals. Its conservative
additional joint coordinate-allowance margin exceeds 48 km for the admitted
case; this is a model sensitivity bound, not an empirical error estimate.

The new consumer projects the already qualified 1,024 same-index count/PPE draws
through Gaussian-weighted Hellinger spatial means at fixed 20 and 100 km scales.
Both signed source LOVE rings remain inspectable; only the original selected
ring 1 determines admission. Regional cover, local cover and PPE retain their
shared replicate index. The regional term is forward-weighted exactly once.
No inverse fit, kernel integration, random draw or original bootstrap ensemble
is rerun. The three nominal forward handoffs are recomputed only for
correspondence.
All three original nominal cover/pollen handoffs pass the unchanged absolute
1e-12 gate; maximum gaps are 5.55e-17 and 1.11e-16 respectively.

These are two **prescribed, unselected sensitivity profiles**. With two local
training places, an inner fit has one local predictor and cannot identify the
bandwidth. Solsø outcomes select neither scale. The distances to BOKE and BUS
are approximately 308 and 334 km, so this is a long-distance extrapolation.
The 20 km profile assigns almost all local weight to BOKE; at 100 km the BOKE
weight is 0.698786 and the BUS weight is 0.301214.

All inputs, admission, handoffs and new predictions are authenticated before the
single scoring-role access to Solsø's pooled observation: Betula 166, Ulmus 8,
N = 174, observed Betula fraction 0.954023. The original sources were previously
exposed; this sequencing does not establish a globally unread or untouched target.
No measured vegetation observation is available.

| Quantity, Solsø only | 20 km | 100 km |
| --- | ---: | ---: |
| Defined / total draws | 860 / 1,024 | 860 / 1,024 |
| Additional model refusals | 0 | 0 |
| Nominal predicted Betula pollen fraction | 0.864084 | 0.891744 |
| Nominal MAE = total variation | 0.089939 | 0.062279 |
| Nominal Hellinger distance | 0.114057 | 0.084215 |
| Nominal count-conditioned deviance | 15.531703 | 8.711265 |
| Conditional mean Betula pollen fraction | 0.864679 | 0.890546 |
| Conditional Betula pollen SD | 0.011373 | 0.010489 |
| Conditional Betula 2.5% / 97.5% draw quantiles | 0.842294 / 0.886154 | 0.869397 / 0.909919 |
| IID conditional-mean Monte Carlo SE | 0.000388 | 0.000358 |
| Conditional mean Hellinger distance | 0.113231 | 0.085320 |

Both profiles preserve all 164 inherited undefined draws, mass 0.16015625;
every unconditional physical composition summary refuses. Conditional moments
use the 860 defined draws, population covariance divisor and linear empirical
quantiles. The SD and draw quantiles describe the conditional training count/PPE
law. They omit target-count sampling, chronology, basin history and calibrated
model discrepancy, and are not calibrated prediction intervals for the observed
fraction. Monte Carlo SE concerns only the estimated conditional expectation.
With two taxa MAE equals total variation algebraically.

Six paired references per profile use exactly the same 860 IDs. Direct-pollen
references themselves are defined on all 1,024 IDs; their 164 rows excluded from
pairing are explicitly distinguished from undefined candidate predictions.
Positive values below mean the Hellinger profile is worse. These are means of
paired draw losses, not losses computed from mean compositions.

| Reference | 20 km mean Hellinger difference | 100 km mean Hellinger difference |
| --- | ---: | ---: |
| Physical training mean | +0.049658 | +0.021746 |
| Direct-pollen training mean | +0.031556 | +0.003645 |
| Physical nearest | -0.000000000054 | -0.027911 |
| Direct-pollen nearest | -0.019761 | -0.047672 |
| Physical inverse squared distance | +0.045692 | +0.017781 |
| Direct-pollen inverse squared distance | +0.027029 | -0.000883 |

Both Hellinger profiles are worse than the physical training mean and physical
IDW reference on this one target. No global ranking or new winner follows.
No defined draw assigns zero probability to a positive observed count. All six
target/scale dispositions survive: two admitted ensembles and four geographic
refusals. Geographic refusals are not invented bootstrap-domain failures. The
original 18 folds, 54 dispositions and 45 older nominal refusals remain unchanged.

The producer and independent observer both consumed committed source
`56c634d2b4a2857277310d18d3d0a06ce4a5a93a`, using the shared environment, `-B`,
bytecode suppression and all five numerical thread settings at one. Commands:

```sh
python -B -m bijux_pollenomics_dev.essd_reproduction.nordic_coupled.geographic_transfer.study --repository . --protocol reports/science/pollen-reconstruction/krageholm-regional-coupled/geographic-transfer/protocol.json --output artifacts/physical-core/krageholm-regional-coupled/geographic-transfer
python -B -m bijux_pollenomics_dev.essd_reproduction.nordic_coupled.geographic_transfer.observer --repository . --protocol reports/science/pollen-reconstruction/krageholm-regional-coupled/geographic-transfer/protocol.json --products artifacts/physical-core/krageholm-regional-coupled/geographic-transfer --output artifacts/verification/krageholm-geographic-transfer
```

Producer process 4.07 s / peak RSS 224,526,336 bytes and observer process 3.51 s /
222,232,576 bytes both pass the prospective 180 s / 512 MiB / 16 MiB bounds.
Final producer products occupy 4,179,940 bytes. All 4,540 tracked Python sources,
protocol, HEAD and index remain stable through both terminal runs. There is no
actual-run retry or post-run product edit. The independent check authenticates
141 source files, 24 accounting owners, three kernels and nine original nominal
vectors without rerunning the original numerical study. Separate 80-digit
Hellinger and scalar forward arithmetic verifies both 1,024-row projections;
independent geography, observation access, losses and all twelve paired
comparisons pass. The integrated 131 controls and configured lint, formatting
and strict types on all 25 changed Python files also pass.

Raw outputs are under
`artifacts/physical-core/krageholm-regional-coupled/geographic-transfer/`;
the 2,704-byte independent result is
`artifacts/verification/krageholm-geographic-transfer/verification.json`, SHA256
`eee212638683b5f913dadb2dd35143b18d675d5c49acde94a8d28d1a4c57f7c0`.
The 1,446-byte producer result has SHA256
`9a1de89af362a1df0a683c72bac758ed6523c5874bb3d098e31fd03e0bdd2d47`.
Resource logs are `artifacts/root/krageholm-geographic-transfer*.time.txt`.
Earlier synthetic fixture failures remain preserved; they are not failed actual
forecasts. This is a conditional exposed geographic-transfer experiment with
one admitted block. It supplies no generalization precision, field-calibrated
coverage, measured vegetation accuracy, original historical reproduction or
untouched confirmation.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** The explicit clip-and-renormalize profile predicts and scores all 54 nominal method cells across six windows and 18 target-period folds at three physical places. Its shared count/PPE working law defines all 55,296 method/draw slots (18 folds × 3 methods × 1,024 replicates). Historical signed-profile results remain nine predictions and 45 refusals. The separate geographic Hellinger study retains its historical signed-profile 860 defined and 164 undefined draws at Solsø; it has not been rerun with clipping.

**Unsupported claim.** Full forest/open/cereal cover, admitted physical inputs, historical-paper reproduction, measured vegetation accuracy, independent regional representativeness, chronology/basin/model-discrepancy uncertainty, calibrated coverage, untouched confirmation or qualified scientific acceptance.

**Actual verification performed.** The adjusted comparison and all-window uncertainty were executed at dbcc4c3435da29d4e066fc34774d3118c46eaf32. Independent nominal verification checked all 54 predictions, matched scores, target exclusion, per-local clipping and closure. Separate Fraction/scalar/RNG/covariance/quantile verification checked all 55,296 method/draw slots, with maximum absolute discrepancy 8.55 × 10⁻¹⁵. The maintained source observer checked 221 source files, 24 owners, 18 fold kernels and 54 nominal predictions. This presentation repair reads saved public accounts; it does not rerun these calculations. Earlier signed bootstrap and geographic-transfer verifications remain bound to their own source and conditioning events.

**Remaining input or review.** The two-taxon panel denominator, saved chronology and kernels, static basins, regional background and parameter transfer remain conditional. Clipping changes the reported cover quantity; uncertainty is computed after the same draw-wise transformation. Chronology, basin history and calibrated model discrepancy are not propagated. No compatible independent measured-vegetation pair or unexposed confirmation cohort is admitted. The separate signed-profile geographic sensitivity retains its finite-footprint and optimistic zero coordinate-error assumptions. Resolver: Source and field experts for physical/parameter comparability; analyst for the declared calculation and genuinely independent measurements. Reopen when: Source-owned geometry, chronology, parameter and denominator evidence or an eligible independent measured target supports a prospective analysis. A new geographic clipping study would require its own named protocol; do not relabel the historical signed study.

**Cause category.** assumption|comparability|data

**Consequence.** The negative-cover calculation blocker is resolved for the declared adjusted estimator. This is a conditional exposed two-taxon forward-pollen development comparison, not a score of reconstructed vegetation. Positive average gains do not imply a gain for every place, window or method.

**Precise next acceptance route.** Use the nonnegative-cover development result, all-window protocol and independent verification for the adjusted comparison. Preserve the historical signed and geographic accounts as distinct profiles. Qualify source-specific physical inputs, a supported taxon/denominator/parameter panel and compatible independent vegetation before claiming scientific accuracy or acceptance.

**Negative or refused result.** The adjusted nominal comparison has zero refused method cells and the declared count/PPE ensemble has no undefined method/draw slots. Zero surviving positive mass remains an explicit failure rule; no failed draw may be dropped or imputed. All three adjusted methods perform worse than matched direct pollen in 5200–5700 cal BP, and nearest-site Solsø is worse averaged across windows. Historical signed-profile 45 nominal refusals and 499/1,024 jointly undefined bootstrap replicates remain unchanged. The separate geographic study still refuses BOKE/BUS; both Solsø profiles retain 164/1,024 undefined draws and are worse than the physical training mean and IDW on their common 860 draws.

**Matched denominator.** Adjusted profile: three physical target places × six repeated windows = 18 folds; three methods give 54 nominal score cells. Shared uncertainty: 24 owner/window count streams and one shared PPE vector per replicate; 18 × 3 × 1,024 = 55,296 method/draw slots, with all 18 folds jointly defined for every replicate. Closed Betula/Ulmus panel and observed-pollen scores, not whole vegetation. Historical signed bootstrap uses exactly 525 common-defined replicate IDs; the separate geographic contrasts use 860 common IDs at one Solsø target with 174 grains on two taxa. These different events and denominators are not pooled.

Retained evidence: [reports/science/pollen-reconstruction/krageholm-regional-coupled/nonnegative-cover/development-result.json](nonnegative-cover/development-result.json), [reports/science/pollen-reconstruction/krageholm-regional-coupled/nonnegative-cover/matched-scores.json](nonnegative-cover/matched-scores.json), [reports/science/pollen-reconstruction/krageholm-regional-coupled/nonnegative-cover/all-window-uncertainty-protocol.json](nonnegative-cover/all-window-uncertainty-protocol.json), [reports/science/pollen-reconstruction/krageholm-regional-coupled/nonnegative-cover/independent-verification.json](nonnegative-cover/independent-verification.json), [reports/science/pollen-reconstruction/krageholm-regional-coupled/predictive-uncertainty/protocol.json](predictive-uncertainty/protocol.json), [reports/science/pollen-reconstruction/krageholm-regional-coupled/geographic-transfer/protocol.json](geographic-transfer/protocol.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
