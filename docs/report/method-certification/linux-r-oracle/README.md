# Local Linux R oracle execution

The [source-bound report](report.json) records an actual Linux ARM64 execution
of source-built R 4.6.0 and the locked DISQOVER 0.9.14 private library. The
[core raw results](oracle/report.json) passed **43/43 cases**, including the 18
prospectively declared optimized LOVE cases. The [source-domain raw
results](source-domains/report.json) passed **23/23 cases**. Both raw directories
include executed R scripts, case manifests, source inputs, individual R vectors,
R completion statuses, and R session information. The report binds their
complete byte inventory to the exact source lock and 1,661 captured executable
source files.

The run reused a previously source-built Linux R prefix and its private
source-provisioned package library. Before execution, the producer verified the
38 locked source archives, the R build and provisioning receipts, **1,227 R
runtime files**, **2,784 private library files**, the installed package-version
closure, and the DISQOVER archive. It mounted the source, runtime, and library
read-only into a container with one CPU, 4 GiB memory, and no execution network.
The container ran Python 3.11.16, NumPy 2.4.6, Pandas 2.3.3, SciPy 1.17.1,
and R 4.6.0 on `aarch64-unknown-linux-gnu`. Its exact image ID and pinned
Python base digest are in the report. The producer checked the governed source
hashes again after both R runners and copied raw results to this directory only
after the complete 43 + 23 gate and byte verification passed.

The [commit context](context.json) binds the generated report's SHA-256 to the
1,661-file executed source SHA set. The first `HEAD` observed just after the
run was `44c89c7c77f720166a86dc73b750b3e9223945d2`; the repository had
advanced to `a862468a8ad93cc2e522bdf0173f81f6b84e8cc9` before the
context annotation was written. The producer verified source *bytes* before
and after execution but did not independently capture Git `HEAD` inside the
run. The result therefore belongs to its recorded byte set and must not be
presented as certification of either commit or a later source revision.

An earlier local run also completed 43 + 23 cases, but its source tree changed
during execution. It was **refused**, with its raw output and refusal receipt
retained under `artifacts/jobs/linux-r-oracle/run/`. The source-closed replay
receipt and container logs are under
`artifacts/jobs/linux-r-oracle/source-closed-run/`. That replay took 17.37
seconds and is the sole admitted local Linux result here.

## Reproduction from the retained local custody

With the original verified R runtime, private library, source archive cache,
and pinned container image still available at the recorded artifact paths, run
the [producer](../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/linux_reference.py)
from the repository root with new absent output destinations:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.lra_validation.linux_reference \
  --repository . \
  --output artifacts/jobs/linux-r-oracle/reproduction \
  --retained artifacts/jobs/linux-r-oracle/reproduction-retained \
  --runtime-tree artifacts/v2/linux-r-runtime/build001 \
  --provision-tree artifacts/v2/linux-r-runtime/provision001 \
  --source-cache artifacts/v2/validation/live-r-integration/acquire-001/sources \
  --image-id-path artifacts/jobs/linux-r-oracle/image.id \
  --dockerfile artifacts/jobs/linux-r-oracle/image-context/Dockerfile
```

The runtime, library, image, and private source cache are local artifacts rather
than repository source files; another machine must restore those exact bytes or
rebuild them from the pinned source lock before this command can replay.

## Release boundary

This result is **local Linux ARM64 numerical evidence**, not a release
certificate. The locked release job requires Ubuntu 24.04 on x86_64 and a
matching GitHub run, attempt, committed source revision, and uploaded artifact
digest. None is supplied by this local run. The [release gate](../reference-release-gate/README.md)
must evaluate its own same-attempt CI certificate. Numerical parity does not
establish stochastic optimizer trajectory parity, independent vegetation
accuracy, or ecological propagation accuracy.
