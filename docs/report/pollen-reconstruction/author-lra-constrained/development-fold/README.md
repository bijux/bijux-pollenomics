# Retrospective BECKHAM development fold with fixed-start LOVE

This separately declared development comparison uses the existing English author
pollen and the original BECKHAM whole-site split: 14 training records, including
the BROADOWN regional anchor, provide 13 local predictor compositions. Each local
predictor has two ring objectives and 32 predeclared positive starts.

All **832 attempts** are retained: **704 newly executed** and **128 authenticated
prior attempts reused** from the [initial-point study](../optimizer-start-sensitivity/README.md).
Across the 26 ring objectives, **716 attempts were accepted and 116 refused**.
These are optimization attempts on existing training data, not independent samples
or uncertainty draws. Convergence from several starts does not calibrate an interval.

| Training predictor | Evidence | Accepted / 32 at 500 m | Accepted / 32 at 1,000 m | Refused / 64 | Selected outer-ring objective |
| --- | --- | ---: | ---: | ---: | ---: |
| COMERSLA | new | 25 | 25 | 14 | 1.73876407 |
| CUTHILL2 | reused | 23 | 23 | 18 | 0.823088674 |
| GOURTEMIRES | new | 27 | 27 | 10 | 0.850459135 |
| HANGINGS | new | 25 | 25 | 14 | 1.11618216 |
| HARESDOWN | new | 31 | 31 | 2 | 1.93016178 |
| LARKBARR | new | 27 | 27 | 10 | 3.1538629 |
| LOBBSBOG | new | 28 | 28 | 8 | 1.65237548 |
| LONGBREACH | reused | 19 | 19 | 26 | 0.587410753 |
| MOLECHAM | new | 28 | 28 | 8 | 0.988601824 |
| NTWITCHEN | new | 30 | 30 | 4 | 0.477802125 |
| WHH05 | new | 32 | 32 | 0 | 6.19412912 |
| WINDMILL | new | 31 | 31 | 2 | 1.76795879 |
| WINNEYS | new | 32 | 32 | 0 | 0.794186643 |

Refused outcomes remain in the denominator:

- 116: Positive directional derivative for linesearch.

All 13 predictors have accepted candidates in both rings. The outer-ring
compositions feed the unchanged spatial and forward-pollen consumer.
Three predictions were written to an exclusive file and authenticated again
before BECKHAM target counts were decoded. The access record binds that freeze.

The scored target retains **699 integer pollen counts**
on the 30-taxon axis. These are descriptive, count-conditioned point scores:

| Spatial baseline | MAE, fraction | RMSE, fraction | Total variation | Count-conditioned deviance |
| --- | ---: | ---: | ---: | ---: |
| Training mean | 0.027367953 | 0.0638812986 | 0.410519295 | 651.873281 |
| Nearest training site | 0.022492854 | 0.0547431089 | 0.33739281 | 516.951129 |
| Inverse squared geodesic distance | 0.0226671397 | 0.0550258122 | 0.340007095 | 516.70642 |

Total variation ranges from 0.3374 to 0.4105, showing substantial pollen-composition mismatch at this target despite successful convergence. All three predeclared baselines remain reported.

Fractions are reported without percentage scaling. A dash preserves a null
metric. Infinite deviance is retained through the explicit impossible-positive-
count flag and null JSON value; no target pseudocount or observation smoothing
is added. Signed taxon errors and all scoring fields remain in the JSON result.

The numerical objective, exact derivative, source counts/PPE/fall speeds, seed
and per-attempt bounds remain fixed: 300 iterations, 16,000 search evaluations
plus one host certification call, and `ftol=1e-8`. Within each ring the minimum
objective among genuinely converged, finite, nonnegative simplex candidates is
selected, with ties broken by start identifier. Refusals cannot win selection.

REVEALS cover percentages retain their native three-decimal rounding and raw
fractional mass in the objective and forward background. Only the regional
initial-point direction is closed to one. After raw optimizer acceptance, the
declared diagnostic adapter records `x`, its sum and the explicit unrounded
`x/x.sum()` model composition, then applies the maintained composition gate.
This uses the normalization already present in LOVE mathematics. It does not
claim identical generic custom-optimizer rounding or a host LRA product.

The source cohort has 15 positive-count sites and 20,732 original grains.
The explicit 30-taxon subcomposition excludes 159 Filipendula grains; its
0.006 m/s source fall speed is outside the optimized profile interval.
The prepared author-TW5 window is labelled as calendar BP, spanning 1,250–1,750 and centred at 1,500. This prepared-input contract does not encode a separate BP reference epoch; the evaluation uses the retained bin literally and performs no calendar conversion or calibration.
The declared circular basin and homogeneous terrestrial-ring geometry support
two local rings through 1,000 m and the existing forward annuli. These are
conditional geometry/transport assumptions, not independently measured historical
vegetation or authenticated landscape boundaries.

The original uniform-start study remains literal: 195 training items,
192 completed and three refused, 14 scored outer folds and a refused BECKHAM
fold. This separate method is not combined with those 14 fold scores as one
homogeneous 15-fold evaluation. The English cohort and source are prior-exposed;
prediction freezing here supplies an operational ordering boundary, not a new
untouched confirmation cohort.

[protocol.json](protocol.json) retains the fixed settings, input/source hashes
and reuse identities. [training.json](training.json) and [trials.jsonl](trials.jsonl)
retain the training decisions, all new attempts and their start/completion events;
the linked earlier report/ledger retain the 128 reused outcomes. [report.json](report.json)
retains the result and refusal/scoring population. [replay.py](replay.py) and
[training.py](training.py) are the source consumer and its numerical adapter.
The completed fold retains [prediction-freeze.json](prediction-freeze.json)
and [outcome-access.json](outcome-access.json).

The numerical run used clean base `f0383c0bfcbbb7baac3f1cd974052550896f0867` with separately authenticated `replay.py`, `training.py` and scientific-protocol files that were absent from that base Git tree. The compact [execution authority](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/author-love-development-fold.json) binds their exact overlay identities, original terminals and independent output review.

The qualified source engine uses explicitly derived discovery metadata. This
numerical study does not qualify an installed wheel/sdist, original R optimizer
parity, global optimality, independent vegetation accuracy, source rights or a
release. Its broader scientific context remains in the
[English LRA account](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/english-lra-pollen-prediction.md).


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-bound retrospective fixed-start English development-fold prediction and descriptive pollen scoring. Preserve its own 832-attempt denominator, raw rounded regional mass, conditional geometry/chronology, prior exposure, prediction freeze and all original-study outcomes.

**Supported claim.** All 13 declared training predictors supplied accepted LOVE compositions at both rings under the frozen fixed-start rule. The unchanged forward consumer produced three separately frozen pollen predictions and retrospective scores for the BECKHAM development target.

**Unsupported claim.** Independent ecological or measured-vegetation accuracy, untouched confirmation, calibrated uncertainty, global optimality, original R optimizer parity, installed distribution qualification, source-rights admission or release approval.

**Actual verification performed.** The actual registered consumer ran on clean base f0383c0bfcbbb7baac3f1cd974052550896f0867 with separately authenticated replay, training and scientific-protocol files absent from that Git tree. Native/common/outer exits were zero. Source/input/runtime custody passed. The new 704 attempts retain 632 acceptances and 72 refusals; the authenticated 128 earlier attempts retain 84 acceptances and 44 refusals. Independent saved-output arithmetic checked all 832 outcomes, 26 ring selections, 13 predictors, exact prediction freeze and three count-conditioned score rows on 699 target grains.

**Remaining input or review.** A homogeneous evaluation across all declared development folds remains separate. Independent compatible physical support, measured vegetation, untouched outcomes and qualified ecological review are required for broader scientific accuracy. This single deterministic point comparison does not calibrate uncertainty.

**Cause category.** algorithm/numerical | assumption | comparability | qualified review

**Consequence.** Preserve every refusal and all three predeclared baselines. Successful convergence still leaves target total-variation distances of 0.410519295, 0.337392810 and 0.340007095; report that mismatch alongside numerical completion. Preserve the original uniform-start study and its BECKHAM refusal.

**Precise next acceptance route.** Evaluate the frozen method consistently across the declared development folds with failure and spatial-dependence accounting. Any independent accuracy or confirmation claim then requires its own admitted cohort, protocol and qualified review.

**Negative or refused result.** 116 of 832 optimizer attempts remain refused for a positive directional derivative during line search. Accepted alternatives preserve those refusals. The substantial pollen mismatch at this development target and the earlier uniform-start BECKHAM refusal remain explicit.

**Matched denominator.** Fourteen training records including one regional anchor; 13 local predictors times two rings times 32 starts gives 832 attempts, comprising 704 new and 128 reused. One previously exposed target, 699 integer counts on the original 30-taxon subcomposition, and three spatial baselines. No independent site or observation is added.

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/development-fold/report.json](report.json) (SHA-256 `84843a2b419392e303cd3ecc8cf8b28461f1ad601c600d2fefa1d7eff8578e58`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/development-fold/training.json](training.json) (SHA-256 `89d0ba05579676d2882ecb1edfbea88c695f9b07aca639dd2930ea2d95b4dae9`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/development-fold/trials.jsonl](trials.jsonl) (SHA-256 `84fae7553048d2439ab744dedf30d016abf89a74184d6e4180149e39ace43655`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/development-fold/prediction-freeze.json](prediction-freeze.json) (SHA-256 `5d57b8bcd859d013ddcd554ab1bea2ef2207a6c42820cf1d69fab4777cb528e1`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/development-fold/outcome-access.json](outcome-access.json) (SHA-256 `c6182a5b334204fbed0fd9a846a1aad260f2247314054b8394c77614e518833a`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/development-fold/protocol.json](protocol.json) (SHA-256 `4e57812229aeb2d3aad448ac638712b675e299c90f535f163b238f7e72e8124d`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/development-fold/replay.py](replay.py).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/development-fold/training.py](training.py).

- [Retained qualification evidence: reports/science/source-cohorts/author-love-development-fold.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/author-love-development-fold.json) (SHA-256 `4d3a460c94fefaf19641c77fef465bb35abd0bd8e46b7251d1def9356d2bef37`).

- [Canonical scientific account: reports/science/english-lra-pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/english-lra-pollen-prediction.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
