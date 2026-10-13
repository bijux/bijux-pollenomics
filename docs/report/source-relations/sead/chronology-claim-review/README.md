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

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
