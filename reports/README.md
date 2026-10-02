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
| What can the Nordic pollen data predict? | [Pollen prediction synthesis](science/pollen-prediction.md), [DK/FI/NO author-axis study](science/denmark-finland-norway-author-pollen.md), [Swedish author-axis study](science/sweden-author-pollen.md), [Sweden-only versus four-country training](science/sweden-training-scope.md), [age and distance sensitivity](science/sweden-spatiotemporal-sensitivity.md), [chronology-block comparison](science/sweden-chronology-block.md) | Observed pollen, prior-exposed development; no independent vegetation score. |
| What did fixed predictors do at newly scored Swedish lakes? | [Sämbosjön observed-pollen evaluation](science/sambosjon-direct-pollen.md), [Lilla Gloppsjön observed-pollen transfer](science/lilla-gloppsjon-direct-pollen.md) | Two separately scored physical sites on a closed 16-label response; prior source-screen exposure and distinct age support limit independent and pooled claims. |
| How did fixed predictors transfer to further Swedish lakes? | [Three-lake Swedish transfer](science/sweden-lake-transfer.md) | Gilltjärnen, Lake Avegöl and Flinkasjön add 63 scored bins; three-site development evidence only. |
| Which cohorts and source fields are fit for each analysis? | [Source cohort account](science/source-cohorts.md) | Four-country count mass and LRA source gates remain separate. |
| Which AADR human IDs reach the four country products? | [Nordic AADR entity account](science/aadr-nordic-entities/README.md) | 1,325 source IDs reconcile to 1,231 country rows and 94 missing-coordinate exclusions; no scientific or map admission. |
| Which animal sample IDs reach the map? | [Animal entity account](science/animal-entity-capability/README.md) | The 1,468 normalized IDs partition into 331 mapped and 1,137 map-excluded samples; scientific admission remains open. |
| Which Norwegian core has the strongest LRA source lineage? | [Dalmutladdo source correspondence](science/dalmutladdo-lra-input/README.md) | 72 samples and all 11 radiocarbon source controls match; conflicting areas and missing age-specific basin/count/PPE evidence keep LRA admission at zero. |
| Which Finnish core has the strongest LRA source lineage? | [Laihalampi source correspondence](science/laihalampi-lra-input/README.md) | 150 source samples and the 25.5 ha reported area correspond; selected ages, dated basin and analytical use remain open. |
| Has real LRA been run and compared? | [English analytical refusal](science/english-analytical-love/README.md), [constrained LOVE study and basin-radius sensitivity](science/english-lra-pollen-prediction.md) | The 31-taxon analytical request refused every fold; the separate 30-taxon constrained route predicted 14 of 15 folds. English author examples only. |
| Which model and parameters should I use? | [Model-use guide](science/model-use.md), [Nordic training search](science/nordic-observed-pollen-selection.md), [matched country transfer](science/nordic-observed-pollen-transfer.md) | Choices are conditional on target, source admission, cohort, support and metric. |
| Do the numerical methods reproduce the source? | [Method correspondence](science/method-correspondence.md), [analytical LOVE ring result](science/analytical-love-ring-sensitivity/README.md), [author REVEALS-to-LOVE interface](science/reveals-love-interface/README.md), [original R reference](../docs/report/method-certification/original-r-reference/README.md) | Source-specific numerical parity, ring sensitivity and draw transfer under declared profiles; not ecological accuracy. |
| What do the independent synthetic landscape challenges establish? | [Host-interface challenge](science/synthetic-host-challenge/README.md), [development parameter sweep](science/synthetic-model-selection/README.md), [governed reconstruction controls](../docs/report/synthetic-validation/reconstruction/README.md) | Calculation and refusal diagnostics only; transport mismatch prevents ecological or real-core parameter claims. |
| What do the six retained synthetic score protocols show? | [Six-protocol metric account](science/synthetic-protocol-metrics/README.md) | 39 requested, 31 scored and eight failed units per target; four local pollen scores are in-sample. The archived profile has a reader compatibility limit. |
| What does the LandClim II paper establish, and how far does our reproduction reach? | [LandClim II paper account](science/landclim-paper.md) | Regional published reconstruction, two-grid numerical parity and an unresolved exact-window archive gap have separate denominators; historical reproduction and independent review remain open. |
| Does the implementation reproduce the paper and archive? | [Publication correspondence](science/publication-correspondence.md), [author method profile](science/publication-correspondence/author-method-profile.md), [two-grid R/native reexecution](science/publication-correspondence/author-example-reexecution.md), [17-site author-example replay](science/publication-correspondence/author-example-site-replay.md), [published-window provenance](science/publication-correspondence/published-window-provenance.md) | We bind and reproduce the released example calculation, then quantify its exact-window archive difference; historical input identity and transformations remain open. |
| Which source inputs are admissible? | [Swedish source and pollen account](science/nordic-pollen-study.md), [Abborrtjärnen method](science/abborrtjarnen-source-method.md), [our Solsø LRA decision](science/solsoe-lra-input.md) | Pollen-only, LRA and measured-vegetation prerequisites differ. |
| What do measured vegetation sources establish? | [Vegetation-reference decision](science/vegetation-reference.md) | Forest plot, historical-map and published-figure evidence support distinct bounded findings; LandClim grid lineage does not supply an independent measurement, and zero pairs validate our predictions. |
| What is established for HYDE and aDNA? | [HYDE source account](science/hyde-cropland-source-account.md), [reindeer published appendix](science/reindeer-appendix-correspondence.md), [animal sample chronology decision](science/animal-sample-chronology.md) | Source accounting and chronology do not by themselves validate vegetation or model skill. |
| Can nearby archaeology contextualize a named lake? | [Our Bjäresjö source decision](science/bjaresjo-context.md) | We matched the modern lake and SEAD display intervals; physical-core and ecological joins remain refused. |
| Do two Swedish lake pollen series move together? | [Bussjösjön and Bökesjön trajectory](science/sweden-lake-trajectory.md) | Observed pollen directions sometimes agree and sometimes contradict; independent SEAD context is incomparable as a vegetation measure, so land use cannot be concluded. |
| Why did we keep the LRA engine separate? | [Our distribution decision](architecture/lra-distribution.md) | We checked a single optional-extra install and kept the engine boundary; public release and rights review remain separate. |
| Why is the LRA backend still Python? | [Our native-backend decision](architecture/native-backend.md) | The measured C++ forward batch failed its latency gate; a future kernel has explicit source-parity, build and release conditions. |
| Which LRA source and prototype functions did we adopt? | [Our source-adoption decision](architecture/lra-source-adoption/README.md) | Original R, candidate Python and adopted engine have separate identities, notices and function dispositions. |

The [open research needs](needed/README.md) list exact evidence questions that
would change current conclusions. An answered question moves into its owning
report and is removed from that open list.

The [report ownership decision](architecture/ownership.md) explains how this
reader library, governed numeric outputs, the website and source-locked
presentations share results without making disposable runs part of the product.

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
