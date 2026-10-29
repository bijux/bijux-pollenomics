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
