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

Species ownership alone does not establish a mappable locality or comparable
chronology. All 11 sample-master locality, coordinate, and chronology fields
remain empty. The paper labels, specimen codes, and age-like strings in the
capture are review evidence only; none becomes an admitted site, date, Nordic
observation, or atlas point through this change.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native DNA specimen/publication/chronology scope and unsupported ecological or pollen extension.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/animal-sample-chronology.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-sample-chronology.md).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
