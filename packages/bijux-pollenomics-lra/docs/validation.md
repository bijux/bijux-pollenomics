# Numerical validation and limits

The live oracle installs the received `vendor/disqover_0.9.14.tar.gz` into an
isolated R library, checks its source SHA-256 marker and version, and retains
`R_session_info.txt`, per-case CSVs, commands and comparison errors. Exact source
SHA-256: `ea496ae82807b52c9dd3d4b39b4dfa294bfac4068e20184ce56187bff70caf5c`.

Run the ordinary numerical tests with the shared repository configuration:

```sh
python -m pytest -c configs/pytest.ini packages/bijux-pollenomics-lra/tests -m "not live_r"
```

The required live-R path belongs to the development package, not the runtime
wheel. `configs/ci/lra-r-source-lock.v1.json` pins the R source, all required package
archives, versions, dependency edges, source-license pointers and numerical
runtime policy. Acquisition verifies these bytes; provisioning installs only the
verified local sources into a private library. It does not resolve rolling CRAN
packages or install into a global library.

From the repository root, the dependency stages are:

```sh
make -C packages/bijux-pollenomics-lra -f ../../makes/packages/bijux-pollenomics-lra.mk reference-fetch
make -C packages/bijux-pollenomics-lra -f ../../makes/packages/bijux-pollenomics-lra.mk reference-build-r
make -C packages/bijux-pollenomics-lra -f ../../makes/packages/bijux-pollenomics-lra.mk reference-provision
make -C packages/bijux-pollenomics-lra -f ../../makes/packages/bijux-pollenomics-lra.mk test-live-r
```

Use the repository's managed background execution for these builds and gates.
`ACT` identifies the installed development Python environment. `LRA_REFERENCE_ROOT`
selects an isolated run directory; failed outputs remain evidence, and a new run
uses a new directory. The authored
[certification workflow](../../../.github/workflows/lra-reference.yml) declares
Linux system prerequisites and records their installed versions.

The certificate retains source, runtime, library and executed-input identities,
raw outputs and distinct case inventories. The release gate requires the latest
relevant completed same-revision workflow and attempt, its actual named job, and
the complete digest-bound artifact. Missing, failed, expired or incomplete
evidence refuses publication; a prepared case list is insufficient. Local R
comparisons do not establish that the Linux source-build workflow has run.

The core oracle contains 25 predeclared deterministic, shared-draw and
candidate-replay cases covering all nine translated source API functions. It is
numerical evidence for those cases, not ecological accuracy, uncertainty coverage
across all domains, unconstrained optimizer convergence or independent held-out
vegetation performance. Expanded scientific workloads remain governed backlog work.

The first actual R run exposed two 1/d LOESS differences and one test sampler
coercion failure. Correcting the LOESS kd-tree allocation cap to match R and
coercing the test-only R probability dataframe fixed these without tolerance
relaxation. Retained regression tests also cover adjacent floating-point series
coordinates, duplicate dataframe indexes, uncertainty-draw hashes, failed optimizer
refusal, parameter normalization collisions and timestamp-independent identities.

Forward pollen predictions use closed local cover fractions, positive PPEs,
nonnegative ring kernels, terrestrial fractions in [0,1] and already PPE-weighted
regional deposition. The profile is homogeneous across local rings. Returned
local, regional and total deposition remain separately inspectable; no observation
at a held-out site is an implicit input to this numerical API.

A separate required source-domain suite contains 23 cases: four source-wrapper
refusal cases, six supported boundary exceptions and thirteen corrected forward
geometry cases. These retain their own profile and denominator alongside the
25-case core suite. The target preparation API preserves the taxon axis across
single-ring slices and records its intentional corrected-matrix profile; it does
not silently claim parity with erroneous source recycling in those slices.
