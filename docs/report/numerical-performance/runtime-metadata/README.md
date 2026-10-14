# Runtime metadata cost in LRA reconstruction

The [reference baseline](reference-baseline.json) identified repeated package
metadata parsing in paired reconstruction. The runtime manifest now caches the
installed NumPy, SciPy and pandas version strings within one immutable numerical
worker environment. Each manifest still receives its own runtime mapping.
Missing distributions retain the original `unknown` value; versions remain in
scientific identity. No kernel, sampler, optimizer, configuration or numerical
output rule changed.

The [measured result](report.json) retains the same seven frozen workloads,
one first call, seven warm timings, scientific-output hashes and the exact raw
measurement digest. The [machine-readable comparison](comparison.json) checks
equal configurations, scientific outputs, native missingness and dependency
versions against the [source-bound baseline](reference-baseline.json). Raw
profiler stacks and local process paths are execution diagnostics, not part of
this reader result.

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
.venv/bin/python -m bijux_pollenomics_dev.native_backend.profile_summary \
  --raw-report artifacts/numerical-performance/runtime-metadata.json \
  --reference-baseline docs/report/numerical-performance/runtime-metadata/reference-baseline.json \
  --output-root artifacts/numerical-performance/runtime-metadata-summary
```

The summary producer refuses a changed workload, contract, scientific output,
native missingness or environment. Compare those fields with the governed
result; timings vary across runs and are not expected to match byte for byte.
The reference baseline pins seven original workload medians, contracts,
scientific output digests and environment to the source report at Git commit
`3d6b04959`, SHA-256 `e9675d170fe8ca8c0fa6ff03d75b6786c560f3c4f6398cd392963f362adbf21f`.
The [current Python baseline](../python-baseline/report.json) is a separate
measurement on later solver source and does not replace that historical
before/after comparator.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Numerical/runtime comparison reader; method correspondence and empirical/historical accuracy acceptance remain separate even when performance measurements pass.

**Supported claim.** Caching three immutable dependency-version strings per worker preserves the retained scientific and missingness outputs and reduces measured cost for several metadata-producing workloads.

**Unsupported claim.** This is no numerical-kernel change, uniform speedup, R parity extension, cross-machine guarantee or ecological accuracy result.

**Actual verification performed.** Read the comparison against its own frozen historical reference, exact dependency equality and seven-workload measurement scope; bound all three accounts without timing or model runs.

**Remaining input or review.** Current-candidate performance or a changed dependency environment needs a new declared comparison; caller dictionaries must remain independent and unknown-version semantics preserved.

**Cause category.** Bounded dependency-metadata optimization with workload-dependent timing.

**Consequence.** A shared immutable string cache may reduce manifest overhead without altering scientific outputs; small below-one ratios cannot be hidden as universal improvement.

**Precise next acceptance route.** Compare the same seven source-bound workloads against the correct frozen reference, verify version/missingness identity and dictionary independence, and retain all timing ratios.

**Negative or refused result.** Warm ratios 0.922 and 0.918 do not improve; tiny forward workloads do not construct manifests, so their variation does not establish a metadata-kernel regression or gain.

**Matched denominator.** Seven workloads with one first and seven warm calls before/after; three dependency names NumPy/SciPy/pandas. Reference is historical commit 3d6b0495 and its own reference-baseline.json, not the later Python baseline.

Qualified authored reader SHA-256: `a684303dd823ad0fe91851b99f8920840b7ef36bdbabea7411abb4179f6182e6`.

- [Retained qualification evidence: docs/report/numerical-performance/runtime-metadata/report.json](report.json) (SHA-256 `1b9712f5d477320913757600eeae60192f07f7bdfc4b8e9df13160f4e3bc4590`).

- [Retained qualification evidence: docs/report/numerical-performance/runtime-metadata/comparison.json](comparison.json) (SHA-256 `2ff33c5a49ed9cfe185fdcdcbddc25a5d3998c40873619ccb676d03b51939a4f`).

- [Retained qualification evidence: docs/report/numerical-performance/runtime-metadata/reference-baseline.json](reference-baseline.json) (SHA-256 `dbe8e46ccfa0bdc2df0db4acd5328c498e00eaaea958971aa06a51939912b656`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md) (source SHA-256 `81407d77987fd391ea470cc975195107085cdf7a934a6716aac7a1b22cb19050`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
