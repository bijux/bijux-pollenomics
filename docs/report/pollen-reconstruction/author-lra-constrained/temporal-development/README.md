---
title: Temporal physical development and refused predictions
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-reporting
review_scope: independently admitted saved point-pollen results
---

# Which temporal physical predictions were actually eligible?

The frozen deterministic uniform-start LOVE profile produced no eligible target
predictions in TW4 and three spatial-method predictions for one target in TW6.
This is a negative and very limited development result. Native execution completed
successfully for both windows, but most complete training sets could not supply
admissible reconstructions. The run does not establish a reliable temporal cohort
or a general ranking of prediction methods.

## Observation units and populations

TW4 uses the source-declared calibrated-BP bin 750–1250 and TW6 uses 1750–2250.
These are source-declared 500-year supports; their reference epoch, calibration
model and age uncertainty remain unqualified here. Different windows are different estimands with different
eligible populations. No epoch conversion or calibrated chronology-uncertainty
propagation is inferred from these source labels.

| Window | Eligible sites | Logical requests | Distinct requests | Completed cache products | Optimizer-refused requests | Prediction slots | Predicted | Refused | Scored |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| TW4 | 13 | 143 | 23 | 20 | 3 | 39 | 0 | 39 | 0 |
| TW6 | 14 | 168 | 25 | 21 | 4 | 42 | 3 | 39 | 3 |

The 27 site-window representations are not 27 independent physical sites: site/core
identities persist across windows. Grids, repeats and periods remain ancestry.
All 17 original site availability dispositions remain bound to the admitted input
account. TW4 retains 22,064 counts after excluding 518 Filipendula counts from
22,582 native counts; TW6 retains 22,842 after excluding 167 from 23,009. The
retained parameter and count axis has 30 original ordered taxa. Unavailable sites
are unavailable observations, even where source-filled files contain zeros.

## Frozen physical policy and training separation

Both windows were frozen before the first post-freeze scoring access. The policy
uses the maintained deterministic optimized LOVE profile, uniform SLSQP starts,
seed 7, two local rings, one repeat, 300 optimizer iterations, 16,000 search
evaluations and tolerance 1e-8. The source-compatible named kernel is `gpm neutral`
with the `disqover-0.9.14-wrapper-v1` fall-speed profile. Local support ends at
1,000 m; the declared outer annulus extends to 10,000 m. The exact shared PPE,
PPE-SD and fall-speed values and scientific configuration are in [report.json](./report.json).
This is not the separate 32-start diagnostic, and no profile was selected from
these three scores.

Each whole-site fold excludes its own target group from regional and local
training. A train-only regional anchor and local predictors form exact numeric
request identities. One host batch per window shares those identities; it does
not share fits across windows. Complete per-window prediction and refusal slots
were saved, fsynced and reopened before post-freeze scoring outcome decode.
The same source labels legitimately train other folds, so this is not a claim
that all source outcomes were globally unread or independently unexposed.

## Actual narrow scored result

Only `author:LOBBSBOG` in TW6 had three eligible method predictions. Its observed
30-taxon NISP is 3,204. The table describes that single target only; the three
rows are alternative methods on the same target, not three independent sites.

| Method | Target | NISP | Total variation | MAE fraction | RMSE fraction | Count-conditioned deviance |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| training_mean | author:LOBBSBOG | 3204 | 0.381980780209 | 0.0254653853473 | 0.0629223204411 | 2813.18113753 |
| nearest_site | author:LOBBSBOG | 3204 | 0.174690965224 | 0.0116460643483 | 0.0282548998961 | 655.20914828 |
| inverse_distance_squared | author:LOBBSBOG | 3204 | 0.103304422776 | 0.00688696151839 | 0.0165404070536 | 486.293761453 |

Within this one target, inverse-distance-squared weighting has the smallest
recorded total variation. It is not a cohort-wide or cross-window winner.
TW4 has no scored target and therefore no defined average error. No refused
prediction is replaced by a zero error. The compact report retains full saved
precision, all signed per-taxon errors, predicted vectors and original observed
counts. Zero-probability positive counts would retain a null deviance and an
explicit flag; none of these three rows has that condition.

## Why native success did not produce a complete prediction cohort

A completed cache product is not automatically a usable closed composition.
The exact saved optimizer nonconvergence details and any composition extraction
refusals are retained per distinct request. Each refused target-method slot
points back to the responsible training request identities. The producer used
strict maintained eligibility rules; it did not clamp values, silently close
invalid vectors, override optimizer refusals, tune starts or omit failed slots.
All 39 refused slots in each window remain visible. Original raw diagnostics
and complete scientific cache members remain retained outside product Git;
[trace-index.json](./trace-index.json) supplies content-addressed references,
including cache-product manifests and original observation/native identities.

## Source and execution qualification

The input producers ran at source epoch `d863e6c939fab8eed3e53c4dc01c52953bc2434a`. The physical
jobs ran the committed temporal source at `d60500153ff589db3b93c38fe3bddde46c2994a9`. These are
separate epochs. The original two scripts and [scientific protocol](./protocol.json)
are already maintained in this directory, with no copied package or runtime tree.
The host metadata declares 0.1.9.dev1646 and the LRA source-build declaration is
0.1.9.dev1462; bounded source metadata and real discovery preflight do not imply
installed-wheel or sdist parity.

| Window | Native elapsed seconds | Completed-child peak RSS bytes | Output bytes |
| --- | ---: | ---: | ---: |
| TW4 | 87.009190 | 258506752 | 1705248 |
| TW6 | 40.795545 | 261505024 | 1812240 |

Both original native stages returned zero with unchanged controlled inputs and
sources. The stage deadline was 420 seconds, the overall envelope 480 seconds,
with one producer worker and one numerical thread. The 1 GiB completed-child RSS
and 64 MiB retained-output limits are postchecks, not operating-system or
aggregate quotas. The unchanged consumer discards the scientific `main` return;
that return was not independently observed. The separate saved-output observer
admitted the actual complete request populations, fold ancestry, conditional
refusals, freeze/journal joins and independent Decimal direct-count metrics.
This qualification relies on source and saved journal/hash correspondence,
not independent wall-clock instrumentation of source access.

## Reproduction and remaining limits

The executable supports `inspect` and `run`; `python replay.py --help` lists the
exact arguments. Reproduction requires the authenticated prepared 30-taxon
window, its projected-input authority, exact request manifest, scientific
protocol and a real current host/LRA metadata preflight. `inspect` records the
request population without fitting. `run` additionally requires the saved
request-manifest pin, current metadata-preflight pin, execution candidate and a
fresh artifact output. A clean clone does not supply the restricted original
source inputs or private raw traces. The existing canonical English LRA account
and its supported export remain the broader explanation; this reader is not a
new canonical paper or a qualified PDF export.

These are prior-exposed development point-pollen comparisons. They do not
measure empirical vegetation accuracy, uncertainty containment, source rights,
human comprehension, confirmatory held-out performance or completion of an
older unresolved report owner. Further model changes require a separately
frozen scientific policy and its own failure-preserving evidence. Actual
unfamiliar-reader feedback remains outstanding; no outreach is inferred.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

This temporal physical-development account retains its own conditional prediction/refusal denominators; the linked canonical account supplies context, not replacement evidence or a different cohort.

**Supported claim.** Actual source-bound deterministic temporal development admits complete request/refusal populations and three point-pollen comparisons at one TW6 target; TW4 has no eligible prediction.

**Unsupported claim.** No reliable whole-cohort or cross-window winner, independent confirmation, vegetation accuracy, chronology-uncertainty containment, installed-package parity or old-owner closure.

**Actual verification performed.** Both original native stages returned zero. Independent full saved-output observation aff389 verified 23/25 unique requests, 143/168 logical joins, all 39/42 slots, request ancestry, refusal causes, freeze/journal binding and Decimal30-taxon metrics; scientific main return remains unobserved.

**Remaining input or review.** Additional independently frozen model development and intended-reader feedback remain; no human comprehension, rights or ecological acceptance has been inferred.

**Cause category.** algorithm/numerical | conditional eligibility | population/comparability | intended-reader review

**Consequence.** TW4 has undefined score averages; TW6 scores describe only LOBBSBOG NISP3204. Refused slots stay in the denominator and cannot be treated as zero error.

**Precise next acceptance route.** Inspect the shared parameter/policy and all refused request causes; freeze any alternative before execution, preserve full failure accounting and collect actual reader feedback separately.

**Negative or refused result.** TW4:20 completed and3 optimizer-refused requests,0 predicted/39 refused slots. TW6:21 completed and4 optimizer-refused requests,3 predicted/39 refused slots; no refusal is repaired or dropped.

**Matched denominator.** TW4:13sites/143logical/23unique/39slots/0scores. TW6:14sites/168logical/25unique/42slots/3scores from one target3204counts;27site-window representations are not27independent physical sites.

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/temporal-development/report.json](report.json) (SHA-256 `17b6b96fce90e1fd05fe35621d94b1289ba401c1f9036b874c3c44e0ac882d2f`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/temporal-development/trace-index.json](trace-index.json) (SHA-256 `4aee58ce6422089c2f76fa672238327092255284bf6a78bc2da4fa2e96acea27`).

- [Retained qualification evidence: reports/science/source-cohorts/author-love-temporal-development.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/author-love-temporal-development.json) (SHA-256 `565e7cbb494dab8721913ab6148a14c78fa2aeb3d97b5e6cce497f7533e8569b`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/temporal-development/protocol.json](protocol.json) (SHA-256 `deb9c4a592f5dcc974e4624aafeaf50cbaad5f3dd407a8d6ac44f24e47c1aae2`).

- [Canonical scientific account: reports/science/english-lra-pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/english-lra-pollen-prediction.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
