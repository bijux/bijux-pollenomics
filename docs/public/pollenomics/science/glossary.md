---
title: Scientific Concepts
audience: reader
type: reference
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-10-03
---

# Scientific concepts

Use these definitions when reading the [results](results.md), the
[source prerequisites](sources.md#before-a-core-can-enter-lra), and an atlas
record. A term names the quantity or evidence role; the linked report supplies
its actual inputs and permitted interpretation.

## Counts, fractions and time

| Term | Meaning in these reports |
| --- | --- |
| Native pollen count | The source's recorded count for a sample and taxon. Retained counts can include excluded or unmapped taxa. A percentage alone does not establish an integer count. |
| Denominator | The total against which a fraction is calculated. All native pollen and an assigned taxon subtotal are different denominators; the report names which one it uses. |
| Closed taxon response | Fractions normalized over one declared taxon set. A closed response may omit substantial native count mass and cannot be read as all vegetation. |
| Taxon target | A declared destination concept for native labels. Assignment, exclusion and unmapped mass stay explicit; a text-label match alone does not qualify pollen productivity. |
| Age model | A source-specific mapping from depth or sample identity to age. An alternate model is retained separately until a model is selected for the intended analysis. |
| cal BP | Calendar years before 1950. A source window labeled BP still needs its own chronology qualification; its label alone does not establish a calibrated sample age. |
| Analysis bin | A declared age interval used to aggregate observations. A point age can select a bin while the source age interval crosses its boundary. Contained-age sensitivity retains only samples whose support fits the declared bin. |

Read [coverage and naming](../../pollenomics-data/overview/coverage-and-naming.md)
for observation units, unresolved denominators and country dimensions. Read
[results and model use](results.md) for the separate point-age and contained-age
comparisons. Marginal age bounds do not supply a joint chronology posterior.

## Predictions and reconstructions

| Term | Meaning in these reports |
| --- | --- |
| Direct pollen prediction | Prediction of the declared observed-pollen response from training pollen. Its target is pollen composition, so its score does not measure vegetation accuracy. |
| LRA | Landscape Reconstruction Algorithm, comprising regional REVEALS and local LOVE reconstruction. Each run needs qualified pollen, chronology, basin, taxon, productivity and transport inputs. |
| REVEALS | The regional vegetation reconstruction component. A retained LandClim grid cell is an existing modeled result; displaying it does not rerun the reconstruction. |
| LOVE | The local vegetation reconstruction component, conditional on its regional contribution and declared model inputs. The repository's numerical profile and optimizer settings belong to the named run. |
| PPE | Pollen productivity estimate for a declared taxon and parameter source. It is a model input, rather than a measured vegetation outcome for the target lake. |
| Fall speed and transport | Inputs describing pollen settling and dispersal in the chosen model. Agreement on one implementation's arithmetic does not select universally suitable parameters. |

The [papers and evidence roles](papers.md) connect these method names to their
source accounts. The [model-use results](results.md#model-settings) state the
settings and refusal conditions of the existing development calculations.

## Evidence and uncertainty

| Term | Meaning in these reports |
| --- | --- |
| MAE | Mean absolute error on a named response and aggregation unit. An equal-bin mean weights supported bins equally; it does not weight every sample or country equally. |
| Hellinger distance | A distance between the declared pollen compositions. It describes a different discrepancy from MAE, so two methods can rank differently under the two metrics. |
| Standard error | A source or model uncertainty summary for the named estimate. Individual-cell standard errors are not a pooled country uncertainty or a confidence interval. |
| Source correspondence | Agreement on specified source inputs, arithmetic or output bytes. Its claim is limited to that comparison. |
| Withheld target | A target excluded from the named training set. Prior source or outcome inspection is reported separately and can limit an independence claim. |
| Measured vegetation reference | A separate measured outcome with matching site, time, taxa and spatial support. A modeled grid or nearby archaeological record is a different evidence role. |
| Refusal | An explicit unsupported or missing-input outcome retained with its reason. A refused calculation is not a zero measurement. |

Start the [atlas walkthrough](../interfaces/atlas-walkthrough.md) to inspect
one modeled-context cell, trace its source and reproduce its bounded summary.
The walkthrough keeps software behavior, source custody and scientific fitness
as separate claims.
