# Python numerical performance baseline

The [retained measurement](report.json) freezes seven workloads, every numerical
source/resource hash, configurations, fixed candidate inputs, thread settings,
software versions and hardware platform. Each workload has one first call and
seven warm timing repetitions; a separate call records cProfile costs. Every
scientific output is identical across timing repetitions.

| Workload | First call, ms | Warm median, ms | Warm range, ms |
|---|---:|---:|---:|
| reveals-interactive | 83.441 | 8.178 | 7.687–9.801 |
| reveals-reference-series | 28.025 | 28.318 | 26.619–29.501 |
| love-analytical | 18.171 | 12.791 | 12.295–12.926 |
| love-optimized-replay | 34.726 | 28.610 | 28.516–29.157 |
| lra-replicated-series | 217.831 | 218.972 | 216.554–239.346 |
| forward-validated | 0.149 | 0.042 | 0.041–0.077 |
| forward-dot-compute | 0.023 | 0.005 | 0.005–0.006 |

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

LOVE outputs preserve undefined cells as null with their original NaN values
identified by path. They are never replaced by zero. The source example's warning
about terrestrial area exceeding geometric ring area remains in the run log;
the production ratio is retained. Timing measures the declared source workflow,
not a new scientific eligibility or accuracy claim. The initial report writer
refused non-JSON NaNs; the corrected writer preserves them explicitly.

The process high-water RSS was 163.80 MiB on the recorded macOS machine, including
imports and all workloads. It is not per-workload incremental memory. First calls
share the process and may reuse kernels warmed by an earlier workload; they are
not isolated cold-cache measurements. The profile records individual Python,
library, conversion and copy functions with their call counts and exclusive and
cumulative costs.

## Reproduce

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
.venv/bin/python -m bijux_pollenomics_dev.native_backend.profiling \
  --repository "$PWD" \
  --output artifacts/numerical-performance/python-baseline.json
```

The producer rechecks its consumed numerical source/input identities after the
measurement. Source changes require a new result. Performance varies with the
recorded machine, software, caches and system load.

The prospective native comparison requires at least 2× end-to-end benefit, no
more than 1.25× peak RSS and the stated scientific tolerances on identical inputs.
This result establishes a bounded Python baseline. It does not decide native
adoption, certify R/C++ parity, measure isolated startup or parallel scaling,
or settle the full backend investigation. Those need their own consumers.
