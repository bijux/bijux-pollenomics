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

**Supported claim.** The current comparison retains every 77-site Swedish candidate and its identity/radius-transfer refusal against 84 published sequences.

**Unsupported claim.** A shared name or sub 10 m point gap does not prove physical core identity or permit radius transfer.

**Actual verification performed.** Read the current summary, 77-row ledger and source manifest, retaining the 37-site historical cohort as a subset; no geographic consumer rerun.

**Remaining input or review.** Original core/coordinate reconciliation, chronology, count support, basin model and rights decisions remain required.

**Cause category.** Metadata proximity is an identity lead only.

**Consequence.** The 34 same-name point leads cannot become 34 admitted cores.

**Precise next acceptance route.** Resolve exact physical core/sample selection with source-holder evidence before attaching published radius or chronology.

**Negative or refused result.** Every row refuses identity/radius transfer; Klotjärnen’s 6.773038 km gap forbids assigning its 56 m radius by name.

**Matched denominator.** 77 Neotoma candidate sites, 68 with points, 84 LandClim sequences; 34 same-name point leads, 16 within 10 m; 0 admitted identities/LRA samples.

- [Retained qualification evidence: docs/report/source-relations/neotoma/landclim-site-identity/report.json](report.json) (SHA-256 `9a0b6aee4ead3f8a658b63a279e74c11210bb680c78d538ed83a4b0b4c90f4cf`).

- [Retained qualification evidence: docs/report/source-relations/neotoma/landclim-site-identity/site-comparison.csv](site-comparison.csv) (SHA-256 `104049578ccd4f6fb0e0df869ffa33ed5033bb8a68d5208e019428de7ee43e8c`).

- [Retained qualification evidence: docs/report/source-relations/neotoma/landclim-site-identity/manifest.json](manifest.json) (SHA-256 `9913f7c86614a73c37ab2417e12a299129f9377213f8623f0da182251cd7d4c4`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
