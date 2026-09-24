# Parity design

## Claims

| Layer | What it establishes | What it does not establish |
|---|---|---|
| Unit/integration tests | Python equations, validation, shapes, contracts and reproducibility | R equivalence |
| Stored R-model checks | Evaluation and independent refit of 45 serialized R LSM curves | Live R wrapper parity |
| Live DISQOVER oracle | Actual R/Python output agreement for prepared cases | Ecological validity |
| Candidate replay | LOVE objective/wrapper agreement on identical candidates | Identical optimiser trajectories |
| Supplied draw tests | Stochastic wrapper agreement on identical draws | Equal R/NumPy RNG streams |

## Exact reference

The live oracle accepts only:

- package `disqover`
- version `0.9.14`
- source archive SHA-256
  `ea496ae82807b52c9dd3d4b39b4dfa294bfac4068e20184ce56187bff70caf5c`

The isolated R installation receives a `SOURCE_SHA256` marker. The oracle checks
both package version and marker before any comparison.

## Commands

```bash
python -m pytest -q
bijux-pollenomics-lra parity stored --output reports/stored_parity.json
python tests/reference/lra_oracle/run_live_r.py --prepare-only
python tests/reference/lra_oracle/install_reference.py
python tests/reference/lra_oracle/run_live_r.py
```

The live suite covers `DispersalFactorK`, `REVEALS`, `REVEALSinR`, `lov`,
`LOVEr`, `calK`, `tf`, `logeuclidean`, and `LOVEoptim`. Prepared Python arrays
are saved as `python_expected_not_R_goldens.npz` to make their provenance
unambiguous.

The optimized-LOVE suite includes a checked prospective declaration for three
source-compatible multi-ring cases. Input counts, shared replay candidates,
the exact DISQOVER archive and resource hashes, and `1e-10` absolute and
relative tolerances are committed before reference execution. The threshold is
fixed independently of prospective R results. It permits only floating-point
drift far below the source wrapper's `1e-4` cover and `1e-2` pollen rounding;
failure blocks this parity claim rather than permitting a retrospective
tolerance change.

The gate checks `calK`, exact taxon and ring axes, deterministic regional cover
and deposition, every candidate objective against the wrapper's normalized
local pollen input, the exact selected candidate, rounded cover and pollen
output, and exact replay iteration, evaluation-count, and success fields.
All-zero cover probes must remain nonfinite. The replay harness must refuse an
all-nonfinite candidate set with its specific declared error; this is not a
claim about native DEoptim refusal behavior. Stochastic optimizer trajectories
are excluded, and synthetic parity is not ecological validation.

Status meanings:

- `passed`: R executed and every numerical/string comparison passed.
- `failed`: R executed but a case or setup assertion failed.
- `blocked`: R, package installation, dependencies, compiler, or setup were
  unavailable. This is not a pass.
- `prepared_not_executed`: scripts and inputs were generated intentionally
  without running R.
