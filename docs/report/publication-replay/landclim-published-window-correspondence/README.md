# LandClim II published-window correspondence

The [row-level ledger](paper-correspondence.csv), [generated report](REPORT.md), and [numerical summary](report.json) compare the author-example Python recomputation with the pinned June 2021 PANGAEA archive on the sole exact shared interval, TW2 at 100–350 BP. All 62 grid/taxon keys pair. For grids 512 and 562, the largest absolute mean gaps are 9.19787 and 10.55270 percentage points; the largest standard-error gaps are 3.21615 and 4.25814 points. This cross-revision comparison has no pass tolerance.

The [source and output manifest](manifest.json) binds the producer and original retained run. Its CSV is newline-normalized for the repository; the generated Markdown and JSON retain their original bytes. A new [independent R/native execution](../landclim-example-reexecution/README.md) produced the same row-level CSV and Markdown. Its JSON differs only in the candidate parity receipt digest because the R/native execution has a new receipt.

After producing that R/native execution, replay this comparison with the repository Python environment and the private author source root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.published_window_correspondence \
  --raw data/landclim/raw \
  --author "$BIJUX_LANDCLIM_AUTHOR_REFERENCE/author" \
  --run artifacts/jobs/landclim-example-reexecution/independent-r-library-run/comparison \
  --reference artifacts/jobs/landclim-example-reexecution/independent-r-library-run/reference \
  --output artifacts/published-window-correspondence/replay
```

Matching keys and units do not authenticate the historical raw-input cohort, the other 24 published intervals, functional-type classification, or measured vegetation accuracy.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Published-product versus released-author-example correspondence, not authenticated original input reconstruction.

**Supported claim.** The exact common 100–350 BP window pairs all 31 taxon mean/SE axes in two author grids against the pinned June 2021 PANGAEA modeled-product archive, with explicit fraction-to-percentage conversion and all residuals retained.

**Unsupported claim.** Paired keys/time support do not establish matching historical raw cohorts, other 24 windows, functional-type identity, statistical equivalence, whole-paper reproduction or independent measured vegetation accuracy.

**Actual verification performed.** The narrative, ledger/source manifest and comparison report were inspected. The retained correspondence has 62 mean and 62 SE pairs with no missing/extra keys and no pass tolerance. This qualification runs no LRA model, R program or numerical comparator.

**Remaining input or review.** Historical 2016 author versus 2021 archive source selection, count revisions, chronology, taxon/PFT transformation and intended-use decisions remain unresolved; the other 24 intervals have different bounds. Independent vegetation observations and qualified review are separate.

**Cause category.** data | comparability | assumption | qualified review

**Consequence.** Large candidate-minus-archive gaps are descriptive cross-revision model differences, not failed source-parity tests or independent field error. Their presence cannot be removed by matching taxon keys or normalizing output.

**Precise next acceptance route.** Authenticate a named historical source cohort/chronology/transformation for the shared window and replay it against the archive; retain all residuals and declare any later comparison criterion before inspecting new outcomes.

**Negative or refused result.** Maximum mean gaps 9.19787/10.55270 pp and SE gaps 3.21615/4.25814 pp remain. Twenty-four nonmatching intervals and unresolved PFT columns are excluded rather than silently matched; no pass tolerance is assigned to archive correspondence.

**Matched denominator.** TW2=[100,350)BP, two grids ×31 taxa =62 keys,62 mean+62 SE =124 values. Six author sites contribute in grid 512 and five in 562. This is one exact interval of 25, not the full 1,128-record study.

Qualified authored reader SHA-256: `dcfc09eaf1fa4ad663395164081ce9a7f07c47f9add1879c7f5c4c59296b30ea`.

- [Retained qualification evidence: docs/report/publication-replay/landclim-published-window-correspondence/report.json](report.json) (SHA-256 `0a22e51a8e109dbadbd713f27b84826421a0e156bdd9d97856a053a4eb0cee32`).

- [Retained qualification evidence: docs/report/publication-replay/landclim-published-window-correspondence/paper-correspondence.csv](paper-correspondence.csv) (SHA-256 `591b32c97d66ceb0884388e41e714f51fd51ff79a01ffc9dbd4ae697a75b91ee`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md) (source SHA-256 `ffcac6cb938189c61113cf92453c4ee1c79fcd9a69305d4bf15fec387bbca898`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
