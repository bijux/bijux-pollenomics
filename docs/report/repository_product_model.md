# Repository product model

- Product: `bijux-pollenomics`
- Governing model: `world_parent_with_filtered_regional_and_country_derivatives`
- Mission: collect world-scale tracked evidence families once, keep Europe-plus and Nordic as governed filtered specializations, and publish country bundles as narrower views of the same accountable repository state

## Scope Lineage

| Scope | Role | Owned paths | Meaning |
| --- | --- | --- | --- |
| `world` | `governing_parent_surface` | `data/`, `docs/report/world/` | the broadest public surface and the parent evidence view for all narrower scopes |
| `europe_plus` | `regional_filter` | `docs/report/regions/europe-plus/` | the stable European bridge between world coverage and Nordic specialization |
| `nordic` | `dense_regional_specialization` | `docs/report/regions/nordic/`, `docs/public/nordic-atlas/` | the narrow regional surface where contextual overlays become intentionally denser |
| `country` | `derived_country_bundle` | `docs/report/countries/<country-slug>/` | reader-facing country bundles derived from the same upstream evidence and scope rules |

## Shared Runtime Stages

- collect source-family data into tracked raw trees
- normalize source-family evidence into reviewable files under data/
- review recovery depth, chronology meaning, and publication caveats
- publish world, regional, and country outputs from one governed state

## Drift Rules

- world is the governing parent surface; narrower scopes may filter it but may not fork separate truth rules
- Europe-plus exists as a stable region definition rather than as an ad hoc pre-Nordic convenience layer
- Nordic specialization may increase contextual density, but it may not invent a second publication model
- country bundles answer geography-first reader questions and must remain derivations of one broader evidence state
