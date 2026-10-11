# Isolated forward worker memory

The [retained measurement](report.json) ran the same deterministic finite forward
batch through optimized NumPy and the private C++17 buffer interface. It adds
isolated process RSS and worker startup/export timing to the [in-process
comparison](../native-forward/README.md). These arrays are numerical stress
inputs, not observed pollen or vegetation. The two methods received identical
input hashes and their exported fractions matched within absolute `1e-12` and
relative `1e-10` tolerances in every repetition.

| Cover rows × rings × taxa | Median NumPy peak RSS | Median native peak RSS | Native / NumPy peak | Median NumPy call | Median native call |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 × 8 × 3 | 167.7 MB | 168.3 MB | 1.004 | 0.023 ms | 0.041 ms |
| 32 × 128 × 32 | 169.2 MB | 167.8 MB | 0.992 | 0.033 ms | 0.047 ms |
| 512 × 256 × 64 | 168.4 MB | 168.5 MB | 1.001 | 0.097 ms | 0.156 ms |
| 8192 × 256 × 512 | 305.7 MB | 274.7 MB | 0.899 | 12.397 ms | 14.488 ms |

The first three shapes repeat the in-process comparison's scale. Their calls
never exceeded the RSS high water mark already set by Python/NumPy import and
input preparation, so a zero reported call increment is **not** a zero
allocation claim. The added large stress shape makes the output and NumPy
intermediates visible in process RSS: all five NumPy calls raised the high water
mark by about 33.6 MB, while native calls did not. Its native process peak was
about 31 MB lower, but the native call remained slower. The five full-worker
times per method and shape, including import, library loading, input creation,
and NPY export, are retained in the report. At these scales startup dominates
the worker totals, so small differences in them are not a kernel speed claim.

Each method ran five independent workers per shape with numerical threads set
to one. The compiler and binary identities, source hashes, every raw call and
whole-worker duration, and pre/post process RSS are in the report. macOS
`ru_maxrss` is recorded in bytes; the producer converts Linux KiB to bytes.
The large shape was added after the first three-shape run revealed the import
high-water blind spot; it is an exploratory memory stress, not a prospectively
declared adoption gate. The earlier diagnostic remains in the local
`artifacts/jobs/native-memory/measured-apple-clang/` run directory.

**Keep the optimized NumPy path for this forward boundary.** The prior
validated-facade comparisons failed the declared 2× native latency benefit at
all three original shapes. Lower RSS on one synthetic large worker does not
meet that adoption criterion. This decision does not certify a complete
LOVE/REVEALS replacement or waive other native acceptance clauses. The C++
binary remains an experimental regenerable artifact; ordinary installation
has no compiler dependency. Source DISQOVER oracle parity, other platforms,
packaging and full-pipeline throughput require separate evidence.

## Reproduce

From the repository root, use a fresh root-artifact destination:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 \
.venv/bin/python -m bijux_pollenomics_dev.native_backend.memory_compare \
  --repository "$PWD" \
  --output "$PWD/artifacts/jobs/native-memory/reproduction" \
  --compiler /usr/bin/clang++
```

The producer requires an absent output directory under `artifacts/`, verifies
source/input/output hashes and numerical parity, and refuses undeclared shapes.
Peak RSS and timing depend on the operating system and current process state.
