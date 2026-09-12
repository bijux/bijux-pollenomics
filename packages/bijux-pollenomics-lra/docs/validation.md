# Numerical validation and limits

The live oracle installs the received `vendor/disqover_0.9.14.tar.gz` into an
isolated R library, checks its source SHA-256 marker and version, and retains
`R_session_info.txt`, per-case CSVs, commands and comparison errors. Exact source
SHA-256: `ea496ae82807b52c9dd3d4b39b4dfa294bfac4068e20184ce56187bff70caf5c`.

Package-scoped commands, run through the completion program's background job manager:

```sh
python -m pytest -c packages/bijux-pollenomics-lra/pyproject.toml packages/bijux-pollenomics-lra/tests
python packages/bijux-pollenomics-lra/tests/reference/lra_oracle/install_reference.py --library artifacts/v2/engine/r-library
python packages/bijux-pollenomics-lra/tests/reference/lra_oracle/run_live_r.py --library artifacts/v2/engine/r-library --output artifacts/v2/engine/live-r
```

The current oracle contains 25 predeclared deterministic, shared-draw and
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
