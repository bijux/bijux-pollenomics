# LandClim published-window uncertainty envelopes

The [62-row envelope ledger](taxon-envelopes.csv) compares the reported mean
± one standard error for each of 31 taxa in grids 512 and 562 at the shared
100–350 BP window. Each grid has **0 of 31 disjoint envelopes** by the declared
gap criterion. The [generated report](REPORT.md) and [numerical summary](report.json)
retain the exact counts and source identities; the [manifest](manifest.json)
binds their bytes to the governed [three-way correspondence](../landclim-published-window-provenance/README.md).

This is a descriptive cross-version comparison. The two result sets may share
historical inputs, and their dependence is unknown; overlap is not a
significance test. It does not establish measured vegetation accuracy or
reproduction of the complete published study.

Reproduce from the repository root into a new artifact directory:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.published_window_uncertainty \
  --correspondence-csv docs/report/publication-replay/landclim-published-window-provenance/paper-correspondence.csv \
  --provenance-report docs/report/publication-replay/landclim-published-window-provenance/report.json \
  --output artifacts/landclim-published-window-uncertainty/replay
```

The producer emits CRLF CSV line endings. The governed ledger uses LF with
identical parsed rows.
