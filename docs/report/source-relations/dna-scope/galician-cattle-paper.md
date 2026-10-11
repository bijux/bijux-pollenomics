# Galician cattle primary-paper review

The [source review](galician-cattle-paper.json) identifies the primary
[PLOS One article](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0249537)
for BioProject `PRJNA705960`. The paper explicitly names that BioProject. Its
[dating supplement](https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0249537.s001&type=supplementary)
and [sequencing supplement](https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0249537.s002&type=supplementary)
were captured with the article under `artifacts/jobs/galician-cattle-paper/`.
The [2022 correction](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0269578)
corrects the third author's name. Eleven [ENA BioSample XML](https://www.ebi.ac.uk/ena/browser/api/xml/SAMN18106827)
records were captured under `artifacts/jobs/galician-cattle-paper/biosamples/`.
The report records byte counts, SHA-256 digests, original URLs, and the
governed ENA archive-metadata digest.

| Source population | Count | Species evidence |
| --- | ---: | --- |
| Dating supplement specimen rows | 18 | 15 *Bos taurus*, 3 *Bos primigenius* |
| Sequencing supplement paper labels | 11 | 8 `Bt_` labels, 3 `Bp_` labels |
| ENA BioSample accessions for the BioProject | 11 | 8 *Bos taurus*, 3 *Bos primigenius* source taxon rows |

These are **three distinct identity units**. Each source-owned ENA BioSample
alias matches exactly one label in the paper dating supplement after
punctuation normalization; the report retains all eleven accession, alias,
paper-row, specimen-code, and species pairs. Every pair agrees on source
species. This establishes the sample identity crosswalk but does not promote a
sample to the product.

The current project catalog is owned by *Bos taurus* and its primary-paper
field remains unpinned. Three of its eleven archive samples are source-owned
*Bos primigenius*. Promoting the paper link without correcting mixed-species
ownership would hide a real source conflict. This review therefore records
the paper as an identified source candidate, while leaving species assignment,
locality, chronology, and point admission unchanged. The Galician project
supplies no Nordic sample by itself.

## Reproduce

From the repository root, with the captured official files retained under
`artifacts/jobs/galician-cattle-paper/`, run:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.galician_cattle_review \
  --repository . --capture artifacts/jobs/galician-cattle-paper \
  --output artifacts/jobs/galician-cattle-paper/reproduction.json
```

The producer checks the article DOI and BioProject, correction scope, both
supplement row populations, eleven unique archive accessions, and the eleven
source-owned BioSample aliases. It refuses a missing or colliding paper alias,
paper/archive taxonomy disagreement, or a changed source identity. Five
focused regressions cover the identity and refusal rules.
