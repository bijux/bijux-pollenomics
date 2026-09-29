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
