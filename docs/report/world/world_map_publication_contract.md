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
| Goat aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `23` |
| Horse aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `63` |
| Horse aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `12` |
| Cat aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `24` |
| Cat aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `15` |
| Sheep aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Pig aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Cattle source-sample chronology | `shared_world_scale_layer` | Governed animal project sample chronology |  | `31` |
| Goat source-sample chronology | `shared_world_scale_layer` | Governed animal project sample chronology |  | `5` |
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

**Actual verification performed.** The source-bound three-scope producer at a18530b54 completed in 326.099 s. Independent decoded preservation and all three actual JavaScript index-factory checks passed in 65.517 s aggregate, preserving unrelated science and retained chronology context. Freshly served World Chromium passed 22 source-backed and labelled synthetic temporal cases; this does not qualify general browser behavior, external providers or query latency. World now has 1713 point uses across 15 point layers within 16 layer rows.

**Remaining input or review.** Qualified family-specific geography, chronology, rights and biological interpretation remain separate. Completed preservation/index and narrow World temporal checks do not qualify all browser/provider/export behavior or query latency.

**Cause category.** Map software/publication contract with incomplete scientific/global coverage.

**Consequence.** World filters may expose declared records but cannot manufacture environmental coverage or turn present-day framing boundaries into historical nationality.

**Precise next acceptance route.** Retain the qualified current source/assets and exact native identities; qualify source-family scientific roles and any additional delivery/latency claim through its own scoped check.

**Negative or refused result.** Nordic environmental/archaeology overlays are withheld from world; source metadata country assignments and scientific flags remain separately governed.

**Matched denominator.** 16 layer rows=15 point layers+1 boundary layer with 4 polygons; 1713 point uses=1231 human+163 animal-locality+319 source-chronology record uses. Shared identities can appear in multiple layers.

- [Retained qualification evidence: docs/report/world/world_map_publication_contract.json](world_map_publication_contract.json) (SHA-256 `9fda0df60f16a49b954d846fc3e933c1ad1f43ba734fe6fb58147080e0f30431`).

- [Canonical scientific account: reports/science/country-evidence-status.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/country-evidence-status.md).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
