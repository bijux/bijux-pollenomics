---
title: Directory Layout
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# Directory Layout

The tracked evidence tree keeps three surfaces separate inside `data/adna/`.
The first is the species-owned ancient-DNA surface where domesticated-animal curation roots keep evidence grouped by species before it is promoted into shared governance or shared publication.

- `data/adna/species/<latin_name>/` for species-owned raw, normalized, manifest, report, and review files
- `data/adna/governance/` for cross-species audits, caveat ledgers, contracts, and source registries
- `data/adna/final/` for shared atlas-ready and country-ready downstream animal outputs

## Reader Anchors

- [`data/adna/species/ovis_aries/`](../../../data/adna/species/ovis_aries/README.md)
- `data/adna/species/equus_caballus/`
- `data/adna/species/bos_taurus/`
- `data/adna/species/canis_lupus_familiaris/`
- `data/adna/species/camelus_dromedarius/`
- `data/adna/species/rangifer_tarandus/`
- `data/adna/species/equus_asinus/`
- `data/adna/species/felis_catus/`
- [`data/adna/governance/source_library/`](../../../data/adna/governance/source_library/project_registry.json)
- [`docs/report/sweden/`](../../report/sweden/README.md)
- [`docs/report/nordic-atlas/`](../../report/nordic-atlas/nordic-atlas_map.html)

The directory layout matters because map outputs are downstream proof surfaces.
The tracked species roots and source library are where the evidence basis lives.
The `final/` tree is only for shared downstream products that have already been
derived from the species-owned evidence chain.
