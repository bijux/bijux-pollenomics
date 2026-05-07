---
title: Directory Layout
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# Directory Layout

The tracked evidence tree keeps three surfaces separate. The first is the
species-owned ancient-DNA surface, which is where domesticated-animal curation roots
live before they become public report or atlas rows.

- `data/adna/<latin_name>/` for species-owned raw, normalized, manifest, report, and review files
- `docs/report/<country-slug>/` for published country bundles
- `docs/report/nordic-atlas/` for the shared public atlas bundle

## Reader Anchors

- [`data/adna/ovis_aries/`](../../../data/adna/ovis_aries/README.md)
- `data/adna/equus_caballus/`
- `data/adna/bos_taurus/`
- `data/adna/canis_lupus_familiaris/`
- `data/adna/camelus_dromedarius/`
- `data/adna/rangifer_tarandus/`
- `data/adna/equus_asinus/`
- `data/adna/felis_catus/`
- [`data/adna/source_library/`](../../../data/adna/source_library/project_registry.json)
- [`docs/report/sweden/`](../../report/sweden/README.md)
- [`docs/report/nordic-atlas/`](../../report/nordic-atlas/nordic-atlas_map.html)

The directory layout matters because map outputs are downstream proof surfaces.
The tracked species roots and source library are where the evidence basis lives.
