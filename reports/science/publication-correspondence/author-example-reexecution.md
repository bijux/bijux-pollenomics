# How we reexecuted the released LandClim author example

## Our decision

We executed the released author R calculation and the current source Python
REVEALS implementation on both released example grids. We compared only
estimates whose source pollen counts establish support. This is numerical
correspondence on those examples, without a historical 1,128-record claim or
independent vegetation accuracy.

## What we ran

The numerical calculation used clean source commit
`e282e08d796528488b438edd3ea661fb94b97b5d`. All 193 private snapshot members,
26 used author inputs and the unchanged author R function were authenticated.
The maintained report names 59 native Python source files; the
registered plans additionally retain the complete source and runtime custody.
R 4.6.0 and zipfR 0.6.70 ran in the declared isolated Linux ARM64 container;
Python 3.11.13 ran on the recorded macOS host. This mixed execution is not a
same-revision hosted x86_64 or historical-runtime certificate.

The author R function bodies were unchanged. Pure `KPf` results were memoized
by exact input tuple. The current Python calculation used the original run's
actual 1,000-draw source-site bootstrap indices, preserving the full site IDs.
The two numerical stages returned zero. Their original third observer and
whole job returned one; a later independent saved-output observer passed.
Those records remain distinct.

The [execution report](../../../docs/report/publication-replay/landclim-example-reexecution/report.json)
binds 77 original R CSVs and the two native checksum closures of 53 and 52
files. The new [cell ledger](../../../docs/report/publication-replay/landclim-author-example-correspondence/paper-correspondence.csv)
was produced separately without repeating R or Python numerical calculations.
Its first observer refused an incorrect off-support NaN assertion; the corrected
saved-ledger observer passed with terminal SHA-256 `71d5f761f80e074d30fb1b13c4c0d53a3d34c86f9d5fa3dfa9e045bfb1ffbf45`.
Private source bytes remain external, and all older failures are retained.

## What we found

| Author grid | Sites | Bins | Taxa | Available site-bins | Maximum mean difference | Maximum SE difference |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 512 | 9 | 25 | 31 | 97/225 | `1.25455e-13` | `6.4615e-14` |
| 562 | 8 | 25 | 31 | 87/200 | `1.83881e-13` | `7.15331e-14` |

All 14,074 supported regional and site-level mean/SE pairs pass the original
absolute/relative bounds: `1e-11`/`1e-10` for means and `5e-8`/`1e-9` for
standard errors. The 184 available site-bins and 241 unavailable site-bins are
joined to the original pollen-count tables. Seven regional bins lack support.
Original R serializes zeros in unsupported cells; these are placeholders,
not measured absences or paired estimates. Current Python serializes missing
values there. Neither representation supplies observation support.

The current files belong to this genuine new execution epoch. We do not
claim byte identity with the earlier `9dd1` receipt, whose raw original proof
is unavailable. Older numerical tables and limitations remain in Git history.

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

Supply the actual saved-output directory with `--output`
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

The report records the host and container versions separately. Its source
hashes bind the actual calculation even when repository HEAD advances. A
future run has a new receipt and must be qualified separately.

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
and research-needs register.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Released 2016 author-R and current source-Python REVEALS example grids execute on the same prepared source profile.

**Unsupported claim.** Historical June 2021 archive production or independent ecological accuracy.

**Actual verification performed.** The original author R and current source Python stages genuinely completed on commit e282e08d796528488b438edd3ea661fb94b97b5d. Their original third-observer refusal and whole-job exit1 remain unchanged. The complete saved-source observer on 2784d4eae839e4a4e43f80ec77fd26bd0172aff0 passed; the separate maintained correspondence writer on e1ca9def55e7cd3e68ac6f20270059e743373251 returned0, while its original observer and aggregate returned1. The corrected saved-ledger observer genuinely passed with terminal 71d5f761f80e074d30fb1b13c4c0d53a3d34c86f9d5fa3dfa9e045bfb1ffbf45, rejoining every one of 14,074 ordered mean/SE cells to original R/current Python and the complete source support. Published reexecution report SHA256 4deb4e836c9ef8b81d5c29809bc2df7aed4d9dadef208f1cd866466e17d8b99f; ledger SHA256 1380633da596cfa0a51ec94ef885a7e94eecc617e37d78d0ed7c4f22121f5029. All184 available and241 unavailable site-bins remain source-bound. Original R off-support zero placeholders remain excluded; Python off-support values remain missing. Original mean/SE tolerances,1000 exact shared bootstrap draws and all17 source sites remain retained. Historical9dd1 raw proof is unavailable and is not used. No new math is executed for publication and no full1128study, independent vegetation, Nordic, source-rights, human or official release acceptance is asserted.

**Remaining input or review.** The 17-site author R/native example calculation is reproduced, but it does not bind historical archive source revisions, other windows or independent vegetation truth. Resolver: LandClim historical producer and qualified publication reviewer Reopen when: An authenticated production input snapshot links a named published grid/window to the author computation.

**Cause category.** data|comparability

**Consequence.** Treat the exact example as a calculation control, not proof of historical input identity.

**Precise next acceptance route.** An authenticated production input snapshot links a named published grid/window to the author computation. Then update reports/science/publication-correspondence.md.

**Negative or refused result.** No paired example mismatch within declared tolerance; historical archive gaps remain separately observed.

**Matched denominator.** 17 prepared site files; grid 512 nine sites, grid 562 eight sites; 25 time bins and 31 taxa.

Retained evidence: [docs/report/publication-replay/landclim-example-reexecution/report.json](../../../docs/report/publication-replay/landclim-example-reexecution/report.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-claim-semantic-sha256: 414684ab7ccba9d78526fead0151d180bc5aba590c282d80564b097bab1eca53 -->
<!-- scientific-authored-source-sha256: e89bdd5d78cc63267c53ba9133f4b1012e429fbadb1293d669297ca288aed199 -->
<!-- scientific-verification-and-limits:end -->
