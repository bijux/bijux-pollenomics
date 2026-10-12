# Native R comparison for the published LOVE workload

The [retained result](report.json) closes the identical-input comparison left
open by the [published workload profile](../love-source-profile/README.md).
The profile's `love-optimized-replay` contract uses the packaged `LOVEexample`:
one local and one regional pollen row, 10 taxa, 36 rings, a maximum local ring
of 10, two deterministic repeats, and the same 32 fixed candidate vectors at
each supported ring. Its contract SHA-256 is
`478b28478239789509a9dff15e0d6bb84d4428a363df5bf59eb3e26e16e16b2a`.

The [producer](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/numerical-performance/love-source-comparison/compare.py) exports pollen, parameters, rings, and the candidate
matrix to one CSV input set. Each numeric CSV has a hexadecimal-float sidecar
that preserves the exact binary values across R and Python decimal parsers.
It checks the exported numbers against the packaged values and checks R's
parsed doubles and labels against Python's. Then **both** the current Python
public `run_love` call and native source-R `LOVEoptim` read those same files.
Without the sidecars, base R's decimal parser differs by one binary unit in
some candidate and ring cells, despite identical CSV text.
The [R replay](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/numerical-performance/love-source-comparison/replay.R) uses the installed DISQOVER 0.9.14 source with R 4.6.0.
Only regional/local random sampling and RcppDE's search are replaced by
deterministic samplers and fixed-candidate evaluation, using the maintained
source oracle support file. Each engine evaluates 32 candidates at each of eight active
ring/repeat combinations. The other six requested rings have undefined local
results because they contain no terrestrial area.

| Paired output | Shape | Finite pairs | Maximum absolute difference |
| --- | ---: | ---: | ---: |
| Ring factors `K` | 36 × 10 | 360 | 5.11e-15 |
| Mean local cover | 10 × 10 | 40 | 0 |
| Mean local pollen | 10 × 10 | 40 | 0 |
| Best objective | 10 × 2 | 8 | 4.67e-15 |

Column names, shapes, and undefined cells also agree. The eight selected
candidate indices agree; all are row 1 of this particular monotone candidate
set. The predeclared comparison tolerance is `3e-10` absolute plus `1e-10`
relative. This establishes **identical-input source-method agreement for this
fixed-candidate LOVEexample call**. It does not compare RcppDE with SciPy search
trajectories, optimizer convergence, stochastic draws, timing, ecological
accuracy, or an independent reconstruction of the paper's simulated landscape.
The source example is a computational fixture.

The retained JSON binds the profiled workload contract, all 56 unchanged
profile source files, the DISQOVER source archive, the replay producers, the
ten shared input files. Native R checked its version, DISQOVER version, and
installed source archive identity before execution. Raw
inputs, paired arrays, R session details, stdout/stderr, and command context
are generated under the chosen `artifacts/jobs/` output directory.

Reproduce from the repository root after preparing the pinned isolated R
library described in the [current R oracle](../../method-certification/current-r-oracle/README.md):

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python docs/report/numerical-performance/love-source-comparison/compare.py \
  --output artifacts/jobs/love-source-contract-replay \
  --library artifacts/jobs/native-r-reproduction/library
```

The output directory must be absent before the command. The producer refuses
changed source bytes relative to the published workload profile, so a later
engine change requires a new measured comparison rather than inheritance of
this result.
