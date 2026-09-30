# Python numerical performance baseline

The [retained measurement](report.json) records seven workloads, numerical
source/resource hashes, workload contracts, thread settings, software versions
and hardware platform. Each workload has one first call and seven warm timing
repetitions; a separate call records total cProfile cost. Scientific-output
and nonfinite-semantics digests preserve the comparison contract without
publishing raw result arrays or machine-specific profiler stacks. Every
scientific output was identical across timing repetitions.

| Workload | First call, ms | Warm median, ms | Warm range, ms |
|---|---:|---:|---:|
| reveals-interactive | 82.211 | 2.971 | 2.875–5.216 |
| reveals-reference-series | 21.688 | 21.392 | 20.822–37.899 |
| love-analytical | 13.218 | 7.217 | 7.042–7.438 |
| love-optimized-replay | 26.120 | 22.934 | 22.601–23.773 |
| lra-replicated-series | 90.800 | 89.167 | 88.027–90.497 |
| forward-validated | 0.139 | 0.041 | 0.040–0.051 |
| forward-dot-compute | 0.029 | 0.005 | 0.005–0.006 |

The REVEALS workloads use one and all 45 retained Tiefer See rows with 21 taxa.
LOVE uses the retained 10-taxon, 36-ring example: eight analytical repeats or
two optimized repeats with the same 32 declared candidates per repeat. Candidate
replay measures objective evaluation; it does not benchmark search convergence.
The paired series is eight explicitly synthetic coordinate replicas, not eight
independent sites or an ecological study. Its per-bin regional/local draw counts
and configurations are retained.

The synthetic 128-ring/32-taxon forward comparison distinguishes the complete
validated public call from an equivalent prevalidated dot-product calculation.
Focused checks compare those scientific outputs at absolute `1e-12` and relative
`1e-10` tolerance. Compute-only latency excludes validation, conversion and
owned diagnostic outputs; its ratio cannot establish a facade or pipeline gain.
The microsecond kernel timings have only seven repetitions and should not support
an adoption decision without batched, isolated measurements.

LOVE outputs preserve undefined cells as null with their original NaN meanings
identified by path before hashing; they are never replaced by zero. Timing
measures the declared source workflow, not a new scientific eligibility or
accuracy claim.

The process high-water RSS was 164.78 MiB on the recorded macOS machine, including
imports and all workloads. It is not per-workload incremental memory. First calls
share the process and may reuse kernels warmed by an earlier workload; they are
not isolated cold-cache measurements. The retained report gives total
profiler cost, not per-function stacks.

The seven scientific outputs, nonfinite meanings and workload contracts match
the separate isolated worker result. Timing and process RSS variation between
runs does not establish a speed change.
The source inventory excludes the ignored generated `_build_version.py`, whose
SCM label changes during builds without changing the numerical method.

## Reproduce

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
.venv/bin/python -m bijux_pollenomics_dev.native_backend.profiling \
  --repository "$PWD" \
  --output artifacts/numerical-performance/python-baseline-raw.json
.venv/bin/python -m bijux_pollenomics_dev.native_backend.baseline_summary \
  --raw-report artifacts/numerical-performance/python-baseline-raw.json \
  --output artifacts/numerical-performance/python-baseline-summary.json
```

The measurement producer rechecks consumed numerical source/input identities;
the summary producer refuses incomplete timing or changed output meanings.
New source bytes require a new measurement. Performance varies with the
recorded machine, software, caches and system load.

The prospective native comparison requires at least 2× end-to-end benefit, no
more than 1.25× peak RSS and the stated scientific tolerances on identical inputs.
This result establishes a bounded Python baseline. A later
[forward comparison](../native-forward/README.md) and
[isolated worker measurement](../native-memory/README.md) make a scoped
non-adoption decision for one C++ batch boundary. This baseline alone does not
certify source-R/C++ parity, parallel scaling or the full backend investigation.
