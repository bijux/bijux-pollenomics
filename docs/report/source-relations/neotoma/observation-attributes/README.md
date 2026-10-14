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

The pinned regression at
`packages/bijux-pollenomics/tests/unit/collection/sources/neotoma/relational/test_observation_source_trace.py`
selects the raw datum by native parents and taxon ID, derives its observation
identifier from the source payload digest, and compares every field above with
the retained relational row. The [native hierarchy audit](../native-roundtrip/README.md)
checks payload preservation across the full pinned snapshot. This trace checks
one sampled normalized observation and its parent IDs. It does not establish
chronology choice, taxonomic acceptance, a pollen denominator or scientific
admission.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

**Supported claim.** The bounded Typha trace preserves one native datum’s parent chain, source attributes and null denominator in relational fields.

**Unsupported claim.** One source-labelled pollen datum is not a taxonomically accepted pollen denominator or a validated whole-snapshot convenience projection.

**Actual verification performed.** Read the exact source/relational field trace and pinned native/variable reconciliation accounts; no raw-table or regression rerun.

**Remaining input or review.** Source-specific taxon classification, chronology choice, counting denominator and use decisions remain unreviewed.

**Cause category.** Source attributes and derived convenience classifications have distinct authority.

**Consequence.** NISP 1 and source pollen labels remain recorded facts, not whole-pollen comparability.

**Precise next acceptance route.** Resolve the scoped concept/counting scheme and selected sample-age support before treating the observation as an LRA input.

**Negative or refused result.** source_denominator remains null/not_provided_by_source; context and symmetry source nulls are not imputed.

**Matched denominator.** 1 Typha datum at site 12/unit 12/dataset 12/sample 355236, taxon 309, NISP 1; 0 new samples or independent full-snapshot checks.

Qualified authored reader SHA-256: `9d1f99ad09615504c16ee3ddfdcb615b567c553cd9665092f903918e43f8db26`.

- [Retained qualification evidence: docs/report/source-relations/neotoma/native-roundtrip/report.json](../native-roundtrip/report.json) (SHA-256 `d8ea1c10cb91dee71af6554c4e43e246ba9a972f48df9a47df7afe294717f869`).

- [Retained qualification evidence: docs/report/source-relations/neotoma/variable-surface/report.json](../variable-surface/report.json) (SHA-256 `d2c60c1f63927410bc8341b9ed0c16257c0d6a9e9ffa78179e8a2ccb65eb099b`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
