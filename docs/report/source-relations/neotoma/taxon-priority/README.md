# Neotoma pollen concept review priority

The [current priority table](priority.json) is generated from the corrected
[12,388-sample source screen](../pollen-screen/README.md) and the complete
[1,351-row Neotoma source-concept review](../../../../../data/neotoma/review/source_taxon_concepts.json).
The concept ledger is a scoped, exact-row extraction from a larger private
source-union review bundle. Its SHA-256 is
`981a3ed090e9bd276221924ee2a59bd5c2d55c6c8bc9a2fa37451a8ca97219c5`;
the parent review bundle identity and file digest are retained inside it. The
scoped ledger preserves all Neotoma concepts without publishing the private
Rootsi rows from the parent bundle.

The priority table has SHA-256
`d2e3b1947c0cb698a6a2ab48aa6be3a85680b495f596dda1ec50cd411c17924f`.
It covers 10,637 necessary count/typed-age sample leads and **228,323**
agreeing source-pollen-labelled count observations across **1,006** concept
rows. Country observation counts are Sweden 108,167, Denmark 3,407, Norway
84,824, Finland 28,496 and unassigned 3,429. The exact source units remain
separate: 228,028 `NISP` observations sum to 9,808,390; 295 `NISP digitized`
observations sum to 12,911. The two sums are not combined into a pollen
denominator. All 1,006 selected concepts remain `needs_discussion` and zero
samples are admitted to LRA. Frequencies prioritize expert review; they do not
approve taxon identity, ecological role, PPE, fall speed or source rights.

The same 1,006 scientific rows were obtained when the source-bound priority
consumer read the original full review bundle. The scoped ledger changes only
the review bundle identity and the count of review rows outside the selected
Neotoma concepts; it does not change any selected concept, country count, native
unit or exact count sum.

The [dataset attribution](dataset-attribution.json) has SHA-256
`aa4920ea2466ee16b00cbc1aecf5d8b3f512ac009e6c4d7a02096063512d1c52`.
It reconciles every selected concept and all 228,323 observations to 169
source dataset IDs: Sweden 82, Denmark 2, Norway 52, Finland 28 and unassigned
5. All 169 identify the European Pollen Database and have a source-listed DOI
value. A dataset DOI is an attribution lead, not verification of a particular
original publication or a reuse decision. The complete concept-to-dataset
observation and distinct-sample counts remain in the machine-readable export;
zero samples are admitted to LRA.

The [published parameter-name candidate review](../parameter-candidates/README.md)
binds these source concepts to literal strings in the LandClim II PPE/FSP table.
It retains unmatched names and distinct native/digitized count units without
approving any taxon or LRA parameter mapping.
The [author taxonomy candidate ledger](../author-taxonomy-candidates/README.md)
also compares all 1,006 priority concepts with the author's broader taxonomy
lookup, retaining excluded and unmatched names for qualified review.

To replay, read the governed screen `report.json`, the scoped concept ledger and
the validated Neotoma raw and relational roots. Call
`prioritize_neotoma_candidate_taxa` from
`bijux_pollenomics.analysis.lra.materialization.neotoma.taxon_priority` with
those three inputs, then serialize the result with
`bijux_pollenomics.analysis.lra.materialization.models.canonical_bytes`.
The consumer verifies the raw and normalized manifests, source sample identities,
review digest, concept identities and every screened pollen observation before
returning the table.
Run `attribute_neotoma_priority_datasets` from the adjacent
`taxon_provenance` module with the same source evidence, screen and concept
ledger plus the governed priority table to replay the dataset attribution.
