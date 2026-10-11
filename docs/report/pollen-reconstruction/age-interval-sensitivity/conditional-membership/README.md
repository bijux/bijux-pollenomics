# Abborrtjärnen conditional age-bin membership

The [report](report.json) bounds one source quantity: pooled counts in the existing closed 16-taxon set divided by all native pollen counts for ABBO samples assigned to each of the four previously selected 500-calibrated-year BP bins. The [membership ledger](membership.csv) lists every one of the 107 source samples against every bin. It distinguishes eight wholly contained memberships, 49 overlaps and 371 outside relationships across 428 sample–bin rows. A sample may overlap more than one bin; those relationships are not simultaneous assignments.

For each bin, wholly contained samples are fixed and each overlapping sample is optionally included. The exact lower and upper pooled fractions are 483/2203–14/41 (1500–2000 BP), 2283/6823–3847/8958 (2000–2500 BP), 1895/4979–5103/11483 (2500–3000 BP), and 167/409–3963/7111 (4500–5000 BP). These are independent **per-bin outer bounds**, conditional on treating the published LegacyAge S5 marginal 95% intervals as possible-age sets. They are not joint 95% confidence bounds: no joint age posterior, depth monotonicity or age probabilities were supplied. They describe a pollen-count fraction, not individual-taxon cover, reconstructed vegetation, prediction error or a revised age model.

The [joint-membership diagnostic](../joint-membership/report.json) checks whether the per-bin endpoints can occur together when each sample receives exactly one possible age. None of the 16 combinations of lower or upper endpoints across the four bins is attainable. Some endpoints require a sample to lie in incompatible bins, or exclude every age location available to it. The individual per-bin bounds remain valid; their endpoints do not form a jointly attainable envelope. This calculation supplies no age probabilities or depth-order constraints.

The producer consumes the unchanged [107-row support ledger](../age-bin-support.csv), its [source manifest](../input-manifest.json), [configuration](../config.json), and the same five pinned Neotoma/profile/LegacyAge source files. It rechecks their bytes before publication and preserves the earlier interval-contained outputs. The source count denominator is native NISP, while the numerator is the selected closed 16 taxa; neither is a LANDCLIM or LRA admission decision. The four bins were selected after inspection in a previously exposed development cohort.

From the repository root, write to an absent directory beneath `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.pollen_age_support.abborrtjarne_membership \
  --repository . --output artifacts/jobs/abborrtjarne-conditional-membership
cmp artifacts/jobs/abborrtjarne-conditional-membership/report.json \
  docs/report/pollen-reconstruction/age-interval-sensitivity/conditional-membership/report.json
cmp artifacts/jobs/abborrtjarne-conditional-membership/membership.csv \
  docs/report/pollen-reconstruction/age-interval-sensitivity/conditional-membership/membership.csv
```

The age intervals come from [LegacyAge 1.0 S5, PANGAEA 933132](https://doi.org/10.1594/PANGAEA.933132). Original Neotoma/EPD attribution and source terms remain in the [parent source account](../README.md).
