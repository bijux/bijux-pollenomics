# Runtime metadata cost in LRA reconstruction

The [baseline profile](../python-baseline/report.json) identified repeated package
metadata parsing in paired reconstruction. The runtime manifest now caches the
installed NumPy, SciPy and pandas version strings within one immutable numerical
worker environment. Each manifest still receives its own runtime mapping.
Missing distributions retain the original `unknown` value; versions remain in
scientific identity. No kernel, sampler, optimizer, configuration or numerical
output rule changed.

The [measured result](report.json) repeats the same seven frozen workloads, with
one first call, seven warm timings and one separate profile call each. The
[machine-readable comparison](comparison.json) verifies equal configurations,
scientific outputs, native missingness and dependency versions.

| Workload | Baseline warm median, ms | Cached warm median, ms | Baseline/cached latency ratio |
|---|---:|---:|---:|
| reveals-interactive | 8.178 | 3.356 | 2.437× |
| reveals-reference-series | 28.318 | 21.676 | 1.306× |
| love-analytical | 12.791 | 7.478 | 1.710× |
| love-optimized-replay | 28.610 | 23.551 | 1.215× |
| lra-replicated-series | 218.972 | 94.532 | 2.316× |
| forward-validated | 0.042 | 0.046 | 0.922× |
| forward-dot-compute | 0.005 | 0.006 | 0.918× |

The replicated paired series improved by about 2.3× on the recorded machine.
The two tiny forward controls do not build runtime manifests, so their timing
differences are system/timer variation rather than benefit from this change.
No uniform speedup is claimed. The workload and cache interpretation limits of
the baseline still apply; these measurements do not decide C++ adoption.

The process cache is bounded to three dependency names and stores immutable
strings. Numerical workers assume their installed environment remains unchanged.
Independent manifests retain independent dictionaries: a caller modifying one
runtime mapping cannot change another manifest or the cached version values.
Regressions check both normal and missing dependency identities, one read per
distribution, scientific identity preservation and mapping ownership.

Selected checks include provenance, paired workflow and adoption boundary tests.
The existing source geometry warnings are retained. Kernel/R correspondence is
unchanged; no new source-R replay is claimed.

## Reproduce

Run the same installed baseline producer against this numerical source:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
.venv/bin/python -m bijux_pollenomics_dev.native_backend.profiling \
  --repository "$PWD" \
  --output artifacts/numerical-performance/runtime-metadata.json
```

Compare the retained scientific outputs and missing-value semantics as well as
timings. The original baseline retains its source identity and is not rewritten
with the cached producer's hashes.
