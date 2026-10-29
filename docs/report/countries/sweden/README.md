# Sweden Homo sapiens aDNA v66 Report

This bundle summarizes Homo sapiens ancient-DNA release metadata from AADR `v66`.
It inventories only Homo sapiens aDNA sample rows that match the `Sweden` country filter. Environmental and archaeology context layers are published in the shared map bundle, not duplicated here.

## Summary

- Country filter: `Sweden`
- Unique Homo sapiens aDNA samples: `416`
- Unique localities: `77`
- Latitude range: `55.377740` to `63.200000`
- Longitude range: `11.300700` to `18.700000`

This country bundle is valid even when the filter returns zero Homo sapiens aDNA samples. In that case the CSV, GeoJSON, and markdown exports remain present so downstream checks can distinguish an empty result from a missing artifact.
Locality rows now preserve the combined BP coverage of the samples they aggregate.

## Dataset Coverage

| Dataset | Sweden rows |
| --- | ---: |
| `1240k` | 416 |
| `ho` | 416 |

The report deduplicates samples by `genetic_id` across datasets. Dataset row counts can differ by coverage, but the combined inventory for `Sweden` contains `416` unique Homo sapiens aDNA samples in AADR `v66`.

## Output Files

- Shared interactive map: <a href="../../regions/nordic/nordic_map.html">Nordic Evidence Surface</a>
- Full sample inventory: [`sweden_aadr_v66_samples.csv`](./sweden_aadr_v66_samples.csv)
- Locality summary: [`sweden_aadr_v66_localities.csv`](./sweden_aadr_v66_localities.csv)
- Map-ready GeoJSON: [`sweden_aadr_v66_samples.geojson`](./sweden_aadr_v66_samples.geojson)
- Machine-readable summary: [`sweden_aadr_v66_summary.json`](./sweden_aadr_v66_summary.json)
- Full markdown sample table: [`sweden_aadr_v66_samples.md`](./sweden_aadr_v66_samples.md)

## Top Localities

| Locality | Samples | Latitude | Longitude | BP coverage | Datasets |
| --- | ---: | ---: | ---: | --- | --- |
| Frälsegården (Västra Götalands län, Falköping, Falbygden) | 54 | 58.1644 | 13.4547 | 3859-5336 BP | `1240k,ho` |
| Oland | 32 | 56.8792364 | 16.7212765 | 763-1766 BP | `1240k,ho` |
| Varnhem (Västra Götalands län, Skara) | 31 | 58.38 | 13.65 | 726-1074 BP | `1240k,ho` |
| Frojel (Gotlands län, Gotland) | 29 | 57.34 | 18.19 | 889-1061 BP | `1240k,ho` |
| Rössberga (Götaland, Västergötland) | 26 | 58.183333 | 13.65 | 4488-5412 BP | `1240k,ho` |
| Kopparsvik (Gotlands län, Gotland) | 22 | 57.63 | 18.28 | 889-1061 BP | `1240k,ho` |
| Albäcksbacken Maglarp (Southern Sweden/ Skåne) | 15 | 55.37774 | 13.095066 | 788-4853 BP | `1240k,ho` |
| Hjelmars rör (Västra Götalands län, Falköping, Falbygden) | 15 | 58.1697 | 13.578 | 4815-5335 BP | `1240k,ho` |
| Västerbjers (Gotland, Gothem parish) | 15 | 57.58 | 18.7 | 4383-5043 BP | `1240k,ho` |
| Kronan (Kalmar län, Mörbylånga) | 12 | 56.4 | 16.6 | 274 BP | `1240k,ho` |
| Landbogården (Västra Götalands län, Falköping, Falbygden) | 11 | 58.1775 | 13.4344 | 1699-5354 BP | `1240k,ho` |
| Sigtuna, church 1 (St Gertrud) | 9 | 59.617314 | 17.72361 | 684-1110 BP | `1240k,ho` |
| Falköping-5 (Västra Götalands län, Falköping) | 8 | 58.166 | 13.573 | 3587-4009 BP | `1240k,ho` |
| Kanaljorden (Östergötlands län, Motala) | 8 | 58.535 | 15.046 | 7448-7868 BP | `1240k,ho` |
| Sandby Borg (Kalmar län, Mörbylånga) | 7 | 56.55 | 16.63 | 1447-1503 BP | `1240k,ho` |


## Animal aDNA Country Outputs

- Tracked animal species represented: `2`
- Country-resolved animal sample rows: `5`
- Country-resolved animal locality rows: `3`
- Supporting tracked projects: `2`
- Sample evidence-backed rows: `5`
- Chronology-provenance-backed rows: `5`
- Coordinate-provenance-backed rows: `5`

### Animal Output Files

- Machine-readable animal summary: [`sweden_animal_adna_v66_summary.json`](./sweden_animal_adna_v66_summary.json)
- Animal sample rows CSV: [`sweden_animal_adna_v66_samples.csv`](./sweden_animal_adna_v66_samples.csv)
- Animal sample rows markdown: [`sweden_animal_adna_v66_samples.md`](./sweden_animal_adna_v66_samples.md)
- Animal species summary CSV: [`sweden_animal_adna_v66_species.csv`](./sweden_animal_adna_v66_species.csv)
- Animal localities GeoJSON: [`sweden_animal_adna_v66_localities.geojson`](./sweden_animal_adna_v66_localities.geojson)
- Animal citation appendix: [`sweden_animal_adna_v66_citations.md`](./sweden_animal_adna_v66_citations.md)
- Animal warning appendix: [`sweden_animal_adna_v66_warnings.md`](./sweden_animal_adna_v66_warnings.md)

### Country-Resolved Animal Species

| Common name | Latin name | Animal scope | Locality rows | Assignment posture | Caution |
| --- | --- | --- | ---: | --- | --- |
| cattle | Bos taurus | wild_or_progenitor_context | 2 | exact_country | wild or progenitor context; not domesticated-core support; sample support remains sparse; coordinates remain approximate or inferred |
| sheep | Ovis aries | domesticated_core | 1 | exact_country | coordinates remain approximate or inferred |



## Lake Evidence Richness

- Sweden lake evidence richness JSON: [`sweden_lake_evidence_richness_v66.json`](./sweden_lake_evidence_richness_v66.json)
- Sweden lake evidence registry CSV: [`sweden_lake_evidence_richness_v66_registry.csv`](./sweden_lake_evidence_richness_v66_registry.csv)
- Sweden lake evidence scenario CSV: [`sweden_lake_evidence_richness_v66_scenarios.csv`](./sweden_lake_evidence_richness_v66_scenarios.csv)
- Sweden lake evidence distance-band CSV: [`sweden_lake_evidence_richness_v66_bands.csv`](./sweden_lake_evidence_richness_v66_bands.csv)
- Sweden lake evidence GeoJSON: [`sweden_lake_evidence_richness_v66.geojson`](./sweden_lake_evidence_richness_v66.geojson)
- Sweden lake evidence map: [`sweden_lake_evidence_richness_v66_map.html`](./sweden_lake_evidence_richness_v66_map.html)
- Sweden lake evidence markdown: [`sweden_lake_evidence_richness_v66.md`](./sweden_lake_evidence_richness_v66.md)
- Chronology caveat: the linked markdown report keeps source-by-source temporal guardrails explicit; zero-interval context layers remain spatial evidence only.


## Lake Archaeology-Weight Sensitivity

- Sensitivity JSON: [`sweden_lake_archaeology_sensitivity_v66.json`](./sweden_lake_archaeology_sensitivity_v66.json)
- Sensitivity CSV: [`sweden_lake_archaeology_sensitivity_v66.csv`](./sweden_lake_archaeology_sensitivity_v66.csv)
- Reader explanation: [`sweden_lake_archaeology_sensitivity_v66.md`](./sweden_lake_archaeology_sensitivity_v66.md)



## Southern Sweden Land-Use Synthesis

- Full temporal synthesis JSON: [`sweden_land_use_synthesis_v66.json`](./sweden_land_use_synthesis_v66.json)
- Full temporal synthesis CSV: [`sweden_land_use_synthesis_v66.csv`](./sweden_land_use_synthesis_v66.csv)
- Target decisions and reader explanation: [`sweden_land_use_synthesis_v66.md`](./sweden_land_use_synthesis_v66.md)



## Lake Fieldwork Preparation

- Sweden lake fieldwork preparation JSON: [`sweden_lake_fieldwork_preparation_v66.json`](./sweden_lake_fieldwork_preparation_v66.json)
- Sweden lake fieldwork preparation CSV: [`sweden_lake_fieldwork_preparation_v66.csv`](./sweden_lake_fieldwork_preparation_v66.csv)
- Sweden lake fieldwork preparation markdown: [`sweden_lake_fieldwork_preparation_v66.md`](./sweden_lake_fieldwork_preparation_v66.md)



<!-- scientific-account-route:begin -->
## Scientific verification and limits

AADR source Political Entity and country-product row disposition; scientific chronology/geography/rights admission remains false.

**Supported claim.** This Sweden bundle inventories 416 published AADR v66 genetic IDs at 77 localities under the source Political Entity filter; country labels are publication selection.

**Unsupported claim.** Neither source country labels nor metadata dates establish historical nationality, qualified geography/chronology, ancestry, migration or farming. Five animal samples at three localities, blocked lake rankings and modeled land-use windows have separate units and admission.

**Actual verification performed.** Read this bundle reader and current summary; reconciled 416 CSV rows/distinct genetic IDs and 77 locality rows with the source-account disposition. No genotypes, source download, model or scientific-admission review was rerun. The earlier six-stage native-zero wording is retained historical prose. These current checks do not recover or validate its missing original receipts. The currently authenticated earlier saved-evidence job had inventory exit zero, observer exit one and aggregate exit one; a later saved observer and the separate current human export passed in their own recorded epochs. A separate maintained source replay from commit 601112dd1f4b9e09d2cfdec7fa57d9f4ae3303a7 produced the current default 29-field human CSVs, GeoJSON and complete typed records for all four countries. An independent original-ANNO reconstruction checked every value and retained 1231 unique published IDs; the saved source account still has 1325 IDs and 94 coordinate exclusions. The original row-support audit found 1211 duplicate IDs, 0 disjoint support pairs and 0 merged-hull gaps. Those are literal observed counts, not chronology calibration; all 1325 source chronology decisions still require review. A separate saved human/animal observer preserves false pollen eligibility and measurement-leakage flags, all four blocked native taxon witnesses and the original failed aggregate. The joint metadata check supports software-domain separation for these observed populations, but whole ADNA-001 remains open because no fresh current animal source-to-country producer is established. The public source packet and bounded metadata authority preserve exact inputs, source epochs and receipts. Historical v1 products and the original lifecycle account are unchanged. Genotype, biology, rights, ecology, PROP-004, pollen and LRA admission remain unestablished. A separate current human source export and current animal public-API export have both completed with independent full typed/default-writer observers. Human source commit 601112dd1f4b9e09d2cfdec7fa57d9f4ae3303a7 and animal source commit ad591c301bcadb6a3f963caa836a2e38a16d0de4 remain distinct. Their 263 watched source resources and shared observed origins match. The current joint metadata observation checked all 54 queries and 162 products: 49 typed fields, 29 default CSV fields and complete default GeoJSONs. It observed source-domain separation while preserving human metadata_only and animal archive_reads or mitogenome_only source modalities. Four source-owned taxon contexts remain blocked; the generic CSV/GeoJSON schema omits those typed-only block fields and does not imply scientific admission. The earlier metadata callback 17984 exited zero with partial/wholefalse flags; those historical fields are unchanged. The original saved native [0,1]/whole1 remains failed; no missing historical six-stage receipt has been recovered. Current human and animal native stages and their separate metadata captures exited zero, and current joint observation 51102 exited zero. These are current software/data-contract observations, without new genotype, biological, rights, qualified chronology, ecological or LRA acceptance. Historical 1,325 human review-required records and three missing historical backlink metadata digests remain separate. Existing published products, ownership roles and full original acceptance criteria are unchanged.

**Remaining input or review.** Authenticate each Sweden source row, chronology, coordinate interpretation, rights and intended reuse before scientific comparison; keep duplicate source-panel membership distinct from genetic IDs.

**Cause category.** Source metadata selection and unresolved scientific admission.

**Consequence.** The 416 visible IDs are a filtered publication inventory; they are not 416 independent people, validated dates or an admitted population estimate.

**Precise next acceptance route.** Review reports/science/aadr-nordic-entities/report.json and its exact decision population, then resolve missing coordinates and qualified chronology/geography/rights at native record IDs before an independently declared biological comparison.

**Negative or refused result.** 0 of 416 source-labelled Sweden IDs are excluded for missing coordinates; map_admitted and scientifically_admitted remain false. Both 1240k and ho contain 416 rows.

**Matched denominator.** Sweden: source-labelled genetic IDs 416; published unique genetic IDs 416; coordinate exclusions 0; locality rows 77. Dataset counts {"1240k": 416, "ho": 416} count panel membership, not additional people. Five animal samples at three localities, blocked lake rankings and modeled land-use windows have separate units and admission.

Qualified authored reader SHA-256: `f3f2297b896b5a5803297984fa07e917fef87bf37f42e92e9e2adbf4f25e5415`.

- [Retained qualification evidence: docs/report/countries/sweden/sweden_aadr_v66_summary.json](sweden_aadr_v66_summary.json) (SHA-256 `2bb540d46edcb2080604b33c8acdc45157e5d5bc508ba5c7c191049785c0cf50`).

- [Retained qualification evidence: docs/report/countries/sweden/sweden_aadr_v66_samples.csv](sweden_aadr_v66_samples.csv) (SHA-256 `e8f9badb88be58eea8d3e838a71a777b6cc4a87e356e9ddd5ee19327d9de870b`).

- [Retained qualification evidence: docs/report/countries/sweden/sweden_aadr_v66_localities.csv](sweden_aadr_v66_localities.csv) (SHA-256 `5d00df28727080ae8832747ec4f967f4c0d535b8adc354f4d6144a2bbc443adb`).

- [Retained qualification evidence: reports/science/aadr-nordic-entities/report.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/aadr-nordic-entities/report.json) (SHA-256 `73d0ba6d098d7314c9cb3e348f3d76806e3b1e2f2a3d4dacbc0df123728b4196`).

- [Retained qualification evidence: reports/science/source-cohorts/adna-current-contract-adjudication.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/adna-current-contract-adjudication.json) (SHA-256 `7c1abf2b936ad95182ea3137c8e7a1df1f5553b2ceac2df7a9fe32a993e744a9`).

- [Retained qualification evidence: reports/science/source-cohorts/adna-current-domain-evidence.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/adna-current-domain-evidence.json) (SHA-256 `cdef4f083b1ab0c674a83e7d2c961b968b2e3539a38a527b99a04bb91681380e`).

- [Canonical scientific account: reports/science/aadr-nordic-entities/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/aadr-nordic-entities/README.md) (source SHA-256 `4739814c5a1b2b690beb0d57de5432df785ae31914d64e5c881170b885b5c841`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
