# Nordic Evidence Surface Map Publication Contract

Nordic is the regional detail surface. It keeps the shared human and animal evidence layers, then adds Nordic-only environmental, archaeology, boundary, and fieldwork overlays that remain interpretable at this scale.

## Engine Decision

One shared map document engine serves every published scope. Scope differences must be encoded in governed bounds, layer eligibility, default basemap, and reader caveats rather than hidden in separate renderer forks.

## Scope Posture

- Scope key: `nordic`
- Scope kind: `region`
- Parent scope: `europe_plus`
- Default basemap: `street`
- Default distance circle diameter: `20 km`

The opening extent stays tight on Nordic countries so lake, site, and archaeology context reads as map content rather than background noise.

## Layer Inventory

| Layer | Publication role | Source | Coverage posture | Visible records |
| --- | --- | --- | --- | ---: |
| AADR-v66 aDNA samples | `shared_world_scale_layer` | Allen Ancient DNA Resource | Country assignment follows the AADR political entity field. | `1231` |
| Fieldwork documentation | `scope_specific_overlay` | Bijux fieldwork | Observed sampling location documented on 2026-02-26 at Lyngsjön Lake. | `1` |
| LandClim pollen sites | `scope_specific_overlay` | LandClim | Pollen sequences staged from the LandClim normalization bundle. | `490` |
| Neotoma pollen sites | `scope_specific_overlay` | Neotoma | Pollen and paleoecology sites staged from the Neotoma normalization bundle. | `193` |
| SEAD sites | `scope_specific_overlay` | SEAD | SEAD site inventory for spatial context. Site envelopes summarize source chronology and are not dated events or interval evidence. | `2069` |
| Sweden archaeology site discovery | `scope_specific_overlay` | SEAD with RAÄ density context | Every geolocated Swedish SEAD site, represented by each linked numeric chronology interval or by one explicitly unresolved temporal record. | `8799` |
| Cattle aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `4` |
| Sheep aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Pig aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Cattle source-sample chronology | `shared_world_scale_layer` | Governed animal project sample chronology |  | `5` |
| Goat source-sample chronology | `shared_world_scale_layer` | Governed animal project sample chronology |  | `0` |
| Horse source-sample chronology | `shared_world_scale_layer` | Governed animal project sample chronology |  | `2` |
| Cat source-sample chronology | `shared_world_scale_layer` | Governed animal project sample chronology |  | `0` |
| Sheep source-sample chronology | `shared_world_scale_layer` | Governed animal project sample chronology |  | `4` |
| Pig source-sample chronology | `shared_world_scale_layer` | Governed animal project sample chronology |  | `2` |
| Neotoma sample pollen-presence context | `scope_specific_overlay` | Neotoma | Dated source samples with positive reported pollen observations; not reviewed pollen-sum events. | `9988` |
| Neotoma literal ecological codes | `scope_specific_overlay` | Neotoma | Literal source ecological codes without cross-source equivalence or propagation claims. | `25165` |
| Neotoma exact source taxa | `scope_specific_overlay` | Neotoma | Exact source taxon identities without accepted ecological classification or propagation claims. | `215751` |
| Country boundaries | `region_filtered_layer` | Natural Earth country boundaries | Published country outlines used for framing and scope-aware map filtering. | `4` |
| LandClim REVEALS time-window grids | `scope_specific_overlay` | LandClim | Time-window-specific REVEALS grid estimates from published LandClim PANGAEA datasets. | `2515` |
| RAÄ archaeology density | `scope_specific_overlay` | RAÄ Fornsök | Sweden only. Density cells summarize `Fornlämning` counts. | `106` |

## Filter Surfaces

- Country filters
- Layer toggles
- Search
- Time window
- Distance circles
- Basemap switch
- Accepted scientific comparison when qualified classifications are available
- Neotoma source-sample, literal-code, and exact-label chronology
- Oldest-to-present BP window navigation and playback
- PANGAEA 937075 exact-window modeled context
- Modeled-context visible-frame export
- Animal species focus when animal layers are present
- Animal scope when animal layers are present
- Animal coordinate confidence when animal layers are present
- Animal temporal windows when animal layers are present
- Nordic animal leads only when animal layers are present

## Legend Sections

- Human evidence markers
- Animal evidence markers when present
- Context overlay symbols
- Density ramp when archaeology density is visible
- Nordic environmental context markers
- Nordic boundary and archaeology overlays
- Fieldwork documentation marker when checked-in gallery media is present

## Caveats

- Nordic-specific overlays describe the current Nordic recovery slice and must not be generalized outward.
- Animal points can remain visible even when their Nordic relevance is regional rather than one exact country.
- Approximate or inferred coordinates remain visible with explicit warnings instead of being silently dropped.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Cross-domain map/evidence wrapper; country/source entity accounting and explicit ecological/chronological limits remain separate.

**Supported claim.** The retained nordic contract declares its parent scope, eligible layers and shared renderer; the default distance circle is20 km diameter.

**Unsupported claim.** A display circle, layer visibility rule or software contract is not a pollen basin radius, physical dispersal support, scientific source admission or an observed ecological boundary.

**Actual verification performed.** The current saved atlas consumer at 1b338ee91 reconciles all 1,481 normalized source records. Native map assembly at that source passed in 333.12 seconds, RSS 5,366,333,440 B; independent decoded preservation and search references passed in 35.10 seconds, RSS 708,460,544 B. All unrelated scientific payloads, dates and coordinates are preserved. Current world/Europe index factories pass; Nordic qualification is reused only after exact code, bootstrap, controller, wire and semantic equality. Actual served runtime passes 27 cases, including four contextual Qinghai dates and a recovered horse owner. Seventeen targeted reader guards pass. Prior failures and their corrections are retained; no model or source census replay.

**Remaining input or review.** Broader browser/provider/export behavior, query latency and each layer's scientific/source-rights decisions remain separate from the completed source-bound preservation/index and narrow served-temporal checks.

**Cause category.** Map delivery and scope contract.

**Consequence.** Shared rendering makes publication behavior consistent without conferring scientific equivalence on mixed layers.

**Precise next acceptance route.** Retain the qualified current scope and native identities; execute additional browser/export/provider or latency cases only for their defined delivery claim, and qualify source-family scientific roles separately.

**Negative or refused result.** Literal ecological codes and exact source taxa remain source-owned display contexts, not reviewed biological signal admission. Approximate and country-unresolved animal records keep their caveats; excluded broader-scope overlays remain separate.

**Matched denominator.** Four represented countries and 21 declared layer rows, including the separate Neotoma literal ecological-code and exact source-taxon display layers. The 20 km circle is a display diameter, not a scientific sampling denominator.

- [Retained qualification evidence: docs/report/regions/nordic/nordic_map_publication_contract.json](nordic_map_publication_contract.json) (SHA-256 `0325fc93569ba08387aa28c77e6d143a6b5214ac766a6a2ac28e0cd652fed1cd`).

- [Canonical scientific account: reports/science/country-evidence-status.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/country-evidence-status.md).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
