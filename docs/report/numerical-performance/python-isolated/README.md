# Isolated Python workload memory

The [measurement](report.json) runs each of the seven declared [Python baseline](../python-baseline/README.md) workloads in five fresh processes with numerical threads set to one. Each worker records the process RSS high water mark before and after one public call, call time, full worker time, its scientific output digest, and a digest of nonfinite output meanings. The producer compares those digests against the retained baseline and rejects a different workload contract, output, or nonfinite meaning. Every observed scientific output matched the retained baseline.

| Workload | Median process peak MiB | Median peak increment MiB | Median call ms | Median full worker s |
| --- | ---: | ---: | ---: | ---: |
| reveals-interactive | 161.6 | 2.6 | 70.69 | 1.47 |
| reveals-reference-series | 161.4 | 2.7 | 87.75 | 1.49 |
| love-analytical | 161.7 | 2.5 | 55.88 | 1.45 |
| love-optimized-replay | 161.0 | 2.5 | 73.22 | 1.47 |
| lra-replicated-series | 161.2 | 2.5 | 135.49 | 1.54 |
| forward-validated | 158.7 | 0.0 | 0.10 | 1.39 |
| forward-dot-compute | 158.4 | 0.0 | 0.02 | 1.39 |

These peaks include Python startup, imports, and construction of only the named
fixture. The before/after difference is a process high water increment, not
allocated bytes. A zero increment can occur when the call stays below the peak
reached during setup. The full worker duration includes startup, named fixture
construction, one call, and receipt serialization. It is not a cold-cache
kernel latency or a comparable full study pipeline time.

The current solver source closure matches the refreshed shared-process baseline. All
35 workers matched its workload contracts, scientific outputs and nonfinite
meanings. The earlier isolated report constructed all seven fixtures in each
worker and used an older source closure; its timings are not a controlled
before/after speed comparison. This Python-only measurement makes no C++
adoption decision. The [forward worker comparison](../native-memory/README.md)
contains the separate bounded C++ memory and latency decision.

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
