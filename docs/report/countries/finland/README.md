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

**Actual verification performed.** Read this bundle reader and current summary; reconciled 32 CSV rows/distinct genetic IDs and 6 locality rows with the source-account disposition. No genotypes, source download, model or scientific-admission review was rerun.

**Remaining input or review.** Authenticate each Finland source row, chronology, coordinate interpretation, rights and intended reuse before scientific comparison; keep duplicate source-panel membership distinct from genetic IDs.

**Cause category.** Source metadata selection and unresolved scientific admission.

**Consequence.** The 32 visible IDs are a filtered publication inventory; they are not 32 independent people, validated dates or an admitted population estimate.

**Precise next acceptance route.** Review reports/science/aadr-nordic-entities/report.json and its exact decision population, then resolve missing coordinates and qualified chronology/geography/rights at native record IDs before an independently declared biological comparison.

**Negative or refused result.** 92 of 124 source-labelled Finland IDs are excluded for missing coordinates; map_admitted and scientifically_admitted remain false. 1240k contributes 23 rows and ho 32; present-day rows remain visible.

**Matched denominator.** Finland: source-labelled genetic IDs 124; published unique genetic IDs 32; coordinate exclusions 92; locality rows 6. Dataset counts {"1240k": 23, "ho": 32} count panel membership, not additional people. Two sheep samples at Kastelholm supply one locality; most source-labelled Finnish human IDs lack coordinates.

Qualified authored reader SHA-256: `aacf2f10e0f41e3efd7a2a08f871109007d8d16e367f06b98b3771783b109788`.

- [Retained qualification evidence: docs/report/countries/finland/finland_aadr_v66_summary.json](finland_aadr_v66_summary.json) (SHA-256 `d84243c21847ea16a75bab9ae1bf157f589335fa6ee0c37e18f8721ba8ce4332`).

- [Retained qualification evidence: docs/report/countries/finland/finland_aadr_v66_samples.csv](finland_aadr_v66_samples.csv) (SHA-256 `1b1ab06d05f28fcfa42c26fc12dc33e1588a23c3eab0a917f4892d156d578edb`).

- [Retained qualification evidence: docs/report/countries/finland/finland_aadr_v66_localities.csv](finland_aadr_v66_localities.csv) (SHA-256 `a51ee57bf9b4f82970f2f36cfe61896a6f4c08f9d4bcb6735d112c638a771546`).

- [Retained qualification evidence: reports/science/aadr-nordic-entities/report.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/aadr-nordic-entities/report.json) (SHA-256 `73d0ba6d098d7314c9cb3e348f3d76806e3b1e2f2a3d4dacbc0df123728b4196`).

- [Canonical scientific account: reports/science/aadr-nordic-entities/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/aadr-nordic-entities/README.md) (source SHA-256 `629106e651dfb865dd106c95e5e05f332316fe33da3a3b27218ebcc81e3922af`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
