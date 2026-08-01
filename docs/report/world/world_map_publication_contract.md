# World Evidence Surface Map Publication Contract

World is the governing publication surface. It keeps every published country inside one shared map and excludes Nordic-only context overlays that would look more complete than they really are at broader scale.

## Engine Decision

One shared map document engine serves every published scope. Scope differences must be encoded in governed bounds, layer eligibility, default basemap, and reader caveats rather than hidden in separate renderer forks.

## Scope Posture

- Scope key: `world`
- Scope kind: `world`
- Parent scope: `-`
- Default basemap: `voyager`
- Default distance circle diameter: `40 km`

The opening extent keeps a broad trans-Atlantic and Eurasian frame so the root publication surface reads as a parent scope rather than a Nordic detail page with a bigger title.

## Layer Inventory

| Layer | Publication role | Source | Coverage posture | Visible records |
| --- | --- | --- | --- | ---: |
| AADR-v66 aDNA samples | `shared_world_scale_layer` | Allen Ancient DNA Resource | Country assignment follows the AADR political entity field. | `1231` |
| Dromedary Camel aDNA site evidence | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `1` |
| Goat aDNA site evidence | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `26` |
| Horse aDNA site evidence | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `207` |
| Sweden lake aggregate top 40 | `scope_specific_overlay` | Sweden lake evidence | Optional Nordic atlas overlay for the top 40 Sweden lakes in the aggregate evidence ranking. | `40` |
| Sweden lake consensus top 40 | `scope_specific_overlay` | Sweden lake evidence | Optional Nordic atlas overlay for the top 40 Sweden lakes that recur across scenario rankings. | `40` |
| Sweden lake fieldwork shortlist | `scope_specific_overlay` | Sweden lake evidence | Optional Nordic atlas overlay for the published Sweden fieldwork shortlist. | `20` |
| Sweden lake 10 km top 40 | `scope_specific_overlay` | Sweden lake evidence | Optional Nordic atlas overlay for the top 40 Sweden lakes in the 10 km evidence scenario. | `40` |
| Sweden lake 20 km top 40 | `scope_specific_overlay` | Sweden lake evidence | Optional Nordic atlas overlay for the top 40 Sweden lakes in the 20 km evidence scenario. | `40` |
| Sweden lake 30 km top 40 | `scope_specific_overlay` | Sweden lake evidence | Optional Nordic atlas overlay for the top 40 Sweden lakes in the 30 km evidence scenario. | `40` |
| Sweden lake 40 km top 40 | `scope_specific_overlay` | Sweden lake evidence | Optional Nordic atlas overlay for the top 40 Sweden lakes in the 40 km evidence scenario. | `40` |
| Sweden lake 50 km top 40 | `scope_specific_overlay` | Sweden lake evidence | Optional Nordic atlas overlay for the top 40 Sweden lakes in the 50 km evidence scenario. | `40` |
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
