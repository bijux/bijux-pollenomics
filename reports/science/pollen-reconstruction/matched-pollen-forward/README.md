# Conditional matched physical-forward pollen predictions

This development comparison asks whether a fixed physical inverse-to-forward
route changes restricted-panel pollen error relative to a direct count-panel
baseline on the **same eligible training sources and target windows**. It uses
retained counts and previously computed transport factors. It does not fit a
new model, optimize PPE, or calculate new kernels.

The completed producer retained eight source cores at seven physical places,
four Swedish target cores and 77 target windows. Two training scopes give
154 prediction contexts and two prediction families give 308 outcomes:
200 scored and 108 refused. All requested contexts remain in the
[prediction freeze](prediction-freeze.json), and all family outcomes, signed
errors and target denominators remain in the [score table](scores.json).
The [native report](report.json) retains the complete matched summary.

## Method and source population

| Component | Definition and limitation |
| --- | --- |
| Swedish targets | ABB (Abborrtjärnen), BOKE (Bökesjön), BUS (Bussjösjön) and TIB (Tibetanus); their original native dataset, collection and physical-site identities remain in every context. |
| Source pool | Four Swedish cores plus four Nordic source cores. Solsø 81 and 83 are two cores at one physical place, not two independent sites. |
| Swedish-only scope | Eligible sources from the four Swedish cores; exclude the complete target physical place. |
| Pooled eligible Nordic scope | Apply the same target exclusion, exact panel, window, positive projected-count and PPE-transfer requirements to all eight cores. It is not a four-country matched result. |
| Physical-forward family | Invert each eligible source's observed panel through its saved K and shared PPE; average closed cover compositions equally by physical place; forward that composition through the target's saved K and PPE. |
| Direct baseline | Average eligible source count-panel fractions equally by physical place, using exactly the same source eligibility. |
| Target forward support | One homogeneous land annulus with terrestrial fraction one and zero separate regional-background deposition. Saved radii, wind 3 m/s, D=0.12, gamma=0.25 and 100 km regional extent remain assumptions. |
| Scores | MAE and total variation in pollen-fraction units, with signed taxon errors. The scored panels each have two complementary taxa, so MAE and total variation coincide here. |
| Uncertainty | Point predictions only. No propagated or calibrated interval is published. |

BOKE's original Betula/Fraxinus/Ulmus counts are explicitly projected and
reclosed to **Betula/Ulmus** for both target and training denominators.
Fraxinus is excluded from this estimand, not filled with a zero. Other target
panels and all reported counts remain explicit. A source must contain every
target taxon; an unmeasured taxon never becomes an observed zero. Exact
CalBP window membership and whole-place exclusion are preserved.
The [declared protocol](../../../../docs/report/pollen-reconstruction/matched-pollen-forward/assumptions/protocol.json)
records the fixed source identities, axes, windows and assumptions.

## Coverage and refusals

The entries below are **per family**: the physical and direct families had
the same scored/refused coverage in this execution. Counts are target windows,
not additional physical sites. Every refusal was `no_eligible_training_source`;
none was converted to a zero prediction or silently dropped.

| Target | Windows | Swedish-only scored / refused | Pooled eligible Nordic scored / refused |
| --- | ---: | ---: | ---: |
| ABB | 22 | 0 / 22 | 22 / 0 |
| BOKE | 13 | 13 / 0 | 13 / 0 |
| BUS | 19 | 13 / 6 | 17 / 2 |
| TIB | 23 | 0 / 23 | 22 / 1 |

The freeze also retains every individual training-source exclusion. Across
all contexts there are 154 whole-target-place exclusions, 607 panel
incompatibilities, 308 sources outside the declared training scope and
30 missing exact-window matches. These are repeated eligibility decisions,
not independent samples or 1,099 failed models. The original source/window
records, admitted zeros and projection denominators remain in the JSON.

## Matched results, including the poorer BUS outcome

A joint comparison requires **both families in both scopes** to score the
same target, panel, counts and window. Only 26 windows at two physical sites
meet that condition: 13 at BOKE and 13 at BUS. ABB and TIB have pooled scores
but lack the Swedish-only counterpart, so their scores do not enter these
matched averages. Windows are averaged within each target, then the two
physical targets receive equal weight.

| Training scope | Prediction family | BOKE MAE / TV | BUS MAE / TV | Two-target mean MAE / TV |
| --- | --- | ---: | ---: | ---: |
| Swedish-only | Direct panel mean | 0.149995 | 0.149995 | 0.149995 |
| Swedish-only | Physical forward | 0.149644 | 0.149967 | 0.149805 |
| Pooled eligible Nordic | Direct panel mean | 0.087016 | 0.154539 | 0.120778 |
| Pooled eligible Nordic | Physical forward | 0.061348 | 0.154732 | 0.108040 |

The table displays six decimals; the JSON retains the complete native machine
precision. The pooled physical-forward mean is lower than its direct baseline on this
matched pair, but the gain is not uniform: **BUS is worse under pooled
physical forwarding** (0.154732 versus 0.154539).
Its pooled physical score is also worse than its Swedish-only physical score.
BOKE supplies the stronger pooled improvement. This two-site result does not
select a generally superior physical model or explain an isolated transport,
geometry or country effect. The extra pooled source in the jointly matched comparisons is Danish
Solsø 83 on exactly 12 pooled prediction contexts. The Nordic label does
not create matched Norwegian or Finnish target evidence.

## Numerical and publication identity

The producer completed with native and collector exit zero on source epoch
`a890b5e433fd2679768b588bae2774aa3d382e17`; all 6,668 input pins agreed before
and after execution. The underlying saved Swedish source epoch is
`1988f522002e8bb5362083b9e8b46bd4fa17685e` and the saved Nordic source epoch is
`33d45ecfd6be7d275b69a7a7350bb72ae7c5269e`. These are distinct epochs.

The three native JSON products are published byte for byte. Their original
run-local references are preserved inside them; the
[publication map](publication.json) associates each original identity with
its repository path. Publication does not relabel a native run as executing
on the later publication commit.

The independent 50-digit Decimal check completed with native and collector exit zero, checking 1424 values at the frozen absolute tolerance 1e-12. Its maximum absolute error was 1.9653480873864026090362878350698437E-16, with no mismatches. It independently joined all 154 context dispositions and 308 family outcomes; this numerical agreement does not certify scientific failure causality, field accuracy or calibrated uncertainty.

## Interpretation and next evidence

All retained input JSON and counts were parsed and validated before
prediction, and these development outcomes were already exposed. Target
counts are absent from the predictor interface, the complete target place is
excluded from training, and all 154 prediction contexts were persisted before
`score_pollen` ran. This is **freeze before scoring**, not an unread-target,
untouched-test or global information-isolation claim.

No independent measured vegetation, field PPE covariance, source-supported
spatial vegetation law or ecological interval calibration was evaluated.
Rights and qualified human scientific review remain source-specific and open.
A new validation claim needs a frozen, independently supported physical
cohort and reference with compatible site, time, taxonomy and spatial support.
The present conditional restricted-panel result does not establish complete
model-search or physical-prediction validation.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** A previously exposed conditional matched physical inverse-to-forward point-pollen comparison against the same-source direct panel baseline; the producer preserves all contexts, scores and refusals.

**Unsupported claim.** Untouched predictive accuracy, measured vegetation accuracy, calibrated uncertainty, four-country matched generalization, historical reproduction, source rights or full model-development/physical-prediction acceptance.

**Actual verification performed.** Actual source-bound producer and collector completed at a890b5e433fd2679768b588bae2774aa3d382e17 with all 6,668 pins unchanged. The exact 154 prediction contexts, 308 family outcomes, 200 scores and 108 refusals are retained byte for byte. The independent 50-digit Decimal check completed with native and collector exit zero, checking 1424 values at the frozen absolute tolerance 1e-12. Its maximum absolute error was 1.9653480873864026090362878350698437E-16, with no mismatches. It independently joined all 154 context dispositions and 308 family outcomes; this numerical agreement does not certify scientific failure causality, field accuracy or calibrated uncertainty.

**Remaining input or review.** The fixed saved geometry, transport and homogeneous annulus are conditional; previously exposed restricted-panel development has only two jointly scored physical targets and no independent measured vegetation or calibrated interval. Source-use permissions and qualified review remain separate. Resolver: Physical source and taxon/chronology custodians and qualified ecological reviewer Reopen when: Freeze a source-supported physical cohort with an independent reference aligned by place, time, taxonomy and spatial support, and resolve analytical-use permissions before a new validation claim.

**Cause category.** data|assumption|comparability|access/rights|qualified review

**Consequence.** Keep the lower two-target pooled physical mean conditional on these two sites and restricted panels; retain the poorer BUS outcome and every excluded or refused population.

**Precise next acceptance route.** The independent Decimal check is complete for this exact conditional calculation. A stronger scientific validation requires the frozen independent source-supported physical cohort/reference, analytical-use permissions and qualified review stated above; the current development result does not discharge those requirements.

**Negative or refused result.** 108 family outcomes refused for lack of an eligible training source. On 13 jointly matched BUS windows, pooled physical-forward MAE/TV 0.15473205802209306 is worse than the direct baseline 0.15453909793199222 and the Swedish-only physical result 0.14996673023384896.

**Matched denominator.** Eight source cores at seven physical places; four Swedish target cores and 77 windows; two scopes produce 154 contexts and two families 308 outcomes, including 200 scored and 108 refused. Only 26 windows at BOKE and BUS, 13 each, are jointly scored by all four methods. Each target panel has two taxa; equal windows within target then equal physical targets.

Retained evidence: [reports/science/pollen-reconstruction/matched-pollen-forward/prediction-freeze.json](prediction-freeze.json), [reports/science/pollen-reconstruction/matched-pollen-forward/scores.json](scores.json), [reports/science/pollen-reconstruction/matched-pollen-forward/report.json](report.json), [reports/science/pollen-reconstruction/matched-pollen-forward/decimal-comparison.json](decimal-comparison.json), [reports/science/pollen-reconstruction/matched-pollen-forward/publication.json](publication.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
