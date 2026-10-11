# Isolated Python workload memory

The [measurement](report.json) runs each of the seven declared [Python baseline](../python-baseline/README.md) workloads in five fresh processes with numerical threads set to one. Each worker records the process RSS high water mark before and after one public call, call time, full worker time, its scientific output digest, and a digest of nonfinite output meanings. The producer compares those digests against the retained baseline and rejects a different workload contract, output, or nonfinite meaning. Every observed scientific output matched the retained baseline.

| Workload | Median process peak MiB | Median peak increment MiB | Median call ms | Median full worker s |
| --- | ---: | ---: | ---: | ---: |
| reveals-interactive | 162.4 | 2.5 | 77.84 | 1.68 |
| reveals-reference-series | 161.5 | 2.8 | 96.89 | 1.68 |
| love-analytical | 161.9 | 2.6 | 62.65 | 1.66 |
| love-optimized-replay | 162.9 | 2.6 | 80.00 | 1.66 |
| lra-replicated-series | 161.3 | 2.5 | 152.61 | 1.75 |
| forward-validated | 160.3 | 0.0 | 0.10 | 1.61 |
| forward-dot-compute | 159.4 | 0.0 | 0.02 | 1.62 |

These peaks include Python startup, imports, and construction of **all seven** retained fixtures because the existing workload factory constructs them together. The before/after difference is a process high water increment, not allocated bytes. A zero increment can occur when the call stays below the peak reached during setup. The full worker duration includes startup, fixture construction, one call, and receipt serialization. It is not a cold-cache kernel latency or a comparable full study pipeline time.

The current source closure differs from the earlier shared-process baseline in `bijux_pollenomics_lra/provenance/manifest.py`; both file identities are in the report. Scientific outputs and workload contracts match, but the two timing sets are not an identical-source latency comparison. This Python-only measurement makes no C++ adoption decision. The [forward worker comparison](../native-memory/README.md) contains the separate bounded C++ memory and latency decision.

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
