# Norway Homo sapiens aDNA v66 Report

This bundle summarizes Homo sapiens ancient-DNA release metadata from AADR `v66`.
It inventories only Homo sapiens aDNA sample rows that match the `Norway` country filter. Environmental and archaeology context layers are published in the shared map bundle, not duplicated here.

## Summary

- Country filter: `Norway`
- Unique Homo sapiens aDNA samples: `130`
- Unique localities: `69`
- Latitude range: `58.064000` to `70.117388`
- Longitude range: `5.126941` to `19.017706`

This country bundle is valid even when the filter returns zero Homo sapiens aDNA samples. In that case the CSV, GeoJSON, and markdown exports remain present so downstream checks can distinguish an empty result from a missing artifact.
Locality rows now preserve the combined BP coverage of the samples they aggregate.

## Dataset Coverage

| Dataset | Norway rows |
| --- | ---: |
| `1240k` | 119 |
| `ho` | 130 |

The report deduplicates samples by `genetic_id` across datasets. Dataset row counts can differ by coverage, but the combined inventory for `Norway` contains `130` unique Homo sapiens aDNA samples in AADR `v66`.

## Output Files

- Shared interactive map: <a href="../../regions/nordic/nordic_map.html">Nordic Evidence Surface</a>
- Full sample inventory: [`norway_aadr_v66_samples.csv`](./norway_aadr_v66_samples.csv)
- Locality summary: [`norway_aadr_v66_localities.csv`](./norway_aadr_v66_localities.csv)
- Map-ready GeoJSON: [`norway_aadr_v66_samples.geojson`](./norway_aadr_v66_samples.geojson)
- Machine-readable summary: [`norway_aadr_v66_summary.json`](./norway_aadr_v66_summary.json)
- Full markdown sample table: [`norway_aadr_v66_samples.md`](./norway_aadr_v66_samples.md)

## Top Localities

| Locality | Samples | Latitude | Longitude | BP coverage | Datasets |
| --- | ---: | ---: | ---: | --- | --- |
| Sund (Central Norway/ Trøndelag) | 13 | 63.8604 | 11.307 | 3030-4544 BP | `1240k,ho` |
| Bergen | 11 | 60.359 | 5.358 | 0 BP | `ho` |
| Public Library Site/Folkebibliotekstomten (Trondheim) | 7 | 63.43 | 10.39 | 634-866 BP | `1240k,ho` |
| Skongeneshelleren (Western Norway/ Sogn and Fjordane) | 6 | 62.02973527 | 5.126940543 | 1240-1943 BP | `1240k,ho` |
| Skien nor (Nor South, Vestfold og Telemark, Telemark) | 4 | 59.22 | 9.59 | 926-1566 BP | `1240k,ho` |
| Hummervikholmen (Agder, Søgne nor) | 3 | 58.064 | 7.7437 | 9262-9486 BP | `1240k,ho` |
| Joa (Central Norway/ Trøndelag) | 3 | 64.65448 | 11.208485 | 1009-1468 BP | `1240k,ho` |
| Joa, Namsos M (Central Norway/ Trøndelag) | 3 | 64.65448 | 11.208485 | 1007-1316 BP | `1240k,ho` |
| Skjeggesnes (Northern Norway/ Nordland) | 3 | 63.74603 | 11.2983 | 3101-3597 BP | `1240k,ho` |
| Toldnes (Central Norway/ Trøndelag) | 3 | 63.9758 | 11.3946 | 1533-3942 BP | `1240k,ho` |
| Tomeide, Nesna M (Northern Norway/ Nordland) | 3 | 66.262731 | 12.724308 | 1158-1777 BP | `1240k,ho` |
| Vik, Klepp (Western Norway/ Rogaland) | 3 | 58.712198 | 5.525827 | 957-1353 BP | `1240k,ho` |
| Arnestad store (24/1) (Nor South, Hedmark, Åmot) | 2 | 61.15 | 11.34 | 942-1058 BP | `1240k,ho` |
| Bergvin (Central Norway/ Trøndelag) | 2 | 63.74603 | 11.2983 | 1806-4914 BP | `1240k,ho` |
| Eid (Central Norway/ Lines, Trøndelag) | 2 | 64.0331 | 9.89233 | 3374-6154 BP | `1240k,ho` |


## Animal aDNA Country Outputs

No tracked non-human animal locality lead is currently assignable to `Norway`
with the current repository rules, so this country bundle ships only the human AADR
surface for now.





<!-- scientific-account-route:begin -->
## Scientific verification and limits

AADR source Political Entity and country-product row disposition; scientific chronology/geography/rights admission remains false.

**Supported claim.** This Norway bundle inventories 130 published AADR v66 genetic IDs at 69 localities under the source Political Entity filter; country labels are publication selection.

**Unsupported claim.** Neither source country labels nor metadata dates establish historical nationality, qualified geography/chronology, ancestry, migration or farming. No country-resolved animal samples are published; this is no evidence of historical animal absence.

**Actual verification performed.** Read this bundle reader and current summary; reconciled 130 CSV rows/distinct genetic IDs and 69 locality rows with the source-account disposition. No genotypes, source download, model or scientific-admission review was rerun. The earlier six-stage native-zero wording is retained historical prose. These current checks do not recover or validate its missing original receipts. The currently authenticated earlier saved-evidence job had inventory exit zero, observer exit one and aggregate exit one; a later saved observer and the separate current human export passed in their own recorded epochs. A separate maintained source replay from commit 601112dd1f4b9e09d2cfdec7fa57d9f4ae3303a7 produced the current default 29-field human CSVs, GeoJSON and complete typed records for all four countries. An independent original-ANNO reconstruction checked every value and retained 1231 unique published IDs; the saved source account still has 1325 IDs and 94 coordinate exclusions. The original row-support audit found 1211 duplicate IDs, 0 disjoint support pairs and 0 merged-hull gaps. Those are literal observed counts, not chronology calibration; all 1325 source chronology decisions still require review. A separate saved human/animal observer preserves false pollen eligibility and measurement-leakage flags, all four blocked native taxon witnesses and the original failed aggregate. The joint metadata check supports software-domain separation for these observed populations, but whole ADNA-001 remains open because no fresh current animal source-to-country producer is established. The public source packet and bounded metadata authority preserve exact inputs, source epochs and receipts. Historical v1 products and the original lifecycle account are unchanged. Genotype, biology, rights, ecology, PROP-004, pollen and LRA admission remain unestablished. A separate current human source export and current animal public-API export have both completed with independent full typed/default-writer observers. Human source commit 601112dd1f4b9e09d2cfdec7fa57d9f4ae3303a7 and animal source commit ad591c301bcadb6a3f963caa836a2e38a16d0de4 remain distinct. Their 263 watched source resources and shared observed origins match. The current joint metadata observation checked all 54 queries and 162 products: 49 typed fields, 29 default CSV fields and complete default GeoJSONs. It observed source-domain separation while preserving human metadata_only and animal archive_reads or mitogenome_only source modalities. Four source-owned taxon contexts remain blocked; the generic CSV/GeoJSON schema omits those typed-only block fields and does not imply scientific admission. The earlier metadata callback 17984 exited zero with partial/wholefalse flags; those historical fields are unchanged. The original saved native [0,1]/whole1 remains failed; no missing historical six-stage receipt has been recovered. Current human and animal native stages and their separate metadata captures exited zero, and current joint observation 51102 exited zero. These are current software/data-contract observations, without new genotype, biological, rights, qualified chronology, ecological or LRA acceptance. Historical 1,325 human review-required records and three missing historical backlink metadata digests remain separate. Existing published products, ownership roles and full original acceptance criteria are unchanged.

**Remaining input or review.** Authenticate each Norway source row, chronology, coordinate interpretation, rights and intended reuse before scientific comparison; keep duplicate source-panel membership distinct from genetic IDs.

**Cause category.** Source metadata selection and unresolved scientific admission.

**Consequence.** The 130 visible IDs are a filtered publication inventory; they are not 130 independent people, validated dates or an admitted population estimate.

**Precise next acceptance route.** Review reports/science/aadr-nordic-entities/report.json and its exact decision population, then resolve missing coordinates and qualified chronology/geography/rights at native record IDs before an independently declared biological comparison.

**Negative or refused result.** One of 131 source-labelled Norway IDs is excluded for missing coordinates; map_admitted and scientifically_admitted remain false. 1240k contributes 119 rows and ho 130; present-day Bergen rows remain in this metadata inventory.

**Matched denominator.** Norway: source-labelled genetic IDs 131; published unique genetic IDs 130; coordinate exclusions 1; locality rows 69. Dataset counts {"1240k": 119, "ho": 130} count panel membership, not additional people. No country-resolved animal samples are published; this is no evidence of historical animal absence.

- [Retained qualification evidence: docs/report/countries/norway/norway_aadr_v66_summary.json](norway_aadr_v66_summary.json) (SHA-256 `0ca91dd558b9fc1a868720100eef530aa71dbe5f8b189f0c7025efd81e8f57ee`).

- [Retained qualification evidence: docs/report/countries/norway/norway_aadr_v66_samples.csv](norway_aadr_v66_samples.csv) (SHA-256 `021fbef6979f47d19e6b9df915b0ca73742243401239b8d60ba022b0e3e22396`).

- [Retained qualification evidence: docs/report/countries/norway/norway_aadr_v66_localities.csv](norway_aadr_v66_localities.csv) (SHA-256 `e162ec0bf12b1385972264b7e9d93c1424b5cf8ccf277dc1e1ed82032a4d7df1`).

- [Retained qualification evidence: reports/science/aadr-nordic-entities/report.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/aadr-nordic-entities/report.json) (SHA-256 `73d0ba6d098d7314c9cb3e348f3d76806e3b1e2f2a3d4dacbc0df123728b4196`).

- [Retained qualification evidence: reports/science/source-cohorts/adna-current-contract-adjudication.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/adna-current-contract-adjudication.json) (SHA-256 `7c1abf2b936ad95182ea3137c8e7a1df1f5553b2ceac2df7a9fe32a993e744a9`).

- [Retained qualification evidence: reports/science/source-cohorts/adna-current-domain-evidence.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/adna-current-domain-evidence.json) (SHA-256 `cdef4f083b1ab0c674a83e7d2c961b968b2e3539a38a527b99a04bb91681380e`).

- [Canonical scientific account: reports/science/aadr-nordic-entities/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/aadr-nordic-entities/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
