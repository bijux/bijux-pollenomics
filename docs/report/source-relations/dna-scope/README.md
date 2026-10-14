# Human and animal ancient-DNA source scope

The [source-bound review](report.json) checks the current AADR human release and
animal ancient-DNA point surface for identity, chronology, source lineage, and
claim separation. Its six governed JSON inputs and eleven animal source
artifacts are bound by byte counts and SHA-256 digests. The producer also
rechecks all three AADR captured-input digests declared by the human
accountability review.

| Population | Unit and current count | Authority limit |
| --- | --- | --- |
| AADR v66 | 51,005 annotation rows across 1240K and HO; 27,755 Genetic IDs | Source accountability only; no scientific or genotype-analysis admission |
| Animal foundation | 1,468 final sample rows | Preparation population; validation is not wholly passing |
| Animal point surface | 170 features backed by 331 distinct sample IDs | 117 domesticated-core and 53 wild/progenitor-context features; neither is pollen |
| Nordic animal subset | 8 locality features backed by 12 sample IDs | Geographic subset of the animal point surface, not a separate sample census |

All 170 animal features have unique feature IDs, distinct sample IDs,
sample/site/project identity consistent with the point-accountability ledger,
paper DOI, source locator, native chronology text, and explicit dating basis.
Their chronology evidence classes remain separate: 129 direct radiocarbon, 35
historical/recent, three archaeological context, two modeled sample dates,
and one broad-period label. The 170 features use nine project/paper pairs and
eleven present source artifacts. The review does not turn a broad or contextual
date into a direct radiocarbon date.

The [foundation validation](../../animal_foundation_validation.json) still
fails its paper-linkage check for **11 PRJNA705960 sample rows**. A separate
[primary-paper review](galician-cattle-paper.md) now identifies the DOI and
reconciles all eleven source-owned BioSample aliases to paper labels, while
retaining the mixed *Bos taurus*/*Bos primigenius* project conflict. The
paper link has not been promoted into the project catalog. Two pig point
features name alternative evidence paths where the supplementary workbook is
present but the named project archive HTML is absent. Their exact feature IDs
and source-path status are in the machine-readable report. A missing alternate
path is recorded as a lineage gap; no substitute path or paper was invented.
The point-accountability ledger passes for its 170 features, but that does
not clear the broader 1,468-row foundation or qualified source review.

No cross-source association, pollen evidence, or scientific completion is
admitted by this review. Human and animal denominators, source versions,
chronology bases, and publication routes remain distinct.

## Reproduce

From the repository root, write a new result under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.dna_scope_review \
  --repository . --output artifacts/jobs/dna-source-scope/reproduction.json
```

Six focused source-scope regressions, strict mypy, and Ruff checks passed. The
producer refuses changed AADR raw digests, duplicate
animal sample identities, missing point accountability, missing chronology
basis, or a point whose source artifact has no present path.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native DNA specimen/publication/chronology scope and unsupported ecological or pollen extension.

**Supported claim.** The retained scope report separates AADR v66 annotations from animal aDNA project and point evidence.

**Unsupported claim.** Its historical 170-feature/331-sample animal population and dating classes are not the current horse-qualified atlas population; neither DNA family is pollen evidence.

**Actual verification performed.** Read the retained scope JSON and its historical input pins alongside the current animal capability account; no acquisition, genotype analysis or source producer was rerun.

**Remaining input or review.** A current scope-producer regeneration and sample-owned lineage review remain required after the horse source-age refusals.

**Cause category.** Historical source snapshot and unresolved biological/chronological admission.

**Consequence.** The old locality/evidence-class totals cannot certify current map scope or cross-source comparison.

**Precise next acceptance route.** Regenerate the governed DNA scope consumer from the qualified animal foundation, retain its predecessor, and review the eleven Galician paper-link rows.

**Negative or refused result.** Both human scientific admission and cross-source/pollen admission are false; foundation validation is false.

**Matched denominator.** Retained AADR: 51,005 annotation rows/27,755 Genetic IDs; retained animal: 1,468 foundation rows, 170 historical locality features/331 sample IDs; no new observations.

Qualified authored reader SHA-256: `bbe8a1e307d4c94803e7a60377a293760b16c9c9a6526d43e0f8a15646ade0c6`.

- [Retained qualification evidence: docs/report/source-relations/dna-scope/report.json](report.json) (SHA-256 `b44651d55f6cb74e833fd2e508144f08647c164ae72931b0f8c19c695f598a81`).

- [Retained qualification evidence: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md) (SHA-256 `3a0a899e96cfe7d95bdef41012516f39ce2b68606212efecafe1d909b6ccd045`).

- [Canonical scientific account: reports/science/animal-sample-chronology.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-sample-chronology.md) (source SHA-256 `0f4b689193ff2e872be0155dc77e48be083f917812248c6b29cb6b364c390545`).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md) (source SHA-256 `3a0a899e96cfe7d95bdef41012516f39ce2b68606212efecafe1d909b6ccd045`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
