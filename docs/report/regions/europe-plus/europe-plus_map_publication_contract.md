# Europe-plus Evidence Surface Map Publication Contract

Europe-plus is a governed regional filter view. It keeps only Europe-plus countries from the broader publication surface and still withholds Nordic-only overlays that would overstate regional context coverage.

## Engine Decision

One shared map document engine serves every published scope. Scope differences must be encoded in governed bounds, layer eligibility, default basemap, and reader caveats rather than hidden in separate renderer forks.

## Scope Posture

- Scope key: `europe_plus`
- Scope kind: `region`
- Parent scope: `world`
- Default basemap: `street`
- Default distance circle diameter: `30 km`

The opening extent centers the European frame while keeping enough margin for future expansion into non-Nordic Europe-plus countries.

## Layer Inventory

| Layer | Publication role | Source | Coverage posture | Visible records |
| --- | --- | --- | --- | ---: |
| AADR-v66 aDNA samples | `shared_world_scale_layer` | Allen Ancient DNA Resource | Country assignment follows the AADR political entity field. | `1231` |
| Cattle aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `4` |
| Sheep aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Pig aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Cattle source-sample chronology | `shared_world_scale_layer` | Governed animal project sample chronology |  | `5` |
| Goat source-sample chronology | `shared_world_scale_layer` | Governed animal project sample chronology |  | `0` |
| Horse source-sample chronology | `shared_world_scale_layer` | Governed animal project sample chronology |  | `2` |
| Cat source-sample chronology | `shared_world_scale_layer` | Governed animal project sample chronology |  | `0` |
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

- Europe-plus is derived from the world publication surface by governed country filtering, not by a second evidence pipeline.
- Nordic-only pollen, archaeology, and fieldwork overlays remain absent here on purpose.
- Future non-Nordic Europe-plus additions should arrive by country onboarding, not by custom one-off bundle logic.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Cross-domain map/evidence wrapper; country/source entity accounting and explicit ecological/chronological limits remain separate.

**Supported claim.** The retained europe-plus contract declares its parent scope, eligible layers and shared renderer; the default distance circle is30 km diameter.

**Unsupported claim.** A display circle, layer visibility rule or software contract is not a pollen basin radius, physical dispersal support, scientific source admission or an observed ecological boundary.

**Actual verification performed.** Read this reader's scientific narrative and its retained machine account and checked the physical evidence identity. This qualification reran no producer, predictor, numerical oracle, browser or source-acquisition consumer.

**Remaining input or review.** Actual provider/browser/export behavior and each layer's scientific/source rights decisions remain separate requirements.

**Cause category.** Map delivery and scope contract.

**Consequence.** Shared rendering makes publication behavior consistent without conferring scientific equivalence on mixed layers.

**Precise next acceptance route.** Replay the configured scope and its browser/export checks using exact layer/source identities, then review scientific use under the appropriate data contract.

**Negative or refused result.** Nordic-specific overlays remain excluded from Europe-plus; approximate and country-unresolved animals keep their caveats.

**Matched denominator.** Four represented countries,11declared layer rows; circle30 km is a display diameter, not a scientific sampling denominator.

Qualified authored reader SHA-256: `4754102a54e9de26213f5ae069334e34fbf6a8f5143e4286cce46ae02069e931`.

- [Retained qualification evidence: docs/report/regions/europe-plus/europe-plus_map_publication_contract.json](europe-plus_map_publication_contract.json) (SHA-256 `20c59f4f2ebed816f8363b19996edbe4dbdba683677c41052ca39bf5b7217dbf`).

- [Canonical scientific account: reports/science/country-evidence-status.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/country-evidence-status.md) (source SHA-256 `b07462b1cd31fae284b29d0b6319ac5fbfcadd0e9eabb35ab290240f0818ae3e`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md) (source SHA-256 `3a0a899e96cfe7d95bdef41012516f39ce2b68606212efecafe1d909b6ccd045`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
