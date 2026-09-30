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
| Has real LRA been run and compared? | [English analytical refusal](science/english-analytical-love/README.md), [constrained LOVE study and basin-radius sensitivity](science/english-lra-pollen-prediction.md) | The 31-taxon analytical request refused every fold; the separate 30-taxon constrained route predicted 14 of 15 folds. English author examples only. |
| Which model and parameters should I use? | [Model-use guide](science/model-use.md), [Nordic training search](science/nordic-observed-pollen-selection.md), [matched country transfer](science/nordic-observed-pollen-transfer.md) | Choices are conditional on target, source admission, cohort, support and metric. |
| Do the numerical methods reproduce the source? | [Method correspondence](science/method-correspondence.md), [analytical LOVE ring result](science/analytical-love-ring-sensitivity/README.md), [original R reference](../docs/report/method-certification/original-r-reference/README.md) | Source-specific numerical parity and ring sensitivity under declared profiles; not ecological accuracy. |
| What do the independent synthetic landscape challenges establish? | [Host-interface challenge](science/synthetic-host-challenge/README.md), [development parameter sweep](science/synthetic-model-selection/README.md), [governed reconstruction controls](../docs/report/synthetic-validation/reconstruction/README.md) | Calculation and refusal diagnostics only; transport mismatch prevents ecological or real-core parameter claims. |
| Does the implementation reproduce the paper and archive? | [Publication correspondence](science/publication-correspondence.md), [two-grid R/native reexecution](science/publication-correspondence/author-example-reexecution.md), [17-site author-example replay](science/publication-correspondence/author-example-site-replay.md), [published-window provenance](../docs/report/publication-replay/landclim-published-window-provenance/README.md) | We reproduce the released example calculation and trace WHH05 from raw counts to its estimate; historical archive inputs and transformations remain open. |
| Which source inputs are admissible? | [Swedish source and pollen account](science/nordic-pollen-study.md), [Abborrtjärnen method](science/abborrtjarnen-source-method.md), [Solsø lineage](../docs/report/countries/denmark/solsoe-source-lineage/README.md) | Pollen-only, LRA and measured-vegetation prerequisites differ. |
| What is established for HYDE and aDNA? | [HYDE source account](science/hyde-cropland-source-account.md), [reindeer published appendix](science/reindeer-appendix-correspondence.md), [animal sample chronology decision](science/animal-sample-chronology.md) | Source accounting and chronology do not by themselves validate vegetation or model skill. |
| Can nearby archaeology contextualize a named lake? | [Our Bjäresjö source decision](science/bjaresjo-context.md) | We matched the modern lake and SEAD display intervals; physical-core and ecological joins remain refused. |
| Why did we keep the LRA engine separate? | [Our distribution decision](architecture/lra-distribution.md) | We checked a single optional-extra install and kept the engine boundary; public release and rights review remain separate. |
| Where did historical run material go? | [Our artifact custody decisions](architecture/artifact-custody.md), [LandClim author acquisition](architecture/artifact-custody/landclim-author-acquisition.md) | Exact private source and result custody precedes each bounded retirement. |

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
