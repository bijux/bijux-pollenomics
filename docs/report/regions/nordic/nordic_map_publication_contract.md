# Nordic Evidence Surface Map Publication Contract

Nordic is the regional detail surface. It keeps the shared human and animal evidence layers, then adds Nordic-only environmental, archaeology, boundary, and fieldwork overlays that remain interpretable at this scale.

## Engine Decision

One shared map document engine serves every published scope. Scope differences must be encoded in governed bounds, layer eligibility, default basemap, and reader caveats rather than hidden in separate renderer forks.

## Scope Posture

- Scope key: `nordic`
- Scope kind: `region`
- Parent scope: `europe_plus`
- Default basemap: `terrain`
- Default distance circle diameter: `20 km`

The opening extent stays tight on Nordic countries so lake, site, and archaeology context reads as map content rather than background noise.

## Layer Inventory

| Layer | Publication role | Source | Coverage posture | Visible records |
| --- | --- | --- | --- | ---: |
| AADR-v66 aDNA samples | `shared_world_scale_layer` | Allen Ancient DNA Resource | Country assignment follows the AADR political entity field. | `1231` |
| Fieldwork documentation | `scope_specific_overlay` | Bijux fieldwork | Observed sampling location documented on 2026-02-26 at Lyngsjön Lake. | `1` |
| LandClim pollen sites | `scope_specific_overlay` | LandClim | Pollen sequences staged from the LandClim normalization bundle. | `492` |
| Neotoma pollen sites | `scope_specific_overlay` | Neotoma | Pollen and paleoecology sites staged from the Neotoma normalization bundle. | `200` |
| SEAD sites | `scope_specific_overlay` | SEAD | Environmental archaeology sites staged from the SEAD normalization bundle. | `2069` |
| Horse aDNA site evidence | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Country boundaries | `region_filtered_layer` | Natural Earth country boundaries | Published country outlines used for framing and scope-aware map filtering. | `4` |
| LandClim REVEALS grid cells | `scope_specific_overlay` | LandClim | REVEALS grid cells compiled from published LandClim PANGAEA datasets. | `88` |
| RAÄ archaeology density | `scope_specific_overlay` | RAÄ Fornsök | Sweden only. Density cells summarize `Fornlämning` counts. | `106` |

## Filter Surfaces

- Country filters
- Layer toggles
- Search
- Time window
- Distance circles
- Basemap switch
- Animal species focus when animal layers are present
- Animal scope when animal layers are present
- Animal coordinate confidence when animal layers are present
- Animal chronology buckets when animal layers are present
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
