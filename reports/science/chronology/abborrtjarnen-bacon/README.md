# Why the archived Bacon route is refused for joint ABBO age uncertainty

We prepared a new ABBO chronology to ask how shared age uncertainty affects
four existing frozen pollen predictors. Source inspection and independent
review identified two reasons to refuse the proposed equal-weight posterior
route **before any core was fitted**. No ABBO age draw, score or admission
result was produced. The [proposed protocol](protocol.json) preserves the
question and its source assumptions; it is not an executed study.

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

These findings do not change the retained LegacyAge S5 marginal intervals,
the earlier set-based age bounds, or their conditional pollen sensitivities.
They do not retrospectively correct or quantify bias in a published result.
They identify why the proposed probabilistic extension cannot yet use the
archived route as written. The original chronology and real-core acceptance
remain open; no human approval or additional field evidence is implied.

## Reproduce the bounded helper check

From the repository root, with the existing shared library:

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
