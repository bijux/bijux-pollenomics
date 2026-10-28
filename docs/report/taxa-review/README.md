# Source-bound taxa review package

The current private review projection contains **10,908 rows** from the source
authorities listed below. Its rows preserve source identities, native names and
qualifiers, country observation counts, exact-unit values, source citations and
separate proposed group, LRA taxon, PFT, PPE and fall-speed fields. Every row
remains `needs_discussion`; all proposed mappings start unset. The package is
for qualified review, with no classification admission or publication right.
The completed projection has bundle SHA-256
`74df58ba0befcf51b3d78937dc9c8ec2f3b078552c8026c1477a0316e79a76f5`;
the completion reader verified all three payload members and their byte counts.
The physical JSON SHA-256 is
`d4f56ef2128fa395d91d422e80dbf0d40533e487c392561b49fa6f356bdcff26`.
This identifies the retained capture, including its inventory locator and
working-source overlay; rebuilding with another locator can change its bundle
identity. The [readiness account](readiness.json) and
[source account](source-account.json) record the actual execution scope.

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
relational Neotoma manifests. The SHA-256 values for the native priority
and dataset attribution in the retained
full-review capture are respectively:

- `fce4fd4d80397df99210f7fc48357029239f0a3afe2965daaf5068bc3712be7d`
- `afc74c40713040f1429468c3dea66d76af857b80d2a1ac93affad85a8b5d180d`

These projections bind the full 10,908-row private package. The
[governed scoped review](../source-relations/neotoma/taxon-priority/README.md)
binds only its 1,351 Neotoma concepts. File and bundle identities are distinct;
current whole-file equality to the earlier full-review capture is not claimed.

The exact dataset-publication responses reside in the private source store at
`neotoma/publication-links/2026-09-29/`. Its 169-response capture manifest has
SHA-256 `d6dee3065e6fcfae8a7e484406cf37e2b5aa0424bee66d3a6922bbbdc1e867da`.
The manifest retains each source URL, retrieval time, byte count and digest;
58 prior exact responses were reused and 111 additional datasets were queried.
The current retained citation report has SHA-256
`ee7938ed84e97f2f208bb6e720c1f0bdef697c5b76de1bd0482c00c4fdbcb1e9`.
It records 223 linked publication records across 169 datasets: 149 with one
provider-primary publication, seven with multiple provider-primary links, two
with links but no primary flag and eleven without a linked publication.
Publication DOI is null on 172 records. All 169 datasets identify the European
Pollen Database as their constituent database. The citation leads have not
been independently checked against original publications.

The capture manifest names the earlier full-review attribution digest
`9bb1bebdf9155fa8ba2ebb7afb5b743258730aad967201fba6c0bdef13a5eb63`.
Those attribution bytes were unavailable during the current qualification.
The current capture independently checked all 169 response files, digests,
native dataset identities and links against the current candidate datasets.
The old attribution digest is retained lineage only. The existing
`taxa_review.neotoma_priority` replay requires an exact original attribution
binding and refuses this newly rebuilt package against the old manifest;
its strict refusal remains in place. No fresh source request, original-paper
verification or rights admission was performed.

## Parameter, chronology and basin review intake

The parameter consumer needs the physical completed-review hash, the physical
priority hash and the physical provenance hash as well as native source
identities. Native priority and attribution projections do not provide those
file bindings themselves. The maintained IO adapter verifies the completed
package and both native files, checks their semantic identity and writes
separate bound projections into a fresh directory. It preserves all original
files and refuses mismatched hashes, incomplete completion receipts, foreign
source snapshots and pre-existing unsupported bindings.

Set `PRIVATE_REVIEW_DIRECTORY`, `NATIVE_PRIORITY`, `NATIVE_PROVENANCE` and the
three expected SHA-256 variables to exact private captured files and their
trusted hashes. Bind the files with:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.taxa_review.lra_parameters.intake \
  --review-directory "$PRIVATE_REVIEW_DIRECTORY" \
  --priority "$NATIVE_PRIORITY" --provenance "$NATIVE_PROVENANCE" \
  --review-sha256 "$REVIEW_SHA256" --priority-sha256 "$PRIORITY_SHA256" \
  --provenance-sha256 "$PROVENANCE_SHA256" \
  --output-directory artifacts/jobs/taxa-review/parameter-file-bindings
```

The 112 LandClim/LRA source rows yield 72 parameter authority rows: 62
have parseable PPE candidates and 70 have parseable fall-speed candidates.
These counts overlap and do not signify accepted taxon/parameter bindings.

The full review package includes unresolved taxon concepts, source citations,
proposed classification fields and source-native PPE/fall-speed candidates.
The chronology/basin projection separately provides the complete candidate
sample and site denominators, original age claims, observed area/unit candidates
and missing or conflicting evidence. The actual qualification used the
[source-authenticated prerequisite projection](../source-relations/neotoma/lra-prerequisites/README.md)
and retained its exact governed bytes. No basin scale or chronology was
accepted to make a row executable.

The returned-decision routes are:

| Review surface | Maintained import validator | Required scope |
| --- | --- | --- |
| Full taxon package | `taxa_review validate-return` | Every 10,908-row source identity and current bundle |
| Taxon/PPE/fall speed | `lra_parameters.decisions.validate_lra_parameter_decisions` | Every 1,006 concept, exact bound priority/provenance/review and parameter evidence |
| Chronology/basin | `lra_prerequisites.decisions.validate_returned_prerequisite_decisions` | Every 10,637 sample and 163 site, rebuilt native authorities and exact selected evidence |

For the taxon CLI, set `RETURNED_TAXON_DECISIONS` to the reviewer-return JSON:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.taxa_review validate-return \
  --bundle "$PRIVATE_REVIEW_DIRECTORY/taxa-review.json" \
  --decisions "$RETURNED_TAXON_DECISIONS" \
  --output artifacts/jobs/taxa-review/taxon-return-intent.json
```

The parameter validator receives the generated review projection, returned
JSON and exact bound `priority`, `provenance`, `review` and
`provenance_file_sha256`. The chronology/basin validator receives its
source-authenticated projection, returned JSON, original native `evidence`,
`lakeparameter_capture_root` and expected capture digest. These are intent
validation paths: a valid return does not grant reviewer authentication,
biological acceptance, source rights or canonical import.

The current qualification exercises these three routes with complete,
explicitly controlled unresolved fixtures. They are not received human
reviews. Stale bundle/source identities, duplicate taxon identities, incomplete
parameter denominators and incomplete chronology denominators are refused.
The exact execution, focused checks and independent structural audit are
recorded in the [source account](source-account.json). Detailed vectors, source
records, CSV review rows and controlled returns remain private; only this
aggregate account is public.

The old 3,538-sample, 58-dataset projection used an earlier source screen and
is not the current cohort.
