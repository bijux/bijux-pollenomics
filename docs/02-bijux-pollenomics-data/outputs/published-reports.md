---
title: Published Reports
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# Published Reports

Published report bundles now live under one governed geography tree:

- `docs/report/index.md`
- `docs/report/how-to-read.md`
- `docs/report/world/`
- `docs/report/regions/europe-plus/`
- `docs/report/regions/nordic/`
- `docs/report/countries/<country-slug>/`

Country bundles are still the narrowest reader-facing answer, but they now sit
inside a broader world -> region -> country model instead of beside one shared
atlas with ad hoc links.

The report tree now also has one reader-facing portal. Use that portal first if
you do not already know which packet family you need.

## Direct Files

- [report portal](../../report/index.md)
- [how to read the report tree](../../report/how-to-read.md)
- [map surfaces guide](../../report/maps/index.md)
- [scope-filtered outputs guide](../../report/scopes/index.md)
- [evidence reviews guide](../../report/reviews/index.md)
- [scientific caveats guide](../../report/caveats/index.md)
- [maintainer truth guide](../../report/maintenance/index.md)
- [world evidence surface](../../report/world/README.md)
- [world map publication contract](../../report/world/world_map_publication_contract.md)
- [world point traceability](../../report/world/world_point_traceability.md)
- [Europe-plus evidence surface](../../report/regions/europe-plus/README.md)
- [Europe-plus map publication contract](../../report/regions/europe-plus/europe-plus_map_publication_contract.md)
- [Nordic evidence surface](../../report/regions/nordic/README.md)
- [Nordic map publication contract](../../report/regions/nordic/nordic_map_publication_contract.md)
- [Nordic point traceability](../../report/regions/nordic/nordic_point_traceability.md)
- [Sweden country bundle](../../report/countries/sweden/README.md)
- [Norway country bundle](../../report/countries/norway/README.md)
- [Sweden animal sample query](../../report/countries/sweden/sweden_animal_adna_v66_samples.md)
- [Norway animal sample query](../../report/countries/norway/norway_animal_adna_v66_samples.md)
- [animal point evidence review](../../report/animal_point_evidence_review.md)
- [animal intake recovery review](../../report/animal_intake_recovery_review.md)
- [animal sample database review](../../report/animal_sample_database_review.md)
- [animal country coverage](../../report/animal_country_species_coverage.md)
- [animal output honesty](../../report/animal_output_honesty.md)
- [animal atlas exclusion report](../../report/animal_atlas_exclusion_report.md)
- [repository truth posture](../../report/repository_truth_posture.md)
- [repository recovery review](../../report/repository_recovery_review.md)
- [repository source family matrix](../../report/repository_source_family_matrix.md)
- [repository source acquisition queue](../../report/repository_source_acquisition_queue.md)
- [publication geography registry](../../report/publication_geography_registry.md)
- [publication geography subset validation](../../report/publication_geography_subset_validation.md)
- [publication country onboarding contract](../../report/publication_country_onboarding_contract.md)
- [published reports summary](../../report/published_reports_summary.json)
- `data/evidence_artifact_contracts.json`
- `data/source_fact_ownership_registry.json`

## What The Geography Tree Is Good For

- giving a serious newcomer one route into maps, scope bundles, reviews, caveats, and maintainer truth packets
- showing the broadest world-facing evidence surface first
- deriving Europe-plus and Nordic views through explicit reusable filters
- publishing one inspectable contract for scope bounds, basemap posture, layer roles, and caveats per shared map surface
- showing which animal rows currently survive one country filter
- keeping citations, warnings, and sample tables together
- exposing the difference between visible rows and blocked rows at world, region, and country scale

## Read In This Order

1. Open the [report portal](../../report/index.md).
2. Open [how to read the report tree](../../report/how-to-read.md) if your question is still vague.
3. Choose [maps](../../report/maps/index.md), [scopes](../../report/scopes/index.md), [reviews](../../report/reviews/index.md), or [caveats](../../report/caveats/index.md).
4. Drop to one world, regional, or country bundle only after you know why that narrower surface is the right answer.

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
summary JSON files keep exact sample, site, chronology, and coordinate evidence
locators for every published animal row, and the broader world and regional
surfaces keep the parent lineage visible.

The governing file contract for those bundle families is published in
`data/evidence_artifact_contracts.json`, and the owning-truth registry that
distinguishes bundle views from governing sample and site surfaces is published
in `data/source_fact_ownership_registry.json`.
