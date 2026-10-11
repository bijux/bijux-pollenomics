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
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q \
  -o cache_dir=artifacts/jobs/lra-parity/cache \
  --basetemp=artifacts/jobs/lra-parity/tmp \
  packages/bijux-pollenomics-lra/tests/reference/test_parity.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m bijux_pollenomics_dev.lra_validation.reference_replay \
  --repository . \
  --bundle docs/report/method-certification/original-r-reference/reference-bundle \
  --output artifacts/jobs/lra-parity/reference-replay
```

Run these from the repository root with absent output paths. The second command
compares current Python to authenticated retained R vectors. Live R preparation
and execution are separate source-locked operations described by the
[local Linux oracle](../../../../docs/report/method-certification/linux-r-oracle/README.md).
The engine installs no console script; the host owns its LRA commands.
The host's `bijux-pollenomics validate-lra-input REQUEST --input-root ROOT`
validates the evidence and configuration. Its
`bijux-pollenomics run-lra REQUEST --input-root ROOT --output DIR` writes a new
exploratory product. `run-lra-batch` takes a batch request plus `--input-root`,
`--cache-root`, and `--report-root`; `render-lra-report` reads a saved product
with pinned manifest and geometry hashes. These command names and required
arguments are defined by the host's
[`lra.py`](../../../../packages/bijux-pollenomics/src/bijux_pollenomics/command_line/parsing/subcommands/lra.py)
parser; source helper names in the table below are implementation functions,
not console commands.

## Source-to-test map

The vendored DISQOVER 0.9.14 archive is the R source for every compatible row.
The [adoption manifest](../adoption-manifest.json) accounts for the received
Python files and definitions; the [architecture map](../architecture-migration.json)
assigns their current owners. These rows bind the numerical equations and R
entry points to current tests and retained case IDs.

| Source R entry point and equation | Engine owner | Direct tests and R cases |
| --- | --- | --- |
| `R/dispersal_models.R`: `DispersalFactorK`, LSM/GPM and basin deposition | `dispersal/kernels.py`, `dispersal/loess.py` | `tests/unit/dispersal/test_dispersal.py`; C0000–C0014 |
| `R/REVEALS.R`: `REVEALS`, `REVEALSinR`, cover ratio and pollen/PPE sampling | `reconstruction/regional.py`, `reconstruction/draws.py`, `workflows/regional.py` | `tests/unit/reconstruction/test_reveals.py`; C0015–C0018 |
| `R/lover.R`: `lov`, `LOVEr`, analytical local cover from local pollen and regional background | `reconstruction/analytical.py`, `workflows/local.py` | `tests/unit/reconstruction/test_love.py`; C0019 and C0023 |
| `R/loveoptim.R`: `calK`, `tf`, `logeuclidean`, `LOVEoptim`, forward deposition and bounded objective | `reconstruction/optimized.py`, `optimization/solver.py` | `tests/unit/reconstruction/test_love.py`, `tests/unit/optimization/test_solver.py`; C0020–C0022 and C0024–C0042 |

The source-specific ring geometry, draw rounding, and unsupported source shapes
are recorded in [source compatibility](source-compatibility.md). The separate
historical multi-site aggregation and corrected uncertainty equations are
identified in their own method reports; the DISQOVER rows do not certify them.

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
