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
| Horse aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `66` |
| Horse aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `13` |
| Cat aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `24` |
| Cat aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `15` |
| Sheep aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Pig aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Tracked animal aDNA localities | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Cattle source-sample chronology | `shared_world_scale_layer` | Governed animal project sample chronology |  | `31` |
| Goat source-sample chronology | `shared_world_scale_layer` | Governed animal project sample chronology |  | `5` |
| Horse source-sample chronology | `shared_world_scale_layer` | Governed animal project sample chronology |  | `258` |
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

**Supported claim.** The current world publication retains the human metadata population and carries 167 animal locality features for 335 mapped normalized records plus 335 distinct source-chronology record uses. Typed child supports preserve original dates and gaps; these display populations do not establish independent animals or ecological events.

**Unsupported claim.** A consistent renderer or broad opening extent is not scientific source admission, complete world coverage or proof of valid chronology at every point.

**Actual verification performed.** The retained saved atlas consumer at 1b338ee91 reconciles all 1,481 normalized source records. Native map assembly at that source passed in 333.12 seconds, RSS 5,366,333,440 B; independent decoded preservation and search references passed in 35.10 seconds, RSS 708,460,544 B. All unrelated scientific payloads, dates and coordinates are preserved. Current world/Europe index factories pass; Nordic qualification is reused only after exact code, bootstrap, controller, wire and semantic equality. Actual served runtime passes 27 cases, including four contextual Qinghai dates and a recovered horse owner. Seventeen targeted reader guards pass. Prior failures and their corrections are retained; no model or source census replay. Current chronology metadata at b3e8a50528562486a8c1c98f77e147f4bf23f603 prepares twelve JSONs in0.856s/RSS109969408B;565inputs+HEAD/index stable. Independent0.669s binds all121sourcepins and exact3native sidecars/9owned copies, changing only3identities+refusal1157→1158 percopy. All430HTML/static/controller/index files and relevant renderer code remain exact originalmap output/epoch; no fullmap, index or browser rerun. Three sourcepointlayers remain exact335/13/13.

**Remaining input or review.** Qualified family-specific geography, chronology, rights and biological interpretation remain separate. Completed preservation/index and narrow World temporal checks do not qualify all browser/provider/export behavior or query latency.

**Cause category.** Map software/publication contract with incomplete scientific/global coverage.

**Consequence.** World filters may expose declared records but cannot manufacture environmental coverage or turn present-day framing boundaries into historical nationality.

**Precise next acceptance route.** Retain the qualified current source/assets and exact native identities; qualify source-family scientific roles and any additional delivery/latency claim through its own scoped check.

**Negative or refused result.** Nordic environmental/archaeology overlays are withheld from world; source metadata country assignments and scientific flags remain separately governed.

**Matched denominator.** 1,733 point-layer record uses across fifteen point layers: 1,231 human metadata records + 167 animal locality features + 335 source-chronology uses. Human metadata retains 447 localities. The 335 mapped animal records and 335 source-chronology uses have different identity populations despite equal counts. Global animal accounting is 1,482 normalized records = 335 mapped + 1,147 exclusions. All 1,493 source chronology owners = 335 displayable + 1,158 refusals. Do not pool these units.

- [Retained qualification evidence: docs/report/world/world_map_publication_contract.json](world_map_publication_contract.json) (SHA-256 `df7767866ebcf0847e6865378b5a391a3d67a67c412f4115e5738bad3f276d65`).

- [Canonical scientific account: reports/science/country-evidence-status.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/country-evidence-status.md).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
