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


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-bound conditional reconstruction or exposed pollen development wrapper; own source assumptions and exact scored/refused populations must be preserved alongside account links.

**Supported claim.** Exact per-bin outer bounds describe the pooled selected-16-taxon count fraction over optional overlapping ABBO samples, conditional on treating reported marginal 95% age intervals as possible-age sets. A separate joint-membership diagnostic refuses all simultaneous endpoint combinations.

**Unsupported claim.** A jointly attainable uncertainty envelope, joint 95% confidence bounds, calibrated age probabilities, a revised age model, individual-taxon vegetation cover, prediction error or LandClim/LRA admission.

**Actual verification performed.** The membership report/ledger and separate joint-membership report were inspected against their source-bound 107-sample support and selected-bin definition. This qualification does not rerun the bound optimization or joint diagnostic and supplies no joint chronology posterior.

**Remaining input or review.** No joint age posterior, probabilities or depth-monotonicity constraints are supplied. Four bins were chosen after inspection in an exposed development cohort. Independent per-bin count bounds cannot identify a joint temporal history or vegetation estimand.

**Cause category.** data | assumption | comparability | qualified review

**Consequence.** Keep each bin bound separate. A sample may appear as an overlap relationship in several bins but may not be simultaneously assigned to incompatible ages; endpoint combinations are not a probability distribution.

**Precise next acceptance route.** Obtain a source-qualified joint age/depth model with stated probabilities and temporal support, then define joint membership and uncertainty under a prospective analysis. New LRA or vegetation claims require separate physical and measured-reference admission.

**Negative or refused result.** All 16 lower/upper endpoint combinations across the four bins are jointly unattainable under one possible age per sample. The individual per-bin bounds remain valid; their endpoints do not form a jointly attainable envelope.

**Matched denominator.** 107 ABBO source samples × 4 selected bins = 428 sample-bin relationships: 8 contained, 49 overlaps and 371 outside. Numerator is pooled counts in the closed 16-taxon set; denominator is all native pollen NISP. Bounds are 483/2203–14/41, 2283/6823–3847/8958, 1895/4979–5103/11483 and 167/409–3963/7111 for the four named bins.

- [Retained qualification evidence: docs/report/pollen-reconstruction/age-interval-sensitivity/conditional-membership/report.json](report.json) (SHA-256 `bcd838ffc4bf9221761686c180d086d62482d09bd40880a4dd75b1024ac40340`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/age-interval-sensitivity/conditional-membership/membership.csv](membership.csv) (SHA-256 `6ca70c45e9c292b485ceea31aee3cda9aa92ffb5fdc404b9f6cc70158a62a2cc`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/age-interval-sensitivity/joint-membership/report.json](../joint-membership/report.json) (SHA-256 `27ef48efc9b835251f9cc5ebf621a01dd855047e523657bf1cdb7dc91ddee940`).

- [Canonical scientific account: reports/science/abborrtjarnen-source-method.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/abborrtjarnen-source-method.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
