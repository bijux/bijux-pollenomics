# World Evidence Surface Map Publication Contract

World is the governing publication surface. It keeps every published country inside one shared map and excludes Nordic-only context overlays that would look more complete than they really are at broader scale.

## Engine Decision

One shared map document engine serves every published scope. Scope differences must be encoded in governed bounds, layer eligibility, default basemap, and reader caveats rather than hidden in separate renderer forks.

## Scope Posture

- Scope key: `world`
- Scope kind: `world`
- Parent scope: `-`
- Default basemap: `street`
- Default distance circle diameter: `40 km`

The opening extent keeps a broad trans-Atlantic and Eurasian frame so the root publication surface reads as a parent scope rather than a Nordic detail page with a bigger title.

## Layer Inventory

| Layer | Publication role | Source | Coverage posture | Visible records |
| --- | --- | --- | --- | ---: |
| AADR-v66 aDNA samples | `shared_world_scale_layer` | Allen Ancient DNA Resource | Country assignment follows the AADR political entity field. | `1231` |
| Cattle aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `22` |
| Goat aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `26` |
| Goat aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `1` |
| Horse aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `63` |
| Horse aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `10` |
| Cat aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `24` |
| Cat aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `15` |
| Sheep aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Pig aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Cattle source-sample chronology | `shared_world_scale_layer` | Governed animal project sample chronology |  | `31` |
| Goat source-sample chronology | `shared_world_scale_layer` | Governed animal project sample chronology |  | `9` |
| Horse source-sample chronology | `shared_world_scale_layer` | Governed animal project sample chronology |  | `242` |
| Cat source-sample chronology | `shared_world_scale_layer` | Governed animal project sample chronology |  | `35` |
| Sheep source-sample chronology | `shared_world_scale_layer` | Governed animal project sample chronology |  | `4` |
| Pig source-sample chronology | `shared_world_scale_layer` | Governed animal project sample chronology |  | `2` |
| Country boundaries | `region_filtered_layer` | Natural Earth country boundaries | Published country outlines used for framing and scope-aware map filtering. | `4` |

## Filter Surfaces

- Country filters
- Layer toggles
- Search
- Time window
- Distance circles
- Basemap switch

## Legend Sections

- Human evidence markers
- Animal evidence markers when present
- Context overlay symbols
- Density ramp when archaeology density is visible

## Caveats

- World is the parent publication scope, not a claim that worldwide contextual coverage is already complete.
- Nordic environmental and archaeology overlays are withheld here until broader equivalents exist.
- Country counts still describe Homo sapiens AADR rows even when animal layers are also visible.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Cross-domain map/evidence wrapper; country/source entity accounting and explicit ecological/chronological limits remain separate.

**Supported claim.** The retained contract defines world scope, shared document engine, eligible layers, filters and visible publication counts.

**Unsupported claim.** A consistent renderer or broad opening extent is not scientific source admission, complete world coverage or proof of valid chronology at every point.

**Actual verification performed.** Read 17 layer rows and source-role contract; reconciled 16 point layers plus 4 boundarypolygons, with human, animal-locality and sample-chronology layer units separate. No browser or publisher was run.

**Remaining input or review.** Current native asset/browser qualification and qualified family-specific geography, chronology, rights and biological interpretation remain separate requirements.

**Cause category.** Map software/publication contract with incomplete scientific/global coverage.

**Consequence.** World filters may expose declared records but cannot manufacture environmental coverage or turn present-day framing boundaries into historical nationality.

**Precise next acceptance route.** Run exact current source/assets through maintained map publication and native browser consumers; retain source-family refusals and separately qualify scientific roles before inference.

**Negative or refused result.** Nordic environmental/archaeology overlays are withheld from world; source metadata country assignments and scientific flags remain separately governed.

**Matched denominator.** 17 layer rows=16 point layers+1 boundary layer carrying 4 polygons; visible point records 1719=1231 human+165 animal-locality+323 sample-chronology record uses. Shared identities can appear in multiple layers.

- [Retained qualification evidence: docs/report/world/world_map_publication_contract.json](world_map_publication_contract.json) (SHA-256 `0c0f9dd06622b6dfc4a12a91048242cac639690295f14646fce10dac6559d384`).

- [Canonical scientific account: reports/science/country-evidence-status.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/country-evidence-status.md).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
