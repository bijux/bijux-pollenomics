# Galician cattle primary-paper review

The [source review](galician-cattle-paper.json) identifies the primary
[PLOS One article](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0249537)
for BioProject `PRJNA705960`. The paper explicitly names that BioProject. Its
[dating supplement](https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0249537.s001&type=supplementary)
and [sequencing supplement](https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0249537.s002&type=supplementary)
are retained with the article under `data/adna/review/galician_cattle/`.
The [2022 correction](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0269578)
corrects the third author's name. Eleven [ENA BioSample XML](https://www.ebi.ac.uk/ena/browser/api/xml/SAMN18106827)
records are retained under `data/adna/review/galician_cattle/biosamples/`.
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
species. This establishes the sample identity crosswalk without resolving
sample locality or chronology or admitting an atlas point.

The current project catalog is owned by *Bos taurus* and its primary-paper
field remains unpinned. Three of its eleven archive samples are source-owned
*Bos primigenius*. Promoting the paper link without correcting mixed-species
ownership would hide a real source conflict. This review records the paper as
an identified source candidate while retaining the sample-owned 8/3 taxonomy.
Locality, chronology, and point admission remain unresolved. The Galician
project supplies no Nordic sample by itself.

## Reproduce

From the repository root, after `make root-check-env`, run:

```sh
PYTHONPATH=packages/bijux-pollenomics-dev/src:packages/bijux-pollenomics/src \
PYTHONDONTWRITEBYTECODE=1 artifacts/root/check-venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.galician_cattle_review \
  --repository . \
  --output artifacts/release-verification/galician-cattle-paper-reproduction.json
```

The producer checks the article DOI and BioProject, correction scope, both
supplement row populations, eleven unique archive accessions, and the eleven
source-owned BioSample aliases. It refuses a missing or colliding paper alias,
paper/archive taxonomy disagreement, or a changed source identity. Five
focused regressions cover the identity and refusal rules.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native DNA specimen/publication/chronology scope and unsupported ecological or pollen extension.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/animal-sample-chronology.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-sample-chronology.md).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
