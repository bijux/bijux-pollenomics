---
title: LRA Engine Integration
audience: contributor
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-09-12
---

# LRA engine integration

`bijux-pollenomics-lra` owns numerical REVEALS, analytical and optimized LOVE,
coupled reconstruction, exact-coordinate series and forward pollen deposition.
The canonical host owns source admission, chronology, taxa, experiment splits,
commands and product publication. The extension imports neither the host nor its
development toolkit. Its implementation is Python, NumPy and SciPy.

The supported Python facade is `bijux_pollenomics_lra.api`. Installed metadata
registers group `bijux_pollenomics.extensions`, name `lra`, target
`bijux_pollenomics_lra.api:extension_descriptor`. Loading checks installed identity
and compatibility; missing dependencies and incompatible implementations are
observable refusals. There is no standalone engine command or automatic fallback.

| Engine domain | Responsibility |
| --- | --- |
| `models` | Configuration, results, validated dimensions and errors |
| `dispersal` | Deposition factors and source-compatible LOESS curves |
| `reconstruction` | Regional/local equations, draws and forward observation model |
| `optimization` | Bounded solver, replay and convergence diagnostics |
| `workflows` | Stage composition and coordinate pairing |
| `provenance` | Input, backend and scientific content identity |
| `outputs` | Numerical serialization and byte checksums |
| `resources` | Versioned models, schemas and examples |

Tests mirror those responsibilities. Exact-source R tooling lives under
`tests/reference` and does not ship in the runtime wheel. The numerical core does
not write products. Result serialization is explicit; the host decides whether
an output is scientifically eligible for release.

The adopted calculations retain the explicitly named DISQOVER 0.9.14 source
profile. Source geometry conventions, analytical estimates outside physical
fractions, uncertainty omissions and optimizer failure are observable. A numeric
pairing coordinate is not a canonical source ID or an automatically inferred age.
Publication-specific multi-site aggregation requires its own verified profile.

Pollen and vegetation validation have different targets and scores. Holding every
target pollen sample out requires a spatial predictor and a forward observation
model; LOVE itself needs local pollen. Grouped folds and dependency closure guard
the training boundary. Synthetic recovery and R parity establish numerical
behavior; they do not establish ecological accuracy or qualified review.

`prepare_forward_inputs` constructs target-specific kernels and regional
deposition through the engine facade, without target pollen or a target count
total. Its corrected-matrix preparation profile is recorded separately from the
forward observation profile. The host retains the parameter, geometry, time and
training-source lineage; it never substitutes a training basin for target geometry.

Hatch/VCS, the workspace lock, Make/tox, test discovery and CI govern the package.
Its GPL license and source attribution are package-owned. Repository license
synchronization must not replace them with the host's Apache license. The
release matrix builds the optional engine alongside the host. Publication checks
bind staged distributions to the release revision and require a same-revision
actual-R certificate. Matrix inclusion and local build evidence do not establish
scientific acceptance or authorize publication.

A bounded C++ objective experiment agreed numerically with Python and R but did
not meet its predefined performance thresholds against prepared NumPy. That
kernel remains Python. This finding does not establish that every possible
native optimization is unsuitable; further native adoption requires measured
benefit, binding safety and platform evidence through the same Python facade.

## Host boundary

The host facade is `bijux_pollenomics.analysis.lra.api`; its `inputs`, `engine`,
`execution` and `outputs` packages have distinct owners and mirrored unit tests.
The CLI delegates to the same service. `validate-lra-input` verifies a declared
request and installed configuration; `run-lra` executes it and publishes a new
local exploratory bundle. Neither command grants source or scientific approval.

The request records sample/site identities separately from exact numeric pairing
coordinates. All source age intervals remain typed BP support. An explicit
`declared_bin_stationarity` decision identifies common time bins containing the
full support of every paired sample; matching a numeric key alone cannot
establish chronological compatibility. This is a declared modeling assumption,
not a chronology review verdict. Included/excluded sample identities must be
disjoint and unique.

Geometry records use metres and square metres, with explicit source references.
The optimized profile consumes terrestrial-to-ring area ratios; it needs
regional rings beyond the separately declared local `max_ring`. The analytical
profile does not apply partial terrestrial masks and refuses them. Arithmetic
checks do not independently verify source geometry. The optimized source
objective uses nominal PPE; its nested method manifest retains that source
limitation even when other stages draw PPE uncertainty.

Products retain source-file hashes, explicit omissions, numerical units, actual
installed engine identity, code/resource inventories, diagnostic files and
separate operational/scientific hashes. Source and code changes during a run
refuse publication. Before/after file inventories are mutation checks; they do
not attest Python objects already loaded in a long-lived process. Certification
uses fresh installed processes and pinned dependencies.

Product reopening and cache reuse belong to the host's output and execution
domains. `read_lra_product` checks the complete file inventory, request and
scientific identity graph, rejecting incomplete bundles, symlinks, unexpected
files and changed numerical bytes. An independently retained manifest digest
can identify an expected bundle; internal consistency alone does not establish
authorship or scientific approval.

Saved primary tables must agree with the request's taxa, numeric coordinates,
ring support, method and declared result units. Numeric fields reject malformed
or nonfinite values; source-defined empty SD/local-statistic cells remain missing.
Binary Monte Carlo arrays are byte-verified, without claiming a fresh numerical
recomputation. A final inventory check detects changes during reopening; returned
paths are not a promise that another process cannot subsequently change the files.

`run_lra_cached` revalidates source evidence and numerical configuration on every
call. The key includes the complete request, installed engine identity, host and
engine code/resources, Python/platform and dependency versions, and declared
numerical thread environment. Parameter, source-identity or implementation
changes select a different entry. A cache hit verifies the saved product before
returning it. Corrupt entries refuse without replacement; simultaneous writers
receive `lra_cache_busy` without polling. Interrupted writers may leave a lock
and staging directory for explicit recovery after checking that its owner has
stopped. The cache does not automatically infer that a lock is stale. This is a
local product cache; no distributed scheduling or measured batch throughput is
implied by this interface.

Directory publication requires an atomic no-replace operation on the destination
filesystem. The Linux and macOS paths use their native exclusive-rename
primitives; Windows uses its nonreplacing rename behavior. Unsupported systems
or filesystems refuse publication instead of falling back to a racy existence
check. Failed staging directories remain available for diagnosis. Local macOS
execution evidence does not certify the other operating systems.

The primitive contracts are documented by the
[Linux rename manual](https://www.man7.org/linux/man-pages/man2/renameat2.2.html)
and [Apple's rename flag definitions](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/sys/stdio.h).

## Source admission and experiment ownership

`analysis.lra.materialization` owns the source-to-request boundary. Its Neotoma
admission audit retains exact source cells, count units, chronology alternatives,
conflicts and per-sample refusals. Necessary numeric count eligibility does not
authorize taxon grouping, PPE, chronology or basin geometry. Source audits remain
separate products until those scientific requirements have actual evidence.

The private `analysis.lra.materialization.requests` facade projects explicitly
declared synthetic Neotoma fixtures into the existing `lra-request.v1` contract.
It requires synthetic origin and country inputs bound in the raw receipts, replays
the existing source normalizer across all normalized surfaces and reconciliation,
and binds every selected count cell and chronology claim to its source records. It
preserves zero, refuses missing or incompatible values and incomplete
denominators, retains the original evidence, and publishes through the shared no-
replace filesystem primitive. Request projection does not import the optional
numerical engine. Real or unspecified source provenance is refused; this facility
supplies no qualified taxonomy, chronology, PPE, geometry or empirical
reconstruction approval.

The shared `analysis.classification.events.assess_classification_eligibility`
service checks reviewed source/taxon membership without requiring positive pollen
detection. Zero, null and absent measurements remain distinct. This review
projection does not admit counts, chronology or an LRA run. Its current pinned
authority is Neotoma-specific and contains zero accepted mappings; the API cannot
create scientific approval or extend that authority to another source.

`analysis.lra_validation.experiments` owns training-fold reconstruction and
subsequent observation scoring. Its first profile is explicitly synthetic:
`prepare_experiment_predictions` runs the existing batch/cache service, reopens
training products, applies a named baseline and prepares target-specific forward
geometry. The regional anchor retains its full training ancestry and is separately
identified from local predictor sites. Both inversion and forward grids declare
the same physical basin and selected outer support radius.

Prediction publication precedes `score_experiment_predictions`, which accepts a
separate outcome inventory and records attempted outcome access. Every requested
fold, baseline and target receives a score or explicit failure/exclusion result.
Changing held-out pollen cannot affect that site's training fit or frozen
prediction. Vegetation and pollen are scored separately; training mean, nearest
site and inverse-distance-squared are named baselines. Their deterministic
predictions have no predictive intervals, and overlapping-fold scores do not
constitute independent fixed-model evaluation units. The first profile does not
admit final evaluation or empirical source observations.

The host CLI exposes the same two phases. Set the existing batch service's
numerical thread controls, prepare the declared synthetic experiment, and retain
its reported `manifest_sha256` before scoring:

```bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
bijux-pollenomics prepare-lra-experiment experiment.json \
  --input-root inputs --cache-root cache --output predictions --max-workers 1
bijux-pollenomics score-lra-experiment predictions \
  --expected-manifest-sha256 "$prediction_manifest_sha256" \
  --outcome-root outcomes --outcome-inventory outcomes/inventory.json \
  --output scores
```

The scoring command verifies the expected prediction identity before opening the
outcome inventory. Both commands emit JSON identifying the saved product and its
accounting. Preparation exits `0` when every requested prediction was generated,
`2` for a refusal or partial result, and `130` for an accounted-for interruption.
Scoring exits `2` if any requested score is missing, refused or excluded. A zero
exit reports operational success; `scientific_acceptance` remains
`not_evaluated`. The original prediction and separate score products retain all
requested denominators and target-specific results.

The separate `analysis.lra_validation.spatial.fit_spatial_model` facade fits
`clr-wgs84-rbf-ridge-v1`: centred log-ratio vegetation fractions regressed on
radial basis features centred only at declared training sites. It reuses the
host's unrounded WGS84 distances. Lengthscale, ridge penalty and matched-support
identity are required declarations. All training fractions must be positive;
zeros refuse without an invented replacement rule. The numerical least-squares
backend is loaded only when fitting, through the optional NumPy dependency.

The [CLR definition](https://scikit.bio/docs/latest/generated/skbio.stats.composition.clr.html)
and [ridge objective](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.Ridge.html)
define its transformation and fitted objective. This is an exploratory geographic
model choice, not evidence that the model is ecologically accurate. It has an
unpenalized intercept, one equally weighted composition per predictor group,
and explicit solver diagnostics. The basis features do not assume a geographic
covariance kernel. Every fitted coefficient, centre, parameter and denominator
is bound to the model digest. Target coordinates are supplied after fitting;
target observations are not accepted. The profile produces point predictions,
with uncertainty, parameter selection and final evaluation left to separately
governed experiment stages. The current baseline experiment runner does not
silently substitute this fitted model for any named baseline.

## Saved-product reporting

`bijux_pollenomics.reporting.lra_products.api` owns the bridge from verified saved
products to exploratory reports. It uses the host's existing static atlas writer,
map renderer and shared exclusive-output publisher. Reporting never invokes the
numerical engine. Display geometry is a separate, hash-pinned input bound to the
product and site identities; reconstruction ring coordinates do not become map
locations or geographic footprints.

The first mapped profile admits synthetic paired reconstructions with one
nonnegative, typed BP bin and explicit point anchors. Unsupported geography,
profiles or temporal support remain in the tables and refusal accounting.
Regional and local model anchors carry textual R/L cues. These are model context,
not measured vegetation, propagation edges or accepted scientific reconstructions.

One native selection controls roles, sites, taxa and bins across the table,
anchors, URL and selected download. Shared time and layer controls also constrain
mapped rows. Rows refused geographic display remain inspectable under the native
selection, with that temporal-refusal policy declared in the export. Original CSV
decimal text and missing values retain their source locators and units.

The native view has an independent digest, avoiding a cycle with the enclosing
report manifest. URLs bind that digest and a validated selection; stale or
malformed selections visibly refuse export until corrected. Selected downloads
declare their JSON serialization and hash the exact emitted UTF-8 bytes. Neither
a matching digest nor an interactive report establishes ecological accuracy.
