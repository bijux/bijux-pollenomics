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

**Actual verification performed.** The retained saved atlas consumer at 1b338ee91 reconciles all 1,481 normalized source records. Native map assembly at that source passed in 333.12 seconds, RSS 5,366,333,440 B; independent decoded preservation and search references passed in 35.10 seconds, RSS 708,460,544 B. All unrelated scientific payloads, dates and coordinates are preserved. Current world/Europe index factories pass; Nordic qualification is reused only after exact code, bootstrap, controller, wire and semantic equality. Actual served runtime passes 27 cases, including four contextual Qinghai dates and a recovered horse owner. Seventeen targeted reader guards pass. Prior failures and their corrections are retained; no model or source census replay. Current chronology metadata at b3e8a50528562486a8c1c98f77e147f4bf23f603 prepares twelve JSONs in0.856s/RSS109969408B;565inputs+HEAD/index stable. Independent0.669s binds all121sourcepins and exact3native sidecars/9owned copies, changing only3identities+refusal1157→1158 percopy. All430HTML/static/controller/index files and relevant renderer code remain exact originalmap output/epoch; no fullmap, index or browser rerun. Three sourcepointlayers remain exact335/13/13.

**Remaining input or review.** Broader browser/provider/export behavior, query latency and each layer's scientific/source-rights decisions remain separate from the completed source-bound preservation/index and narrow served-temporal checks.

**Cause category.** Map delivery and scope contract.

**Consequence.** Shared rendering makes publication behavior consistent without conferring scientific equivalence on mixed layers.

**Precise next acceptance route.** Retain the qualified current scope and native identities; execute additional browser/export/provider or latency cases only for their defined delivery claim, and qualify source-family scientific roles separately.

**Negative or refused result.** Nordic-specific overlays remain excluded from Europe-plus; approximate and country-unresolved animals keep their caveats.

**Matched denominator.** Four represented countries,11declared layer rows; circle30 km is a display diameter, not a scientific sampling denominator.

- [Retained qualification evidence: docs/report/regions/europe-plus/europe-plus_map_publication_contract.json](europe-plus_map_publication_contract.json) (SHA-256 `288cd8acd6e6a31659ae49a944a25bf1d307cf681f7155f00af5d9f1893d3f50`).

- [Canonical scientific account: reports/science/country-evidence-status.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/country-evidence-status.md).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
