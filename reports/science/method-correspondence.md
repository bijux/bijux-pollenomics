# What we reproduced from the numerical method

We [bound the released author profile](publication-correspondence/author-method-profile.md)
to its 17 example sites, 31-taxon PPE/covariance axis and 25 bins. We
checked bounded numerical contracts against retained author source cases
in our [original-R certification](../../docs/report/method-certification/original-r-reference/README.md).
We then compared the installed Python publication profile with an
independently executed author-R example in the
[author-example correspondence](../../docs/report/publication-replay/landclim-author-example-correspondence/README.md).
All 14,074 supported fractional cover and standard-error values meet the
declared tolerances. Maximum absolute mean and SE residuals are 1.83881e-13
and 7.15331e-14. We claim calculation correspondence for these two grids,
not full historical input closure or ecological accuracy.

We reproduced 17 prepared author-example files byte for byte from 871 raw
sample rows and 15,028 matching prepared cells in the
[raw-to-prepared replay](../../docs/report/source-relations/landclim/author-example-taxon-support/README.md).
We have not authenticated the historical Nordic publication revisions.

We also compared the original 2016 REVEALS function with a pinned later
LRA release by Petr Kuneš on one author 225 BP window. The [four-case
comparison](../../docs/report/method-certification/petrkunes-r-comparison/README.md)
includes a single lake, unequal lake pair, six active sites and the full
nine-site grid. All 124 matched cover values and 124 standard errors agree at
the retained CSV precision, with identical site-bootstrap indices. Feeding
those indices into our historical native profile matches the tagged R full-grid
cover and SE values within the declared tolerances in a separately retained
Python execution. At committed source `14a3cec7ac1b0a05f122411d4fde9bb5b397280e`,
a new R-only invocation exited zero in 28.307 seconds and reproduced the three
R CSVs byte for byte: 124 finite cover pairs, 124 finite SE pairs with exact
zero differences, and all 6,000 original-site bootstrap positions. A separate
saved-output observer passed after its initial raw-versus-prepared label
assertion was corrected using the existing authenticated crosswalk; no R or
Python model was relaunched. Source inputs, committed code and dependency
metadata remained stable. Peak child RSS was 103,841,792 bytes and outputs
25,810 bytes. The historical Python report was not rerun or relabelled. This
checks one conditional code lineage, not historical R custody, the uncertain
2022 executable, corrected uncertainty, source rights or Nordic ecology.

## Numerical coverage and uncertainty scope

The supported method workflows and the field evidence have separate scopes.
The [engine/host contract](../../docs/public/pollenomics/architecture/lra-engine.md)
and [source-to-test map](../../packages/bijux-pollenomics-lra/docs/reference/parity.md)
identify regional REVEALS, signed analytical and optimized LOVE, heterogeneous
multisite aggregation, exact-coordinate series and forward pollen products.
Actual source-locked R execution, shared draws, fixed-candidate wrapper replay
and achieved-objective checks establish their declared numerical behavior.
The [distribution account](../architecture/lra-distribution.md) retains the
separate fresh noneditable wheel/sdist checks. The
[original-delivery audit](../architecture/lra-source-adoption/README.md#original-package-and-adapter-deliveries)
now reconciles the received source variants with their adoption owners.
These qualifications retain their execution epochs and explicit refusals.

Sensitivity does not require assigning an unsupported probability law to every
physical input. The retained separate ensembles preserve their specified
relationships and answer the following conditional questions:

| Axis | Existing ensemble and dependence | Supported interpretation |
| --- | --- | --- |
| Basin geometry | [Three radius factors × 14 sites × three methods](../../docs/report/pollen-reconstruction/author-lra-constrained/radius-sensitivity/README.md): 126 paired rows; linked inner annulus edges and areas change together while vegetation/training fits remain fixed. | Forward transport sensitivity to the declared circular basin; neither a new inverse reconstruction nor measured geometry uncertainty. |
| Transport parameters | [Five source transport profiles](../../docs/report/pollen-reconstruction/author-lra-constrained/nested-transport/README.md): all 3,375 candidate dispositions and 45 selected slots, with fixed taxa, PPE and optimizer budgets. | Conditional source-profile comparison, with original failed fit processes and separate saved-product qualification preserved. |
| PPE parameters | [Three source mean/SD profiles](../../docs/report/pollen-reconstruction/author-lra-constrained/nested-ppe/README.md): all 2,025 candidate dispositions; each changed vector propagates coherently through regional, local and forward calculations. | Deterministic marginal sensitivity; not a joint PPE distribution or covariance interval. |
| Spatial model | [32 setting/spatial pairs and 480 ranking rows](../../docs/report/pollen-reconstruction/author-lra-constrained/development-setting-selection/README.md), retaining eight prerequisite-refused pairs and three aliases; the separate [three-place physical-forward account](pollen-reconstruction/spatial-field-forward/README.md) retains 18 matched contexts and 54 family dispositions. | Dependent exposed development comparisons; no sampled vegetation-field law or untouched accuracy claim. |
| Joint chronology/count/PPE | [32,000 saved ABBO age states](pollen-reconstruction/abborrtjarnen-age-ppe/README.md), source-supported complete population 31,999, four windows/20 components and 30 contrasts; shared PPE, age/PPE interaction and all undefined rows remain. | Conditional working-law moments and common-covariance sensitivity; the empty window still prevents an unconditional composition result. |
| Shared site/PPE sampling | [1,024 paired author replicates](../../docs/report/method-certification/author-site-uncertainty/README.md), six sites/ten taxa, one shared PPE vector per replicate. | Explicit site/PPE dependence for that declared profile; not independent site-wise PPE sampling or field calibration. |

Together with the equation/domain/property checks below, these qualify the
implemented numerical and sensitivity capabilities. The 20% radius perturbation
is not an empirical basin distribution, source mean±SD is not a covariance law,
and a spatial-method comparison is not a vegetation-field draw. Static geometry,
source-specific parameter transfer and selected chronology remain assumptions
where the owning study says so. Measured vegetation accuracy, justified joint
physical uncertainty, historical publication reproduction and untouched
confirmation require their own source evidence; numerical agreement cannot
supply them. No model, draw, score or oracle was rerun for this reconciliation.

## Optimizer budget accounting

We independently challenged an earlier differential-evolution solver against
its corrected successor on 135 combinations of dimension, fixed bounds,
population size and evaluation budget. In both executed runs, 54 cases changed
the reported completed-generation count; 81 did not. Every case retained the
same objective-evaluation trace, random-generator state and other result fields.
The corrected snapshots in that comparison precede today's
solver, so this is evidence for the historical accounting change, not a fresh
135-case certification of current code. Our [current focused regression](../../packages/bijux-pollenomics-lra/tests/unit/optimization/test_solver.py)
checks completed generations and exact evaluations at four budgets. Generation
accounting alone says nothing about the quality of a vegetation optimum or
agreement with the original R optimizer.

## Optimized LOVE on shared objectives

We compared the installed RcppDE and Python searches on three declared LOVE
objectives with identical pollen, deposition, background, PPE, bounds and
iteration cap. In the [governed solution-quality study](../../docs/report/method-certification/optimizer-solution-quality/README.md),
both achieved objective values within `1e-4` of the independently derived
optima. Evaluating each selected candidate in the other implementation gave
absolute objective gaps below `1e-10`. The [three result rows](../../docs/report/method-certification/optimizer-solution-quality/summary.csv)
include a composition-ambiguous case where different cover vectors are equally
good; we judged objective quality and common-candidate arithmetic, not vector
identity. Python reported success after 29–40 iterations and 600–1,230
evaluations. R used its full 400-iteration cap in all three cases. These
small, declared objectives support bounded numerical solution quality; they
do not establish identical random search paths, global convergence on other
landscapes or ecological accuracy.

We also [replayed analytical LOVE across ten example rings](analytical-love-ring-sensitivity/README.md).
Only three satisfy the source's local-basin boundary; 16 of their 30
taxon/ring estimates are negative and six exceed one. We retained those
unconstrained results to show ring sensitivity rather than presenting an
invented closed vegetation composition or a recommended Nordic radius.

## Current and historical native R comparisons

The [historical native R capture](../../docs/report/method-certification/current-r-oracle/README.md#historical-native-capture)
at source `064d1237fd743d957538fff2cbae74db06e17338` passed 43 core and
23 source-domain cases. Its 97 numeric CSV files matched the earlier capture
byte for byte, and 48 comparisons with the original R reference passed. Those
are dated historical results, not a certification of every subsequent source edit.

On 23 October 2026 we executed native R again against source
`b25d0fbf9f667819e1a08da64634240644a6580d`. All 43 core and 23 domain cases
passed. The core population includes 18 prospective optimized LOVE cases; the
original R reference contains no corresponding results for those 18. All 48
available historical comparisons passed separately. The [ordered R values](method-certification/current-native-r-values.csv)
retain all 5,828 coordinates, including labels, NaNs and signed values. This
new run establishes bounded numerical correspondence, not a new claim of
byte-identical reproduction of the old R run.

After correcting decimal CSV parsing, a Python-only comparison at
`2df67941a29a7c203037badcd303a9766bb5d5d4` confirmed all 66 current cases and
48 historical pairs. The [114 case rows](method-certification/current-native-r-comparisons.csv)
retain their original absolute/relative tolerances, exact coordinates and
nonfinite masks. Current Python versus R has a maximum absolute error of
2.4868995751603507e-14 across 5,828 entries; current versus original R has a
maximum of 3.197442310920451e-14 across 1,922 entries. The full current population
contains 169 character labels, 3,865 finite numbers and 1,794 NaNs. Matching NaNs
retain their source meaning and do not establish finite optimizer success.
The historical subset is not an additional independent scientific population.

Pandas' numeric conversion had rounded some 17-digit source decimals to different
binary64 values. The maintained reference readers now validate the same lexical
and range contract, then convert the original decimal tokens with correctly
rounded binary64 conversion. No source token, coordinate or numerical tolerance
was changed. The 38 focused regressions cover real R tokens, exact coordinates,
nonfinite/character values and malformed or overflowing input. An independent
standard-library CSV/float audit confirms all 48 historical pairs. Neither this
parser repair nor the Python-only recheck executes R again.

We used R 4.6.0 with DISQOVER 0.9.14 and the existing locked dependency source
archives, unchanged in place. The [R source lock](../../configs/ci/lra-r-source-lock.v1.json)
and original reference certificate identify those inputs. Python 3.11.13 used
NumPy 2.4.6, SciPy 1.17.1 and pandas 2.3.3. The shared editable distribution still
reported `0.1.9.dev841`; the actual consumed code was checked against Git and
remained stable during execution. This is distinct from the
[built-wheel installation check](../architecture/lra-distribution.md).

After removing source-copying from the maintained domain command, we reran only
its 23 cases at `f8747e20a0015b37a884769ad6d61cbebbce2332`. Every raw R vector,
geometry, parameter and case result exactly matched the first run: 286 values,
including the same NaN positions. No mathematical code or tolerance changed.
The command now reads its three scripts from their canonical package; it writes
no Python or R source copies. The same shared library serves both runs.

To reproduce on a suitably provisioned environment, run the maintained
`packages/bijux-pollenomics-lra/tests/reference/lra_oracle/run_live_r.py` and
`run_source_domains.py` with `--library` pointing to the shared locked R library
and separate `--output` directories. The latter requires no copied scripts.
The first fresh run used the maintained core CLI and direct canonical domain R
script with its maintained case preparation and expectations. Dependency
preparation and execution took 104.30 seconds in total; the maintained domain
rerun took 3.033 seconds. Re-running a numerical comparison does not imply a
new ecological study, historical publication input closure, global optimizer
convergence or a release certificate.

We also ran the [same ten-taxon `LOVEexample` inputs](../../docs/report/numerical-performance/love-source-comparison/README.md)
through native R and Python with binary-identical values and 32 fixed
candidates at each of eight active ring/repeat calls. Cover and pollen agree
exactly; ring factors differ by at most 5.11e-15 and objective values by at
most 4.67e-15. All eight selected candidate indices agree. This checks
fixed-candidate calculation, while optimizer searches and Nordic vegetation
remain outside the comparison.

We checked a separate source behavior in a [controlled optimized LOVE
regression](../../packages/bijux-pollenomics-lra/tests/unit/reconstruction/test_optimized_profile.py):
two distinct sampled local PPE vectors produce identical cover, pollen and
objective values when regional cover, local pollen counts and candidates are
held fixed. The source-compatible optimized objective uses nominal local PPE
despite sampling a local PPE vector. We do not count that sampled vector as
propagated local PPE uncertainty or infer the paper's Figure 2 from this test.

## A real publication difference

We compared the exact shared TW2 interval, 100–350 BP, in our
[paper correspondence account](publication-correspondence.md). The archived PANGAEA
937075 means differ from author-R by up to 9.19787 percentage points in grid
512 and 10.5527 in grid 562; SE gaps reach 3.21615 and 4.25814 points.
Only one of 25 window intervals matches exactly. We retain the differences
without shifting windows or renaming taxon groups because the possible source
revision or transformation explanation remains unverified. Our
[row ledger](../../docs/report/pollen-reconstruction/paper-correspondence.csv)
and [PFT crosswalk](publication-correspondence/pft-crosswalk/README.md)
give the exact cells and arithmetic.

We closed archived ISTS/TBS **mean arithmetic** on the source taxon groups
over 10,500 grid/window rows. We did not identify the archive's biological
ISTS definition or SE covariance transformation. The paper, deposit prose
and archive expose different PFT counts or positions. We still need a
provider-bound historical input and transformation packet to reproduce the
full paper.

## Current LOVE wrapper comparison

At source `01ca11bb1eea641b13a9b4ea6fc350bad08fb627`, a new maintained
[consumer](../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/native_backend/love_comparison/execution.py)
compared complete Python and source-R LOVE calls on the same packaged
`LOVEexample`. The protocol and 42 controlled tests were committed before the
actual run. The run exited zero in **6.844 seconds**, with unchanged source,
inputs and installed source archive. It used the existing shared R library;
no installation, C++ build or paper-simulation reconstruction was performed.
The earlier [historical comparison](../../docs/report/numerical-performance/love-source-comparison/README.md)
and its source gate remain unchanged.

One local and one regional pollen row, ten taxa and 36 rings supply the inputs.
The maximum local ring is ten, with two deterministic repeats and 32 fixed
candidates at each active ring/repeat. Five decimal tables and five hexadecimal
sidecars preserve identical parsed binary64 values, taxon names and order.
Regional/local sampling and the R search are replaced by the existing test-only
fixed samplers and candidate replay. This is not untouched RcppDE search or a
comparison of stochastic optimizer trajectories. Eight active calls return
256 search evaluations; Python additionally performs eight mandatory solver
certifications per complete call. The extra work is retained in its timing.

The [580-cell paired ledger](method-certification/love-wrapper-values.csv)
preserves both writers' original numeric tokens. Cover is a fraction and local
pollen is a percentage. Row indices retain each product's native row order:
ten requested local rings for cover/pollen/objective, and 36 source rows for
`K`; objective columns identify the two repeats. The source's six undefined
local rings remain missing: R writes `NaN`, Python an empty CSV cell. These
tokens are not zeros. All output column names, shapes and missing masks agree.

| Product | Shape | Finite paired cells | Undefined paired cells | Maximum absolute gap |
| --- | ---: | ---: | ---: | ---: |
| Mean cover | 10 × 10 | 40 | 60 | 0 |
| Mean local pollen | 10 × 10 | 40 | 60 | 0 |
| Best objective | 10 × 2 | 8 | 12 | 4.663e-15 |
| Ring factor `K` | 36 × 10 | 360 | 0 | 5.103e-15 |

All 448 finite pairs meet the original `3e-10` absolute plus `1e-10` relative
tolerance. The 132 missing pairs retain the source outcome. Every active call
selects candidate one from this monotone candidate set; exact candidate IDs and
32-return budgets agree. Both implementations also refuse the separate
all-undefined candidate control. Neither the selected row nor numerical
agreement establishes optimizer convergence or a useful landscape estimate.

Each fresh engine process made one first and five warm complete wrapper calls.
Parsing precedes those clocks; regional preparation, ring factors, objective
replay and result summaries are inside them. Every repeat returned identical
products and selection traces within its engine. The R timer resolves
milliseconds. All five numerical thread environment settings were one.

| Call | Python milliseconds | R milliseconds |
| --- | ---: | ---: |
| First | 76.774 | 420 |
| Warm 1 | 24.092 | 418 |
| Warm 2 | 22.868 | 479 |
| Warm 3 | 23.111 | 381 |
| Warm 4 | 22.743 | 366 |
| Warm 5 | 22.517 | 368 |
| Warm median | 22.868 | 381 |

The observed warm-wrapper ratio is **16.66 R/Python** for this fixture.
It is not a kernel, larger-study or complete application speedup. Whole worker
wall times were **1.174 seconds Python** and **3.646 seconds R**. Those include
imports, setup, all six calls, exports, refusal controls and diagnostics;
subtracting call time does not isolate startup. Python's measured setup after
imports was 4.822 ms and export 3.379 ms. R's pre-call setup was 760 ms and
post-call export 72 ms; its setup includes source/library checks as well as
parsing, so these setup categories are not equivalent measurements.

Native whole-process peak RSS was **136.67 MiB Python** and **203.28 MiB R**.
These high-water marks include setup and are not incremental kernel allocations.
The machine was macOS 26.6.2 arm64, Python 3.11.13 with NumPy 2.4.6,
pandas 2.3.3 and SciPy 1.17.1, and R 4.6.0 with DISQOVER 0.9.14.
Python used Accelerate; R reported its `libRblas` and LAPACK 3.12.1. Different
libraries, one workstation and five warm samples do not identify a language
effect or supply a timing confidence interval. First calls are not a claim of
empty operating-system caches. The editable/imported LRA version still reported
`0.1.9.dev841`; the actual consumed source is the Git revision above, not a
new built release or hosted qualification.

Reproduce with the existing qualified R library and an absent output directory:

```bash
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -B -m bijux_pollenomics_dev.native_backend.love_comparison \
  --repository . --library "$R_LIBRARY" \
  --output artifacts/love-wrapper-comparison
```

The consumer checks the original DISQOVER archive and installed source marker,
requires committed clean consumed code, and preserves failed native exits and
changed/missing-input refusals. Its aggregate deadline is 120 seconds with
outputs below 16 MiB. This actual run wrote 89,687 bytes. It supplies current
fixed-candidate method correspondence and bounded wrapper timings; it does not
complete the representative 128-call or three-way R/Python/C++ investigation,
justify C++ adoption, establish ecological accuracy or qualify a release.

## Original kernel boundary comparison

The existing native cases cover all five kernel methods, but do not cross the
original large-lake integration-step or peatland cutoff branches. Before new
numerical outcomes, we fixed a separate 30-case comparison with the unchanged
DISQOVER 0.9.14 function. It advances the source-branch obligation; it does not
rerun or extend the historical 66/48-case populations.

The reference is the existing
[original archive](../../packages/bijux-pollenomics-lra/vendor/disqover_0.9.14.tar.gz),
SHA-256 `ea496ae82807b52c9dd3d4b39b4dfa294bfac4068e20184ce56187bff70caf5c`,
whose `disqover/R/dispersal_models.R` declares basin diameter in metres.
Its lake calculation uses a 2 m outer integration step below diameter 2000 m
and a 10 m step at or above 2000 m. The inner annulus integration retains its
separate 2 m step and original area normalization. For peatland the source
subtracts the outer contribution from the inner when `regionCutoff <= 1000000`,
and returns the inner contribution alone above it.
The source documentation calls `regionCutoff` a reconstruction diameter while
the body passes it directly to a distance function. We test the **literal
argument in metres** without halving it or silently correcting that convention.
The source also uses basin diameter for GPM peatland `din`, and basin radius
for the other methods; those existing differences remain.

The fixed matrix uses fall speed `0.03 m/s` and wind speed `3 m/s` for
`lsm unstable`, `lsm unstable low`, `gpm neutral`, `gpm unstable` and `1overd`:

| Source branch | Basin diameter (m) | Literal regionCutoff argument (m) | Cases |
| --- | --- | --- | --- |
| Lake integration step | 1999, 2000, 2001 | 100000 | 15 |
| Peatland outer contribution | 100 | 999999, 1000000, 1000001 | 15 |

We compared each original R scalar with the current Python scalar at the same
literal inputs. The inherited kernel criterion was
`abs(R - Python) <= 3e-10 + 1e-10 * abs(Python)`, fixed before execution.
Scalar shape and finite/NaN/signed-infinity masks must match. Original R `NA`
and `NaN` tokens remain distinguishable in the raw output; both compare to
Python NaN under the existing `equal_nan` convention. Matching them is evidence
of the returned source behavior, not finite numerical success. Negative values
and warnings remain visible. In particular, an undefined unused outer contribution
above the peatland cutoff is not grounds to replace or refuse a finite returned
inner contribution. Unexpected errors, missing cases, timeout, source changes or numerical
disagreement fail the comparison without dropping rows or widening tolerances.

The maintained
[consumer](../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/kernel_branches.py)
uses the already provisioned shared R library. It authenticates the original
archive and existing source lock, verifies the actual R version, locked package
versions, loaded DISQOVER namespace path and source marker, then calls
`disqover::DispersalFactorK` without copying or redefining its body. Python calls
the maintained `DispersalFactorK`. The source, stored LSM resource and reference
inputs must be committed and unchanged before and after execution. Raw R tokens,
per-case warnings/errors and one comparison CSV are retained alongside the
actual R session and process outcome. The 30 calls use one R batch, an aggregate
60-second deadline and outputs below 1 MiB. The pre-run peak-memory estimate was
256 MiB; the observed peak below exceeded that estimate.

The first invocation at `0153e4c1e53916c480a235afe61d6ed4b22b3639` exited one
before any R kernel calls. Its dependency guard compared normalized R version
text with literal lock strings: installed `2.2-8` became `2.2.8`. All 37 raw
installed versions actually matched. That failed attempt computed 30 Python
values but did not retain them or produce a comparison CSV. Its original
failure and command remain preserved. We changed the guard to read literal
DESCRIPTION `Version` fields, without changing installed packages, source
equations, inputs, the 30-case matrix or numerical tolerances.

The qualified execution used committed source
`e1c881985f904b589c22a09e92cc5fa48774d66e` and the same shared R library.
Its actual command was:

```sh
mkdir -p artifacts/science/kernel-branches
.venv/bin/python -B -m bijux_pollenomics_dev.lra_validation.kernel_branches \
  --repository "$PWD" \
  --library "$PWD/artifacts/qualification/native-reference/library" \
  --rscript /usr/local/bin/Rscript \
  --output "$PWD/artifacts/science/kernel-branches/qualified-comparison"
```

The [30-row comparison](method-certification/kernel-branch-comparisons.csv)
retains **26 finite pairs and four matching R `NA`/Python NaN returns**. All 30
meet the unchanged comparison criterion; that is not 30 finite successes.
All 15 lake cases are finite. The four undefined cases are the two LSM methods
on peatland at cutoff arguments 999999 and 1000000 m: the outer prediction is
outside the stored model support. At 1000001 m the original branch ignores that
outer contribution and returns finite inner values. This is source behavior,
not permission to extrapolate an LSM curve or choose a physically preferred
regional extent.

The largest finite absolute residual is about `1.86526e-15`; the largest relative
residual to Python is about `1.58103e-12`, both on the 1999 m lake `1overd` case.
Six R rows, all `1overd`, retain the warning
`k-d tree limited by memory. ncmax= 661` twice per row. There are no Python
warnings, returned errors or negative finite values. Warning-bearing results
are not silently discarded, and numerical correspondence does not establish
scientific suitability of that method.

The native supervisor exited zero in 5.090 seconds, including 3.183 seconds
inside the consumer and 2.877 seconds for the R batch. The consumer wrote
17,763 bytes. Observed peak child RSS was **326,926,336 bytes**, above the
256 MiB planning estimate; the run did not establish a 256 MiB memory bound.
Source, archive and Git identity stayed unchanged during execution.
Forty-two focused controls, configured static checks and independent source/code
review passed before this qualified run; the controls include separate R
primitive shape and version-metadata checks, not live kernel outcomes.

A separate standard-library observer exited zero in 0.124 seconds, checking
all 30 fixed input identities, raw decimal conversions, scalar return states,
nonfinite masks, warnings, residuals and original threshold decisions. It did
not invoke R or either kernel. This is independent arithmetic on the **same
native outputs**, not an independent dispersal model or ecological measurement.
The sole comparison CSV was moved once to the maintained location above.
Raw R tokens, session information, warnings and both attempts remain in their
artifact directories. The recorded qualified command keeps its original output
path; reproducing it requires a new absent directory rather than overwriting
the retained attempt.

This comparison cannot
establish a physical discontinuity, a preferred basin convention, complete
source-branch coverage, historical 2024 software identity, optimizer convergence,
ecological accuracy or a hosted release certificate.

## Minimum lake diameter: one refusal and two finite comparisons

The original function constructs the lake integration points with
`seq(from = 2, to = dBasin/2 - 1, by = 2)` below diameter 2000 m. For diameter
5 m the upper limit is 1.5 m, below the starting point, so the original sequence
refuses. At 6 and 7 m the source admits its first one-annulus calculation.
The Python entry point explicitly refuses a diameter below 6 m. Neither the
earlier 30 boundary cases nor the older native cohort tested these three inputs.

Before calculating new outcomes, we fixed the separate
`minimum-lake-diameter` population: **5, 6 and 7 m lake diameters**, only
`gpm neutral`, literal cutoff argument `100000 m`, fall speed `0.03 m/s` and
wind speed `3 m/s`. The original installed function evaluates its **fitted GPM
LOESS**; a raw exponential is not substituted as an oracle. The existing default
30-case population, input order, output schema and saved result remain unchanged.

The 5 m contract requires a paired refusal, separately labelled from numerical
success. R must return the exact sequence-domain error
`wrong sign in 'by' argument`, length zero and an empty value token; Python must
raise its existing `ValidationError` for a source lake diameter below 6 m.
One-sided refusal, an unrelated error or an unexpected returned value fails.
Both 6 and 7 m must return finite real scalars and meet the unchanged criterion
`abs(R - Python) <= 3e-10 + 1e-10 * abs(Python)`; an all-error or all-NaN
population cannot pass. Negative finite values, warnings and actual errors
remain inspectable. The three-row result declares `expected_outcome` and
`outcome`; a paired refusal is never counted as a finite numerical comparison.

The code and protocol were committed before execution at
`4a9b9fa6924d2f52dfddfeeb0274dba4901b0994`. The same source/runtime guards
remained strict; a case-level refusal cannot excuse a parent failure.
The actual invocation was:

```sh
.venv/bin/python -B -m bijux_pollenomics_dev.lra_validation.kernel_branches \
  --repository "$PWD" \
  --library "$PWD/artifacts/qualification/native-reference/library" \
  --rscript /usr/local/bin/Rscript \
  --population minimum-lake-diameter \
  --output "$PWD/artifacts/science/kernel-branches/minimum-lake-diameter"
```

The [three-row result](method-certification/minimum-lake-comparisons.csv)
retains exactly **one paired refusal and two finite comparisons**:

| Diameter (m) | Original R return | Python return | Outcome |
| --- | --- | --- | --- |
| 5 | Sequence-domain error | `ValidationError` | Paired refusal, no numerical value |
| 6 | 0.37521741576178552 | 0.3752174157617857 | Finite pair within original tolerance |
| 7 | 0.36685143180649976 | 0.36685143180649993 | Finite pair within original tolerance |

Both finite absolute gaps are `1.6653345369377348e-16`. All three prespecified
contracts pass; that does not mean three numerical successes. There are no
case-level warning rows. R namespace messages about overwritten DEoptim/RcppDE
imports remain in the raw process stderr; we do not claim an entirely
warning-free R process.

The native supervisor exited zero in 5.302 seconds, including 1.526 seconds
inside the consumer and 1.395 seconds for R. It produced 8,149 artifact bytes,
with peak child RSS 177,045,504 bytes. Fifty-six focused profile checks, ten
runtime-isolation checks, configured static checks and independent review
preceded execution. Source and inputs stayed unchanged. A separate observer
exited zero in 0.147 seconds, checking the three saved input identities, exact
paired error contract, decimal tokens and both original tolerance decisions.
It invoked neither kernel nor R, and supplied no independent physical oracle.

The sole comparison CSV was moved once to the maintained location above; its
recorded command keeps the original output path. Raw R values, errors, session
and process messages remain in the artifact directory. Reproduction requires
an absent output directory. This computational boundary does not determine
ecological site eligibility or recommended physical lake dimensions. The result
does not establish complete branch coverage, physical accuracy or release
qualification, and it neither reruns nor replaces the separate 30-case result.

## Conditional covariance numerical-domain refusals

The fixed-site and joint fixed-site conditional covariance APIs have a finite
binary64 calculation domain in addition to their scientific assumptions. Finite
counts, deposition, PPE and PPE covariance do not guarantee a representable
corrected total, derivative or propagated covariance. Both consumers must retain
that failure as `ValidationError` even when a caller raises on NumPy floating-point
warnings. A partly computed composition is not a usable covariance result.

A direct pre-edit check at base source `38a830f777afa75d17b8cf0a4935b2b206ae6d60`
exercised four two-taxon requests in both consumers with
`warnings.simplefilter("error", RuntimeWarning)` and `np.errstate(all="raise")`.
All cells were declared measured; there was one fixed count support. Seven of
the eight calls leaked `FloatingPointError`; only the fixed-site propagated
covariance case already raised `ValidationError`:

| Counts | Deposition | PPE | PPE covariance | Numerical failure |
| --- | --- | --- | --- | --- |
| `(1,1)` | `(1e-308,1e-308)` | `(1,1)` | identity | Corrected total overflows |
| `(0,1)` | `(1e-308,1e308)` | `(1,1)` | identity | Zero-count-axis derivative overflows |
| `(1,1)` | `(1e308,1e308)` | `(5e-324,5e-324)` | identity | PPE derivative overflows |
| `(1,1)` | `(1e200,1e200)` | `(1e-200,1e-200)` | `1e200 * identity` | Propagated covariance is nonfinite |

Review identified a fifth request, counts `(1,1)`, deposition
`(1e308,1e-308)`, unit PPE and zero PPE covariance. Two direct calls after the
derivative changes still raised `FloatingPointError` in the unmodified closure
division. Under ordinary warning handling that division returned `(0,1)`,
silently losing a taxon with positive observed counts. Both consumers now refuse
that unrepresentable positive composition. Measured zero remains a distinct,
permitted value.

The original terminal outcomes are retained in
`artifacts/method-certification/covariance-domain-before.txt`. The maintained
consumers now inspect numerical results before using them downstream, retaining
the existing corrected-total refusal and adding explicit nonfinite derivative
refusals. The joint consumer checks finiteness before normalizing a covariance.
Local warning handling permits these reasoned refusals without depending on the
caller's warning policy. Equations, covariance assumptions, profiles, count
denominators and numerical tolerances are unchanged.

The focused checks retain all ten requests as explicit refusals. Four positive
controls (two consumers by two equal-response cases) independently use the
binomial identity `Var(n1/N) = p*(1-p)/N`: `(30,70)` with deposition
`(1e308,1e308)` gives `p=0.3` and variance `0.0021`; `(1,1)` with deposition
`(2e-308,2e-308)` gives `p=0.5` and variance `0.125`. Common correction factors
cancel analytically. These finite extreme requests still return the two
complementary covers and their signed closed covariance under the same strict
warning policy. Existing heterogeneous-geometry, shared-PPE, native-support,
finite-law and public-contract checks provide separate relevant regression
evidence; the finite-law checks distinguish exact moments from delta approximation.
Two separate controls retain the representable subnormal cover `1e-308` for
deposition `(1e308,1)`, counts `(1,1)` and unit PPE. Those controls claim only
preservation of positive composition: their squared counting scale lies below
binary64 and the returned counting covariance is zero, not an exact moment.

The actual precommit command was:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -c configs/pytest.ini \
  packages/bijux-pollenomics-lra/tests/unit/reconstruction/uncertainty/test_covariance_correction_domain.py \
  packages/bijux-pollenomics-lra/tests/unit/reconstruction/uncertainty/test_fixed_site_covariance.py \
  packages/bijux-pollenomics-lra/tests/unit/reconstruction/test_joint_fixed_site_covariance.py \
  packages/bijux-pollenomics-lra/tests/unit/reconstruction/test_joint_covariance_public_contract.py \
  --basetemp artifacts/method-certification/pytest-covariance-cover-domain -q
```

It passed **111 checks** in 0.19 seconds on reviewed working changes based on the
source above. Configured Ruff lint/format and strict mypy checks passed for the
three changed Python files. This is affected-consumer precommit verification, not an exact-HEAD
R comparison or a new physical experiment. A finite-input numerical refusal does
not supply chronology/geometry uncertainty, historical reproduction, measured
vegetation accuracy or full method certification.

## How to use this result

We use the selected author profile to test numerical fidelity to the
retained R example. We use the separate archive comparison to investigate
historical source identity. We do not treat either as measured vegetation
validation. Our [English LRA development study](english-lra-pollen-prediction.md)
provides a distinct real reconstruction and withheld forward-pollen test;
we summarize its matched direct-pollen scores and model conditions in the
[prediction report](pollen-prediction.md).


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Declared original-R/native and fixed candidate numerical cases agree within retained tolerances. Separately, current fixed-candidate LOVE wrapper arithmetic agrees and first/warm timings are measured on one declared workstation/fixture. A separate original-source kernel boundary comparison matches 26 finite scalars and four R NA/Python NaN returns across the fixed 30-case lake-diameter and peatland-cutoff matrix, retaining source warnings and original tolerances. A separate prespecified minimum-lake profile retains one exact paired domain refusal at diameter 5 m and two finite original-R/Python comparisons at 6/7 m using fitted GPM LOESS; it does not count the refusal as numerical success. A separate current four-case source-R replay reproduces three retained CSVs exactly on shared author/tagged inputs; its 248 finite pairs and 6,000 original-site indices do not establish historical R custody or independent validation.

**Unsupported claim.** Global optimizer convergence, identical stochastic paths, historical publication source identity or ecological validity. C++ benefit, larger-study speedup, a causal language effect or hosted release qualification.

**Actual verification performed.** Fresh R at b25d0fbf9 passed 43 core and 23 domain cases; faithful-decimal Python recheck at 2df67941a passed 66 current cases and 48 historical pairs. Maintained domain CLI at f8747e20a reproduced 23 raw vectors exactly. Historical author-example 14,074 values and 17 prepared files are retained separately; not rerun here. At committed source 01ca11bb1, one new actual R/Python LOVEexample wrapper comparison passed in 6.844 seconds: 448 finite pairs plus 132 shared missing cells, exact labels/shapes/eight candidate IDs, first plus five warm calls per engine. 42 controlled tests and one independent code review preceded execution; source/input/archive unchanged. At committed e1c881985, the separate 30-case kernel comparison exited zero: supervisor 5.090269959 s, consumer 3.182995083 s, R batch 2.876523666 s, 17,763 artifact bytes and peak child RSS 326,926,336 bytes. All 26 finite pairs and four returned-mask pairs meet unchanged rtol 1e-10 and atol 3e-10; maximum finite absolute/relative residuals are 1.8652614175440618e-15/1.5810337635524618e-12. Forty-two controlled checks, configured static checks and independent code/source review passed. A separate standard-library raw-token/input/scalar/mask/warning/residual audit exited zero in 0.124126375 s, without R or kernel calls. The first 0153 attempt failed a normalized-versus-literal dependency-version guard before R kernel calls; 30 Python values were computed but unretained. The raw DESCRIPTION guard repair changed no lock, installation, equation, case or tolerance; the original failure remains preserved. At committed 4a9b9fa69, the separate three-case minimum-lake profile exited zero: supervisor 5.301670958 s, consumer 1.5255795 s, R batch 1.395404167 s, 8,149 artifact bytes and peak child RSS 177,045,504 bytes. One exact R sequence-domain/Python ValidationError refusal and two finite pairs satisfy their unchanged contracts; both finite absolute gaps are 1.6653345369377348e-16. Fifty-six profile checks, ten runtime-isolation checks, static checks and independent review preceded execution. A separate saved-token/input/domain-error/tolerance observer exited zero in 0.146800541 s without R or kernel calls. The original fitted-source function, raw source and input identities remained unchanged. At committed 14a3cec7ac1b0a05f122411d4fde9bb5b397280e, the R-only replay exited zero in 28.307267125 s with peak child RSS 103,841,792 bytes and 25,810 output bytes, no R stderr and stable committed source, 13 raw R inputs, three tagged files and 38 package DESCRIPTION files. Three CSVs reproduced byte for byte; a separate observer verified 248 finite zero-difference pairs, 124 labels and 6,000 original-site indices. Its first raw-versus-prepared label assertion failed before numeric comparison and was corrected with the existing authenticated crosswalk; no R or Python reconstruction was relaunched. The historical Python report remains unchanged. Coverage reconciliation additionally reuses the independently qualified 126 paired radius rows, 3,375 transport and 2,025 PPE candidate dispositions, 32 setting/spatial pairs with 480 rankings, 1,024 shared site/PPE replicates and 32,000 joint age states; no scientific rerun. The actual original-delivery audit at 7c00afc96 and independent standard-library reader verify all 77 TAR/TGZ/manifest paths and four integration joins, reported at a3158afca.

**Remaining input or review.** Declared R/native cells and fixed-candidate objectives agree; random search paths, global convergence outside tested cases, full historical input identity and ecological accuracy are not established. Resolver: Method implementation/optimizer owner and independent scientific reviewer Reopen when: New authenticated source case or changed algorithm is tested against the original oracle with convergence and ecological reference separately.

**Cause category.** algorithm/numerical|comparability

**Consequence.** Use parity only for the named profile, not a different core or vegetation accuracy.

**Precise next acceptance route.** New authenticated source case or changed algorithm is tested against the original oracle with convergence and ecological reference separately. Then update reports/science/publication-correspondence.md.

**Negative or refused result.** No mismatch within declared paired numeric tolerances; untested stochastic/global cases are not zero error. Six requested local LOVE rings remain undefined; all active calls choose candidate one, and both engines refuse the all-undefined control. Python retains eight extra mandatory certifications. Four boundary returns remain undefined: both LSM methods on peatland at literal cutoff arguments 999999 and 1000000 m; above the branch cutoff they return finite inner contributions. Six 1overd rows retain the native memory warning twice each; no Python warnings or negative finite values. Thirty criterion passes do not mean 30 finite results, complete source-branch coverage, a preferred geometry or ecological validity. Observed peak RSS of 326,926,336 bytes exceeds the 256 MiB planning estimate, so no 256 MiB bound is established. The 5 m minimum-lake case remains a paired refusal without numerical output; it is not a third finite success. There are zero case-level warning rows in that three-case result, while namespace overwritten-import messages remain in R process stderr. The computational 6 m boundary is not ecological site eligibility, a recommended physical lake size or full branch/release qualification. The current R replay does not authenticate the historical R execution or exact 2022 publication version, resolve source GPL-2/MIT rights, certify uncertainty, or supply field/human/release acceptance. The initial observer label failure remains preserved.

**Matched denominator.** Current native: 43 core plus 23 domain cases, 5,828 entries (169 labels, 3,865 finite, 1,794 NaN); historical 48 pairs / 1,922 entries exclude 18 prospective cases. Separately, 17 sites, 184 supported site-windows, 31 taxa and 14,074 author mean/SE values; separate four-case one-window R lineage: 124 cover values plus 124 standard errors. Separate current LOVE fixture: one local/regional row, ten taxa, 36 rings, maximum local ring ten, two repeats, eight active calls / 256 search returns plus eight Python certifications per call; 580 paired cells with 448 finite and 132 missing; one first / five warm complete calls per engine. Separate kernel boundary population: 30 scalar pairs on identical inputs, five fixed methods, fall speed 0.03 m/s and wind 3 m/s. Lake diameters 1999/2000/2001 m at literal cutoff 100000 m; peatland diameter 100 m at literal cutoffs 999999/1000000/1000001 m. All 15 lake and 11 peatland pairs are finite; four peatland mask pairs remain undefined. This population is separate from the 66 current/48 historical cases and fixed-candidate LOVE wrapper population. Separate minimum-lake profile: three literal lake diameters 5/6/7 m, only gpm neutral, fall speed 0.03 m/s, wind 3 m/s and literal cutoff argument 100000 m; one paired refusal plus two finite scalar pairs. Its expected_outcome/outcome labels remain separate from the unchanged 30-case result. Separate current source-R replay: four cases by 31 taxa, 124 finite cover plus 124 finite SE pairs, and 1,000 rows by six original-site bootstrap positions; no new Python computation.

Retained evidence: [docs/report/method-certification/original-r-reference/README.md](../../docs/report/method-certification/original-r-reference/README.md), [docs/report/method-certification/optimizer-solution-quality/README.md](../../docs/report/method-certification/optimizer-solution-quality/README.md), [reports/science/method-certification/love-wrapper-values.csv](method-certification/love-wrapper-values.csv), [reports/science/method-certification/kernel-branch-comparisons.csv](method-certification/kernel-branch-comparisons.csv), [reports/science/method-certification/minimum-lake-comparisons.csv](method-certification/minimum-lake-comparisons.csv), [reports/science/method-certification/current-native-r-values.csv](method-certification/current-native-r-values.csv), [reports/science/method-certification/current-native-r-comparisons.csv](method-certification/current-native-r-comparisons.csv), [docs/report/method-certification/petrkunes-r-comparison/README.md](../../docs/report/method-certification/petrkunes-r-comparison/README.md).


This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
