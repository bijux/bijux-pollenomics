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

The producer and governed CSV both use LF line endings, so all three generated
outputs can be compared byte for byte. This comparison admits no Swedish LRA
sample and does not resolve core identity, rights, chronology or pollen-count
denominators.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
