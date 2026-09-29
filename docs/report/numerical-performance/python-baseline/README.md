# Python numerical performance baseline

The [retained measurement](report.json) freezes seven workloads, every numerical
source/resource hash, configurations, fixed candidate inputs, thread settings,
software versions and hardware platform. Each workload has one first call and
seven warm timing repetitions; a separate call records cProfile costs. Every
scientific output is identical across timing repetitions.

| Workload | First call, ms | Warm median, ms | Warm range, ms |
|---|---:|---:|---:|
| reveals-interactive | 68.505 | 2.681 | 2.564–4.098 |
| reveals-reference-series | 19.546 | 19.226 | 19.181–19.332 |
| love-analytical | 11.873 | 6.489 | 6.444–6.621 |
| love-optimized-replay | 23.649 | 21.241 | 21.187–21.461 |
| lra-replicated-series | 83.968 | 82.052 | 81.585–82.148 |
| forward-validated | 0.082 | 0.041 | 0.040–0.046 |
| forward-dot-compute | 0.021 | 0.005 | 0.005–0.006 |

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

The process high-water RSS was 163.45 MiB on the recorded macOS machine, including
imports and all workloads. It is not per-workload incremental memory. First calls
share the process and may reuse kernels warmed by an earlier workload; they are
not isolated cold-cache measurements. The profile records individual Python,
library, conversion and copy functions with their call counts and exclusive and
cumulative costs.

This measurement refreshes an older retained baseline on the current numerical
source. All seven scientific outputs and nonfinite meanings match the older
measurement exactly. Three REVEALS-inclusive workload contracts now include the
declared fall-speed profile, and eight source identities differ. The timing
differences between the two reports therefore do not establish a speed change.

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
This result establishes a bounded Python baseline. A later
[forward comparison](../native-forward/README.md) and
[isolated worker measurement](../native-memory/README.md) make a scoped
non-adoption decision for one C++ batch boundary. This baseline alone does not
certify source-R/C++ parity, parallel scaling or the full backend investigation.
