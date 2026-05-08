---
title: Output Surface Classes
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Output Surface Classes

The repository ships several different kinds of outputs. They should not be
read with one shared confidence level.

## Current Classes

| Class | What belongs here | Main examples | How to read it |
| --- | --- | --- | --- |
| Pollen-driven context outputs | direct pollen or paleoecological context layers | `docs/report/nordic-atlas/nordic_pollen_site_sequences.geojson`, `nordic_pollen_sites.geojson`, `nordic_reveals_grid_cells.geojson` | first-class context for pollenomics questions |
| Contextual support outputs | archaeology, boundary, and fieldwork layers | `nordic_environmental_sites.geojson`, `sweden_archaeology_density.geojson`, `nordic_country_boundaries.geojson`, `docs/04-fieldwork/` | contextual framing, not direct pollen or sample evidence |
| Recovery-bound animal outputs | sample-backed but still partial animal aDNA outputs | `docs/report/nordic-atlas/nordic-atlas_animal_atlas_evidence.json`, `docs/report/*/*_animal_adna_v66_summary.json` | usable only with the release gate and support packets beside them |
| Pipeline scaffolding and review packets | governance, truth, and audit packets | `docs/report/repository_truth_posture.md`, `repository_source_family_matrix.md`, `animal_publication_release_gate.md` | review surfaces that explain trust and gaps, not scientific evidence on their own |

## Reader Anchors

- [`docs/report/repository_cross_domain_evidence_matrix.md`](../../report/repository_cross_domain_evidence_matrix.md)
- [`docs/report/repository_atlas_input_audit.md`](../../report/repository_atlas_input_audit.md)
- [`docs/report/repository_source_explainer_audit.md`](../../report/repository_source_explainer_audit.md)

## Boundary

The atlas and country bundles mix these classes visually. The docs should keep
their confidence levels separate so readers do not mistake a strong framing or
review packet for direct scientific balance.
