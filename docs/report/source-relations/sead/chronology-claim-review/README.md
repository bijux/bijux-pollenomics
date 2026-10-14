# SEAD chronology claim and age-basis review

This review checks every **25,109** typed chronology claim in the pinned
`sead-full-evidence-39bfff6a-ce80714e` source capture against the independently
retained raw chronology table row. It verifies all six normalized claim-part
digests, five chronology-table payload digests, the raw age-type table,
admission, and acquisition manifest. The [report](report.json) retains those
input hashes, exact denominators, and seven representative source-age gold
examples. [claims.csv](claims.csv) retains one review decision for every claim.

| Source age basis | Claims | Reviewed meaning |
| --- | ---: | --- |
| AD calendar years with bounded nonnegative BP result | 13,170 | `1950 − native AD year` matches both captured BP endpoints; eligible for chronology display only |
| Dendrochronology `From` uncertainty | 1,094 | Native AD conversion matches, but one-sided dates have no bounded interval and remain context only |
| AD calendar years with negative BP result | 60 | Native conversion matches, but canonical numeric interval is refused |
| Relative periods | 10,057 | Context only; no governed numeric-period mapping |
| Radiometric/geochronology ages | 87 | Context only; calibration basis is unspecified |
| Modelled analysis-entity ages | 641 | Unresolved source-age basis |
| **All claims** | **25,109** | Every source row has one retained, unselected claim review |

The raw `tbl_age_types` authority contains exactly one type: ID `1`, **AD**,
described as Gregorian calendar-era dates. The source-backed AD gold examples
include 1845 AD → 105 BP and 2007 AD → −57 BP. The latter remains refused.
The direct policy tests also exercise the declared calibrated-BP, CE, BCE,
and unknown-age branches. Those test values are synthetic branch checks:
this pinned capture supplies **no** native calibrated-BP or BCE type to certify
against a real SEAD row.

The 13,170 `eligible` claims have the producer's `chronology_display_only`
role. All 25,109 claims retain `propagation_eligibility=refused`; this review
approves no event, ecological mapping, or scientific chronology admission.
Source qualifiers remain visible in the per-claim CSV. All **1,094** captured
dendrochronology claims labeled `From` have only one native year and no paired
row for the same analysis entity. Their captured BP conversion remains
verifiable, but the producer refuses numeric display for these open-ended
claims. Qualified uncertainty review remains open.

The producer is
`bijux_pollenomics.collection.sources.sead.evidence.review.chronology_claims`.
From the repository root, replay to an absent destination with:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -c \
  'from pathlib import Path; from bijux_pollenomics.collection.sources.sead.evidence.review.chronology_claims import write_sead_chronology_age_review; write_sead_chronology_age_review(Path("data"), Path("artifacts/jobs/sead-chronology-claim-review/replay"))'
```

The producer refuses a changed pinned index or payload digest, a mismatched
native age value or age-type ID, a changed AD conversion, duplicate or missing
claims, denominator drift, or any contextual/unresolved claim promoted to a
numeric interval. It does not reacquire a changing source snapshot.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-native/context/propagation evidence: source units and eligibility/refusal populations do not become pollen observations or ecological events.

**Supported claim.** All 25,109 captured chronology claims retain a native-age review with explicit display-only eligibility and refusal bases.

**Unsupported claim.** Synthetic calibrated-BP/BCE branch tests do not certify native SEAD rows, and display eligibility is not ecological/scientific chronology admission.

**Actual verification performed.** Read all age-basis totals and seven native-backed gold examples in report.json plus per-claim decision schema; no calibration or chronology replay.

**Remaining input or review.** Relative-period mapping, unspecified radiometric/modelled bases, open-ended uncertainty and qualified scientific use remain unresolved.

**Cause category.** Source-backed AD conversion is narrower than chronology/event approval.

**Consequence.** 13,170 display-eligible claims cannot become 13,170 propagated events.

**Precise next acceptance route.** Obtain source-specific age/calibration/uncertainty decisions and classification authority before changing claim or propagation admission.

**Negative or refused result.** 11,939 claims not display eligible; all 25,109 propagation statuses refused; 1,094 From dates lack bounded intervals.

**Matched denominator.** 25,109 claims: 13,170 bounded nonnegative AD conversions, 1,094 open-ended, 60 negative BP, 10,057 periods, 87 radiometric, 641 modelled unresolved; 1 native AD type.

Qualified authored reader SHA-256: `dbd34aebcdd2a18090d6b8608b9647a778344af81cbf71face671a2dc96ffa8a`.

- [Retained qualification evidence: docs/report/source-relations/sead/chronology-claim-review/report.json](report.json) (SHA-256 `6e1d9c759862257fafe7b8b2c32c7b9d0b8a8c9860955ed06e4772f447056fa9`).

- [Retained qualification evidence: docs/report/source-relations/sead/chronology-claim-review/claims.csv](claims.csv) (SHA-256 `e3ec1cc2c01cb9addea5247a1d116b4009b436fdab9f062efcb4ffde0a9c6546`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
