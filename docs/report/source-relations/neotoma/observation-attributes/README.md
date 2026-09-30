# Neotoma observation attribute trace

The pinned raw snapshot `sha256:b2bcb99157e10b0c9f13c228acc12eabcb39d96a1f39c86ec25e34aacd78c791`
contains a Typha latifolia observation in
`data/neotoma/raw/neotoma_pollen_dataset_downloads/part-001.json`. Its native
parent chain is site `12` → collection unit `12` → dataset `12` → sample
`355236`. The datum has taxon ID `309`. The materialized observation in
`data/neotoma/relational/surfaces/observations/part-00002.json` is
`neotoma:observation:355236:2f2a52b05b5870355f17:1`, from materialization
`7d9bf04538f6fc9db0582a85656defc3b262b86b782d99bf310d2fec4ae96406`.

| Raw datum field | Raw value | Relational field | Relational value |
|---|---|---|---|
| `units` | `NISP` | `source_unit` | `NISP` |
| `value` | `1` | `source_value` | `1` |
| `element` | `pollen` | `source_element` | `pollen` |
| `elementtype` | `pollen` | `source_element_type` | `pollen` |
| `taxongroup` | `Vascular plants` | `source_taxon_group` | `Vascular plants` |
| `ecologicalgroup` | `AQVP` | `source_ecological_group` | `AQVP` |
| `variablename` | `Typha latifolia` | `source_reported_name` | `Typha latifolia` |
| `taxonid` | `309` | `source_taxon_id` | `309` |
| `context` | source null | `source_context` | source null |

The relational parent IDs are `neotoma:site:12`,
`neotoma:collection-unit:12`, `neotoma:dataset:12` and
`neotoma:sample:355236`. The source taxon ID also resolves to the convenience
variable ID `neotoma:variable:309`. The source datum is retained in full as
`source_payload`; its supplied null `symmetry` is retained there, without a
separate convenience field. The raw datum supplies no count denominator. The
relational row reports `source_denominator: null` and
`denominator_status: not_provided_by_source`; neither supplies a denominator
for a whole-pollen claim. `unit_family: count`,
`aggregation_key: neotoma:exact-unit:NISP` and
`detection_status: reported_value` are derived classifications, not additional
raw attributes.

The [pinned regression](../../../../../packages/bijux-pollenomics/tests/unit/collection/sources/neotoma/relational/test_observation_source_trace.py)
selects the raw datum by native parents and taxon ID, derives its observation
identifier from the source payload digest, and compares every field above with
the retained relational row. The [native hierarchy audit](../native-roundtrip/README.md)
checks payload preservation across the full pinned snapshot. This trace checks
one sampled normalized observation and its parent IDs. It does not establish
chronology choice, taxonomic acceptance, a pollen denominator or scientific
admission.
