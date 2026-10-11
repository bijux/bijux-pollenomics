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
