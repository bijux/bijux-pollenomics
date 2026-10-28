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

A subsequent [native R source replay](../../method-certification/current-r-oracle/README.md)
passes 18 optimized LOVE cases on three declared fixtures with the installed
engine source hashes. Those cases do not use this profiled `LOVEexample`
workload, so they establish current-source method parity within their own
contracts but do not supply a same-input R comparator here.

The later [LOVEexample source comparison](../love-source-comparison/README.md)
uses one exported input and candidate set for native R 4.6.0/DISQOVER 0.9.14
and the profiled Python public-call contract. It passes the fixed-candidate
ring factors, objective values, selected candidates, and cover/pollen outputs.
The decision below remains the decision of this profiling run; the later
comparison does not measure a compiled implementation or search convergence.

**Decision:** retain the Python engine and do not write a new speculative C++
kernel for this workload. To reopen the native candidate, profile a declared
larger qualified LOVE workload and execute source R and Python on identical
candidate inputs. A new C++ candidate should target a
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


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Numerical/runtime comparison reader; method correspondence and empirical/historical accuracy acceptance remain separate even when performance measurements pass.

**Supported claim.** The retained one-thread LOVEexample profile finds no single deterministic component dominating the public call and therefore supports retaining Python for this workload.

**Unsupported claim.** Profile fractions do not establish an unprofiled speedup, optimizer convergence, independent ecological accuracy or a compiled adoption benefit.

**Actual verification performed.** Read the retained 12-warm-call workload, source closure, timing interpretation and separate identical-input R comparison. Bound both accounts without rerunning profiling, R or LOVE.

**Remaining input or review.** A larger qualified workload and an isolated boundary occupying at least half of full-call cost are needed before reopening a compiled candidate; present-source qualification remains separate.

**Cause category.** Measured performance decision with explicitly bounded historical source correspondence.

**Consequence.** No speculative C++ adoption follows from the measured profile, and later R fixture cases cannot silently substitute for this exact workload.

**Precise next acceptance route.** Profile a named qualified workload, retain output/missingness identity, then apply the declared conversion-inclusive twofold full-call gate to any actual compiled proposal.

**Negative or refused result.** The largest diagnostic component remains below half the call. Eight of 45 shared files differed from the earlier R closure; later 18 optimized R cases use other fixtures, while the separate exact LOVEexample comparison has its own account.

**Matched denominator.** One first call, 12 warm calls and one instrumented call; 56 source pins; first 76.382 ms, warm median 21.601 ms (21.382–23.300 ms), profiled 45.400 ms, whole-process peak 167.9 MB. Timings describe one recorded machine and workload.

- [Retained qualification evidence: docs/report/numerical-performance/love-source-profile/report.json](report.json) (SHA-256 `7cc846537a95eedcbde215f450fdc9a434c6dab73e93565decf771c19ddd3e7e`).

- [Retained qualification evidence: docs/report/numerical-performance/love-source-comparison/report.json](../love-source-comparison/report.json) (SHA-256 `73655d3f9ba41d3c20b7db5fa43360a60ded61d70d1603a1628cf7a6de8b6413`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
