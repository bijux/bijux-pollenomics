# Research reports

Start with the scientific question, then follow the linked result to its input
identity, producer, score table and limitations. The detailed governed outputs
currently live under `docs/report/`; this root library is the reader entry point
while their producer paths are migrated by domain.

| Question | Read first | Evidence boundary |
| --- | --- | --- |
| What can the Nordic pollen data predict? | [Pollen prediction synthesis](science/pollen-prediction.md), [four-country author-axis study](../docs/report/regions/nordic/author-target-pollen/README.md) | Observed pollen, prior-exposed development; no independent vegetation score. |
| Which cohorts and source fields are fit for each analysis? | [Source cohort account](science/source-cohorts.md) | Four-country count mass and LRA source gates remain separate. |
| Has real LRA been run and compared? | [Constrained English LOVE study](../docs/report/pollen-reconstruction/author-lra-constrained/README.md) | 14 of 15 source folds predicted; one optimizer refusal; English author examples only. |
| Do the numerical methods reproduce the source? | [Method correspondence](science/method-correspondence.md), [original R reference](../docs/report/method-certification/original-r-reference/README.md) | Source-specific numerical parity under declared profiles; not ecological accuracy. |
| Does the implementation reproduce the paper and archive? | [Publication correspondence](../docs/report/pollen-reconstruction/paper-correspondence.md), [published-window provenance](../docs/report/publication-replay/landclim-published-window-provenance/README.md) | Matched and divergent source revisions remain explicit. |
| Which source inputs are admissible? | [Swedish source and pollen account](../docs/report/pollen-reconstruction/README.md), [Abborrtjärnen method](../docs/report/source-relations/neotoma/abbo-published-method/README.md), [Solsø lineage](../docs/report/countries/denmark/solsoe-source-lineage/README.md) | Pollen-only, LRA and measured-vegetation prerequisites differ. |
| What is established for HYDE and aDNA? | [HYDE source account](../docs/report/regions/nordic/hyde-country-cropland/README.md), [reindeer published appendix](../docs/report/source-relations/dna-scope/reindeer-published-appendix.md) | Source accounting and chronology do not by themselves validate vegetation or model skill. |

The [open research needs](needed/README.md) list exact evidence questions that
would change current conclusions. An answered question moves into its owning
report and is removed from that open list.

The [report ownership map](architecture/ownership.md) records the existing
`docs/report/` size and path dependencies, and the proposed boundary for each
kind of material while report producers are migrated by domain.

## How to read a claim

Check its source and physical-site identity, count/taxon denominator, age and
spatial support, training exclusion, prediction publication identity, scored
coverage, uncertainty and source rights. A synthetic test, source-R parity,
observed-pollen prediction, LRA reconstruction and measured vegetation
comparison answer different questions. The linked report states which one it
supports.

The website publishes selected explanations under `docs/public/`. Governed
numeric tables, private source receipts and reproducibility detail stay with
their owned report until the report migration updates all consumers together.
