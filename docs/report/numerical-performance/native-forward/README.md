# Measured native forward boundary

The [retained comparison](report.json) evaluates a standalone C++17 batch through
a private C buffer interface, the optimized NumPy batch and an independent R
matrix equation. All use the same deterministic binary64 covers, kernels,
fractions, PPE and regional deposition. These are numerical stress arrays, not
observed pollen or independent vegetation measurements. Every input hash and
source/toolchain identity is retained. The compact report stores scientific-output
digests, exact comparison errors and timing blocks. Raw R results are retained
beside it; local compiler commands and large Python/native output arrays are
execution diagnostics.

| Cover rows | Rings | Taxa | NumPy/native validated batch latency ratio | Largest difference from public Python |
|---:|---:|---:|---:|---:|
| 1 | 8 | 3 | 0.928× | 2.22e-16 |
| 32 | 128 | 32 | 0.897× | 9.71e-17 |
| 512 | 256 | 64 | 0.722× | 8.33e-17 |

A ratio below one means the native path is slower. All three tested shapes fail
the prospectively declared 2× latency benefit. **Retain the optimized NumPy batch
for this forward boundary; do not adopt this private C++ interface.** This is a
scoped performance result, not a waiver of the wider native investigation. It
does not rule out other bindings, objective kernels, cached geometry or workloads.

The independent R equation, optimized NumPy and native output each agree with
the public Python forward workflow within absolute `1e-12` and relative `1e-10`
tolerances. This R equation comparison is distinct from source DISQOVER parity.
The public Python reference computes its full inspectable deposition result;
measured batch interfaces return owned pollen fractions only. No complete public
API replacement, optimizer convergence or backend adoption is certified here.

## Measurement and ownership

Each method has one warmup and nine timed blocks: 200 calls per block for the
first two shapes, 40 for the largest. The report retains every per-call timing,
compute-only paths, complete batch validation/conversion paths and the shared
conversion/validation cost separately. C++ additionally validates its numeric
buffers during computation, and that cost is counted. R latency includes process
startup, input loading, equation and export, so it is not a kernel speed ratio.

The signature is bound once after compilation. Python converts arrays to aligned,
contiguous native binary64 buffers explicitly; copies are included in facade
latency when required. Inputs stay alive through the synchronous call. The native
function does not mutate them, exceptions stay inside the C boundary, and outputs
own their storage. Read-only and strided inputs, dimensions, post-validation NaN
mutation, zero mass and two concurrent calls have focused regressions.

The installed Apple clang compiled with `-std=c++17 -O3 -fPIC -dynamiclib`; no
fast-math, dependency installation or production packaging change was used.
The compiler/binary hashes and R version are in the report. The numerical thread
variables were one. The two-call concurrency regression is an explicit bounded
ownership check, not a parallel scaling measurement.

An [isolated worker measurement](../native-memory/README.md) now records per-method
process peak RSS and startup/export cost on the same machine. Other platforms,
alternate bindings, cancellation, platform wheels, source-R parity, SBOM and
complete-pipeline throughput remain separate acceptance surfaces. The binary is
a regenerable root artifact; the standalone C++ source, Python producer and R
equation are retained in the development package. Ordinary runtime installation
gains no compiler dependency.

## Reproduce

Use the installed compiler and R interpreter with a fresh artifact destination:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
.venv/bin/python -m bijux_pollenomics_dev.native_backend.forward_compare \
  --repository "$PWD" \
  --output "$PWD/artifacts/numerical-performance/native-forward" \
  --compiler /usr/bin/clang++ --rscript /usr/local/bin/Rscript
```

The comparison producer refuses an existing destination and checks its numerical
input/source closure after measurement. Select the reader result from that raw
measurement and the retained R reference files:

```sh
.venv/bin/python -m bijux_pollenomics_dev.native_backend.forward_summary \
  --raw-report artifacts/numerical-performance/native-forward/report.json \
  --reference-root docs/report/numerical-performance/native-forward \
  --output artifacts/numerical-performance/native-forward-summary.json
```

The summary producer checks every input CSV identity, R result, output shape,
numerical comparison, timing block and adoption ratio before selecting fields.
Platform-dependent timing is not reproduced bit for bit; source, shape,
numerical tolerance and refusal contracts are explicit.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Numerical/runtime comparison reader; method correspondence and empirical/historical accuracy acceptance remain separate even when performance measurements pass.

**Supported claim.** The private C++17 forward spike matches the declared NumPy and independent R-equation outputs within absolute 1e-12 plus relative 1e-10 on three synthetic shapes, while failing its full-call speed gate.

**Unsupported claim.** Independent equation agreement is not original DISQOVER domain parity, production ABI adoption, portable packaging, parallel scaling or whole-workflow acceleration.

**Actual verification performed.** Read the retained compiler/platform, prospective gate and conversion-inclusive measurement scope and bound report bytes; no compilation, R or timing runs were repeated.

**Remaining input or review.** A production proposal needs representative whole-call benefit, complete source parity and supported-platform distribution/ABI ownership before adoption.

**Cause category.** Numerical spike verification with a negative performance decision.

**Consequence.** Correct arithmetic in a standalone candidate does not justify adding its native binary to the production package.

**Precise next acceptance route.** Retain validated facade/conversion costs and the twofold speed and 1.25 RSS-ratio gates in a newly declared representative comparison before changing adoption.

**Negative or refused result.** Validated ratios 0.928, 0.897, 0.722 are slower than NumPy and below 2.0. A two-call concurrency check is not a scaling experiment.

**Matched denominator.** Three batch/ring/taxon shapes: 1×8×3, 32×128×32, 512×256×64; one warmup, nine blocks, 200 calls per block for the first two and 40 for the largest. Original DISQOVER parity and isolated RSS are separate scopes.

- [Retained qualification evidence: docs/report/numerical-performance/native-forward/report.json](report.json) (SHA-256 `4d16a1400d6878f2abf21f796fb190dd72a365f0dd40295639b8635bd807d1d5`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
