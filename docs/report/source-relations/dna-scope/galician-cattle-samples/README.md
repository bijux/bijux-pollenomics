# Galician cattle sample species

The PRJNA705960 BioProject mixes domestic cattle and aurochs. Its project
catalog remains headed `Bos taurus`, while the [sample master](../../../../../data/adna/governance/source_library/projects/PRJNA705960/sample_master.json)
now keeps each BioSample's ENA taxon: eight `Bos taurus` (tax ID 9913) and
three `Bos primigenius` (tax ID 9909). The three aurochs retain
`project_species_mismatch`; the project label is not used to recast them as
domestic cattle. Stable BioSample IDs are unchanged.
The curated and [normalized sample records](../../../../../data/adna/species/bos_taurus/normalized/sample_records.json)
carry the same 8/3 distinction; all 11 retain `sample_context_blocked`
publication status.

The [row review](samples.csv) reconciles all 11 ENA accessions with the
retained PLOS paper sample labels through source-owned ENA BioSample aliases.
The [machine-readable report](report.json) binds the earlier paper crosswalk
and its 16 primary capture files by SHA-256. The article's dating table lists
18 specimens; the sequenced sample mapping and ENA capture each contain the
same 11 distinct BioSamples. The source capture identifies the paper, but its
project-level paper linkage has not been promoted into the governed source
library.

Species ownership alone does not establish a mappable locality or comparable
chronology. All 11 sample-master locality, coordinate, and chronology fields
remain empty. The paper labels, specimen codes, and age-like strings in the
capture are review evidence only; none becomes an admitted site, date, Nordic
observation, or atlas point through this change.
