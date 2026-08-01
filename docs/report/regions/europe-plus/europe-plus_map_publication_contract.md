# Europe-plus Evidence Surface Map Publication Contract

Europe-plus is a governed regional filter view. It keeps only Europe-plus countries from the broader publication surface and still withholds Nordic-only overlays that would overstate regional context coverage.

## Engine Decision

One shared map document engine serves every published scope. Scope differences must be encoded in governed bounds, layer eligibility, default basemap, and reader caveats rather than hidden in separate renderer forks.

## Scope Posture

- Scope key: `europe_plus`
- Scope kind: `region`
- Parent scope: `world`
- Default basemap: `light`
- Default distance circle diameter: `30 km`

The opening extent centers the European frame while keeping enough margin for future expansion into non-Nordic Europe-plus countries.

## Layer Inventory

| Layer | Publication role | Source | Coverage posture | Visible records |
| --- | --- | --- | --- | ---: |
| AADR-v66 aDNA samples | `shared_world_scale_layer` | Allen Ancient DNA Resource | Country assignment follows the AADR political entity field. | `1231` |
| Horse aDNA site evidence | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
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

- Europe-plus is derived from the world publication surface by governed country filtering, not by a second evidence pipeline.
- Nordic-only pollen, archaeology, and fieldwork overlays remain absent here on purpose.
- Future non-Nordic Europe-plus additions should arrive by country onboarding, not by custom one-off bundle logic.
