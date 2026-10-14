# Human and animal ancient-DNA source scope

The [source-bound review](report.json) checks the current AADR human release and
animal ancient-DNA point surface for identity, chronology, source lineage, and
claim separation. Its six governed JSON inputs and ten animal source
artifacts are bound by byte counts and SHA-256 digests. The producer also
rechecks all three AADR captured-input digests declared by the human
accountability review.

| Population | Unit and current count | Authority limit |
| --- | --- | --- |
| AADR v66 | 51,005 annotation rows across 1240K and HO; 27,755 Genetic IDs | Source accountability only; no scientific or genotype-analysis admission |
| Animal foundation | 1,468 final sample rows | Preparation population; validation is not wholly passing |
| Animal point surface | 165 features backed by 322 distinct sample IDs | 117 domesticated-core and 48 wild/progenitor-context features; neither is pollen |
| Nordic animal subset | 8 locality features backed by 12 sample IDs | Geographic subset of the animal point surface, not a separate sample census |

All 165 animal features have unique feature IDs, distinct sample IDs,
sample/site/project identity consistent with the point-accountability ledger,
paper DOI, source locator, native chronology text, and explicit dating basis.
Their chronology evidence classes remain separate: 124 direct radiocarbon, 35
historical/recent, three archaeological context, two modeled sample dates,
and one broad-period label. The 165 features use eight project/paper pairs and
ten present source artifacts. The review does not turn a broad or contextual
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
The point-accountability ledger passes for its 165 features, but that does
not clear the broader 1,468-row foundation or qualified source review.

Five PRJEB31613 horse points and their nine sample memberships are excluded
from this current dated point surface because their source age support was
not qualified. The 245 normalized PRJEB31613 sample rows and original source bytes remain
retained. The preceding 170-feature/331-sample scope is preserved in its
original report revision; it is not the current point denominator.

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

**Supported claim.** The current source-bound scope consumer separates AADR v66 annotation accountability from animal aDNA foundation and current dated point evidence.

**Unsupported claim.** Source accountability and dated point membership do not establish genotype-analysis admission, biological taxon truth, pollen evidence, vegetation accuracy or cross-source scientific comparability.

**Actual verification performed.** Two actual ordinary configured producers regenerated this scope report from its six current governed inputs. Independent source comparison confirms 165 unchanged retained point rows and 322 unique sample IDs; exactly five PRJEB31613 points and nine memberships were removed from the historical 170/331 surface. Human-source values are unchanged and all current input hashes/bytes were checked. Native producers returned zero; old tracked-byte checkers refused the correctly changed output. No acquisition, genotype analysis or qualified human source review was performed.

**Remaining input or review.** Eleven Galician foundation paper-link rows, source-owned chronology and biological identity decisions, and qualified scientific/use review remain unresolved. Removal of unqualified-age points does not clear the 1,468-row foundation.

**Cause category.** Current source-population reconciliation with unresolved biological, chronological and scientific admission.

**Consequence.** Use the current 165-feature/322-sample dated surface while retaining all 1,468 foundation rows and excluded original source evidence. Neither source-family denominator is a pollen cohort or an accuracy population.

**Precise next acceptance route.** Review and adopt the actual regenerated scope and its current source identities; qualify the eleven Galician paper-link rows and each intended chronology/biological use separately. Re-execute this consumer if its governed source inputs change.

**Negative or refused result.** Both human scientific admission and cross-source/pollen admission are false; foundation validation is false.

**Matched denominator.** AADR: 51,005 annotation rows/27,755 Genetic IDs. Animal: 1,468 foundation rows, 165 locality features/322 distinct sample IDs, eight project/paper pairs and ten point-referenced source artifacts; Nordic subset eight features/12 sample IDs. No new observations.

Qualified authored reader SHA-256: `85cad1a5745a9734f5bd72c2ef8e26ffcdd51aa78282b57b862cd4732f546f8b`.

- [Retained qualification evidence: docs/report/source-relations/dna-scope/report.json](report.json) (SHA-256 `dd88281f34bd1c685b4abda3ba46565c704d9769849d17f83eab97f805ae653d`).

- [Retained qualification evidence: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md) (SHA-256 `fdca2e23ab7891334135a9b72600149ec44ac2b4c8f5e7452da1ccec7289281d`).

- [Canonical scientific account: reports/science/animal-sample-chronology.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-sample-chronology.md) (source SHA-256 `0f4b689193ff2e872be0155dc77e48be083f917812248c6b29cb6b364c390545`).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md) (source SHA-256 `fdca2e23ab7891334135a9b72600149ec44ac2b4c8f5e7452da1ccec7289281d`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
