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

**Actual verification performed.** Read this bundle reader and current summary; reconciled 130 CSV rows/distinct genetic IDs and 69 locality rows with the source-account disposition. No genotypes, source download, model or scientific-admission review was rerun.

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

- [Canonical scientific account: reports/science/aadr-nordic-entities/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/aadr-nordic-entities/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
