# SEAD country source-unit accounting

The [country ledger](rows.csv) counts the governed full-evidence SEAD capture at
five distinct source levels. A site counts as linked when at least one captured
`tbl_sample_groups` row points to it. Physical samples follow
`tbl_physical_samples.sample_group_id`; analysis entities follow
`tbl_analysis_entities.physical_sample_id`; analysis values follow
`tbl_analysis_values.analysis_entity_id`. A dataset counts once per country when
an analysis entity at a site in that country carries its `dataset_id`. The
dataset is a shared source object, not a physical sample or an analysis value.

| Country | Assigned sites | Sites with groups | Groups | Physical samples | Analysis entities | Datasets | Analysis values |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Sweden | 1,925 | 1,103 | 3,712 | 28,483 | 117,786 | 40,703 | 68,705 |
| Denmark | 59 | 59 | 504 | 1,520 | 4,059 | 1,874 | 0 |
| Norway | 45 | 45 | 177 | 2,257 | 7,970 | 722 | 0 |
| Finland | 40 | 38 | 39 | 48 | 103 | 93 | 0 |

The four assigned countries contain 2,069 retrieved sites, 1,245 sites with
sample groups, 4,432 groups, 32,308 physical samples, 129,918 analysis
entities, 43,392 distinct datasets and 68,705 analysis values. All 43,392
datasets have a linked analysis entity in one country in this capture; no
dataset crosses countries here. Twenty-five Swedish analysis entities have a
null `dataset_id`. They remain in the entity count and contribute no dataset
membership. Analysis values in this captured source table all trace to Swedish
sites; zero in another country means zero captured rows in that table, not an
absence of environmental observations from all source tables.

The 103 `REVIEW` and 23 `UNASSIGNED` discovered sites were excluded from the
assigned raw relation capture. Their source-unit fields are blank because
their sample and analysis rows were not retrieved. They are not zeros or
country-specific assignments. The source supplied no site country field; the
assigned country is the versioned strict boundary-containment decision.

The [report](report.json) binds the six raw source tables and receipts to the
governed admission, normalized source-key ledger, normalized observation
relation index, country decisions and materialization manifest. The producer
checks unique source keys, each required parent join, site UUID/country
bindings, table counts, payload digests and the complete per-country sums.
Dataset membership is resolved through an analysis entity because
`tbl_datasets` itself has no site or country key. The acquisition release
remains refused; this accounting does not admit chronology, pollen, ecological
or propagation events.

## Reproduce

From the repository root, choose an absent destination under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.sead_country_source_units \
  --repository "$PWD" \
  --output "$PWD/artifacts/sead-country-source-units/replay"
```

Compare `report.json` and `rows.csv` byte for byte against this directory.
The producer refuses an existing destination and altered source identities or
unresolved joins.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-native/context/propagation evidence: source units and eligibility/refusal populations do not become pollen observations or ecological events.

**Supported claim.** The country unit ledger preserves distinct site, group, physical sample, analysis entity, dataset and analysis value populations through native relations.

**Unsupported claim.** Dataset membership is not a physical specimen count, and zero captured analysis values outside Sweden is not absence of environmental evidence.

**Actual verification performed.** Read the six-row country decision ledger and raw table/unit totals with null dataset links; no relational consumer rerun.

**Remaining input or review.** Scientific chronology, measurement/taxon meaning, rights and excluded coordinate authority remain unqualified.

**Cause category.** Source entities and country decision strata have different denominators.

**Consequence.** Excluded review/unassigned unit fields stay blank rather than zero or country assigned.

**Precise next acceptance route.** Qualify exact entity/measure/date/use semantics and country scope before aggregating units as scientific observations.

**Negative or refused result.** 25 Swedish entities have null dataset ID; 0 ecological/pollen/propagation admission; capture release refused.

**Matched denominator.** 2,069 sites/1,245 group-linked sites/4,432 groups/32,308 physical samples/129,918 entities/43,392 datasets/68,705 analysis values; 0 cross-country datasets.

- [Retained qualification evidence: docs/report/source-relations/sead/source-unit-accounting/report.json](report.json) (SHA-256 `68bd83e4fa7f7ce9beaa0c354129cf236b3c5542914976fa25a812c94c6c6c02`).

- [Retained qualification evidence: docs/report/source-relations/sead/source-unit-accounting/rows.csv](rows.csv) (SHA-256 `b2d7c66c6b75571745feba0cfb037c4f813c3989f616bd16bebc050dc004cc00`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
