# Representative public-call performance

The completed Python run at commit `19642380cc6051ed9d6cfc3fbddfdb56b4feeba7`
found no named boundary that met the declared conservative hotspot rule in all
three isolated workers. This result does not authorize another C++ kernel.
The [complete report](report.json) and retained source capsule preserve all
measurements, scientific outputs, controls and execution logs.

The author workload uses six real source sites, ten taxa and 1,024 stored
conditional joint draws. The larger LOVE workload makes 128 computational
repetitions of one published ten-taxon, 36-ring fixture with 32 fixed candidate
evaluations per call. It is not 128 independent sites, and it does not measure
optimizer search convergence or vegetation accuracy.

Each primary worker makes a first public call and seven warm calls. Times below
are seconds; peak RSS is bytes for the whole completed worker. First-call does
not mean a proven cold operating-system cache. Loading/construction/conversion
is measured separately from the public call; complete stage wall time retains
process startup, and output projection has its own eight retained observations.

| Workload | Worker | First call | Warm median | Warm min–max | Loading/conversion | Peak RSS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| author-conditional-joint-draws | 0 | 0.000830583 | 0.000955250 | 0.000718250–0.001085167 | 1.833391 | 209158144 |
| author-conditional-joint-draws | 1 | 0.000831333 | 0.000773917 | 0.000755208–0.000871875 | 1.830982 | 210649088 |
| author-conditional-joint-draws | 2 | 0.000830417 | 0.001012708 | 0.000738416–0.001045375 | 1.921863 | 209125376 |
| love-larger-fixed-candidate-batch | 0 | 2.867185417 | 2.807402709 | 2.764516167–2.960262625 | 1.942868 | 241401856 |
| love-larger-fixed-candidate-batch | 1 | 2.842722250 | 2.775882334 | 2.744842292–2.830636750 | 1.981767 | 240025600 |
| love-larger-fixed-candidate-batch | 2 | 2.816526417 | 2.789399542 | 2.754365875–2.816887417 | 1.977462 | 252493824 |

Three separate unprofiled measurements of each named boundary preserve baseline,
passthrough, instrumented, inside-boundary and clock costs. The conservative
inside share must reach 50% with at most 5% instrumentation overhead in every
worker. `_closed_joint_draws` shares were 4.25%, 18.69% and 36.19%; `tf` shares
were 20.74%, 20.00% and 21.04%; `calK` shares were 10.67%, 10.99% and 9.89%.
No nested costs are summed. The separately retained cProfile observations are
diagnostic, and their slower timings are not unprofiled hotspot evidence.

Equal-total-work process scaling measures two identical public workload calls:
sequential versus two concurrent fresh processes. Author calls took 4.623789 s
versus 2.415267 s; LOVE calls took 10.846914 s versus 5.434702 s. These include
startup/loading and describe this machine and workload only. Six vendor
environment variables requested one numerical thread; native thread counters
were not observed. Maximum worker concurrency was two.

The original eight stages and independent scientific/output observer passed.
Completed-child peak RSS was 252,493,824 bytes. The 2 GiB completed-child RSS and
256 MiB logical-output budgets passed; no operating-system quota or complete
descendant RSS census is claimed. Scientific values, missing/nonfinite markers,
input identities and repeated-output hashes were preserved exactly.

The production backend remains Python/NumPy/SciPy. The earlier forward C++
experiment's conversion-inclusive ratios 0.928, 0.897 and 0.722 all failed the
prospective 2× adoption gate; its memory result remains separately scoped.
This run did not execute a compiler or source R. A future native proposal still
needs a qualifying workload/boundary, identical-input source-R/Python comparison,
conversion-inclusive benefit, memory and build/maintenance evidence. Other
regional/time-series/optimizer/ESSD workloads, platform portability, scientific
applicability, rights, human review and final release acceptance remain separate.

The capsule redistributes first-party source/control and complete actual output
and log bytes. Private author input files and runtime binaries remain hash-only
references. Transporting these observations reruns no model, benchmark or R code.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Actual representative Python public-call measurements and retained negative native-adoption evidence; scientific correspondence, broader workloads, human review and release gates retain their separate scopes.

**Supported claim.** Completed Python measurements preserve six real author sites, ten taxa and 1,024 conditional joint draws, plus a separate larger LOVE computational workload; no named boundary qualifies as a conservative hotspot in all three isolated workers.

**Unsupported claim.** This bounded machine/workload result grants no new C++ kernel, same-input source-R timing, optimizer convergence, ecological accuracy, portability, native thread-count guarantee or final release acceptance.

**Actual verification performed.** Original eight-stage execution and independent scientific/output review passed at commit 19642380cc6051ed9d6cfc3fbddfdb56b4feeba7. A separate two-stage metadata assembly and independent retained transport review preserved all 66 output/log files, all 14 worker measurements and six first-plus-seven-warm series without a new model, benchmark, profile, compiler or R call.

**Remaining input or review.** A future native proposal requires a qualifying representative boundary, identical-input source-R/Python comparison, conversion-inclusive speed benefit, memory/build/maintenance evidence and separately qualified platforms and scientific use.

**Cause category.** Measured negative native-adoption result with bounded retained numerical and resource custody.

**Consequence.** Python/NumPy/SciPy remains the production backend; diagnostic cProfile costs cannot substitute unprofiled conservative boundary measurements.

**Precise next acceptance route.** Declare a representative workload and prospective conservative hotspot/adoption thresholds before another native implementation; preserve source/input identities, startup/loading/conversion, first/warm spread, complete scientific outputs and memory evidence.

**Negative or refused result.** No boundary reaches at least 50 percent conservative inside share with at most 5 percent instrumentation overhead in every isolated worker. Earlier compiled forward conversion-inclusive ratios 0.928, 0.897 and 0.722 all fail the 2x gate. Source R and compiler execution are false for this run.

**Matched denominator.** Six actual author sites, ten taxa, 1,024 conditional draws; 128 repetitions of one ten-taxon, 36-ring LOVE fixture with 32 fixed candidates, not 128 sites. Three first-plus-seven-warm workers per workload; 14 workers including equal-total two-call sequential/two-process scaling. Six vendor thread limits were requested only; maximum completed worker RSS was 252493824 bytes.

- [Retained qualification evidence: docs/report/numerical-performance/representative-public-calls/report.json](report.json) (SHA-256 `5249ce851a8c720fd5c2b62e10bb7b0aac9cb0a8926520c677bdc87134e427c3`).

- [Retained qualification evidence: docs/report/numerical-performance/native-forward/report.json](../native-forward/report.json) (SHA-256 `4d16a1400d6878f2abf21f796fb190dd72a365f0dd40295639b8635bd807d1d5`).

- [Retained qualification evidence: docs/report/numerical-performance/native-memory/report.json](../native-memory/report.json) (SHA-256 `6fcac93d4ccb79e80f8bedecb131e209e026800d7b979129025e47a628976f06`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
