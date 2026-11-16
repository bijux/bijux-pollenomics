---
title: Pollen-productivity references
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-11-16
---

# Pollen-productivity references

Relative pollen productivity (RPP), uncertainty and fall speed are separate
inputs to pollen reconstruction. Matching a taxon label supplies a source lead;
local use also needs compatible taxonomy, reference taxon, regional conditions,
model and basin assumptions.

| Reference | Retained evidence | Interpretation |
| --- | --- | --- |
| [Wieczorek and Herzschuh 2020](../../../../data/validation/pollen-productivity/wieczorek-herzschuh-2020/README.md) | 110 European rows across two deposited versions, with source-cell locators | Compiled uncertainty is labelled SE; missing European Ulmus productivity remains missing |
| [Schild et al. 2025](../../../../data/validation/pollen-productivity/legacyvegetation-2025/README.md) | Two publisher workbooks, receipts, 369 original estimates and 524 regional synthesis rows | Original SE and synthesized SD remain distinct labels; duplicated source rows and coverage discrepancies remain explicit |

Each reference has a `source.json` with attribution, exact file hashes, column
mapping and limitations. The 2025 compilation overlaps earlier studies and is
not an independent replication of the 2020 parameters. Continental and
hemispheric values remain separate. Neither reference automatically replaces a
selected model profile or supplies a covariance matrix.

The [Neotoma source workflow](neotoma-source-resources.md) can supply candidate
native taxon and chronology evidence. Its identifiers do not establish an
applicable parameter profile. Likewise, [LandClim modeled panels](landclim-modeled-panels.md)
and pollen-derived LegacyVegetation covers do not supply independent measured
ancient vegetation targets. Parameter selection, source overlap and scientific
admission remain separate from collecting these references.
