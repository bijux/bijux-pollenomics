---
title: LandClim Modeled Nordic Panels
audience: reader
type: reference
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-10-01
---

# LandClim modeled Nordic panels

The [LandClim II source grid](landclim.md) offers four distinct model views for Denmark, Finland, Norway, and Sweden across 25 published PANGAEA 937075 windows. These are reconstructed percentage-cover estimates with source standard errors, not observed local pollen or independently measured vegetation. A modeled cell and time window must not be read as a site sample or a propagation event.

| View | Source code | Meaning in the source classification |
| --- | --- | --- |
| Evergreen trees | ET | Land-cover type |
| Summer-green trees | ST | Land-cover type |
| Open land | OL | Land-cover type |
| Agricultural land — cereals | AL | Plant functional type within OL; it is not an additional disjoint land-cover total |

The [400-row country and source-window inventory](../../../report/regions/nordic/landclim-modeled-panels/panels.csv) retains the high-, low-, and no-pollen-data grid-cell counts for each view. It gives the minimum and maximum individual-cell estimate and standard error among cells with model data. The ranges are descriptive; the standard errors are not pooled or transformed into country uncertainty. A missing-model cell contributes to the coverage denominator and never becomes numeric zero.

| Country | Grid cells per window | Cell-window rows | With model data | No pollen data |
| --- | ---: | ---: | ---: | ---: |
| Denmark | 6 | 150 | 74 | 76 |
| Finland | 19 | 475 | 375 | 100 |
| Norway | 24 | 600 | 551 | 49 |
| Sweden | 26 | 650 | 568 | 82 |

The [source-bound report](../../../report/regions/nordic/landclim-modeled-panels/README.md) and its [machine-readable receipt](../../../report/regions/nordic/landclim-modeled-panels/report.json) record the exact source bytes and calculation. Source windows remain discrete, from 11,200–11,700 BP through 0–100 BP. The map's modeled-context controls use the same source metric families and keep modeled evidence separate from observed pollen layers.

We also checked the [published map transport](../../../report/source-relations/landclim/map-export-lineage/README.md) against all 2,515 normalized temporal features. The 1,875 LandClim II cell windows retain 47 estimate and standard-error metrics: 73,696 numeric pairs and 14,429 explicit null pairs across the four countries. The [browser download check](../../../report/source-relations/landclim/browser-export/README.md) reconciles a selected 32-cell Denmark/Sweden frame at 0–100 BP, including all 47 paired metrics and explicit nulls. The archive supplies WGS84 longitude/latitude centers under PANGAEA's geocode policy; our one-degree polygons are derived geometry with no separate file-level CRS declaration. Metadata overlap with pollen sources does not establish independent validation or the historical contributors to each modeled cell.
