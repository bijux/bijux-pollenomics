---
title: Artifact Contracts
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# Artifact Contracts

Published artifacts are part of the runtime contract because they are checked
in and reviewed like code.

## Main Artifact Families

- country bundles under `docs/report/<country-slug>/`
- the shared atlas under `docs/report/nordic-atlas/`
- root-level report artifacts under `docs/report/` that summarize public animal
  coverage, chronology overlap, first appearance, and scenario posture
- report summaries and map payloads produced by the reporting package
- atlas candidate ranking sidecars that summarize locality proximity against
  tracked context layers

## Direct Reader Anchors

- [shared atlas map](../../report/nordic-atlas/nordic-atlas_map.html)
- [shared atlas evidence rows](../../report/nordic-atlas/nordic-atlas_animal_atlas_evidence.json)
- [Sweden country bundle](../../report/sweden/README.md)
- [animal atlas readiness](../../report/animal_atlas_readiness.md)
- [animal country coverage](../../report/animal_country_species_coverage.md)
- [repository truth posture](../../report/repository_truth_posture.md)
- [repository claim audit](../../report/repository_claim_audit.md)
- [sample-backed species evidence](../../../data/adna/species/ovis_aries/normalized/sample_records.json)

## Stable Path Anchors

- `reporting/bundles/paths.py` defines the named path families for country and atlas bundles
- country bundles include `README.md`, sample tables, species tables, locality GeoJSON, citations, warnings, and summary JSON outputs
- the shared atlas includes the map HTML document, animal evidence rows, point traceability, and summary JSON outputs
- root-level report artifacts include `animal_output_audit.*`, `animal_atlas_readiness.*`, `animal_country_species_coverage.*`, repository truth packets, chronology overlap artifacts, and scenario posture artifacts

## First Proof Check

- `docs/report/`
- `src/bijux_pollenomics/reporting/bundles/paths.py`
- `src/bijux_pollenomics/reporting/rendering/`
- `tests/unit/test_reporting_artifacts.py`
- `tests/regression/test_country_report.py`
