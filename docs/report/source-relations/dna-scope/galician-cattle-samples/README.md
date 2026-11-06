# Galician cattle sample species

The PRJNA705960 BioProject mixes domestic cattle and aurochs. Its project
catalog remains headed `Bos taurus`, while the [sample master](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/data/adna/governance/source_library/projects/PRJNA705960/sample_master.json)
now keeps each BioSample's ENA taxon: eight `Bos taurus` (tax ID 9913) and
three `Bos primigenius` (tax ID 9909). The three aurochs retain
`project_species_mismatch`; the project label is not used to recast them as
domestic cattle. Stable BioSample IDs are unchanged.
The curated and [normalized sample records](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/data/adna/species/bos_taurus/normalized/sample_records.json)
carry the same 8/3 distinction; all 11 retain `sample_context_blocked`
publication status.

The [row review](samples.csv) reconciles all 11 ENA accessions with the
retained PLOS paper sample labels through source-owned ENA BioSample aliases.
The [machine-readable report](report.json) binds the paper crosswalk and its
16 primary capture files by SHA-256: fifteen retained in
`data/adna/review/galician_cattle/` and the governed ENA project archive. The
article's dating table lists
18 specimens; the sequenced sample mapping and ENA capture each contain the
same 11 distinct BioSamples. The current source library binds the primary paper and original supplements
in place. The source-review JSON retains its original identified-not-promoted
state as historical provenance, while this current sample report records
catalogue linkage. Whole-project expected/deposition counts remain unknown.

The separately requested [literal context table](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/galician-sample-context.csv)
now exposes all 110 cells on those eleven crosswalk rows, including native site,
radiocarbon, calibrated-BP, calendar, dating-lab and contextual strings. The
[chronology account and reproduction command](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-sample-chronology.md#literal-galician-sample-context)
explain cell types, the present blank `G27` and the modern-carbon sample whose
label must not become 60 BP or a Cobas locality. The current default report refreshes seven metadata leaves. The eleven-row
species CSV and all110literal cells retain their original bytes; all
site/date/point admission decisions remain unchanged.

Species ownership alone does not establish a mappable locality or comparable
chronology. All 11 sample-master locality, coordinate, and chronology fields
remain empty. The paper labels, specimen codes, and age-like strings in the
capture are review evidence only; none becomes an admitted site, date, Nordic
observation, or atlas point through this change.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native DNA specimen/publication/chronology scope and unsupported ecological or pollen extension.

**Supported claim.** The Galician sample account preserves eight Bos taurus and three Bos primigenius through normalized and curated consumers.

**Unsupported claim.** Species resolution does not resolve locality, calibrated sample chronology, Nordic relevance or point eligibility.

**Actual verification performed.** The opted-in consumer ran at 85de3133f, exit zero in 2.30 s, preserving 110 literal cells for eleven BioSamples. An independent original-workbook DOM check confirms all cells, headers, types, values, blank/formula states and crosswalk rows. Fifty controlled cases and one native original-writer test pass with configured lint/types. The earlier default-byte preservation belongs to its original source epoch. Current default report from988d1ff12 passes2.126s/RSS88096768B; only seven typed metadata leaves change, eleven-row CSV and all16source pins remain exact. Catalogue linkage is source curation, not sample context admission.

**Remaining input or review.** Current catalogue linkage is encoded. Sample-owned locality, chronology, whole-project deposition scope, scientific use and independent qualified interpretation remain unresolved.

**Cause category.** Sample identity is resolved more narrowly than spatial and temporal context.

**Consequence.** All eleven remain outside atlas points despite their resolved sample species.

**Precise next acceptance route.** Use the retained primary/supplement/ENA crosswalk and unchanged110literal cells to resolve specimen-owned site, selected chronology and use scope; keep all unresolved context refused.

**Negative or refused result.** Three aurochs remain distinct from the domestic-cattle project label; all eleven sample locality/date/point decisions remain unresolved or refused. The original paper review identified_not_promoted state is historical; current catalogue linkage is encoded.

**Matched denominator.** 11 BioSamples, eight domestic cattle/three aurochs; 18 paper specimens are a separate population. Literal context exports 110 cells: 109 shared strings/one present blank, zero formulas. All eleven remain point/context blocked.

- [Retained qualification evidence: docs/report/source-relations/dna-scope/galician-cattle-samples/report.json](report.json) (SHA-256 `2752a7ed321bbb6a0dffc02a4db20717e8c39a885f839844df42237af836e7d7`).

- [Retained qualification evidence: docs/report/source-relations/dna-scope/galician-cattle-samples/samples.csv](samples.csv) (SHA-256 `a423250b6e9d7f963bbda64f8ff483a906147b611ef32e51ec6a5745341adc39`).

- [Retained qualification evidence: reports/science/source-cohorts/galician-sample-context.csv](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/galician-sample-context.csv) (SHA-256 `fb8d552cd807198397766459e6475de3ff085b20d9d32fe0e8c281994cd935d9`).

- [Canonical scientific account: reports/science/animal-sample-chronology.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-sample-chronology.md).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
