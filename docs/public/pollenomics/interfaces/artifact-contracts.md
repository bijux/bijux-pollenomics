---
title: Artifact Contracts
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-10
---

# Artifact Contracts

Published artifacts are part of the runtime contract because they are checked
in and reviewed like code.

That means the public outputs are not optional decoration around the runtime.
They are part of what the runtime is for. If the runtime writes a bundle, map,
or audit surface, you should be able to inspect that artifact directly and
understand what family it belongs to.

## Main Artifact Families

- country bundles under `docs/report/countries/<country-slug>/`
- the world surface under `docs/report/world/` and regional surfaces under `docs/report/regions/`
- root-level report artifacts under `docs/report/` that summarize public animal
  coverage, chronology overlap, first appearance, and scenario posture
- report summaries and map payloads produced by the reporting package
- atlas candidate ranking sidecars that summarize locality proximity against
  tracked context layers

## Direct Inspection Anchors

- [world map](../../../report/world/world_map.html)
- [world animal evidence rows](../../../report/world/world_animal_atlas_evidence.json)
- [Sweden country bundle](../../../report/countries/sweden/README.md)
- [animal atlas readiness](../../../report/animal_atlas_readiness.md)
- [animal country coverage](../../../report/animal_country_species_coverage.md)
- [animal output honesty](../../../report/animal_output_honesty.md)
- [animal atlas exclusion report](../../../report/animal_atlas_exclusion_report.md)
- [repository truth posture](../../../report/repository_truth_posture.md)
- [repository claim audit](../../../report/repository_claim_audit.md)
- sample-backed species evidence in `data/adna/species/ovis_aries/normalized/sample_records.json`

## Stable Path Anchors

- `reporting/bundles/paths.py` defines the named path families for country and atlas bundles
- country bundles include `README.md`, sample tables, species tables, locality GeoJSON, citations, warnings, and summary JSON outputs
- the world surface includes the map HTML document, animal evidence rows, point traceability, and summary JSON outputs
- root-level report artifacts include `animal_output_audit.*`, `animal_output_honesty.*`, `animal_atlas_readiness.*`, `animal_atlas_exclusion_report.*`, `animal_country_species_coverage.*`, repository truth reviews, chronology overlap artifacts, and scenario posture artifacts

## What This Contract Prevents

- report outputs should not drift into ad hoc names or locations
- the same output family should not move silently between public and transient
  roots
- documentation pages may explain an artifact, but they should not replace the
  governed file itself
- publication logic should not present a surface as stable if its path contract
  is still fluid

## First Proof Check

- `docs/report/`
- `src/bijux_pollenomics/reporting/bundles/paths.py`
- `src/bijux_pollenomics/reporting/rendering/`
- `tests/unit/test_reporting_artifacts.py`
- `tests/regression/test_country_report.py`
