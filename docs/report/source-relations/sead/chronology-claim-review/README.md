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
| AD calendar years with nonnegative BP result | 14,264 | `1950 − native AD year` matches both captured BP endpoints; eligible for chronology display only |
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

The 14,264 `eligible` claims have the producer's `chronology_display_only`
role. All 25,109 claims retain `propagation_eligibility=refused`; this review
approves no event, ecological mapping, or scientific chronology admission.
Source qualifiers remain visible in the per-claim CSV. In particular, **1,094**
dendrochronology claims carry the native `From` uncertainty label even where
the current producer records a display-eligible calendar-year boundary. This
review verifies their age basis and captured conversion; it does not certify
that an open-ended source qualifier is a bounded physical dating interval.
Qualified uncertainty review remains open.

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
