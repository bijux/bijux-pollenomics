---
title: Nordic Atlas Point Publication
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Nordic Atlas Point Publication

An animal point reaches the atlas only after four evidence checks hold:

1. a curated sample row exists
2. a site evidence row points to a paper, supplement, or archive text
3. a coordinate provenance row explains the mapping basis
4. the final candidate packet confirms that the row still keeps all of those anchors

## Direct Proof Files

- `data/adna/species/ovis_aries/normalized/sample_records.json`
- `data/adna/species/ovis_aries/normalized/site_evidence.json`
- `data/adna/species/ovis_aries/normalized/coordinate_provenance.json`
- `data/adna/final/atlas/animal_atlas_point_candidates.json`
- `data/adna/final/atlas/animal_atlas_candidate_accountability.json`
- [atlas evidence rows](../../report/nordic-atlas/nordic-atlas_animal_atlas_evidence.json)
- [animal point traceability](../../report/nordic-atlas/nordic-atlas_animal_point_traceability.json)

## Construction Rules

- direct published coordinates outrank named-site geocoding
- named-site geocoding stays visible only when the mapping basis is explicit
- unresolved or region-only geography stays out of the point layer
- country outputs inherit the same evidence rows; they do not invent a second animal interpretation

## Why The Final Candidate Packet Matters

`data/adna/final/atlas/` is not trusted just because a row exists there. The
candidate accountability packet must still show sample, site, chronology, and
coordinate anchors for every published row.
