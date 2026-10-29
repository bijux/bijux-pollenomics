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
