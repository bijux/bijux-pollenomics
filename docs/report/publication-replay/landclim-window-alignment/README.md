# LandClim author and archive time windows

The [25-row window ledger](window-correspondence.csv) compares the author
example's BP bounds with the published PANGAEA 937075 filename intervals by
time-window index. **Only TW2, 100–350 BP, matches both bounds exactly.**
Twenty-four shared indices have different time support; TW3 already ends at
750 BP in the author example and 700 BP in the archive. The
[generated report](REPORT.md), [summary](report.json) and [manifest](manifest.json)
retain all intervals, source identities and output hashes.

This axis check permits the separately reported exact-TW2 numerical
correspondence. It does not authenticate the historical raw-input cohorts or
reproduce other published windows. Run the producer from the repository root
into a new artifact directory:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.published_window_alignment \
  --bins ../bijux-pollenomics-data/landclim/author-reference/author/bins.csv \
  --lookup ../bijux-pollenomics-data/landclim/author-reference/author/TWlookup.csv \
  --author-report docs/report/publication-replay/landclim-method-profile/reference/report.json \
  --published-report docs/report/publication-replay/landclim-published-window-correspondence/report.json \
  --output artifacts/landclim-window-alignment/replay
```

The producer writes LF line endings. A source-bound replay matches all three
governed outputs byte for byte.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Published-product versus released-author-example correspondence, not authenticated original input reconstruction.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md) (source SHA-256 `ffcac6cb938189c61113cf92453c4ee1c79fcd9a69305d4bf15fec387bbca898`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
