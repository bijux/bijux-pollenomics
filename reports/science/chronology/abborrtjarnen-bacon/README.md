# ABBO joint ages: verified arithmetic and failed convergence

The new fixed-transition ABBO age model produced all 8,000 requested joint
states and scores, but failed its prespecified convergence criteria. An
independent consumer verified every saved score and retained the refusal.
These values describe an unsuccessful conditional computation; they do not
establish a qualified joint posterior, chronology accuracy or field acceptance.
The [result](result.json) records the numerical population and diagnostics.

The separately preserved [archived proposal](protocol.json) was refused
before fitting. The source-law checks below explain why it was not used for
the new model. That proposal remains unexecuted.

## Sources and an actual numerical witness

The [LegacyAge paper](https://essd.copernicus.org/articles/14/1331/2022/)
names Bacon 2.5.3. We inspected the [official archived package](https://cran.r-project.org/src/contrib/Archive/rbacon/rbacon_2.5.3.tar.gz),
277,370 bytes, SHA-256
`95d5d1906df6882b8542eabaae4c22540c937dff99fec2f057f442b75184dcb0`.
One copy is cached under `artifacts/physical-core/`; no vendor source was
copied into maintained packages. The package and IntCal 0.1.3 installed once
into the existing shared R library in 12.34 seconds. Installation establishes
runtime availability, rather than validity of a scientific interpretation.

For a core without hiatuses, `src/bacon.h::SetThetas` maps sampler innovations
to physical accumulation rates backwards:
`x_K = alpha_K`, `x_j = w*x_(j+1) + (1-w)*alpha_j`.
The t-walk writes its sampler state. The non-Plum branch of
`src/input.cpp::outputFiles` returns before converting those columns to
physical rates. `R/read_write.R::Bacon.AnaOut` separates the energy column,
while `R/calc.R::Bacon.Age.d` directly integrates the remaining columns.
Reading innovations as physical rates therefore need not reproduce the
age function used by the likelihood.

An actual call to the installed 2.5.3 helper demonstrates the difference on
two synthetic sections, without running a sampler. With top age 0,
innovations 2 and 10, memory 0.5 and thickness 5 cm, the physical first rate
is 6. Integrating that rate gives age 30 at 5 cm; integrating the raw
innovation gives 10.

| Depth (cm) | Helper on raw innovation columns | Helper on physical-rate columns | Independent analytical physical age |
| --- | ---: | ---: | ---: |
| 0 | 0 | 0 | 0 |
| 5 | 10 | 30 | 30 |
| 10 | 60 | 80 | 80 |

The initial one-row mock failed with R's matrix-dimension drop and
`subscript out of bounds`. The corrected observer supplies two identical
synthetic rows so the helper retains its normal matrix shape; it changes no
package code or equation. Those rows are not MCMC draws or observations.

The maintained script ran against the installed 2.5.3 package from committed
source `5123315b23958478fca19b5ca1325e6790fa21d8`, using the reproduction
command below with output `artifacts/physical-core/bacon-source-law-committed.csv`.
It returned exit zero in 0.3039493 seconds; the three raw-helper and physical-rate rows match this
table exactly. No core data or sampler was used.

## Equal-weight saved rows also need a sampling-law check

The 2.5.3 native caller sets a negative save interval, and the t-walk saves
every specified number of accepted joint transitions. Acceptance can change
the partner state while repeating the written state; those repeats do not
restore rejected joint transitions or their holding times. Equal weights on an
accepted-step chain generally do not preserve the target distribution.

An exact finite-state counterexample makes the problem independent of
ABBO or any simulation. Let the target distribution be
`pi = (1/2, 1/3, 1/6)`, with a symmetric proposal to either other state.
Metropolis acceptance probabilities are `q = (1/2, 3/4, 1)`.
The accepted-step invariant distribution is proportional to `pi*q`, giving
`(3/8, 3/8, 1/4)`. This irreducible, aperiodic accepted-step chain retains
that invariant distribution under every fixed number of accepted steps.
It differs from the target despite potentially good mixing diagnostics.
This proves the general concern; it does not measure ABBO bias.

The saved archive supplies no rejected-state dwell counts or weights that
would establish a corrective posterior weighting. Gelman diagnostics and
effective sample size cannot repair a wrong sampling measure. We therefore
refuse to promote these equal-weight rows to a genuine joint age posterior.
Correcting column interpretation alone would not fix that second issue.

The original script also passes deprecated `MinYr`, which 2.5.3 does not
forward to its settings. Its actual default lower bound combines the clock
with each date minus five error arguments. ABBO's source-added calendar
anchor `-52, error=30` gives −202 BP. The prepared protocol therefore names
−202 explicitly; −52 would impose a different, stronger truncation. Neither
value is a newly measured core-top uncertainty.

## A newer method remains a separate possibility

We inspected the official [rbacon 4.0.2 source](https://cran.r-project.org/src/contrib/rbacon_4.0.2.tar.gz)
once, without installing it or fitting a core: 1,208,310 bytes, SHA-256
`be84e057411fde7bfad86af9f1148285ca10adf64af18331a08703ed8f95aa42`.
Its native caller uses a positive, fixed-transition save interval, retaining
rejections. The non-Plum column conversion and direct helper interpretation
still require the same explicit review. A separately named new profile could
combine fixed-transition sampling with source-correct physical-rate extraction,
after its complete law, dependencies and consumer are independently checked.
No silent package substitution or source patch was made.

## The separately declared physical-rate profile

The [new profile](physical-rate-protocol.json) uses rbacon 4.0.2's fixed
transition clock and explicitly transforms its saved innovations into the
physical rates used by the native likelihood. It preserves the refused
archived proposal separately. Both chains retain the same six full precision
source dates and the artificial calendar anchor; only the ABBO target ages
vary. The BUS/BOKE training fits, four predictors, exact 16-label count axis
and bins 3/4/5/9 remain frozen development inputs.

An independent wrapper invokes the unmodified native likelihood's support
and age functions. It checks 64 source-age comparisons, including the actual
nondivisible ABBO depth range, and four source support refusals. An exact
rational observer independently checks those witnesses. The wrapper is a
mathematical source check without MCMC or field observations; it must pass
before the new core run. Agreement with the raw R helper alone is insufficient.

The native oracle replay consumed committed source
`12cd104bfa9600ed31bb3fe6b32bac55cc73cfbc`, returned exit zero in
3.068850917 seconds and retained its outputs under
`artifacts/physical-core/native-likelihood-oracle/`, with artifact-local
`TMPDIR`. All 64 comparisons and four support refusals passed; zero models
were fitted. The maximum native/corrected-helper gap was
`2.2737367544323206e-13` years. Independent exact rational arithmetic found
a maximum native/exact gap of `1.4743761767022079e-12` years. The raw-helper
disagreement reached `59.99992000002` years on these controlled cases;
that number is not an observed ABBO bias.

Two source-preparation failures were retained. First, the updated `rice`
reader required a full IntCal20 file absent from the older directory. The
explicit rintcal 1.4.2 directory supplies that pinned full file and the
byte-identical qualified three-column native curve. Second, the source's
nonempty `th0` argument was not assigned to its returned settings, yielding
`NA` initial ages in the native input. The maintained input adapter assigns
the declared pair to that returned object and calls the unmodified source
writer. No vendor code is patched.

The actual prepare-only consumer then verified a fresh, zero-byte native
output, 51 sections of 5 cm, source support 648–903 cm, seed 314159 and
initial walker ages −52/−22. The requested pollen support remains 648–896 cm.
The 880.5 cm deepest control therefore leaves 15.5 cm extrapolation to the
deepest sample and 22.5 cm to the native model bottom. No radius, country,
taxon/PPE admission or physical basin assumption enters this age model.

Because the requested `d.max=896` exceeds the deepest dated depth of
880.5 cm, the source input writer duplicates the deepest determination at
896 cm and greatly broadens its error. Its generated row has label `NA`,
radiocarbon-age argument **8000 years**, error argument **8,000,000 years**,
reservoir and reservoir-error arguments zero, `t.a=3`, `t.b=4` and `cc=1`.
This is an artificial bottom-extrapolation likelihood term, rather than an
additional measured date, censored date or hard minimum-age bound. It enters
the ordinary IntCal20 Student-t likelihood and is broad but nonconstant.
The native input therefore has eight likelihood rows: six measurements,
one artificial calendar anchor and this generated extrapolation row.
The separately declared `add.bottom=TRUE` appends the model elbow at 898 cm
and gives the native model bottom at 903 cm; it does not generate that row.
Both operations were present in the original preparation and remain
unchanged. No setting or scientific assumption was altered to repair the
directory, and no zero-influence claim is made for the artificial likelihood.

The two fixed seeds request 4,000 retained states each. The complete 7,501
native rows are preserved per chain; frozen source-equivalent burn/tail
selection uses original rows 3502–7501 without further trimming. Saved
parameters have six significant digits; derived ages refer to those same
quantized states. The age and free-parameter diagnostics use the identical
rows. Their acceptance concerns this conditional sampler computation,
rather than chronology accuracy or original core admission; failed
convergence stays refused. Counts, priors and
calibration tables stay fixed, and no shared calibration-curve covariance
is sampled.

The aggregate command has a 600-second wall-clock limit. The 240-second
per-chain figure is a planning estimate. Peak memory is measured by
`time -l`; 1.5 GB memory and 30 MB output are budgets checked after execution,
rather than in-run operating-system caps. Partial and failed chains retain
their actual stage and requested population. Incomplete scoring bins retain
their mass in the all-draw denominator.

Before any core fit, 11 focused tests, strict mypy on eight Python paths and
configured Ruff checks passed. The prepare-only check used the real native
input writer and produced no model draw. The actual run below consumed
committed source and frozen inputs.

The first foreground attempt at committed source
`2556a52701e94cb71232ffe74cf33c7b3c2c7bf8` returned exit 1 in
0.967844916 seconds, before producing draws or a completed chain. The direct
native API concatenates the directory and curve filename; our adapter omitted
its required trailing separator. The failed result and native error remain
under `artifacts/physical-core/abborrtjarnen-joint-chronology/`. Normalizing
the directory and appending `/` repairs that input boundary without changing
source files, observations, priors, seeds, criteria or expected findings.
A bounded native check then opened the qualified curves with zero proposal
iterations. Its one initialization state is retained separately and is not
a posterior draw; no negative-size option was added to the scientific workflow.

## Actual conditional run and refusal

The foreground command consumed committed source
`0d374ce2190e5e44f70c8b28f18612809688af76` with a clean tree and stable
HEAD/index, inputs and shared library throughout. Session 55036 returned
exit zero in **29.720341833 seconds**; peak RSS was **481,722,368 bytes**,
and files before the report occupied **19,996,773 bytes**. Both resource
budgets passed. Raw files, exact command, native inputs, diagnostics and
logs remain in `artifacts/physical-core/abborrtjarnen-fixed-iteration/`.
Both seeds produced 7,501 raw rows and retained the frozen 4,000 each.

| Diagnostic axis | Tested parameters | Failed parameters | Maximum upper 95% Gelman value | Minimum combined ESS |
| --- | ---: | ---: | ---: | ---: |
| 107 sample ages plus memory | 108 | 5 | 1.075272547 | 409.741367 |
| Top age, 51 innovations, memory and energy | 54 | 8 | 1.088025829 | 334.583762 |

The criterion requires every upper value below 1.05 and every ESS at least
400. Five sample ages fail the upper-value criterion; seven innovations
fail ESS and two fail the upper value (one overlaps). The reported status
is **`refused_mcmc_diagnostics`**. The R condition-warning list is empty,
but native stdout separately records 31,680 and 30,438 `WarnBeyondLimits`
warnings for seeds 314159 and 271828, respectively, with the literal message
“calibration attempted beyond MinYr= -202.000000 or MaxYr= 1000000.000000”.
The raw native warnings remain preserved. In the actual 4.0.2 source,
`BaconFix::SetThetas` counts top-age and bottom-age boundary events; it does
not count calibration calls or unique rejected proposals. A top-limit event
rejects support; a bottom age above `MaxYr` increments the counter without
itself rejecting support. Initialization checks can also increment it and
one call can contribute twice. Consequently, the printed counts cannot be
interpreted as rejected-proposal or accepted-evaluation counts, and `MaxYr`
is not an independently enforced hard bottom-age bound in this branch.

A read-only check of all 7,501 saved rows per chain found zero top-age
violations of [−202,1,000,000] BP and zero physical bottom ages above
1,000,000 BP. Top-age ranges were −201.858 to 206.071 and −200.240 to 177.797
BP; physical model-bottom ranges at 903 cm were 7459.926–11062.939 and
8618.423–11398.243 BP. These finite saved-state checks do not establish an
unobserved proposal history or posterior convergence. No seed, prior,
retention rule or criterion was changed, and no extra chain or retuned fit
was run after inspecting this outcome.

All 8,000 states contain positive count mass in all four requested bins:
there are zero empty-bin, zero-mass-bin or incomplete-score refusals. Signed
ages remain unchanged: the chains contain 6,877 and 7,107 negative age cells,
respectively; no retained age exceeds 50,000 BP. These are dependent age cells,
not counts of independent observations. R extraction and independent Python
integration agree within `9.094947017729282e-12` years on all 856,000 values,
below the frozen absolute `1e-8` tolerance.

| Frozen predictor | Mean MAE across saved states | Strict lowest score / all 8,000 states |
| --- | ---: | ---: |
| training_mean | 0.077602985 | 0 / 8000 |
| nearest_site | 0.067704040 | 8000 / 8000 |
| inverse_distance_squared | 0.077466063 | 0 / 8000 |
| clr_rbf_ridge | 0.075153104 | 0 / 8000 |

MAE is in closed-16-label fraction units, equally weighted over four bins.
These are saved-state descriptors, not qualified posterior means or ranking
probabilities. The nearest-site predictor scores lowest on this saved
population; failed diagnostics prevent interpreting its frequency as a
converged posterior result. The complete JSON retains descriptive quantiles
and all paired differences without promoting them to confidence intervals.

The independent checker consumed the same committed source, returned exit
zero in **0.996835542 seconds**, and fitted no model. It checked all 15,002
raw rows, all 107 sample/depth identities, 8,000 saved age/score rows, every
bin count and mass, all method refusals, paired differences and diagnostic
thresholds. Exact rational count closure and prediction arithmetic agree
within absolute `2e-15` score tolerance, relative tolerance zero. This verifies
computation on the saved population while preserving its scientific refusal.
The model/native-boundary/observer selection also passed 23 focused tests;
configured Ruff, strict mypy and R parsing passed for the changed surfaces.

Reproduce the model command from the repository root, substituting a fresh
absent artifact output. It remains a failed prespecified experiment; this
command is supplied for inspection, rather than an instruction to tune it.

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 .venv/bin/python -B -m \
  bijux_pollenomics_dev.source_completion.pollen_age_support.abborrtjarnen_bacon \
  --repository "$PWD" --source-root "$PWD/../-bijux-pollenomics-data" \
  --library "$PWD/artifacts/qualification/native-reference/library" \
  --oracle-summary "$PWD/artifacts/physical-core/native-likelihood-oracle/summary.json" \
  --output "$PWD/artifacts/physical-core/abborrtjarnen-fixed-iteration"
```

The independent saved-result check uses the existing output and an absent
artifact destination:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B \
  packages/bijux-pollenomics-dev/tests/source_completion/pollen_age_support/abborrtjarnen_bacon/test_independent_result.py \
  --repository "$PWD" \
  --result "$PWD/artifacts/physical-core/abborrtjarnen-fixed-iteration" \
  --output "$PWD/artifacts/physical-core/abborrtjarnen-fixed-iteration/independent-check.json"
```

These findings do not change the retained LegacyAge S5 marginal intervals,
the earlier set-based age bounds, or their conditional pollen sensitivities.
They do not retrospectively correct or quantify bias in a published result.
They identify why the proposed probabilistic extension cannot yet use the
archived route as written. The original chronology and real-core acceptance
remain open; no human approval or additional field evidence is implied.

## Reproduce the bounded helper check

The following is the historical command for the committed helper witness.
It requires rbacon **2.5.3** in the specified library. The present shared
library contains 4.0.2, so this command is not executable against that runtime;
the original version guard must remain unchanged. The archived source and
qualified earlier outputs remain available. No second library was created.

Historical invocation from the repository root:

```sh
R_LIBS_USER="$PWD/artifacts/qualification/native-reference/library" \
R_LIBS_SITE='' Rscript --vanilla \
  packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/pollen_age_support/abborrtjarnen_bacon/source_law.R \
  "$PWD/artifacts/qualification/native-reference/library" \
  "$PWD/artifacts/physical-core/bacon-source-law.csv"
```

The output must be absent. The analytical ages use the same stated physical
rate law, independently of the helper. The script asserts both exact vectors
and writes the three inspection rows. The failed one-row attempt and corrected
two-row direct call precede this maintained script; no core fit, convergence
claim or posterior score follows from this controlled witness.

## Separately fixed sampler-accuracy qualification

The [sampler-accuracy protocol](sampler-accuracy-protocol.json) prespecifies
16,000 retained states for each original seed, 32,000 in total. It preserves
the failed 8,000-state experiment above. The original no-retry rule prohibits
extra chains, changed seeds, wider criteria and outcome-tuned priors; it does
not prohibit separately declared numerical accuracy work on the same two
trajectories. This qualification fixes one larger terminal length and permits
no further escalation, new seed or alternative prior after its outcome.

Stock rbacon writes both terminal walkers to `.last` at six significant
digits but does not checkpoint its private random-generator state. Loading
those rounded values through `.init` is a restart, not exact continuation.
Instead, the unchanged fixed-transition sampler is invoked from its original
starts and seeds with native size argument 16,500. Its transition kernel does
not adapt to the requested length; saved states remain 1,325 proposals apart.
The two newly prepared native executable input programs must match the originals
before sampling. Only the recognized first `## Ran on` timestamp comment is
excluded from that comparison; every remaining input byte stays exact. Each complete 19,501-state stream must then begin with its original
5,678,254-byte stream exactly, including the leading blank line and absent
final newline. A numerical tolerance or reformatted row comparison cannot
substitute for that byte check. Original one-based rows 3502–19501 are retained
once; the old retained prefix is not an independent additional sample.

All data, eight likelihood terms, priors, calibration files, native binary,
initial pairs and diagnostic thresholds remain fixed. Every original age,
memory, innovation, top-age and energy criterion must pass. Both prefixes,
joint-age extraction and resource checks precede the frozen score consumer.
A failed gate retains native states, ages and diagnostics with an explicit
unscored refusal. If final storage exceeds the budget after scoring, raw score
files remain, while interpreted descriptors are withheld and the result is
labelled `computed_then_refused_final_resources`. Previously exposed predictions
and failed-run scores do not become untouched validation.

The 600-second native deadline and 1.5 GB measured RSS budget are unchanged.
The separate output ceiling is 100,000,000 bytes, checked after execution.
The original layout contains 20,022,943 bytes: about 11.36 MB native states,
8.24 MB compressed ages and 0.36 MB compressed scores. Native rows increase
by about 2.6 times, while retained age and score exports increase fourfold;
the corresponding estimate is 63,967,189 bytes. The ceiling leaves about
56% headroom over that estimate, without claiming guaranteed compression or
an operating-system storage quota. The original directory stays untouched.

No native fit for this qualification ran during source preparation.
Controlled checks cover literal prefix boundaries, source/runtime identity,
unchanged target inputs, score withholding and resource failures. The first
author invocation passed its source-binding control but had eight fixture
setup errors because its artifact basetemp parent was absent; creating the
parent resolved that setup failure. Separately, the independent observer's
initial invocation had five setup errors and nine passing arithmetic checks;
the same output-parent correction allowed all fourteen controls to pass.
Neither setup correction changed scientific inputs or diagnostic criteria.

The first committed invocation at `39cff6d1c1a345850c1efa1c190d26e690ff01c4`
(owned session 54342) terminated with exit 1 before the first sampler call.
Its guard compared the entire native input including a generated timestamp;
only that first comment differed. Native output was zero bytes and the saved
chain list was empty. The process took 2.59 s, with peak RSS 175,374,336 bytes;
the R preparation command took 1.281334 s with peak RSS 173,424,640 bytes.
That failed attempt remains in `abborrtjarnen-sampler-accuracy/native-run` and
its adjacent execution account. The native parser ignores `#` comment lines
before any model or random-generator operation (`rbacon 4.0.2 src/input.cpp`,
lines 93–100). The repaired guard excludes only the recognized first generated
timestamp and compares all remaining bytes exactly. No scientific observation,
prior, seed, sampler length or diagnostic threshold changed. Nineteen independent controls, configured lint/types and a precommit direct R
input-guard check pass; the latter evaluated only the repaired function against
the original and failed-preparation inputs, with zero sampler calls. A fresh
`native-replay` destination preserves the zero-fit preparation failure.

After source review and commit, the existing command selects this protocol
with `--sampler-accuracy` and a separate absent output directory:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m \
  bijux_pollenomics_dev.source_completion.pollen_age_support.abborrtjarnen_bacon \
  --repository "$PWD" --source-root "$PWD/../-bijux-pollenomics-data" \
  --library "$PWD/artifacts/qualification/native-reference/library" \
  --oracle-summary "$PWD/artifacts/physical-core/native-likelihood-oracle/summary.json" \
  --output "$PWD/artifacts/physical-core/abborrtjarnen-sampler-accuracy/native-replay" \
  --sampler-accuracy
```
