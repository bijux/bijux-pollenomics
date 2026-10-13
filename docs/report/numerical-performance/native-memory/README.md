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
| 1 × 8 × 3 | 166.2 MB | 167.2 MB | 1.006 | 0.018 ms | 0.026 ms |
| 32 × 128 × 32 | 166.5 MB | 167.2 MB | 1.004 | 0.026 ms | 0.032 ms |
| 512 × 256 × 64 | 166.4 MB | 167.2 MB | 1.005 | 0.078 ms | 0.133 ms |
| 8192 × 256 × 512 | 304.6 MB | 273.5 MB | 0.898 | 9.388 ms | 12.507 ms |

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
to one. The compiler flags and binary identity, source hashes, every call and
whole-worker duration, and pre/post process RSS are in the report. Local
build-output paths are excluded. macOS
`ru_maxrss` is recorded in bytes; the producer converts Linux KiB to bytes.
The large shape exposes memory beyond the import high-water mark. It is an
exploratory memory stress, not a prospectively declared adoption gate.

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
MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 \
.venv/bin/python -m bijux_pollenomics_dev.native_backend.memory_compare \
  --repository "$PWD" \
  --output "$PWD/artifacts/jobs/native-memory/reproduction" \
  --compiler /usr/bin/clang++
```

The producer requires an absent output directory under `artifacts/`, verifies
source/input/output hashes and numerical parity, and refuses undeclared shapes.
Peak RSS and timing depend on the operating system and current process state.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Numerical/runtime comparison reader; method correspondence and empirical/historical accuracy acceptance remain separate even when performance measurements pass.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md) (source SHA-256 `81407d77987fd391ea470cc975195107085cdf7a934a6716aac7a1b22cb19050`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
