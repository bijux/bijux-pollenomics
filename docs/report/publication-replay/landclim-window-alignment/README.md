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

The generated CSV uses CRLF line endings; the governed ledger uses LF with
identical parsed rows.
