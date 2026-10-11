# LandClim II author-example correspondence

The [row-level ledger](paper-correspondence.csv), [generated report](REPORT.md), and [numerical summary](report.json) compare the installed LRA publication profile with an independent exact author-R replay on the 17 author sites in grids 512 and 562. All 14,074 supported fractional cover and standard-error values pass the declared source tolerances. Maximum absolute residuals are 1.83881e-13 for means and 7.15331e-14 for standard errors. The 25-bin source profile has unavailable site-bins, which the report counts separately.

The [source and output manifest](manifest.json) binds the producer and the original retained run. Its CSV is newline-normalized for the repository; the generated Markdown and JSON retain their original bytes. A new [independent R/native execution](../landclim-example-reexecution/README.md) produced the same row-level CSV and generated Markdown. Its JSON differs only in the reference receipt digest because the R execution has a new receipt.

After producing that R/native execution, replay this correspondence with the repository Python environment:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.author_example_correspondence \
  --run artifacts/jobs/landclim-example-reexecution/independent-r-library-run/comparison \
  --reference artifacts/jobs/landclim-example-reexecution/independent-r-library-run/reference \
  --output artifacts/author-example-correspondence/replay
```

This is two author grids, not the complete historical paper input set or a vegetation validation.
