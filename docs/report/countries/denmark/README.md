# Denmark Homo sapiens aDNA v66 Report

This bundle summarizes Homo sapiens ancient-DNA release metadata from AADR `v66`.
It inventories only Homo sapiens aDNA sample rows that match the `Denmark` country filter. Environmental and archaeology context layers are published in the shared map bundle, not duplicated here.

## Summary

- Country filter: `Denmark`
- Unique Homo sapiens aDNA samples: `653`
- Unique localities: `295`
- Latitude range: `54.623000` to `57.506536`
- Longitude range: `8.728229` to `14.998540`

This country bundle is valid even when the filter returns zero Homo sapiens aDNA samples. In that case the CSV, GeoJSON, and markdown exports remain present so downstream checks can distinguish an empty result from a missing artifact.
Locality rows now preserve the combined BP coverage of the samples they aggregate.

## Dataset Coverage

| Dataset | Denmark rows |
| --- | ---: |
| `1240k` | 653 |
| `ho` | 653 |

The report deduplicates samples by `genetic_id` across datasets. Dataset row counts can differ by coverage, but the combined inventory for `Denmark` contains `653` unique Homo sapiens aDNA samples in AADR `v66`.

## Output Files

- Shared interactive map: <a href="../../regions/nordic/nordic_map.html">Nordic Evidence Surface</a>
- Full sample inventory: [`denmark_aadr_v66_samples.csv`](./denmark_aadr_v66_samples.csv)
- Locality summary: [`denmark_aadr_v66_localities.csv`](./denmark_aadr_v66_localities.csv)
- Map-ready GeoJSON: [`denmark_aadr_v66_samples.geojson`](./denmark_aadr_v66_samples.geojson)
- Machine-readable summary: [`denmark_aadr_v66_summary.json`](./denmark_aadr_v66_summary.json)
- Full markdown sample table: [`denmark_aadr_v66_samples.md`](./denmark_aadr_v66_samples.md)

## Top Localities

| Locality | Samples | Latitude | Longitude | BP coverage | Datasets |
| --- | ---: | ---: | ---: | --- | --- |
| Vor Frue Kirkegård (Aalborg) | 32 | 57.05 | 9.92 | 73-977 BP | `1240k,ho` |
| Tjærby (Randers Municipality) | 28 | 56.47 | 10.1 | 542-974 BP | `1240k,ho` |
| Ahlgade 15-17 (Holbæk) | 25 | 55.72 | 11.71 | 88-1012 BP | `1240k,ho` |
| Simonsborg (Zealand/ Alsted) | 21 | 55.40315 | 11.66018 | 1520-2008 BP | `1240k,ho` |
| Galgedil (Funen Region) | 16 | 55.5 | 10.33 | 820-1280 BP | `1240k,ho` |
| Kopenhagen (Zealand Region) | 15 | 55.675268 | 12.568294 | 842-958 BP | `1240k,ho` |
| Alken_Enge (Jutland) | 14 | 56.049 | 9.852 | 1414-2394 BP | `1240k,ho` |
| Lillevasby (Zealand) | 14 | 55.6691502 | 12.2092259 | 1520-6104 BP | `1240k,ho` |
| Bogevej (Langeland Region) | 13 | 54.87001 | 10.72 | 942-1058 BP | `1240k,ho` |
| Mosede Fort (Zealand) | 12 | 55.5644395 | 12.2745516 | 1520-2008 BP | `1240k,ho` |
| Asnæs (Zealand) | 11 | 55.81508 | 11.50296 | 1520-2010 BP | `1240k,ho` |
| Bogøvej (Langelands Sønder) | 9 | 54.8711699 | 10.703644 | 670-1278 BP | `1240k,ho` |
| Ribe (Jutland Region) | 9 | 55.33 | 8.76 | 800-1295 BP | `1240k,ho` |
| Hesselbjerg (Jutland Region) | 8 | 55.95 | 10.2 | 1047-1103 BP | `1240k,ho` |
| Bakkendrup (Zealand Region) | 7 | 55.56 | 11.25 | 670-1278 BP | `1240k,ho` |


## Animal aDNA Country Outputs

- Tracked animal species represented: `2`
- Country-resolved animal sample rows: `5`
- Country-resolved animal locality rows: `4`
- Supporting tracked projects: `2`
- Sample evidence-backed rows: `5`
- Chronology-provenance-backed rows: `5`
- Coordinate-provenance-backed rows: `5`

### Animal Output Files

- Machine-readable animal summary: [`denmark_animal_adna_v66_summary.json`](./denmark_animal_adna_v66_summary.json)
- Animal sample rows CSV: [`denmark_animal_adna_v66_samples.csv`](./denmark_animal_adna_v66_samples.csv)
- Animal sample rows markdown: [`denmark_animal_adna_v66_samples.md`](./denmark_animal_adna_v66_samples.md)
- Animal species summary CSV: [`denmark_animal_adna_v66_species.csv`](./denmark_animal_adna_v66_species.csv)
- Animal localities GeoJSON: [`denmark_animal_adna_v66_localities.geojson`](./denmark_animal_adna_v66_localities.geojson)
- Animal citation appendix: [`denmark_animal_adna_v66_citations.md`](./denmark_animal_adna_v66_citations.md)
- Animal warning appendix: [`denmark_animal_adna_v66_warnings.md`](./denmark_animal_adna_v66_warnings.md)

### Country-Resolved Animal Species

| Common name | Latin name | Animal scope | Locality rows | Assignment posture | Caution |
| --- | --- | --- | ---: | --- | --- |
| cattle | Bos taurus | wild_or_progenitor_context | 2 | exact_country | wild or progenitor context; not domesticated-core support; coordinates remain approximate or inferred |
| pig | Sus scrofa domesticus | domesticated_core | 2 | exact_country | sample support remains sparse; point surface relies on named-site geocoding rather than direct coordinates; coordinates remain approximate or inferred |





<!-- scientific-account-route:begin -->
## Scientific verification and limits

AADR source Political Entity and country-product row disposition; scientific chronology/geography/rights admission remains false.

**Supported claim.** This Denmark bundle inventories 653 published AADR v66 genetic IDs at 295 localities under the source Political Entity filter; country labels are publication selection.

**Unsupported claim.** Neither source country labels nor metadata dates establish historical nationality, qualified geography/chronology, ancestry, migration or farming. Five animal samples at four localities are a separate population: three wild/progenitor aurochs and two pigs.

**Actual verification performed.** Read this bundle reader and current summary; reconciled 653 CSV rows/distinct genetic IDs and 295 locality rows with the source-account disposition. No genotypes, source download, model or scientific-admission review was rerun.

**Remaining input or review.** Authenticate each Denmark source row, chronology, coordinate interpretation, rights and intended reuse before scientific comparison; keep duplicate source-panel membership distinct from genetic IDs.

**Cause category.** Source metadata selection and unresolved scientific admission.

**Consequence.** The 653 visible IDs are a filtered publication inventory; they are not 653 independent people, validated dates or an admitted population estimate.

**Precise next acceptance route.** Review reports/science/aadr-nordic-entities/report.json and its exact decision population, then resolve missing coordinates and qualified chronology/geography/rights at native record IDs before an independently declared biological comparison.

**Negative or refused result.** One of 654 source-labelled Denmark IDs is excluded for missing coordinates; map_admitted and scientifically_admitted remain false. Both 1240k and ho contain 653 rows.

**Matched denominator.** Denmark: source-labelled genetic IDs 654; published unique genetic IDs 653; coordinate exclusions 1; locality rows 295. Dataset counts {"1240k": 653, "ho": 653} count panel membership, not additional people. Five animal samples at four localities are a separate population: three wild/progenitor aurochs and two pigs.

Qualified authored reader SHA-256: `9a7c7f5dab66211b59eb044a8400257bd96f2a1210d6b8c50cefef96fdf65a1c`.

- [Retained qualification evidence: docs/report/countries/denmark/denmark_aadr_v66_summary.json](denmark_aadr_v66_summary.json) (SHA-256 `fe6da56c5f4d4032f78e2021e348fdfcd62b5327450dc11a9aa771563dbdd809`).

- [Retained qualification evidence: docs/report/countries/denmark/denmark_aadr_v66_samples.csv](denmark_aadr_v66_samples.csv) (SHA-256 `1628b09c7cc3116b3b95b2e1390107beb5052079e67c00cfabb996f3608269b5`).

- [Retained qualification evidence: docs/report/countries/denmark/denmark_aadr_v66_localities.csv](denmark_aadr_v66_localities.csv) (SHA-256 `c0df6ee0c6f399d2ee78aa1aaac3bfa5795f1ae2586b0e9785f5235fb12764c4`).

- [Retained qualification evidence: reports/science/aadr-nordic-entities/report.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/aadr-nordic-entities/report.json) (SHA-256 `73d0ba6d098d7314c9cb3e348f3d76806e3b1e2f2a3d4dacbc0df123728b4196`).

- [Canonical scientific account: reports/science/aadr-nordic-entities/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/aadr-nordic-entities/README.md) (source SHA-256 `629106e651dfb865dd106c95e5e05f332316fe33da3a3b27218ebcc81e3922af`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
