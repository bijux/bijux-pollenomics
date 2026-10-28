# How we reexecuted the released LandClim author example

## Our decision

We reexecuted the released author R calculation and the installed native
REVEALS calculation on both published example grids. We used the exact retained
author source and its 17 prepared site inputs, then compared cover,
standard errors, site support and undefined-value masks. We treated this as a
calculation correspondence test for those examples. We did not use it as a
test of vegetation accuracy or a reconstruction of the historical 1,128
paper records.

## What we ran

We verified all 193 members of the private author snapshot against its
SHA-256 manifest before execution. We checked the author R function hash,
the pinned `zipfR` 0.6.70 dependency, the execution scripts and 46 native
Python source files. The R run completed first; the native comparison read
its new bootstrap draws and numerical output. The R wrapper memoized exact
repeated calls to the pure `KPf` function without changing the author `KPf`
or `REVEALS` function bodies.

We retained the [execution report](../../../docs/report/publication-replay/landclim-example-reexecution/report.json)
with process exits, source and output hashes, software versions, the original
R receipt and the native comparison. The R receipt hashes 26 used inputs and
77 output CSV files. The two native checksum manifests cover 53 and 52 files.
Private inputs remain in the external source store; run products remain under
`artifacts/jobs/landclim-example-reexecution/`.

## What we found

| Author grid | Sites | Bins | Taxa | Available site-bins | Maximum cover difference | Maximum SE difference |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 512 | 9 | 25 | 31 | 97/225 | `1.2379e-13` | `6.4615e-14` |
| 562 | 8 | 25 | 31 | 87/200 | `7.3219e-14` | `7.1533e-14` |

Every declared regional and site-level cover, standard-error, site-count and
undefined-mask comparison passed. We declared absolute/relative tolerances
of `1e-11`/`1e-10` for cover and `5e-8`/`1e-9` for standard errors. The 77
original R CSV outputs and 101 native grid data files were byte-identical
to the earlier retained run. The timing and path-bearing manifests changed
with the new execution.

We also traced [one raw WHH05 sample to a prepared input and site estimate](author-example-site-replay.md).
That trace explains one of the values within
this two-grid calculation; it does not extend the result to the historical
archive inputs.

## Reproduce and interpret

From the repository root, verify the governed report without the private
author snapshot:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.example_reexecution \
  --verify-report docs/report/publication-replay/landclim-example-reexecution/report.json
```

Add `--output artifacts/jobs/landclim-example-reexecution/independent-r-library-run`
to verify the locally retained R output CSVs, native checksum-listed files,
reference and comparison reports, and execution logs by SHA-256.

For a fresh execution, install the pinned `zipfR` 0.6.70 source archive
(SHA-256 `0c318569cf5dd13ab5ea22f7cf797a2daeda09d8332d89ba54fd2d7c643ecf96`)
from the private source store into a run directory, then supply the author
snapshot, that R library and distinct output paths:

```sh
mkdir -p artifacts/jobs/landclim-example-reexecution/zipfr-library
R CMD INSTALL -l artifacts/jobs/landclim-example-reexecution/zipfr-library \
  "$BIJUX_POLLENOMICS_SOURCE_ROOT/lra/dependencies/zipfR_0.6-70.tar.gz"

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src:packages/bijux-pollenomics-lra/src \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.example_reexecution \
  --repository . --private "$BIJUX_LANDCLIM_AUTHOR_REFERENCE" \
  --r-library artifacts/jobs/landclim-example-reexecution/zipfr-library \
  --output artifacts/jobs/landclim-example-reexecution/another-run \
  --report artifacts/jobs/landclim-example-reexecution/another-report.json
```

The retained report names the macOS, R, Python and library versions of the
observed run; its source hashes bind the calculation even if the repository
HEAD later changes.

We separately checked a [tagged Petr Kuneš R implementation](../../../docs/report/method-certification/petrkunes-r-comparison/README.md)
on one 225 BP window with single, unequal-pair, six-active-site and
full-nine-site inputs. Its selected original-versus-tagged R residuals were
zero; a native replay using tagged full-grid draws matched 31 cover and 31
SE values within source tolerances. The tagged source shares the historical
implementation lineage, and its one-window random stream differs from this
25-window receipt.

We established numerical agreement on the two released author examples.
We have not authenticated the full historical input revisions, resolved
the paper/archive PFT disagreement, cleared private-input redistribution
rights or compared our output with independent measured vegetation. Those
questions remain in our [publication account](../publication-correspondence.md)
and the unresolved source requirements described here.
