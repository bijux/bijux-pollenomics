# What do the Bussjösjön and Bökesjön pollen series show together?

We compared observed `Alnus` and `Plantago lanceolata` pollen at two Swedish
lakes to ask whether their changes point in the same direction. We also asked
whether nearby dated archaeology supports a local land-use conclusion. We
chose 13 common 500-year calibrated-BP bins, from -500 to 6000 BP, and kept
the two lakes' native count denominators separate. The [governed report](../../docs/report/countries/sweden/observed-pollen-trajectory/report.json)
and [48 transition rows](../../docs/report/countries/sweden/observed-pollen-trajectory/transitions.csv)
retain the counts, sample support, comparisons and refusals.

## What we calculated

For each lake and bin, we divided the exact native `Alnus` or `Plantago
lanceolata` count by either all native `NISP` or the declared 16-taxon count
subtotal. We called a transition a shared direction only when both lakes
changed with the same sign under both denominators and passed a fixed 0.5 or
1.0 percentage point threshold. These thresholds describe the retained
series; they are not confidence intervals or ecological effect sizes.

We also compared an equal-lake mean with a fraction pooled from the two
lakes' counts. Each pooled numerator uses the matching pooled denominator;
sample counts do not act as weights. Across 48 taxon, threshold and interval
comparisons, pooling changes **10** all-native direction classes and **9**
closed-16 classes. Four comparisons in each denominator switch between a
qualified increase and a qualified decrease. The choice of lake weighting
can therefore change the apparent direction even with the same two sites and
bins.

## What we found

At the 0.5-point threshold, `Alnus` moves in the same direction in five
transitions and in opposite directions in one; the other 18 cases across both
taxa do not meet the joint denominator and threshold rule. At the 1.0-point
threshold, three `Alnus` transitions agree, one contradicts and 20 cases
across both taxa do not qualify. For example, from
1000–1500 to 500–1000 cal BP, the all-native `Alnus` fraction falls from
**10.00 to 3.69%** at Bussjösjön and **12.53 to 9.55%** at Bökesjön. From
5000–5500 to 4500–5000 cal BP it rises **34.13 to 47.28%** at Bussjösjön
while falling **23.47 to 20.53%** at Bökesjön. Both examples retain their
directions under the 16-taxon denominator. The report also retains a
1000-year aggregation to show the effect of wider bins.

The 48 classifications represent **24 distinct taxon transitions**, each
evaluated at two thresholds. The eight agreement and two contradiction
classifications are therefore not ten independent events. The sole distinct
contradiction is the `Alnus` change from 5000–5500 to 4500–5000 cal BP:
Bussjösjön rises by **13.1536 percentage points** on its native denominator
and **11.1170 points** on the closed-16 denominator, while Bökesjön falls by
**2.9374** and **2.1799 points**, respectively. It passes both declared
thresholds under both denominators; age and spatial uncertainty remain
unresolved.

The denominator can also reverse a direction within one lake. At
Bussjösjön, `Alnus` from 4000–4500 to 3500–4000 cal BP falls by **3.1987
percentage points** among all native pollen `NISP`, but rises by **12.6236
points** within the exact-name 16-taxon subset. Across the 13 common bins,
that subset contains only **20.17–64.63%** of native pollen counts at
Bussjösjön and **47.78–67.00%** at Bökesjön. It includes `Nuphar` but
excludes native `Corylus`, `Pinus`, Poaceae and cereal labels; these fractions
are conditional pollen compositions, not total vegetation or agricultural
cover. The native denominator selects pollen `NISP` observations, so the
restriction is the meaning of the subset rather than inclusion of spores.

We counted overlapping dated SEAD map features within 10 and 20 km of the
Neotoma site points. We also repeated the Bussjösjön circles at the
[published lake-inventory point](../../docs/report/source-relations/neotoma/bussjosjon-basin/README.md),
which lies **2.5264 km** from the Neotoma point. In the 500–1000 BP bin, the
10 km count changes from **129 to 115** dated features. A dated feature is
neither a measured land-use event nor vegetation cover, and the circles are
not historical lake basins.

## Our interpretation and limits

We find descriptive agreement and contradiction in two observed-pollen
series. We cannot infer one regional vegetation trajectory or land-use change
from these comparisons. Sample-age uncertainty, pollen catchments, unresolved
Bussjösjön coordinates and the lack of paired vegetation measurements limit
that inference. Our [source-lineage decision](vegetation-reference.md#why-modeled-cover-is-not-a-vegetation-reference)
also places both lakes among the LandClim inputs for grid 779, so that grid
cannot serve as independent validation of these pollen series. Denmark,
Norway and Finland were not evaluated for this two-lake question. This is an
observed-pollen comparison, not an LRA reconstruction.

The maintained [producer](../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/swedish_lake_trajectory.py)
pins the two pollen profiles, SEAD discovery surface and LandClim lineage by
SHA-256. To reproduce the governed JSON and CSV from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_lake_trajectory \
  --repository . --output artifacts/jobs/swedish-lake-trajectory-replay
```

Compare those two generated files byte for byte with the linked governed
outputs. New age, basin or ecological evidence requires a new qualified
comparison.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** BUS/BOKE Alnus and Plantago pollen changes are classified on both native and closed-16 denominators.

**Unsupported claim.** Regional vegetation trajectory or causal archaeological land-use interpretation.

**Actual verification performed.** Retained 48 transition rows, equal-lake/pooled and SEAD proximity checks are cited; index did not rerun.

**Remaining input or review.** BUS/BOKE pollen transitions have distinct denominators and uncertain ages/catchments; BUS coordinate/basin and nearby SEAD feature meaning remain unresolved, so no causal land-use trajectory follows. Resolver: BUS/BOKE core and SEAD owners plus independent palaeoecological reviewer Reopen when: Dated core/basin and permitted event packets support a reviewer decision on comparable transitions and contradictions.

**Cause category.** data|assumption|comparability|qualified review

**Consequence.** Keep eight agreement/two contradiction classifications descriptive and nonindependent.

**Precise next acceptance route.** Dated core/basin and permitted event packets support a reviewer decision on comparable transitions and contradictions. Then update reports/needed/README.md.

**Negative or refused result.** 38 of 48 classifications cannot give a qualified joint direction; one distinct Alnus contradiction survives declared thresholds, not age/basin review.

**Matched denominator.** 13 common 500-year bins; 24 taxon transitions × two thresholds =48 classifications across two lakes.

Retained evidence: [docs/report/countries/sweden/observed-pollen-trajectory/transitions.csv](../../docs/report/countries/sweden/observed-pollen-trajectory/transitions.csv), [docs/report/source-relations/neotoma/bussjosjon-basin/README.md](../../docs/report/source-relations/neotoma/bussjosjon-basin/README.md).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-claim-semantic-sha256: 77617c0fe237db52a0a803ad2c06c35e44e0cbebb952b5b814918bb51fefe4bf -->
<!-- scientific-authored-source-sha256: 6397cb5c3b80cf314570bebeee07edbfd7f619fe82a42111024638eeece228c9 -->
<!-- scientific-verification-and-limits:end -->
