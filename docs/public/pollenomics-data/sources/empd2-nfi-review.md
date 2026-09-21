---
title: EMPD2–NFI candidate reference review
audience: scientific reviewer
type: reference review
status: proposed; no scientific admission
owner: bijux-pollenomics-docs
last_reviewed: 2026-09-21
---

# EMPD2–NFI candidate reference review

This sheet lists **16 source-review leads, zero admitted vegetation–pollen pairs**.
It is generated from pinned source artifacts and contains no NFI tree measurements.
A distance-selected NFI row is a lead, not a temporal match or a vegetation footprint.
Review decisions require named evidence and a qualified reviewer; blank or silent review is not approval.

- EMPD2 source dossier SHA-256: `bcab3834980f6934143f3a2bf4e2a0155bf3c7024850989de4f0f28f89584c31`
- Unrounded WGS84 spatial report SHA-256: `5d35aed59cb5e3b49582976264837fab1c8d4ffa3dc1937e73bf2f04f32e2c66`
- [Official SLU NFI calibration guide](https://www.slu.se/globalassets/slu.se/om-slu/organisation/institutioner/skoglig-resurshushallning/riksskogstaxeringen/dokument/dokument/info-data-for-calibration.pdf) SHA-256: `793d90e287b2c686d0007f02497e12e8a72a47e5a45531918d9fc71d78499bc8`. It declares CC0 1.0 for this temporary forest-plot subset and says it cannot support geographic-area totals or means.

## Source leads within 1 km

`NULL` below is the source's literal text; `∅` means an absent field. Distances are displayed rounded to 0.01 m only; selection used unrounded values. Source age is not a collection year. Publication counts are source links, not identity decisions.

| EMPD2 sample | Source agebp | Age code | Source context/type | Nearest NFI year | Distance m | Publications | Neotoma identity flag | Collection note cue |
| --- | ---: | --- | --- | ---: | ---: | ---: | --- | --- |
| Bjune_a155 | NULL | B | lake / sediment | 2009 | 722.33 | 1 | none recorded | none recorded |
| Bjune_a163 | NULL | B | lake / sediment | 2010 | 60.10 | 1 | none recorded | none recorded |
| Bjune_a167 | NULL | B | lake / sediment | 2017 | 98.60 | 1 | none recorded | none recorded |
| EPDcoretop_E2 | -20 | A | wetland bog / sphagnum peat | 2011 | 895.09 | 1 | unresolved | none recorded |
| EPDcoretop_E221 | -15 | A | wetland / sediment | 2013 | 427.13 | 1 | unresolved | none recorded |
| EPDcoretop_E344 | -40 | A | lake / sediment | 2020 | 868.87 | 1 | unresolved | none recorded |
| EPDcoretop_E900 | 0 | A | lake / sediment | 2020 | 868.87 | 2 | unresolved | none recorded |
| Nielsen_b4 | -63 | A | lake / sediment | 2013 | 427.12 | 1 | unresolved | source note; review |
| Seppa_b138 | NULL | NULL | NULL / NULL | 2024 | 933.68 | 0 | none recorded | none recorded |
| Seppa_b144 | NULL | NULL | NULL / NULL | 2011 | 236.08 | 0 | none recorded | none recorded |
| Seppa_b147 | NULL | NULL | NULL / NULL | 2009 | 648.47 | 0 | none recorded | none recorded |
| Seppa_b148 | NULL | NULL | NULL / NULL | 2016 | 239.81 | 0 | none recorded | none recorded |
| Seppa_b162 | NULL | NULL | NULL / NULL | 2012 | 284.53 | 0 | none recorded | none recorded |
| Seppa_b165 | NULL | NULL | NULL / NULL | 2016 | 738.50 | 0 | none recorded | none recorded |
| Seppa_b167 | NULL | NULL | NULL / NULL | 2019 | 183.92 | 0 | none recorded | none recorded |
| Seppa_b169 | NULL | NULL | NULL / NULL | 2020 | 614.39 | 0 | none recorded | none recorded |

## Immediate source review

`Nielsen_b4` has the source note “Surface smaple collected September 2013”; its distance-selected NFI row carries 2013 and lies 427.12 m away.
A source note and a matching NFI year do not establish matched collection time. Lake sediment and a forest plot have different support. Cross-database identity flags remain unresolved proximity hypotheses.

For each proposed reference, a qualified reviewer must record: exact collection date and age-type evidence; physical sample/core and cross-database identity; position datum and uncertainty; basin footprint and a defensible point/plot versus regional estimand; compatible measured vegetation variables/units and observation time; taxon/PPE decision; independence and leakage group; and a documented eligible/refused outcome with reason. The benchmark also needs a predeclared minimum independent site/block count, non-null error thresholds and a blind label store before test access.

**Current decision: candidate preparation only. 0/16 paired references admitted. No model accuracy or superiority result.**
