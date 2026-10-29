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


## Conditional depth-order feasibility

A separate [depth-order result](../depth-order/report.json) asks whether all
107 retained marginal age intervals permit one age assignment that is
nondecreasing with native sample depth. Equal depths must share one age.
This is an explicit additional assumption, not a source-confirmed sediment
history. The calculation finds a feasible assignment at all 107 distinct
depths, with each chosen age inside its original closed interval. Five native
negative younger endpoints are retained without truncation. The assignment
is an existence witness, not a fitted chronology, a preferred age curve or a
draw from an age posterior.

All **16** previously refused lower/upper endpoint combinations remain
unattainable. They already fail the original one-age-per-sample membership
constraints; adding depth order does not rescue them. Their individual
refusals and the four independent per-bin bounds above are retained exactly.
No new order-constrained per-bin extrema were calculated.

The retained analysis ran successfully on source revision
`db2f4d5616616472e3baf5c86a5af207f6a0de0f`. Its result SHA-256 is
`d081a52eeb130251aa5448dd1ebd28a91193e0564d332c9f8bb5a93dc64ce920`.
An independent direct-decimal check joined every witness age to its original
interval and native depth and confirmed the within-interval and
nondecreasing-order constraints, without calling the producer again. The
107-row support ledger remains byte-identical (SHA-256
`26ca6dc862790c71a3a7821b027413307dd2334856080a1b07e186177cfb8e01`);
all 428 membership relationships and the original source epoch are retained.

The evidence supports only conditional feasibility for this previously
exposed core and selected bins. A source-qualified joint chronology,
probabilities, calibration/epoch decisions and qualified sediment-history
review remain missing. The cause is missing joint source information and an
unverified order assumption: existence alone cannot establish chronology
accuracy, joint 95% confidence, independence, vegetation accuracy or LRA
admission. A stronger claim requires a source-qualified joint age/depth model
and its stated uncertainty, followed by review of that exact use. The matched
denominator is 107 samples at 107 depths, 428 sample-bin relationships, four
marginal bounds and all 16 refused endpoint combinations.

To reproduce this separate diagnostic, use an absent artifact destination:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.pollen_age_support.depth_order.abborrtjarne \
  --repository . --output artifacts/jobs/abborrtjarne-conditional-depth-order
cmp artifacts/jobs/abborrtjarne-conditional-depth-order/report.json \
  docs/report/pollen-reconstruction/age-interval-sensitivity/depth-order/report.json
```



<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-bound conditional reconstruction or exposed pollen development wrapper; own source assumptions and exact scored/refused populations must be preserved alongside account links.

**Supported claim.** Exact per-bin outer bounds describe the pooled selected-16-taxon count fraction over optional overlapping ABBO samples, conditional on treating reported marginal 95% age intervals as possible-age sets. A separate joint-membership diagnostic refuses all simultaneous endpoint combinations. Under the additional declared nondecreasing native-depth assumption, one within-interval age assignment exists for all 107 samples at 107 distinct depths; this is conditional feasibility only.

**Unsupported claim.** A jointly attainable uncertainty envelope, joint 95% confidence bounds, calibrated age probabilities, a revised age model, individual-taxon vegetation cover, prediction error or LandClim/LRA admission.

**Actual verification performed.** The membership report/ledger, joint-membership report and retained depth-order result were inspected against the source-bound 107-sample support and four selected bins. The actual depth-order analysis succeeded on db2f4d5616616472e3baf5c86a5af207f6a0de0f; a separate direct-decimal check confirmed all witness ages within their original intervals and nondecreasing with native depth. This reader qualification does not rerun any producer, optimization or diagnostic and supplies no joint chronology posterior.

**Remaining input or review.** No source-qualified joint age posterior, probabilities or sediment-history depth-order constraints are supplied. Nondecreasing age with native depth is an explicit additional assumption, not confirmed source history. Four bins were chosen after inspection in an exposed development cohort. Conditional existence does not identify a preferred chronology or vegetation estimand.

**Cause category.** data | assumption | comparability | qualified review

**Consequence.** Keep the per-bin bounds separate and preserve all 16 independently unattainable endpoint combinations. A depth-monotone within-interval witness is an existence result, not a fitted chronology, age-posterior draw or jointly attainable envelope. No order-constrained per-bin extrema were recomputed.

**Precise next acceptance route.** Obtain a source-qualified joint age/depth model with stated probabilities and temporal support, then define joint membership and uncertainty under a prospective analysis. New LRA or vegetation claims require separate physical and measured-reference admission.

**Negative or refused result.** All 16 lower/upper endpoint combinations across the four bins remain jointly unattainable: each already fails the one-age-per-sample constraints before depth order. The original per-bin bounds and individual refusals remain unchanged; five native negative younger endpoints are retained without truncation.

**Matched denominator.** 107 ABBO source samples × 4 selected bins = 428 sample-bin relationships: 8 contained, 49 overlaps and 371 outside. Numerator is pooled counts in the closed 16-taxon set; denominator is all native pollen NISP. Bounds are 483/2203–14/41, 2283/6823–3847/8958, 1895/4979–5103/11483 and 167/409–3963/7111 for the four named bins. The depth-order witness covers the same 107 samples at 107 distinct native depths and retains five negative younger endpoints; all 428 relationships and 16 refused endpoint combinations are preserved.

- [Retained qualification evidence: docs/report/pollen-reconstruction/age-interval-sensitivity/conditional-membership/report.json](report.json) (SHA-256 `bcd838ffc4bf9221761686c180d086d62482d09bd40880a4dd75b1024ac40340`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/age-interval-sensitivity/conditional-membership/membership.csv](membership.csv) (SHA-256 `6ca70c45e9c292b485ceea31aee3cda9aa92ffb5fdc404b9f6cc70158a62a2cc`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/age-interval-sensitivity/joint-membership/report.json](../joint-membership/report.json) (SHA-256 `27ef48efc9b835251f9cc5ebf621a01dd855047e523657bf1cdb7dc91ddee940`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/age-interval-sensitivity/depth-order/report.json](../depth-order/report.json) (SHA-256 `d081a52eeb130251aa5448dd1ebd28a91193e0564d332c9f8bb5a93dc64ce920`).

- [Canonical scientific account: reports/science/abborrtjarnen-source-method.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/abborrtjarnen-source-method.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
