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

Status meanings:

- `passed`: R executed and every numerical/string comparison passed.
- `failed`: R executed but a case or setup assertion failed.
- `blocked`: R, package installation, dependencies, compiler, or setup were
  unavailable. This is not a pass.
- `prepared_not_executed`: scripts and inputs were generated intentionally
  without running R.
