---
title: Artifact Contracts
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Artifact Contracts

Published artifacts are part of the package contract because they are checked
in and reviewed like code. Readers encounter them as the country bundles and
the atlas itself, not as disposable build leftovers.

## Main Artifact Families

- country bundles under `docs/report/<country-slug>/`
- the shared atlas under `docs/report/nordic-atlas/`
- report summaries and map payloads produced by the reporting package

## Stable Path Anchors

- `reporting/bundles/paths.py` defines the named path families for country and
  atlas bundles
- country bundles include `README.md`, sample and locality CSV files, sample
  GeoJSON, sample Markdown, and summary JSON outputs
- atlas bundles include `README.md`, the map HTML document, sample GeoJSON, and
  summary JSON outputs
- bundled map assets copied by the rendering layer are part of the publication
  surface because broken assets break the published reader experience

## First Proof Check

- `docs/report/`
- `src/bijux_pollenomics/reporting/bundles/paths.py`
- `src/bijux_pollenomics/reporting/rendering/`
- `tests/unit/test_reporting_artifacts.py`
- `tests/regression/test_country_report.py`
