# Krageholm geometry and wind sensitivity

For the same 95 selected native samples and fixed Betula–Poaceae panel, substituting a static circle equivalent to 186 ha for the workbook's 837 m radius changes conditional cover by at most **0.10518 percentage points**. This is a declared geometry sensitivity; it does not authenticate the historical basin, sampled core, shoreline date or original paper input selection.

The native capture contains 96 samples from Neotoma dataset 23013, collection unit 16622. The selected Giesecke 2014 MADCAP chronology is native calibrated BP profile 13366, referenced to AD 1950. One point age lies outside the fixed half-open 0–11,700 Cal BP domain, leaving 95 selected samples in 24 of 25 windows. The empty window remains a refusal. Raw age bounds, including two negative younger bounds, remain unchanged in the private source account. The workbook's 96-sample claim is a separate identity assertion.

The 186 ha statement in [Sugita and colleagues' CAA paper](https://proceedings.caaconference.org/files/2007/125_Sugita_et_al_CAA2007.pdf), printed page 388, motivates an analyst-declared circle of radius 769.452 m. This run reuses the retained native captures and the previously checked documentary statement; it does not restore the original PDF or establish a historical geometry match. Both scenarios retain wind 3 m/s, diffusion 0.12, turbulence 0.25, the 100 km outer land annulus, PPE 5.106/1 with SD 0.303/0, and the original literal two-taxon observations.

Each supported window in the original geometry report records conditional counting, shared-PPE and total covariance separately. That original report withholds a paired standard error because it does not supply cross-scenario covariance. The derived [paired covariance account](paired-covariance.json) now supplies that covariance through the maintained public joint fixed-site API, using the same source observations and the declared PPE scenario below. These remain conditional model quantities, with no measured vegetation accuracy, significance or empirical coverage claim.

The [aggregate results](report.json) retain all 25 windows. The [source and execution account](source-account.json) binds the frozen plan, actual native exit, output hashes and independent checks. Four factors agree with independently derived analytical circle-lens integration within 7.13 × 10⁻¹¹; 816 Decimal checks of cover, covariance, standard errors and contrasts agree within 1.44 × 10⁻¹⁶ against a 2 × 10⁻¹³ tolerance. The independent method uses the same Python/SciPy runtime and supplies no original-R or historical reconstruction equivalence.

The maintained producer is `reports/science/krageholm-static-geometry-sensitivity/qualify.py`. Its CLI accepts `--source-root` for the exact retained packet and `--output-root` for a fresh destination. Five source files are pinned in its custody manifest. Individual source ages, depths, counts and sample identities remain private; this account publishes derived aggregates and execution provenance, without assigning redistribution rights to historical source archives. Existing native Neotoma attribution and analytical-use scope remain distinct from the workbook's historical NR restriction.

## Shared count and PPE covariance

The derived calculation pairs the same pooled literal-panel counts and sample membership across both geometries in each of the 24 occupied windows. It retains one multinomial count support per window, reuses each count support across the two geometries, and declares counting independence between disjoint windows. That declaration does not establish environmental independence. The same PPE latent parameters are shared across all windows and geometries. Count–PPE cross-covariance is zero under declared working independence.

The PPE covariance is an **analyst-declared conditional scenario**: it reuses the original input SD magnitudes 0.303 and 0, squares them on the diagonal, and supplies no new estimate or calibration of PPE uncertainty. The zero-variance Poaceae axis requires zero cross-covariance for a positive semidefinite matrix. Original marginal covers and covariance matrices agree within the unchanged 2 × 10⁻¹³ tolerance. The 48 result vectors yield 96 result axes, 24 distinct count supports and full count, PPE and total covariance matrices, including shared PPE between windows.

The alternative-minus-reference conditional standard errors range from **0.001525 to 0.006552 percentage points**. Treating the two geometries as independent would produce standard errors 372–2,721 times larger for these source and parameter choices; this is an independence counterfactual, not a significance test. The maximum mean change remains 0.10518 percentage points. The empty window remains a refusal, and no chronology posterior, geometry probability distribution or historical basin authentication has been supplied.

An independent implementation uses 50-digit Decimal arithmetic, explicit two-taxon quotient derivatives and fixed-total multinomial covariance. It checks all 96 × 96 covariance entries, all 48 × 48 contrast entries, covers, Jacobians and conditional paired standard errors: **39,552 scalar comparisons**, maximum absolute difference 2.43 × 10⁻¹⁵ against the unchanged 2 × 10⁻¹³ tolerance. It imports neither the reconstruction engine nor NumPy, while sharing the interpreter and source numbers. Ten public-API negative controls retain refusals for incompatible count supports, panels, chronology, windows, parameter identities and invalid counts.

The maintained derived producer is `reports/science/krageholm-static-geometry-sensitivity/paired_covariance.py`, with `--source-root` for its exact nine-file retained source packet and `--output-root` for an absent, separate artifact destination. Its [source and execution account](paired-covariance-source.json) binds the protocol, sources, native receipts, independent review and maintained output equality. Detailed joint matrices and native membership remain private. This calculation supplies a conditional paired count/PPE contrast; it does not establish empirical interval coverage, source-use permission, a time-varying basin reconstruction or completed chronology and geometry uncertainty propagation.

## Fixed-radius wind sensitivity

A separate [wind account](wind-sensitivity.json) keeps the same 95 samples, literal Betula–Poaceae panel, 837 m receiving circle, 100 km land annulus, diffusion 0.12, turbulence 0.25 and PPE scenario fixed. It compares analyst-declared winds of **1.5 and 6 m/s** with the retained assumed 3 m/s baseline. These are twofold sensitivity choices, not measured historical winds, fitted parameters or a selected best model.

| Fixed wind compared with 3 m/s | Betula conditional cover change across 24 windows | Conditional paired SE |
| --- | --- | --- |
| 1.5 m/s | −15.03 to −2.57 percentage points | 0.195–0.989 percentage points |
| 6 m/s | +2.35 to +9.50 percentage points | 0.0314–0.581 percentage points |

Poaceae changes by the opposite amount in this closed two-taxon panel. All 25 window slots are retained; the empty slot remains refused. No target vegetation measurement or withheld pollen outcome was scored. The range of changes is a scenario response, not an accuracy or uncertainty interval. The size of an analyst-chosen wind change cannot select a true wind or validate either basin geometry.

The actual native calculation evaluates four new response tuples, two fall speeds at each alternative wind, and reuses only the two exact previously qualified nominal factors. The original source packet, independent baseline factor records and all 24 baseline marginal cover/covariance results agree. No baseline quadrature, old radius reconstruction or R run was repeated. A separate analytical circle-lens integral checks the four new factors, agreeing within 7.52 × 10⁻¹¹ under the unchanged 2 × 10⁻⁸ absolute plus relative comparison tolerance. Production instead averages angular fractions across receiver offsets. Both share source assumptions and Python/SciPy; agreement does not authenticate historical wind.

The public joint fixed-site API retains 72 result vectors and 144 closed-panel axes. Each occupied window has one shared count support across all three winds; the same declared PPE parameters span all windows. Disjoint fixed-point windows are assumed counting-independent, and count–PPE covariance is assumed zero. The full matrices and 96 alternative-minus-nominal contrast axes remain private. The [conditional covariance derivation](../nordic-static-basin-scenarios/joint-uncertainty-method.md) describes this first-order shared-latent model. Fixed wind scenarios do not supply a probability distribution for wind or propagate chronology and dated-basin uncertainty.

An independent standard-library Decimal50 implementation checks **97,392 scalar values**, including every 144 × 144 covariance block and 96 × 96 contrast block, covers, Jacobians and conditional paired standard errors. Maximum absolute discrepancy is 2.20 × 10⁻¹⁶ against the unchanged 2 × 10⁻¹³ tolerance. Thirteen actual negative controls refuse incompatible count/parameter/chronology support, invalid counts or measurement masks, and zero, negative or nonfinite wind. The original source exclusions, diagonal PPE assumption and all effect directions remain visible; no empirical confidence coverage or significant-difference claim follows.

The maintained report CLI is `reports/science/krageholm-static-geometry-sensitivity/wind_sensitivity.py`. It accepts `--source-root` for the exact nine-file retained source packet and `--output-root` for an absent separate artifact destination. Two actual CLI executions through an isolated source bootstrap reproduced the public report, private matrices and engine-origin records byte for byte against the original independently checked calculation. Seven focused custody tests, strict typing of producer/test, and configured Ruff/format passed. The [wind source account](wind-sensitivity-source.json) preserves the actual plans, terminal receipts, source/runtime identities and comparison evidence. Individual native counts, ages, depths and sample identities remain private.

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  .venv/bin/python \
  reports/science/krageholm-static-geometry-sensitivity/wind_sensitivity.py \
  --source-root /path/to/retained-krageholm-source \
  --output-root artifacts/science/krageholm-wind-replay
```

This extends conditional transport sensitivity only. Source core/basin correspondence, historical wind justification, chronology uncertainty, original selected membership, intended-use rights and independent qualified review remain separate acceptance.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Same 95 selected samples and literal two-taxon panel: two fixed geometries differ by at most 0.10518 percentage points. A declared count/PPE scenario preserves shared counts across alternatives and shared PPE across windows, producing conditional paired SE 0.001525–0.006552 percentage points. Same837m source geometry with declared1.5/6m/s winds vs assumed3m/s changes conditional Betula by-15.03to-2.57/+2.35to+9.50percentage points; source95samples and24occupied+1empty slots preserved, shared-count/PPE covariance retained across3winds.

**Unsupported claim.** Historical Krageholm reproduction, accepted time-varying geometry, field vegetation accuracy, significant paired difference or empirically calibrated uncertainty. Estimated historical wind, model selection by scenario magnitude, wind-distribution uncertainty or fullLCI-030physical admission.

**Actual verification performed.** Original lens-factor and 816-scalar audit retained. Actual public joint API and independent Decimal50 quotient/multinomial implementation agree over 39,552 scalar comparisons within 2.43e-15 <=2e-13. Maintained producer report and private matrix match byte for byte; 33 joint API tests, ten negative API controls, seven custody tests, configured Ruff/format and strict typing pass. Four new wind response tuples independently lens-checked (max7.52e-11);97,392Decimal50 cover/Jacobian/covariance/paired-SE comparisons max2.20e-16<=2e-13.13actual negative controls refuse. Original/ref/replay3products byte-identical;7custodytests,strict2,Ruff/formatpass;45engine origins bound to copied5243source.

**Remaining input or review.** Two static geometries are analyst-declared alternatives. Historical basin/core correspondence and time-specific geometry remain unauthenticated; a conditional shared-count/PPE scenario now supplies paired covariance without a geometry or chronology probability distribution. Wind1.5/6m/s alternatives are declared assumptions, not measured historical winds or a wind uncertainty distribution. Resolver: Krageholm source custodian and independent chronology, historical-basin and statistical reviewer Reopen when: Source-qualified original core, dated basin geometry, chronology uncertainty and parameter/use terms, plus independent review of the declared joint dependence model.

**Cause category.** data|assumption|comparability|access/rights|qualified review

**Consequence.** Use conditional paired count/PPE contrasts under explicit shared-support and independence assumptions, preserving source scope and the empty-window refusal. PPE SD 0.303/0 is a declared scenario, not newly estimated or calibrated uncertainty. Treat wind effects as conditional responses under fixed analyst scenarios, not accuracy, significant change or parameter-selection evidence.

**Precise next acceptance route.** Authenticate original core, dated geometry and intended-use terms; supply and review chronology/geometry uncertainty and cross-profile parameter authority before historical, empirical coverage or joint ensemble claims. Supply source-supported wind and transport authority, or independently review a prospectively declared new profile; fixed scenarios do not estimate historical wind.

**Negative or refused result.** One source point outside the domain; one of 25 windows remains empty. Alternate chronologies, overlapping support, incompatible counts/panels/parameter identities and invalid count inputs are refused. No historical basin or empirical uncertainty admission. Wind alternatives retain oneemptywindow and all effect directions; invalid0/negative/nonfinitewind refuses. No calibrated interval or historical wind admission.

**Matched denominator.** 96 native samples; 95 selected in 24 of 25 slots; two taxa and two fixed geometries; 48 vectors, 96 axes, 24 distinct count supports; 39,552 independent scalar comparisons. Wind extension reuses same95selected/96native samples and24occupied+1empty slots;3fixedwinds/72vectors/144axes/24count supports/96contrast axes;4newresponse tuples and2retainednominalfactors.

Retained evidence: [docs/report/pollen-reconstruction/krageholm-static-geometry-sensitivity/report.json](report.json), [docs/report/pollen-reconstruction/krageholm-static-geometry-sensitivity/source-account.json](source-account.json), [reports/science/krageholm-static-geometry-sensitivity/source-custody.json](../../../../reports/science/krageholm-static-geometry-sensitivity/source-custody.json), [docs/report/pollen-reconstruction/krageholm-static-geometry-sensitivity/paired-covariance.json](paired-covariance.json), [docs/report/pollen-reconstruction/krageholm-static-geometry-sensitivity/paired-covariance-source.json](paired-covariance-source.json), [reports/science/krageholm-static-geometry-sensitivity/paired-covariance-protocol.json](../../../../reports/science/krageholm-static-geometry-sensitivity/paired-covariance-protocol.json), [docs/report/pollen-reconstruction/krageholm-static-geometry-sensitivity/wind-sensitivity.json](wind-sensitivity.json), [docs/report/pollen-reconstruction/krageholm-static-geometry-sensitivity/wind-sensitivity-source.json](wind-sensitivity-source.json), [reports/science/krageholm-static-geometry-sensitivity/wind-protocol.json](../../../../reports/science/krageholm-static-geometry-sensitivity/wind-protocol.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
