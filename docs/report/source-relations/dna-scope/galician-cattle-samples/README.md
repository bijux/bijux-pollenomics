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
same 11 distinct BioSamples. The source capture identifies the paper, but its
project-level paper linkage has not been promoted into the governed source
library.

The separately requested [literal context table](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/galician-sample-context.csv)
now exposes all 110 cells on those eleven crosswalk rows, including native site,
radiocarbon, calibrated-BP, calendar, dating-lab and contextual strings. The
[chronology account and reproduction command](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-sample-chronology.md#literal-galician-sample-context)
explain cell types, the present blank `G27` and the modern-carbon sample whose
label must not become 60 BP or a Cobas locality. Original species outputs and
all site/date/point admission decisions are unchanged.

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

**Actual verification performed.** The opted-in consumer ran at 85de3133f, exit zero in 2.30 s, preserving 110 literal cells for eleven BioSamples. An independent original-workbook DOM check confirms all cells, headers, types, values, blank/formula states and crosswalk rows. Fifty controlled cases and one native original-writer test pass with configured lint/types. Default report/CSV bytes remain unchanged.

**Remaining input or review.** Literal source site/date fields are now available for review. Field-specific chronology interpretation, qualified site assignment, project-paper linkage promotion and scoped context approval remain unresolved.

**Cause category.** Sample identity is resolved more narrowly than spatial and temporal context.

**Consequence.** All eleven remain outside atlas points despite their resolved sample species.

**Precise next acceptance route.** Qualify each sample-owned locality/date and project-paper relation, then rerun the scoped sample consumer.

**Negative or refused result.** All eleven have sample_context_blocked; no atlas point, sample chronology or site is admitted.

**Matched denominator.** 11 BioSamples, eight domestic cattle/three aurochs; 18 paper specimens are a separate population. Literal context exports 110 cells: 109 shared strings/one present blank, zero formulas. All eleven remain point/context blocked.

- [Retained qualification evidence: docs/report/source-relations/dna-scope/galician-cattle-samples/report.json](report.json) (SHA-256 `8100babee63c9e86912d097ac5ecebc048f4db4c5b1bdfce8f09120a660fdd9b`).

- [Retained qualification evidence: docs/report/source-relations/dna-scope/galician-cattle-samples/samples.csv](samples.csv) (SHA-256 `a423250b6e9d7f963bbda64f8ff483a906147b611ef32e51ec6a5745341adc39`).

- [Retained qualification evidence: reports/science/source-cohorts/galician-sample-context.csv](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/galician-sample-context.csv) (SHA-256 `fb8d552cd807198397766459e6475de3ff085b20d9d32fe0e8c281994cd935d9`).

- [Canonical scientific account: reports/science/animal-sample-chronology.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-sample-chronology.md).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
