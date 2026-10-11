# LandClim published-window numerical provenance

The [124-row ledger](paper-correspondence.csv) pairs 31 mean and 31 standard
error values in each of grids 512 and 562 at the exact shared 100–350 BP
window. It compares the independent author-R example, the installed LRA
calculation and the pinned June 2021 PANGAEA archive. Installed Python and
author R agree within 1.238×10⁻¹¹ percentage points on these rows. The
largest author-R versus archive mean gaps are 9.19787 and 10.55270 percentage
points. The archive difference is also present in the independent R result.

The [numerical summary](report.json) retains the unrenormalized 31-taxon mean
vectors. Their L1 gaps are 18.481237 and 22.140770 percentage points;
total-variation fractions are 0.092406 and 0.110704. The
[generated interpretation](REPORT.md) records the leading taxa and Hellinger
distances. These are cross-version modeled-product differences, not vegetation
accuracy or a claim that the historical raw-input cohorts match. The
[manifest](manifest.json) binds the producer, governed correspondence inputs,
private taxon crosswalk and outputs.

After the two upstream [author-example](../landclim-author-example-correspondence/README.md)
and [published-window](../landclim-published-window-correspondence/README.md)
ledgers are present, reproduce into a new artifact directory:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.published_window_provenance \
  --author-csv docs/report/publication-replay/landclim-author-example-correspondence/paper-correspondence.csv \
  --author-report docs/report/publication-replay/landclim-author-example-correspondence/report.json \
  --published-csv docs/report/publication-replay/landclim-published-window-correspondence/paper-correspondence.csv \
  --published-report docs/report/publication-replay/landclim-published-window-correspondence/report.json \
  --crosswalk-csv ../bijux-pollenomics-data/landclim/author-reference/reference/taxon-name-crosswalk.csv \
  --output artifacts/landclim-published-window-provenance/replay
```

The producer writes CRLF CSV line endings; the governed ledger uses LF with
identical parsed rows. No untouched publication or vegetation validation
follows from this exact-window correspondence.
