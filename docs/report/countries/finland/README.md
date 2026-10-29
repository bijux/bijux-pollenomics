# Finland Homo sapiens aDNA v66 Report

This bundle summarizes Homo sapiens ancient-DNA release metadata from AADR `v66`.
It inventories only Homo sapiens aDNA sample rows that match the `Finland` country filter. Environmental and archaeology context layers are published in the shared map bundle, not duplicated here.

## Summary

- Country filter: `Finland`
- Unique Homo sapiens aDNA samples: `32`
- Unique localities: `6`
- Latitude range: `60.200000` to `69.910000`
- Longitude range: `22.178000` to `27.030000`

This country bundle is valid even when the filter returns zero Homo sapiens aDNA samples. In that case the CSV, GeoJSON, and markdown exports remain present so downstream checks can distinguish an empty result from a missing artifact.
Locality rows now preserve the combined BP coverage of the samples they aggregate.

## Dataset Coverage

| Dataset | Finland rows |
| --- | ---: |
| `1240k` | 23 |
| `ho` | 32 |

The report deduplicates samples by `genetic_id` across datasets. Dataset row counts can differ by coverage, but the combined inventory for `Finland` contains `32` unique Homo sapiens aDNA samples in AADR `v66`.

## Output Files

- Shared interactive map: <a href="../../regions/nordic/nordic_map.html">Nordic Evidence Surface</a>
- Full sample inventory: [`finland_aadr_v66_samples.csv`](./finland_aadr_v66_samples.csv)
- Locality summary: [`finland_aadr_v66_localities.csv`](./finland_aadr_v66_localities.csv)
- Map-ready GeoJSON: [`finland_aadr_v66_samples.geojson`](./finland_aadr_v66_samples.geojson)
- Machine-readable summary: [`finland_aadr_v66_summary.json`](./finland_aadr_v66_summary.json)
- Full markdown sample table: [`finland_aadr_v66_samples.md`](./finland_aadr_v66_samples.md)

## Top Localities

| Locality | Samples | Latitude | Longitude | BP coverage | Datasets |
| --- | ---: | ---: | ---: | --- | --- |
| Finland, modern | 19 | 60.2 | 24.9 | 0 BP | `1240k,ho` |
| Levanluhta (Isokyro) | 8 | 62.948744 | 22.410146 | 1112-1688 BP | `1240k,ho` |
| Utsjoki | 2 | 69.91 | 27.03 | 0 BP | `1240k,ho` |
| Enontekiö | 1 | 68.383893 | 23.632454 | 0 BP | `ho` |
| Käldamäki | 1 | 63.151 | 22.178 | 1322-1474 BP | `1240k,ho` |
| Levänluhta | 1 | 62.949 | 22.418 | 1258-1474 BP | `1240k,ho` |


## Animal aDNA Country Outputs

- Tracked animal species represented: `1`
- Country-resolved animal sample rows: `2`
- Country-resolved animal locality rows: `1`
- Supporting tracked projects: `1`
- Sample evidence-backed rows: `2`
- Chronology-provenance-backed rows: `2`
- Coordinate-provenance-backed rows: `2`

### Animal Output Files

- Machine-readable animal summary: [`finland_animal_adna_v66_summary.json`](./finland_animal_adna_v66_summary.json)
- Animal sample rows CSV: [`finland_animal_adna_v66_samples.csv`](./finland_animal_adna_v66_samples.csv)
- Animal sample rows markdown: [`finland_animal_adna_v66_samples.md`](./finland_animal_adna_v66_samples.md)
- Animal species summary CSV: [`finland_animal_adna_v66_species.csv`](./finland_animal_adna_v66_species.csv)
- Animal localities GeoJSON: [`finland_animal_adna_v66_localities.geojson`](./finland_animal_adna_v66_localities.geojson)
- Animal citation appendix: [`finland_animal_adna_v66_citations.md`](./finland_animal_adna_v66_citations.md)
- Animal warning appendix: [`finland_animal_adna_v66_warnings.md`](./finland_animal_adna_v66_warnings.md)

### Country-Resolved Animal Species

| Common name | Latin name | Animal scope | Locality rows | Assignment posture | Caution |
| --- | --- | --- | ---: | --- | --- |
| sheep | Ovis aries | domesticated_core | 1 | exact_country | sample support remains sparse; coordinates remain approximate or inferred |





<!-- scientific-account-route:begin -->
## Scientific verification and limits

AADR source Political Entity and country-product row disposition; scientific chronology/geography/rights admission remains false.

**Supported claim.** This Finland bundle inventories 32 published AADR v66 genetic IDs at 6 localities under the source Political Entity filter; country labels are publication selection.

**Unsupported claim.** Neither source country labels nor metadata dates establish historical nationality, qualified geography/chronology, ancestry, migration or farming. Two sheep samples at Kastelholm supply one locality; most source-labelled Finnish human IDs lack coordinates.

**Actual verification performed.** Read this bundle reader and current summary; reconciled 32 CSV rows/distinct genetic IDs and 6 locality rows with the source-account disposition. No genotypes, source download, model or scientific-admission review was rerun. The earlier six-stage native-zero wording is retained historical prose. These current checks do not recover or validate its missing original receipts. The currently authenticated earlier saved-evidence job had inventory exit zero, observer exit one and aggregate exit one; a later saved observer and the separate current human export passed in their own recorded epochs. A separate maintained source replay from commit 601112dd1f4b9e09d2cfdec7fa57d9f4ae3303a7 produced the current default 29-field human CSVs, GeoJSON and complete typed records for all four countries. An independent original-ANNO reconstruction checked every value and retained 1231 unique published IDs; the saved source account still has 1325 IDs and 94 coordinate exclusions. The original row-support audit found 1211 duplicate IDs, 0 disjoint support pairs and 0 merged-hull gaps. Those are literal observed counts, not chronology calibration; all 1325 source chronology decisions still require review. A separate saved human/animal observer preserves false pollen eligibility and measurement-leakage flags, all four blocked native taxon witnesses and the original failed aggregate. The joint metadata check supports software-domain separation for these observed populations, but whole ADNA-001 remains open because no fresh current animal source-to-country producer is established. The public source packet and bounded metadata authority preserve exact inputs, source epochs and receipts. Historical v1 products and the original lifecycle account are unchanged. Genotype, biology, rights, ecology, PROP-004, pollen and LRA admission remain unestablished. A separate current human source export and current animal public-API export have both completed with independent full typed/default-writer observers. Human source commit 601112dd1f4b9e09d2cfdec7fa57d9f4ae3303a7 and animal source commit ad591c301bcadb6a3f963caa836a2e38a16d0de4 remain distinct. Their 263 watched source resources and shared observed origins match. The current joint metadata observation checked all 54 queries and 162 products: 49 typed fields, 29 default CSV fields and complete default GeoJSONs. It observed source-domain separation while preserving human metadata_only and animal archive_reads or mitogenome_only source modalities. Four source-owned taxon contexts remain blocked; the generic CSV/GeoJSON schema omits those typed-only block fields and does not imply scientific admission. The earlier metadata callback 17984 exited zero with partial/wholefalse flags; those historical fields are unchanged. The original saved native [0,1]/whole1 remains failed; no missing historical six-stage receipt has been recovered. Current human and animal native stages and their separate metadata captures exited zero, and current joint observation 51102 exited zero. These are current software/data-contract observations, without new genotype, biological, rights, qualified chronology, ecological or LRA acceptance. Historical 1,325 human review-required records and three missing historical backlink metadata digests remain separate. Existing published products, ownership roles and full original acceptance criteria are unchanged.

**Remaining input or review.** Authenticate each Finland source row, chronology, coordinate interpretation, rights and intended reuse before scientific comparison; keep duplicate source-panel membership distinct from genetic IDs.

**Cause category.** Source metadata selection and unresolved scientific admission.

**Consequence.** The 32 visible IDs are a filtered publication inventory; they are not 32 independent people, validated dates or an admitted population estimate.

**Precise next acceptance route.** Review reports/science/aadr-nordic-entities/report.json and its exact decision population, then resolve missing coordinates and qualified chronology/geography/rights at native record IDs before an independently declared biological comparison.

**Negative or refused result.** 92 of 124 source-labelled Finland IDs are excluded for missing coordinates; map_admitted and scientifically_admitted remain false. 1240k contributes 23 rows and ho 32; present-day rows remain visible.

**Matched denominator.** Finland: source-labelled genetic IDs 124; published unique genetic IDs 32; coordinate exclusions 92; locality rows 6. Dataset counts {"1240k": 23, "ho": 32} count panel membership, not additional people. Two sheep samples at Kastelholm supply one locality; most source-labelled Finnish human IDs lack coordinates.

- [Retained qualification evidence: docs/report/countries/finland/finland_aadr_v66_summary.json](finland_aadr_v66_summary.json) (SHA-256 `d84243c21847ea16a75bab9ae1bf157f589335fa6ee0c37e18f8721ba8ce4332`).

- [Retained qualification evidence: docs/report/countries/finland/finland_aadr_v66_samples.csv](finland_aadr_v66_samples.csv) (SHA-256 `1b1ab06d05f28fcfa42c26fc12dc33e1588a23c3eab0a917f4892d156d578edb`).

- [Retained qualification evidence: docs/report/countries/finland/finland_aadr_v66_localities.csv](finland_aadr_v66_localities.csv) (SHA-256 `a51ee57bf9b4f82970f2f36cfe61896a6f4c08f9d4bcb6735d112c638a771546`).

- [Retained qualification evidence: reports/science/aadr-nordic-entities/report.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/aadr-nordic-entities/report.json) (SHA-256 `73d0ba6d098d7314c9cb3e348f3d76806e3b1e2f2a3d4dacbc0df123728b4196`).

- [Retained qualification evidence: reports/science/source-cohorts/adna-current-contract-adjudication.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/adna-current-contract-adjudication.json) (SHA-256 `7c1abf2b936ad95182ea3137c8e7a1df1f5553b2ceac2df7a9fe32a993e744a9`).

- [Retained qualification evidence: reports/science/source-cohorts/adna-current-domain-evidence.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/adna-current-domain-evidence.json) (SHA-256 `cdef4f083b1ab0c674a83e7d2c961b968b2e3539a38a527b99a04bb91681380e`).

- [Canonical scientific account: reports/science/aadr-nordic-entities/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/aadr-nordic-entities/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
