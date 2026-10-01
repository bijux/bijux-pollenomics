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
