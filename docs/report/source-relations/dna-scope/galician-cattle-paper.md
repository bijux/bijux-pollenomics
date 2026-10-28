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

The current project catalogue retains its *Bos taurus* heading and now links
the primary paper through its explicit BioProject statements. All three
*Bos primigenius* samples remain source-owned aurochs with a visible project
species mismatch. The original source-review JSON keeps its historical
`identified_not_promoted` posture; the current source library separately binds
the existing article, correction and two supplements in place. The current
[sample report](galician-cattle-samples/report.json) records catalogue linkage
without resolving locality, chronology or point admission. The Galician project
supplies no Nordic sample by itself.

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

**Supported claim.** Eleven source-owned ENA aliases identify the eleven sequenced Galician cattle specimens in the primary paper.

**Unsupported claim.** The project-wide Bos taurus label does not identify all sample species, and identifying the paper does not admit site or chronology.

**Actual verification performed.** Read the paper-review JSON, its eleven alias crosswalks, specimen counts and author-name-only correction scope; no paper recapture or dating calculation. Current default report from988d1ff12 passes2.126s/RSS88096768B; only seven typed metadata leaves change, eleven-row CSV and all16source pins remain exact. Catalogue linkage is source curation, not sample context admission.

**Remaining input or review.** Current catalogue linkage is encoded. Sample-owned locality, chronology, whole-project deposition scope, scientific use and independent qualified interpretation remain unresolved.

**Cause category.** Project-level species and sample-level source taxonomy differ.

**Consequence.** Three aurochs must remain visible instead of inheriting a domestic-cattle project label.

**Precise next acceptance route.** Use the retained primary/supplement/ENA crosswalk and unchanged110literal cells to resolve specimen-owned site, selected chronology and use scope; keep all unresolved context refused.

**Negative or refused result.** Three aurochs remain distinct from the domestic-cattle project label; all eleven sample locality/date/point decisions remain unresolved or refused. The original paper review identified_not_promoted state is historical; current catalogue linkage is encoded.

**Matched denominator.** 18 dating-table specimens versus 11 sequenced labels/BioSamples: 8 Bos taurus and 3 Bos primigenius.

- [Retained qualification evidence: docs/report/source-relations/dna-scope/galician-cattle-paper.json](galician-cattle-paper.json) (SHA-256 `34f3899c37c437d55c8a891d834a7f119edf4ede46f076da03160e9f31a8b567`).

- [Canonical scientific account: reports/science/animal-sample-chronology.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-sample-chronology.md).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
