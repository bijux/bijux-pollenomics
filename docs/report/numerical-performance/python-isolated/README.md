# Isolated Python workload memory

The [measurement](report.json) runs each of the seven declared [Python baseline](../python-baseline/README.md) workloads in five fresh processes with numerical threads set to one. Each worker records the process RSS high water mark before and after one public call, call time, full worker time, its scientific output digest, and a digest of nonfinite output meanings. The producer compares those digests against the retained baseline and rejects a different workload contract, output, or nonfinite meaning. Every observed scientific output matched the retained baseline.

| Workload | Median process peak MiB | Median peak increment MiB | Median call ms | Median full worker s |
| --- | ---: | ---: | ---: | ---: |
| reveals-interactive | 161.6 | 2.6 | 68.60 | 1.47 |
| reveals-reference-series | 161.2 | 2.6 | 87.41 | 1.48 |
| love-analytical | 161.0 | 2.6 | 54.82 | 1.45 |
| love-optimized-replay | 160.8 | 2.5 | 71.92 | 1.47 |
| lra-replicated-series | 160.8 | 2.5 | 134.09 | 1.53 |
| forward-validated | 158.2 | 0.0 | 0.10 | 1.39 |
| forward-dot-compute | 158.5 | 0.0 | 0.02 | 1.38 |

These peaks include Python startup, imports, and construction of only the named
fixture. The before/after difference is a process high water increment, not
allocated bytes. A zero increment can occur when the call stays below the peak
reached during setup. The full worker duration includes startup, named fixture
construction, one call, and receipt serialization. It is not a cold-cache
kernel latency or a comparable full study pipeline time.

The solver source closure matches the shared-process baseline. All 35 workers
matched its workload contracts, scientific outputs and nonfinite meanings.
This Python-only measurement makes no C++ adoption decision. The
[forward worker comparison](../native-memory/README.md) contains the separate
bounded C++ memory and latency decision.

## Reproduce

From the repository root, choose an absent directory under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
.venv/bin/python -m bijux_pollenomics_dev.native_backend.isolated_python_baseline \
  --repository "$PWD" \
  --output "$PWD/artifacts/jobs/python-isolated-baseline/reproduction"
```

Memory and timing depend on the machine and process state. The producer pins its consumed source files and retained baseline during each run. The report includes every worker observation, rather than only the medians.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Numerical/runtime comparison reader; method correspondence and empirical/historical accuracy acceptance remain separate even when performance measurements pass.

**Supported claim.** Five fresh single-thread workers for each of seven workloads preserve the baseline output and nonfinite digests while measuring startup-inclusive duration and peak RSS.

**Unsupported claim.** Process isolation does not make filesystem caches cold, isolate allocations or establish native adoption, R parity or ecological performance.

**Actual verification performed.** Read the retained worker counts, baseline relationship and RSS/startup semantics and bound the account; no fresh worker was launched for this qualification.

**Remaining input or review.** A later optimization or platform claim requires its own exact-source full-call comparison and relevant numerical qualification.

**Cause category.** Whole-worker performance observations with explicit startup and import scope.

**Consequence.** The observed duration and high-water increments describe complete workers rather than kernel-only time or memory ownership.

**Precise next acceptance route.** Use an admitted identical workload and source closure, retain each worker and compare full-call costs without subtracting unmeasured import effects.

**Negative or refused result.** Observed zero RSS increments remain compatible with real allocations below an earlier import high-water mark; they are not memory-free results.

**Matched denominator.** Seven workloads×five workers=35 fresh workers; whole RSS 158.2–161.6 MiB, increments 0–2.6 MiB and durations 1.38–1.53 s include imports and setup.

Qualified authored reader SHA-256: `bcb67c38b41de712672a4b3356a347c396f84c73d1691b81bb04911f231bb4fb`.

- [Retained qualification evidence: docs/report/numerical-performance/python-isolated/report.json](report.json) (SHA-256 `1c5f2444bce9d941cf6e7fa45f8c61e0ed04afa067008ab085a3163007c2c17c`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md) (source SHA-256 `81407d77987fd391ea470cc975195107085cdf7a934a6716aac7a1b22cb19050`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
