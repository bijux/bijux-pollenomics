---
title: Published Reports
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Published Reports

Published report bundles live under `docs/report/<country-slug>/`.

Each country bundle is the public answer to a narrower question than the atlas:
which sample-owned animal rows survive country-level publication after the same
site, chronology, and coordinate rules are applied?

## Direct Files

- [Sweden country bundle](../../report/sweden/README.md)
- [Norway country bundle](../../report/norway/README.md)
- [Sweden animal sample query](../../report/sweden/sweden_animal_adna_v66_samples.md)
- [Norway animal sample query](../../report/norway/norway_animal_adna_v66_samples.md)
- [animal point evidence review](../../report/animal_point_evidence_review.md)
- [animal sample database review](../../report/animal_sample_database_review.md)
- [animal country coverage](../../report/animal_country_species_coverage.md)
- [animal output honesty](../../report/animal_output_honesty.md)
- [animal atlas exclusion report](../../report/animal_atlas_exclusion_report.md)
- [repository truth posture](../../report/repository_truth_posture.md)
- [repository recovery review](../../report/repository_recovery_review.md)
- [repository source family matrix](../../report/repository_source_family_matrix.md)
- [repository source acquisition queue](../../report/repository_source_acquisition_queue.md)
- [published reports summary](../../report/published_reports_summary.json)

## What Country Bundles Are Good For

- showing which animal rows currently survive one country filter
- keeping citations, warnings, and sample tables together
- exposing the difference between visible rows and blocked rows at country scale

## Expected Animal Bundle Files

- `README.md`
- `*_animal_adna_*_summary.json`
- `*_animal_adna_*_samples.csv`
- `*_animal_adna_*_samples.md`
- `*_animal_adna_*_species.csv`
- `*_animal_adna_*_localities.geojson`
- `*_animal_adna_*_citations.md`
- `*_animal_adna_*_warnings.md`

Country bundles are not a replacement for the tracked evidence tables. They are
reader-facing summaries derived from them. The current country sample tables and
summary JSON files now keep exact sample, site, chronology, and coordinate
evidence locators for every published animal row.
