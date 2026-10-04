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

The retained CSV uses governed LF line endings. The metadata manifest accounts
for the current physical producer and provenance inputs alongside all three
retained outputs. The historical comparison remains a separate provenance
record; this byte accounting does not establish a current numerical replay.

The retained manifest recorded the earlier 7746-byte envelope producer. The
current 9510-byte producer adds input-custody checks before unchanged numerical
arithmetic and output serialization. Matching output hashes do not prove a
fresh execution of that current producer. The exact prior manifest is preserved
in [the retained custody source](source/retained-custody.json). Its original
execution and historical raw-input qualifications remain unresolved.

A separate metadata-only route records current physical code/input/output hashes
and the distinct historical producer identity, without fitting parameters or
executing envelope comparisons:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.essd.uncertainty_custody \
  --repository . --output artifacts/jobs/landclim-uncertainty-custody/products
```

The metadata writer authenticates the fixed retained envelope bytes and every
upstream provenance product, refuses changed inputs or aliases, and publishes
only an absent artifact manifest. Its historical producer record remains
separate from current physical code. A genuine current envelope replay and
root review are required for a current-execution claim; this custody metadata
is byte accounting and does not supply that claim or scientific admission.
