---
title: Animal Point Construction
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# Animal Point Construction

An animal point reaches the atlas only after four checks hold:

1. a curated sample row exists
2. a site evidence row points to a paper, supplement, or archive text
3. a coordinate provenance row explains the mapping basis
4. the publication surface accepts the point instead of refusing it

## Direct Proof Files

- `data/adna/species/ovis_aries/normalized/sample_records.json`
- `data/adna/species/ovis_aries/normalized/site_evidence.json`
- `data/adna/species/ovis_aries/normalized/coordinate_provenance.json`
- [`nordic-atlas_animal_atlas_evidence.json`](../report/nordic-atlas/nordic-atlas_animal_atlas_evidence.json)

## Construction Rules

- direct published coordinates outrank named-site geocoding
- named-site geocoding is visible only when the geocoding basis is explicit
- unresolved geography stays out of the point layer
- country outputs inherit the same evidence rows; they do not invent a second animal interpretation
