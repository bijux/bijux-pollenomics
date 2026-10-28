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

**Supported claim.** On the exact shared window, all 62 pairs of reported mean±oneSE envelopes overlap under the declared separation criterion; current maintained envelope execution and separate metadata custody retain distinct evidence roles.

**Unsupported claim.** Envelope overlap is not a significance test, equivalence, calibrated confidence coverage, historical source identity, ecological accuracy or reproduction of the full study. A custody manifest cannot substitute numerical execution.

**Actual verification performed.** The narrative distinguishes actual current envelope replay from the separate metadata-only custody writer; its report/ledger and historical custody account were inspected. This qualification runs neither envelope comparisons nor metadata writer, R process or LRA model.

**Remaining input or review.** Cross-version dependence, historical raw-input identity, full covariance and uncertainty construction remain unknown. Matching measured vegetation and qualified uncertainty review are needed for an empirical coverage claim.

**Cause category.** data | assumption | comparability | qualified review

**Consequence.** Report zero disjoint one-SE envelopes as descriptive arithmetic only. Shared historical inputs can induce dependence, and unknown joint covariance prevents interpreting overlap as a hypothesis-test or coverage result.

**Precise next acceptance route.** Qualify the original covariance, historical cohort and mean/SE construction before any inferential comparison; retain the actual current replay receipt and historical producer identity separately. Add independent measured observations and external uncertainty review for coverage.

**Negative or refused result.** No envelopes are disjoint among the 31 taxa in either grid. This zero is not a zero-error or reproduced-history claim. The historical 7,746-byte producer remains separately recorded rather than being relabeled the current implementation.

**Matched denominator.** Two grids ×31 taxa =62 envelope pairs at 100–350 BP; each envelope uses one reported marginal SE in percentage cover. Disjoint=0/31 per grid; other 24 intervals and cross-grid/time dependence are not tested.

- [Retained qualification evidence: docs/report/publication-replay/landclim-published-window-uncertainty/report.json](report.json) (SHA-256 `733da7ce47e2c73a4a5bc0506359244cc3c2ed0ccafe01a59ef08fe79ad78eaa`).

- [Retained qualification evidence: docs/report/publication-replay/landclim-published-window-uncertainty/taxon-envelopes.csv](taxon-envelopes.csv) (SHA-256 `66df138e45330a5674e5d9130f115022c6ed59a4de33f87bc985332feda550fa`).

- [Retained qualification evidence: docs/report/publication-replay/landclim-published-window-uncertainty/source/retained-custody.json](source/retained-custody.json) (SHA-256 `02be1738a20737a9c8ec2b9de065fd88e67162f92223d9ef4417bb4be4f48137`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
