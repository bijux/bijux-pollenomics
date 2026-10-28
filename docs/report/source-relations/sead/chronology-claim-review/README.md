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


## Native annotation custody

The [all-field audit](native-annotations.json) independently checks all **25,109**
captured native date rows across five date kinds, **202,546** original field
cells and their physical, method and reference ownership across **17** tables.
The private typed witness retains every original field and value, including
**56,721** null cells. The source archive and normalized chronology remain
unchanged. The [source account](native-annotations-source.json) binds the actual
producer, independent comparison, resource observations and preserved failed
verification receipts.

| Native field comparison | Cells |
| --- | ---: |
| Exact JSON value and type | 186,797 |
| Native null stored as an empty string | 14,230 |
| Numeric type differs but exact rational value agrees | 1,519 |
| **All native field cells** | **202,546** |

**8,678** claims have at least one stored representation difference. Native
method and uncertainty-label lookups separately have **11,923** exact comparisons
and **47,070** null-to-empty-string comparisons. These are different populations
from native field cells. This audit approves none of these changes as
scientifically harmless. This capture has no null uncertainty-flag cells; the
guards retain such unknown flags in controlled examples instead of silently
converting them into known false values.

The six captured uncertainty definitions and native method/reference relations
are retained explicitly. There are **1,097** `From` uncertainty-label occurrences
across all date kinds; the earlier **1,094** open-ended dendrochronology claims
remain their own population. Missing calibration and model authority, qualified
uncertainty decisions and biological interpretation remain unresolved. All
**25,109** propagation statuses remain refused, with **zero** admitted events.

The maintained producer is
`bijux_pollenomics_dev.source_completion.sead.chronology_annotations`.
With absent public and private artifact destinations, it can replay the aggregate
while keeping the detailed witness outside the public output tree:

```sh
python -m bijux_pollenomics_dev.source_completion.sead.chronology_annotations \
  --repository . --output artifacts/jobs/sead-native-annotations/public \
  --retained-artifacts-root artifacts/jobs/sead-native-annotations/private
```

The configured report owner supplies these paths independently. It refuses
changed source pins, native-row additions/omissions, duplicate or noninteger
native keys, mismatched ownership/reference relations and overlapping or escaped
public/private output destinations. Private witness data is not a report
publication output.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-native/context/propagation evidence: source units and eligibility/refusal populations do not become pollen observations or ecological events.

**Supported claim.** All 25,109 captured chronology claims retain a native-age review and an independent comparison of 202,546 original typed fields, physical ownership and method/reference relations; display and propagation refusals remain explicit.

**Unsupported claim.** Synthetic calibrated-BP/BCE branch tests do not certify native SEAD rows, and display eligibility is not ecological/scientific chronology admission.

**Actual verification performed.** Actual source-bound producer and independent all-row/type/ownership/aggregate verifier passed; 83 annotation, runtime-isolation, receipt and result-schema guards, configured strict typing and lint passed. No calibration, age-model fit or new event admission. Two actual maintained configured reference/replay commands independently reproduced the public aggregate and private witness byte-for-byte; 71 producer/public-private isolation guards and strict10/source lint passed. Canonical ownership and reader validation are separate.

**Remaining input or review.** Relative-period mapping, unspecified radiometric/modelled bases, open-ended uncertainty, scientific equivalence of stored representations and qualified scientific use remain unresolved.

**Cause category.** Source-backed AD conversion is narrower than chronology/event approval.

**Consequence.** 13,170 display-eligible claims cannot become 13,170 propagated events.

**Precise next acceptance route.** Obtain source-specific age/calibration/uncertainty decisions and classification authority before changing claim or propagation admission.

**Negative or refused result.** 8,678 claims differ in stored representation: 14,230 native null field cells become empty strings and 1,519 numeric representations change at equal exact value. No harmlessness approval; all 25,109 propagation statuses remain refused, including 1,094 unbounded dendrochronology From claims.

**Matched denominator.** 25,109 claims / 202,546 native field cells across five date kinds and 17 source tables; 186,797 exact cells, 14,230 null-to-empty and 1,519 numeric-type changes. Original age-basis totals and 13,170 display-only claims remain unchanged.

- [Retained qualification evidence: docs/report/source-relations/sead/chronology-claim-review/report.json](report.json) (SHA-256 `6e1d9c759862257fafe7b8b2c32c7b9d0b8a8c9860955ed06e4772f447056fa9`).

- [Retained qualification evidence: docs/report/source-relations/sead/chronology-claim-review/claims.csv](claims.csv) (SHA-256 `e3ec1cc2c01cb9addea5247a1d116b4009b436fdab9f062efcb4ffde0a9c6546`).

- [Retained qualification evidence: docs/report/source-relations/sead/chronology-claim-review/native-annotations.json](native-annotations.json) (SHA-256 `09940763f6124591f1696fa253d52b259ff410d79798abcb82d56d4868e3f240`).

- [Retained qualification evidence: docs/report/source-relations/sead/chronology-claim-review/native-annotations-source.json](native-annotations-source.json) (SHA-256 `9c252ea5104c0c79de757b659db60db9c59e43d8deadc501e0ca4be5a821311e`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
