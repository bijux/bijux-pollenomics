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

**Supported claim.** The Galician sample account preserves eight Bos taurus and three Bos primigenius through normalized and curated consumers.

**Unsupported claim.** Species resolution does not resolve locality, calibrated sample chronology, Nordic relevance or point eligibility.

**Actual verification performed.** Read report.json and the eleven-row samples.csv, comparing curated species, context-blocked posture and absent sample context; no consumer regeneration.

**Remaining input or review.** Source-owned site and date evidence, project-paper linkage promotion and scoped context review remain absent.

**Cause category.** Sample identity is resolved more narrowly than spatial and temporal context.

**Consequence.** All eleven remain outside atlas points despite their resolved sample species.

**Precise next acceptance route.** Qualify each sample-owned locality/date and project-paper relation, then rerun the scoped sample consumer.

**Negative or refused result.** All eleven have sample_context_blocked; no atlas point, sample chronology or site is admitted.

**Matched denominator.** 11 BioSamples/curated samples, 8 domestic and 3 aurochs; 18 paper specimens are a distinct denominator.

Qualified authored reader SHA-256: `be02f80f46a3f2b6dbe6bb447d72e24be449f3d665021bc95ad07bcede6cf691`.

- [Retained qualification evidence: docs/report/source-relations/dna-scope/galician-cattle-samples/report.json](report.json) (SHA-256 `8100babee63c9e86912d097ac5ecebc048f4db4c5b1bdfce8f09120a660fdd9b`).

- [Retained qualification evidence: docs/report/source-relations/dna-scope/galician-cattle-samples/samples.csv](samples.csv) (SHA-256 `a423250b6e9d7f963bbda64f8ff483a906147b611ef32e51ec6a5745341adc39`).

- [Canonical scientific account: reports/science/animal-sample-chronology.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-sample-chronology.md) (source SHA-256 `0f4b689193ff2e872be0155dc77e48be083f917812248c6b29cb6b364c390545`).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md) (source SHA-256 `fdca2e23ab7891334135a9b72600149ec44ac2b4c8f5e7452da1ccec7289281d`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
