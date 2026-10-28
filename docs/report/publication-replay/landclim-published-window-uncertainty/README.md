# LandClim published-window uncertainty envelopes

The [62-row envelope ledger](taxon-envelopes.csv) compares the reported mean
± one standard error for each of 31 taxa in grids 512 and 562 at the shared
100–350 BP window. The shared published-window contract fixes the archive
identity, window and grid axes for the correspondence and envelope consumers.
Each grid has **0 of 31 disjoint envelopes** by the declared
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

The maintained envelope producer has been executed against the governed
correspondence and provenance inputs. Its 62 grid/taxon mean and reported
standard-error pairs reproduce the three retained outputs, including the CSV
with governed LF line endings. The metadata manifest separately accounts for
the physical producer, provenance inputs and retained output bytes; that
accounting is not the evidence of numerical execution.

The exact prior manifest is preserved in
[the retained custody source](source/retained-custody.json). It identifies the
historical 7746-byte producer separately from the current implementation, whose
exact identity is recorded in the current manifest. The accepted current replay
does not establish the original historical execution or close the historical
raw-input qualifications.

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
separate from current physical code. The separately verified current envelope replay supplies the current-execution
evidence. This custody metadata remains byte accounting and supplies neither
that execution evidence nor scientific admission.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Published-product versus released-author-example correspondence, not authenticated original input reconstruction.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
