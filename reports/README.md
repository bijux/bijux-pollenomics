# Research reports

Start with the scientific question, then follow the linked result to its input
identity, producer, score table and limitations. Most detailed governed outputs
currently live under `docs/report/`. The Bjäresjösjön context screen and
publication PFT crosswalk live beside their root studies. This library is the
reader entry point while other producer paths are migrated by domain.

The [claim-to-evidence index](evidence-index.md) goes directly from each
headline result to its numeric table, input identity, producer and scope.
Run `python3 reports/verify.py` after changing a scientific report or its
governed source. It checks the root page inventory, local links and the
selected result identities in `source-lock.json`; review changed claims before
updating that lock.

| Question | Read first | Evidence boundary |
| --- | --- | --- |
| What can the Nordic pollen data predict? | [Pollen prediction synthesis](science/pollen-prediction.md), [DK/FI/NO author-axis study](science/denmark-finland-norway-author-pollen.md), [Swedish author-axis study](science/sweden-author-pollen.md), [Sweden-only versus four-country training](science/sweden-training-scope.md), [age and distance sensitivity](science/sweden-spatiotemporal-sensitivity.md) | Observed pollen, prior-exposed development; no independent vegetation score. |
| Which cohorts and source fields are fit for each analysis? | [Source cohort account](science/source-cohorts.md) | Four-country count mass and LRA source gates remain separate. |
| Has real LRA been run and compared? | [Constrained English LOVE study and basin-radius sensitivity](science/english-lra-pollen-prediction.md) | 14 of 15 source folds predicted; one optimizer refusal; target-basin forward sensitivity holds fitted vegetation fixed; English author examples only. |
| Which model and parameters should I use? | [Model-use guide](science/model-use.md), [Nordic training search](science/nordic-observed-pollen-selection.md), [matched country transfer](science/nordic-observed-pollen-transfer.md) | Choices are conditional on target, source admission, cohort, support and metric. |
| Do the numerical methods reproduce the source? | [Method correspondence](science/method-correspondence.md), [original R reference](../docs/report/method-certification/original-r-reference/README.md) | Source-specific numerical parity under declared profiles; not ecological accuracy. |
| Does the implementation reproduce the paper and archive? | [Publication correspondence](science/publication-correspondence.md), [published-window provenance](../docs/report/publication-replay/landclim-published-window-provenance/README.md) | Matched and divergent source revisions remain explicit. |
| Which source inputs are admissible? | [Swedish source and pollen account](science/nordic-pollen-study.md), [Abborrtjärnen method](../docs/report/source-relations/neotoma/abbo-published-method/README.md), [Solsø lineage](../docs/report/countries/denmark/solsoe-source-lineage/README.md) | Pollen-only, LRA and measured-vegetation prerequisites differ. |
| What is established for HYDE and aDNA? | [HYDE source account](science/hyde-cropland-source-account.md), [reindeer published appendix](science/reindeer-appendix-correspondence.md), [animal sample chronology decision](science/animal-sample-chronology.md) | Source accounting and chronology do not by themselves validate vegetation or model skill. |
| Can nearby archaeology contextualize a named lake? | [Our Bjäresjö source decision](science/bjaresjo-context.md) | We matched the modern lake and SEAD display intervals; physical-core and ecological joins remain refused. |
| Why did we keep the LRA engine separate? | [Our distribution decision](architecture/lra-distribution.md) | We checked a single optional-extra install and kept the engine boundary; public release and rights review remain separate. |

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
