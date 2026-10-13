# Propagation projections

`analysis.propagation.projection.project_propagation_network` consumes a generated
network and an explicit `PropagationSelection`. It preserves the stored signal,
source and target event identifiers, country codes, observation identifiers,
chronology, exact distance, lag bounds, status and producer provenance. Selection
changes the displayed/exported subset; it does not change scientific eligibility.

Country modes are `all`, `origin`, `destination`, `either_endpoint`,
`within_country` and `cross_border`. Within-country requires equal endpoint
countries in the selected set. Cross-border requires different countries and
at least one endpoint in the selected set. Signals are explicit
`(resolution, feature_key)` pairs; `None` selects all and an empty tuple selects
none. Country and signal selections never merge scientific features.

The production materializer includes `directed_candidates.geojson`,
`indeterminate_pairs.geojson` and `lower_level_edge_union.json` in its content-bound
bundle. Definite and possible candidates enter the directional export; uncertain
order remains in the separate indeterminate export with no arrow. GeoJSON contains
straight endpoint connections, not sampled geodesic arcs or inferred movement
routes. Full-precision WGS84 eligibility distances remain in the properties.

The lower-level union retains each exact feature edge and groups repeated ordered
relations by the governed source site and complete source observation set, followed
by the target site and complete target observation set. `feature_edge_count` counts
exact edge identities. `endpoint_set_relation_count` counts these explicitly
bundled relations. Member edge and oriented event identifiers remain available.
Two signals sharing identical endpoint sets count as two feature edges and one
endpoint-set relation. Partial overlaps and subsets remain separate. Individual
observation pair mappings are unavailable; no Cartesian pairs are inferred.
Whole-pollen edges are excluded from this lower-level union, and the projection
does not construct a whole-assemblage network.

Projection cannot authorize scientific publication or replace classification,
chronology, source or independent scientific review. The materializer retains
its source-owned admission and release refusals. An empty refused source bundle
remains empty; successful software fixtures do not establish real propagation,
causation, migration, local cultivation or an empirical route.
