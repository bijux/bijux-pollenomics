# Published LOVE workload profile

The [retained result](report.json) profiles the installed Python engine on the
published `LOVEexample` input: one local row, 10 taxa, 36 rings, two deterministic
optimized LOVE repeats, and 32 fixed candidates per repeat. This is the same
public-call contract as the [seven-workload baseline](../python-baseline/README.md).
All 12 warm calls returned the baseline's scientific-output and nonfinite-value
digests. Candidate replay measures bounded objective evaluation, not optimizer
convergence or ecological accuracy.
The full candidate vectors remain in the linked baseline contract; this result
binds them by their identical contract hash instead of copying them.

| Observation | This run |
| --- | ---: |
| First public call | 76.382 ms |
| Warm public-call median, 12 calls | 21.601 ms |
| Warm range | 21.382–23.300 ms |
| Profiled public call | 45.400 ms |
| Whole-process peak RSS | 167.9 MB |

The profile used one numerical thread and bound 56 engine/resource/producer files
by SHA-256 before and after measurement. Its raw profile, full command context,
environment, warm samples and function costs are at
`artifacts/numerical-performance/love-optimized-profile.json`; the retained
result stores the raw-file digest and read-set identities. The peak RSS includes
imports and fixture construction, so it is not incremental LOVE allocation.

| Profiled path | Calls | Cumulative time | Share of 45.400 ms |
| --- | ---: | ---: | ---: |
| Ring-factor `calK` | 1 | 6.31 ms | 13.9% |
| Candidate `tf` objective | 264 | 9.01 ms | 19.8% |
| Regional-cover preparation | 2 | 8.80 ms | 19.4% |
| Result summaries | 2 | 7.56 ms | 16.7% |

These paths are separate parts of the public call. The objective includes
forward pollen evaluation; its 264 calls include candidate and final-value
work. `calK` computes repeated ring factors, but contributes only about one
seventh of this profiled call. The profiled call costs more than the unprofiled
median, so these shares diagnose where work occurs rather than predict a native
speedup. No isolated deterministic numerical path dominates enough to justify
another narrow C++ boundary against the declared 2× end-to-end benefit gate.

The [current source-R oracle](../../method-certification/current-r-oracle/README.md)
contains optimized LOVE candidate and wrapper comparisons, but its retained
Python input closure is not the installed source measured here: 8 of 45 common
files differ, including the optimizer solver and optimized LOVE wrapper. The
current workload still matches the retained Python baseline outputs and missing
values. It does not inherit an exact-source R comparison from that earlier run.

**Decision:** retain the Python engine and do not write a new speculative C++
kernel for this workload. To reopen the native candidate, first refresh the
source-R/Python optimized LOVE replay on the present source read set. Then profile
a declared larger qualified LOVE workload. A new C++ candidate should target a
deterministic boundary that consumes at least half of unprofiled public-call
cost, compare identical inputs and values against source R and Python, and
measure conversion-inclusive full-call latency against the prospective 2× gate.
The existing forward C++ comparison and its negative adoption result remain
separate bounded evidence.

The measurement used the installed `.venv` and existing
`bijux_pollenomics_dev.native_backend.profiling.workloads` recipe; no package or
solver source changed. The source geometry warning was retained during timed
calls because the published ring area exceeds its geometric area. The profile
does not measure stochastic draws, search trajectory, another platform or a
complete empirical LRA study.
