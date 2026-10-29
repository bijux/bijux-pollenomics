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


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Numerical/runtime comparison reader; method correspondence and empirical/historical accuracy acceptance remain separate even when performance measurements pass.

**Supported claim.** The retained R 4.6/DISQOVER 0.9.14 and Python comparison agrees on one exactly shared LOVEexample input set with deterministic fixed candidates and preserved missing values.

**Unsupported claim.** Fixed-candidate correspondence supplies no optimizer trajectory or convergence comparison, stochastic draw parity, timing comparison or empirical vegetation accuracy.

**Actual verification performed.** Read the authored method and retained native-R identity, shared decimal/hexadecimal input account and comparison tolerances; bound the physical report. No R, model or comparator was executed for this qualification. Separately, a new conditional LOVE objective report binds completed R and public Python stages from source commit 123c7811e49cc692c32015826c029b8ad99e96d8. Their original whole jobs remain failed; a separate saved-product observer passed. The new report preserves 256 R search returns, 256 Python search returns, eight mandatory Python certifications and the original undefined rings. This does not replace this page's historical source gate, flags or timings.

**Remaining input or review.** A different candidate, random-draw algorithm or ecological landscape needs its own source-bound comparison and qualified interpretation; this historical result does not certify a later release.

**Cause category.** Bounded historical source-method correspondence on a computational fixture.

**Consequence.** Agreement can support this exact fixed-candidate calculation while leaving optimizer and ecological claims unadmitted.

**Precise next acceptance route.** For a changed mathematical surface, declare identical inputs and candidate semantics before the named native R and Python comparison, preserving undefined rings and the original tolerances.

**Negative or refused result.** Six local rings remain undefined, and choosing candidate one in every active call is retained without asserting optimizer convergence.

**Matched denominator.** One local and one regional row, ten taxa, 36 rings, maximum local ring ten, two repeats, eight active ring/repeat calls with 32 candidates each (256 evaluations); five decimal tables plus five hexadecimal sidecars. Absolute tolerance 3e-10 and relative 1e-10.

- [Retained qualification evidence: docs/report/numerical-performance/love-source-comparison/report.json](report.json) (SHA-256 `73655d3f9ba41d3c20b7db5fa43360a60ded61d70d1603a1628cf7a6de8b6413`).

- [Retained qualification evidence: docs/report/method-certification/love-objective-parity/report.json](../../method-certification/love-objective-parity/report.json) (SHA-256 `b225e6034dd4dd39a6ede63918d7e2a4a9980a49fcc41e73e0498a784f0ff8e8`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
