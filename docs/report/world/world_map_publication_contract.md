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

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/country-evidence-status.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/country-evidence-status.md) (source SHA-256 `b07462b1cd31fae284b29d0b6319ac5fbfcadd0e9eabb35ab290240f0818ae3e`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md) (source SHA-256 `3a0a899e96cfe7d95bdef41012516f39ce2b68606212efecafe1d909b6ccd045`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
