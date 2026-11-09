# Why we deferred a compiled LRA backend

## Our decision

We keep the production LRA calculations in Python and NumPy. Our [forward
batch](../../docs/report/numerical-performance/native-forward/README.md) is a
private C++17 experiment, not a runtime backend. On the three declared shared
shapes, its validated call was slower than the optimized NumPy call; the
NumPy/native latency ratios were 0.928, 0.897 and 0.722, below our prospective
2× adoption gate. The [isolated worker result](../../docs/report/numerical-performance/native-memory/README.md)
found about 31 MB less peak RSS for native execution at one additional large
synthetic shape, with a slower median call there too. We have no measured
complete REVEALS or LOVE throughput gain from C++.

We therefore did not add a compiler, native wheel, dispatch path or second
numerical version to the installed engine. This decision applies to the
measured forward boundary. A different kernel still needs a representative
profile, an explicit benefit gate and source-R/Python/native comparison. The
[adoption result](../../docs/report/numerical-performance/native-adoption/README.md)
records the measured scope and its limits.

We also measured an ordinary Python improvement: caching three installed
dependency version strings reduced the recorded replicated-series warm median
from 218.972 to 94.532 ms on one machine. The
[source-bound comparison](../../docs/report/numerical-performance/runtime-metadata/README.md)
checks seven workload contracts and scientific-output hashes. The retained
measurement omits raw profiler stacks and local process paths. This result
supports the metadata-cache change, not a general speedup or a compiled
backend.

We profiled the published [optimized LOVE example](../../docs/report/numerical-performance/love-source-profile/README.md)
through its installed Python public call. Twelve warm calls had a 21.601 ms
median. The profiled call spread time across ring factors, objective evaluation,
regional preparation and summaries; no single deterministic path met our
condition for another narrow C++ experiment. Scientific outputs and missing
values matched the retained Python baseline. The earlier source-R comparison
used eight different engine files, including the optimizer. We have since
[rerun native R](../../docs/report/method-certification/current-r-oracle/README.md)
against the installed source: 18 optimized LOVE cases pass on three declared
fixtures. We then compared [the same `LOVEexample` inputs](../../docs/report/numerical-performance/love-source-comparison/README.md)
in R and Python with fixed candidates. Hexadecimal readback checked every
input double across the two runtimes. Cover and pollen matched exactly;
ring factors and objective values differed by at most 5.11e-15, and all eight
selected candidates agreed. This establishes one bounded source-method
comparison. A larger source-qualified workload, optimizer search behavior and
conversion-inclusive full-call gain remain prerequisites before reconsidering
a native LOVE candidate.

## Boundary we would use if a new kernel qualifies

We would place an optional C++17 extension inside the separately licensed
[`bijux-pollenomics-lra` distribution](../../packages/bijux-pollenomics-lra/pyproject.toml),
behind its existing Python API. The Apache-declared host would continue to
discover the engine through its extension contract. The extension would
accelerate a profiled deterministic numerical batch; Python would retain
source loading, validation, provenance, workflow control and publication
outputs. The [current package backend identity](../../packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/version.py)
remains `python-numpy-scipy` until an adopted backend has its own verified
identity. We would derive the extension and Python facade version from the
same engine release, with no separately versioned native API.

We evaluated two packaging routes against this boundary. The private spike
uses a manually compiled shared library and `ctypes`; it was sufficient to
measure a narrow buffer call, but its artifact has no wheel/platform or
release contract. Retaining Hatchling with a custom compile hook would keep
the present pure-Python build backend, but would require us to own native
build discovery, binary inclusion and platform tagging. If adoption becomes
justified, our preferred candidate is CMake plus pybind11 under a native-aware
build backend such as scikit-build-core, confined to the GPL engine wheel.
That route would still require a demonstrated build and install matrix before
we change the current Hatchling metadata; naming it here does not claim such
a matrix has passed. We would check every Python and operating-system target
we advertise, both source and wheel installs, exact extension loading and
generated SBOM content. A pure-Python fallback would remain explicit, rather
than silently changing scientific outputs by platform.

The [spike source](../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/native_backend/forward_kernel.cpp)
and [facade](../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/native_backend/forward_compare.py)
already establish a small ownership model: caller-owned contiguous binary64
inputs live through a synchronous call; the result owns its storage; the
native function returns a status and catches C++ exceptions at the C boundary.
For any adopted extension we would additionally preserve the public facade's
shape, finite-value and closure refusals, make copy versus zero-copy cost
visible, and test read-only/strided input and concurrent calls. A binding may
release the GIL only after it has acquired stable input ownership and no
Python object access remains inside that section. Native exceptions must map
to the engine's declared Python errors, never leak across a binary boundary.

We would keep sampling and optimizer control in Python for the first accepted
kernel. The engine currently accepts a NumPy generator and explicit regional
draw arrays; moving its RNG or search trajectory into C++ would add an
independent reproducibility contract. A candidate therefore receives the
same frozen arrays and draw indices as Python and source R. We would compare
numerical values, refusal cases, conversion-inclusive latency, full-workflow
time, peak memory and maintenance/build cost. Agreement with our independent
R matrix equation in the forward spike is not source DISQOVER parity or
evidence of optimizer equivalence.

This gives us a selected architecture and a measurable reopening condition
without claiming production adoption. The four-country observed-pollen
results and English author-example LRA study do not establish that Nordic
cores are eligible for LRA; that source admission remains a separate decision.

## Larger retained public-call measurement

The [representative public-call report](../../docs/report/numerical-performance/representative-public-calls/README.md) retains the completed Python measurement at commit `19642380cc6051ed9d6cfc3fbddfdb56b4feeba7`: six actual author sites, ten taxa and 1,024 stored joint draws, plus 128 computational repetitions of one LOVE fixture. Each workload has three isolated first-plus-seven-warm observations, separate loading/conversion and diagnostic profile costs, unprofiled boundary measurements, peak RSS and equal-total one-versus-two-process scaling. None of the three named boundaries reached the conservative 50% share and 5% instrumentation-overhead rule in all workers. No compiler or same-input source R was run, and this result does not reopen the rejected forward C++ adoption or qualify another kernel. Other workload families and the applicable source-R, optimizer, memory/build/platform and scientific acceptance remain separate.

## Full optimized LOVE search through the public API

At source `3621ce70301de9571f4d72e1154b8155db5717ab`, `run_love` used the
exposed `LOVEexample`: ten taxa, 36 input ring rows, ten requested rings and
two repeats. The source-compatible profile used SciPy differential evolution,
seed 7, `stochastic=False`, a 200-iteration cap, tolerance 0.01 and a
20,100-evaluation ceiling per search. No fixed candidates were supplied.

This source-run used CPython 3.11.13 on arm64 macOS 26.6.2, NumPy 2.4.6,
SciPy 1.17.1 and pandas 3.1.1. Five thread-limit environment variables requested
one thread each; vendor thread counts were not measured.

Three fresh workers each made one first call and three warm calls. All twelve
calls completed, each with eight searches reporting successful stopping and
six undefined requested rings. Scientific signatures and solver diagnostics
matched across calls; searches used 4,300–8,400 evaluations. The geometry
warning remains: terrestrial area exceeds geometric ring area, and the source
ratio is retained without clipping.

| Worker | First call, s | Warm median, s | Warm range, s | Peak RSS, MiB |
| --- | ---: | ---: | ---: | ---: |
| 1 | 1.8635 | 1.7957 | 1.7945–1.7989 | 164.8125 |
| 2 | 1.8357 | 1.8071 | 1.7741–1.9026 | 164.8906 |
| 3 | 1.8955 | 1.8637 | 1.8628–1.8810 | 163.9375 |

Calls exclude loading/conversion (0.0015–0.0045 s), writing/projection
(0.0045–0.0063 s), process startup (0.0224–0.0268 s) and imports
(1.279–1.555 s). The 32.9884 s aggregate met the 180 s worker/600 s aggregate
limits. Counted output was 812,019 bytes against 32 MiB; observed RSS stayed
below 1 GiB without an OS quota. Metadata and source/index/input guards stayed
unchanged.

The separate profiled call took 3.6659 s. Its diagnostic stack establishes
neither the low-overhead hotspot gate nor a C++ benefit. This adds full-search
performance evidence, not global-optimum quality, R search-trajectory parity,
ecological, installed-package or platform qualification. The Python backend
decision stands.

Complete API outputs and receipts are retained through the existing
scientific-artifact recovery owner, keyed by logical path
`artifacts/verification/love-optimizer-search/run/`.

## Unprofiled objective boundary in the full search

At source `2de02934d88803640396e3dd5f441e53d219925c`, the same full-search
workload and runtime were measured around `optimized.tf` only. Three fresh
workers each saved one warmup and nine measured calls: three unwrapped
baselines, three no-clock passthroughs and three clocked calls, in balanced
orders. Complete outputs were written after timing; the original function was
restored after every call.

The existing rule subtracts empty-clock cost and worst passthrough spread from
the minimum inside time, then divides by the maximum baseline time.
Instrumentation overhead uses the instrumented and baseline medians. Every
worker must reach at least 50% conservative share with at most 5% overhead;
averaging workers or selecting the best observation cannot qualify it.

| Worker | Conservative objective share | Instrumentation overhead |
| --- | ---: | ---: |
| 1 | 54.5094% | 1.4335% |
| 2 | 55.5239% | 0.6323% |
| 3 | 58.2293% | 0.7006% |

All workers passed. Independent review checked all 30,480 saved CSV cells,
including 11,160 missing values, and 240 solver diagnostics against the
original search reference. All outputs matched; six undefined requested rings
and the geometry warning remain. The aggregate took 60.6836 s, peak observed
RSS was 177,635,328 bytes and counted output was 1,189,204 bytes, within the
unchanged resource limits; source/index/input guards passed.

This unprofiled result qualifies bounded objective-kernel investigation only.
It establishes no C++ benefit, global-optimum quality, source-R parity or field
admission. Production remains Python. The original search evidence is
unchanged; complete boundary outputs and receipts use the existing recovery
owner under `artifacts/verification/love-objective-boundary-cost/run/`.

## Preparing fixed inputs once per LOVE search

The Python change at candidate `380a3e783dfce9facbdf12a05358ba0234c0db7f`
was compared with baseline `490bb893d04cafc5d56a7e89df1bd0e408008c05`.
Each search now owns read-only copies of its regional deposition, ring kernels,
land fractions, productivity and offset observations. Candidate validation and
the shared floating-point arithmetic remain unchanged; public `tf` retains its
standalone refusals. There is no global cache or dependency/ABI addition.

On the same Mac runtime and full-search fixture, three fresh workers per
variant each made one first and three warm calls. Pair order was
baseline/prepared, prepared/baseline, baseline/prepared. Preparation and copies
are included in the full-call timing.

| Pair | Baseline warm median, s | Prepared warm median, s | Reduction |
| --- | ---: | ---: | ---: |
| 1 | 1.7830 | 1.4887 | 16.5051% |
| 2 | 1.7948 | 1.5032 | 16.2461% |
| 3 | 1.7830 | 1.4817 | 16.8998% |

First calls fell from 1.8505–1.8779 s to 1.5387–1.5415 s. Separately measured
loading was 0.00147–0.00150 s, imports 1.278–1.308 s, process startup
0.0224–0.0259 s and writing/projection 0.0045–0.0075 s. Peak observed RSS was
172,916,736 bytes; the 50.2590 s aggregate and 1,125,097 counted output bytes
met the unchanged limits.

Independent review found all 24 scientific outputs and 192 solver diagnostics
exact to the retained reference, including 8,928 missing CSV values. Solver
settings/RNG, six undefined rings and the geometry warning are preserved. We
accept this small Python change for its consistent measured benefit. The earlier `tf`
share describes source `2de02934d`, before preparation; it is not a measurement
of the changed callback. This fixture result establishes no field accuracy,
global-optimum quality, R-trajectory, platform, installed-package or C++
benefit, and does not close all performance outcomes. The prior forward-native
rejection retains its original scope. Complete paired evidence is keyed by
`artifacts/verification/love-prepared-objective-comparison/run/`.
