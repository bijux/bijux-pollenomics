# Swedish Neotoma and LandClim site identity leads

The [row ledger](site-comparison.csv) compares the 77 Swedish candidate sites
in the current [Neotoma prerequisite projection](../lra-prerequisites/README.md)
with 84 Swedish LandClim II metadata sequences. Sixty-eight Neotoma sites have
source point coordinates. Thirty-four have a same-name published sequence with
comparable points, and 16 of those points differ by less than 10 m. These are
review leads only: neither a shared name nor a nearby point establishes a
common pollen core or a historical basin outline. Every row refuses radius
transfer and source identity admission.

Klotjärnen illustrates the boundary. The Neotoma point for site 13336 and the
LandClim `KLO` point are 6.773038 km apart, despite the shared name. The
published 56 m `siteradius` cannot be assigned to that Neotoma core. The
[generated report](REPORT.md) and [numerical summary](report.json) retain the
cohort counts and source hashes. The [manifest](manifest.json) binds the
producer, source inputs and retained outputs. All 37 rows from an earlier,
smaller prerequisite projection have identical values in this current ledger;
the old 37-site denominator is historical, not a substitute for 77.

From the repository root, reproduce the current comparison into a new artifact
directory:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.swedish_site_identity \
  --workbook data/landclim/raw/landclim_ii_site_metadata.xlsx \
  --receipt data/landclim/raw/landclim_sources.json \
  --projection docs/report/source-relations/neotoma/lra-prerequisites/projection.json \
  --sites data/neotoma/relational/surfaces/sites/part-00001.json \
  --output artifacts/swedish-site-identity/replay
```

The generated CSV uses CRLF line endings; the governed copy uses LF with the
same rows. This comparison admits no Swedish LRA sample and does not resolve
core identity, rights, chronology or pollen-count denominators.
