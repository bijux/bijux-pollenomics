# Source-bound taxa review package

The current private review projection contains **10,908 rows** from the source
authorities listed below. Its rows preserve source identities, native names and
qualifiers, country observation counts, exact-unit values, source citations and
separate proposed group, LRA taxon, PFT, PPE and fall-speed fields. Every row
remains `needs_discussion`; all proposed mappings start unset. The package is
for qualified review, with no classification admission or publication right.
The completed projection has bundle SHA-256
`1220483aa405b55aa08da56175d568ba7d3f31bed6f7f9095e804cb3551c5cfb`;
the completion reader verified all three payload members and their byte counts.

| Source family | Review rows | Scope |
| --- | ---: | --- |
| Neotoma | 1,351 | Source taxon concepts and 370,936 source observations |
| SEAD | 1,975 | Source taxon records and 177,763 source observations |
| Rootsi private workbook quarantine | 7,459 | Columns in 107 sheets from 79 workbooks; headers unresolved |
| LandClim | 31 | Reported parameter and crosswalk labels |
| LRA reference resources | 81 | Author example labels and parameters |
| animal aDNA | 10 | Explicit non-pollen identities |
| AADR | 1 | Explicit non-pollen source identity |

The Rootsi inventory is retained beside the 79 workbooks in the private source
store as `landclim/rootsi-workbooks/header-review-inventory.json` (SHA-256
`15a8a0d333c9b0a3928aa0f8e66efbf870860fdc27b8179465a0bee6d2059196`).
Its 7,459 column records carry each source workbook's SHA-256, and all 79
workbook identities agree with that store's custody manifest. The inventory
retains the first six rows as header candidates; it does not select a taxon
header or authorize analytical use. The workbook archive identity is
`f64d4dd411bc92362c9db2701c919063c2432e53fa523052e602da5f1a86183c`.

## Rebuild the private package

Set `ROOTSI_SOURCE_ROOT` to the private `landclim/rootsi-workbooks` directory.
From the repository root, create a fresh artifact directory and copy the
inventory into it before building:

```sh
mkdir -p artifacts/jobs/taxa-review/source-input
cp "$ROOTSI_SOURCE_ROOT/header-review-inventory.json" \
  artifacts/jobs/taxa-review/source-input/header-review-inventory.json
shasum -a 256 artifacts/jobs/taxa-review/source-input/header-review-inventory.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.taxa_review build --root . \
  --rootsi-inventory artifacts/jobs/taxa-review/source-input/header-review-inventory.json \
  --output artifacts/jobs/taxa-review/complete-review
```

Use an absent output directory for each run. The builder records 60 consumed
input files and writes `taxa-review.json`, a CSV projection, review instructions
and a completion receipt with file hashes. The complete JSON and CSV remain
private because the workbook material is restricted. The source inventory in
the private store, the governed source files and this command suffice to
regenerate the package; no prior artifact tree is an input authority.

The reviewer return has not been received. The return validator can check
identity, vocabulary and documented intent, but it cannot grant source rights,
accept taxonomic groups, resolve the LandClim 12-versus-13 PFT discrepancy, or
admit an LRA/vegetation comparison. Neotoma and SEAD observation counts are
source-row frequencies, not comparable pollen mass or coverage percentages.
Current mapping statuses are 7,459 quarantined unclassified, 1,410 unmapped,
1,974 not accepted, 53 not applicable, 11 not applicable to pollen and one
unresolved. These statuses are source projection labels, not reviewer decisions.

## Neotoma priority and citation coverage

The current governed Neotoma source screen yields 10,637 prerequisite samples,
228,323 agreeing pollen count observations and 1,006 unresolved review
concepts across 169 datasets. The country partition and exact source-unit sums
are reported on the [Neotoma source page](../../public/pollenomics-data/sources/neotoma.md).
The replay binds the full private review bundle to the governed raw and
relational Neotoma manifests. Its priority, dataset attribution and screen
SHA-256 values are respectively:

- `68cc019466e4e251e66bff0cdeb6627419b6e6444d844cf5cd01eed25ee2054c`
- `9bb1bebdf9155fa8ba2ebb7afb5b743258730aad967201fba6c0bdef13a5eb63`
- `7d1ec565e9eec4317c61414b553a05b43cfd476a6fd0c087f0a536da8f2554ee`

All 1,006 priority rows and all 169 dataset-attribution rows equal the
[governed scoped review](../source-relations/neotoma/taxon-priority/README.md)
exactly. Their whole-file hashes differ because the private replay binds the
10,908-row full review bundle while the public table binds only its 1,351
Neotoma concepts.

The exact dataset-publication responses reside in the private source store at
`neotoma/publication-links/2026-09-29/`. Its 169-response capture manifest has
SHA-256 `d6dee3065e6fcfae8a7e484406cf37e2b5aa0424bee66d3a6922bbbdc1e867da`.
The manifest retains each source URL, retrieval time, byte count and digest;
58 prior exact responses were reused and 111 additional datasets were queried.
The replayed citation report has SHA-256
`9f37bb406b30beef6d8a2f274cc27ec509441c6c5b0d4d3a31c87aca6e93e24d`.
It records 223 linked publication records across 169 datasets: 149 with one
provider-primary publication, seven with multiple provider-primary links, two
with links but no primary flag and eleven without a linked publication.
Publication DOI is null on 172 records. All 169 datasets identify the European
Pollen Database as their constituent database. The citation leads have not
been independently checked against original publications.

Set `NEOTOMA_PUBLICATION_ROOT` to the private
`neotoma/publication-links/2026-09-29` directory. After building the private
review package as above, reproduce the current source replay with an absent
output directory:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.taxa_review.neotoma_priority \
  --repository . \
  --review-directory artifacts/jobs/taxa-review/complete-review \
  --capture-root "$NEOTOMA_PUBLICATION_ROOT" \
  --output artifacts/jobs/taxa-review/neotoma-replay
```

The replay verifies every capture member, source manifest and candidate
dataset identity before writing its four reports and receipt. All outputs
remain private review projections (`publication_allowed=false`,
`scientific_admission_allowed=false`). The old 3,538-sample, 58-dataset
projection used an earlier source screen and is not the current cohort.
