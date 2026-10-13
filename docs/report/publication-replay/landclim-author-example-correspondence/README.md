# LandClim II author-example correspondence

The [row-level ledger](paper-correspondence.csv), [generated report](REPORT.md), and [numerical summary](report.json) compare the installed LRA publication profile with an independent exact author-R replay on the 17 author sites in grids 512 and 562. All 14,074 supported fractional cover and standard-error values pass the declared source tolerances. Maximum absolute residuals are 1.83881e-13 for means and 7.15331e-14 for standard errors. The 25-bin source profile has unavailable site-bins, which the report counts separately.

The [source and output manifest](manifest.json) records the producer and the original retained run. The original CSV was newline-normalized for the repository; the generated Markdown and JSON retain their original bytes. The current producer writes LF line endings directly. Replaying from the retained original candidate and author-R reference reproduces all three governed files byte for byte. An [independent R/native execution](../landclim-example-reexecution/README.md) produced the same row-level CSV and generated Markdown. Its JSON differs only in the reference receipt digest because that R execution has a new receipt.

Replay the governed correspondence from the original candidate and author-R reference retained in the private source store:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.author_example_correspondence \
  --run ../bijux-pollenomics-data/landclim/two-grid-process/run/run001 \
  --reference ../bijux-pollenomics-data/landclim/author-reference/reference \
  --output artifacts/jobs/author-example-correspondence/replay
```

This is two author grids, not the complete historical paper input set or a vegetation validation.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Published-product versus released-author-example correspondence, not authenticated original input reconstruction.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md) (source SHA-256 `ffcac6cb938189c61113cf92453c4ee1c79fcd9a69305d4bf15fec387bbca898`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
