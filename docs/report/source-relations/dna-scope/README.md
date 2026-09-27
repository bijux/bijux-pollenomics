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
| Animal foundation | 1,450 final sample rows | Preparation population; validation is not wholly passing |
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
fails its paper-linkage check for **11 PRJNA705960 sample rows**. Two pig point
features name alternative evidence paths where the supplementary workbook is
present but the named project archive HTML is absent. Their exact feature IDs
and source-path status are in the machine-readable report. A missing alternate
path is recorded as a lineage gap; no substitute path or paper was invented.
The point-accountability ledger passes for its 170 features, but that does
not clear the broader 1,450-row foundation or qualified source review.

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
