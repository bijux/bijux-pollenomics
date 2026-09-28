# LandClim II two-grid example reexecution

The [fresh-run report](report.json) records a new execution of the retained author R function and the current native REVEALS implementation for author example grids 512 and 562. The R runner completed first; the native comparison then read its newly generated bootstrap draws and numerical outputs. The R wrapper memoizes exact repeated inputs to the pure `KPf` function while preserving the author `KPf` and `REVEALS` function bodies. Both processes exited successfully, and every declared regional and site-level cover and standard-error comparison passed. This is a source-bound two-grid result, not a reconstruction of all 1,128 paper records or a test against measured vegetation.

The private author snapshot remains outside this repository. Before execution, the producer verified all 193 members of its manifest by SHA-256. It checked the author R source hash `7675b6e615cddba328bad506692b3a6a31e00d9273cef5ad4641a1737fddfd87`, pinned `zipfR` 0.6.70, and hashed the three execution/comparison scripts plus 46 native Python source files before and after the run. The original R receipt embeds exact hashes for 26 used inputs and 77 output CSV files. The governed report retains that receipt, the complete comparison report, source hashes, process exit codes, runtime versions, raw-report hashes, and SHA-256 identities for the two native output checksum manifests. Those manifests cover 53 files for grid 512 and 52 files for grid 562. Raw R/native output remains under `artifacts/jobs/landclim-example-reexecution/fresh-run/`.

| Author grid | Sites | Time bins | Taxa | Available site-bins | Regional cover maximum absolute error | Regional SE maximum absolute error |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 512 | 9 | 25 | 31 | 97 | `1.2379e-13` | `6.4615e-14` |
| 562 | 8 | 25 | 31 | 87 | `7.3219e-14` | `7.1533e-14` |

Cover comparisons use absolute tolerance `1e-11` and relative tolerance `1e-10`; SE comparisons use absolute tolerance `5e-8` and relative tolerance `1e-9`. The comparator also requires matching undefined-value masks and equal site counts. Available site-bins are 97/225 and 87/200 respectively; missing source site-bins are explicitly unavailable in the native adapter. The report records the macOS arm64, R, Python, NumPy, pandas, and SciPy versions used here. Its Git commit is the exact source context at execution; the native source hashes are the definitive identity if a later commit changes the tree.

To verify the retained governed claims without the private author snapshot:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.example_reexecution \
  --verify-report docs/report/publication-replay/landclim-example-reexecution/report.json
```

Add `--output artifacts/jobs/landclim-example-reexecution/fresh-run` to verify the locally retained R output CSVs, every native output listed by its checksum manifest, reference and comparison reports, and execution logs by SHA-256. To produce an independent fresh execution, supply the acquired snapshot through `--private` and choose absent `--output` and `--report` paths:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src:packages/bijux-pollenomics-lra/src \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.example_reexecution \
  --repository . --private "$BIJUX_LANDCLIM_AUTHOR_REFERENCE" \
  --output artifacts/jobs/landclim-example-reexecution/another-run \
  --report artifacts/jobs/landclim-example-reexecution/another-report.json
```

The result does not resolve private-input redistribution rights, the publication PFT-count disagreement, full-study input identity, or independent vegetation accuracy.

A separate [tagged Petr Kuneš R comparison](../../method-certification/petrkunes-r-comparison/README.md)
checks one 225 BP author window on single, unequal-pair, six-active-site and
full-nine-site inputs. It finds zero original-versus-tagged R residuals on
those selected cases. A direct native replay using the tagged R full-grid
site draws matches 31 cover and 31 SE values within the declared source
tolerances. The tagged source shares the historical implementation lineage,
and its one-window random stream differs from this full 25-window receipt.
