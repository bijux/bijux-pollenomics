# Troitski: repeated period assertions in an unassigned source context

The native site is **Troitski**, at the recorded point **58.53458° N, 31.284126° E**.
Its membership remains **unassigned**. A bounded selected nineteen-table context profile retains 20 physical samples
and 59 source entity/date assertions. It establishes their recorded relationships,
not an independently validated chronology. The 59 assertions refer to three
period lookup records and one method; 59 dataset records point to one
bibliography record. Each of the 20 physical samples has exactly one distinct
period assignment; the 59 rows repeat those assignments at entity level. They are not 59 independent
dated artifacts or publications.

| Recorded population | Rows |
| --- | ---: |
| Native site | 1 |
| Sample groups | 20 |
| Physical samples | 20 |
| Analysis entities | 59 |
| Relative-date assertions | 59 |
| Relative-period lookup records | 3 |
| Datasets | 59 |
| Method records | 1 |
| Bibliography records | 1 |

There are **223 context rows across nineteen declared tables**. Every queried
batch reached an explicit empty source EOF page; three empty dependency sets
required no query. The full packet preserves 25 one-attempt requests and 26,016
response bytes. Its native UUID remains
`12ae88cc-a58f-4093-8afd-8cbdf1d95795`, with membership **unassigned**.

## Recorded geographic scope

The retained country decision matches the new UUID and coordinates. It records
`no_boundary_containment` and `outside_governed_boundaries`, with no candidate
country under the retained Natural Earth 5.1.1 authority. This is a preserved
classification, not a fresh polygon test or an assignment to a modern country.
It differs from a boundary-proximity review. A bibliography title mentioning
Sigtuna cannot override the native Troitski location or this membership status.

## What the dates establish

All 59 AD-note relationships agree exactly with the numeric calendar fields under
`calendar BP = 1950 - AD`. The source's three BP labels have bounds numerically 50 years
larger than the corresponding numeric calendar-BP fields. The table retains that difference instead of
choosing a reference-year convention or silently correcting the source.

| Period ID | Entity/date assertions | AD endpoints | Numeric calendar BP, older–younger | BP-label bounds, older–younger |
| --- | ---: | --- | --- | --- |
| 459 | 9 | 1100–1130 | 850–820 | 900–870 |
| 463 | 9 | 1130–1170 | 820–780 | 870–830 |
| 495 | 41 | 900–1000 | 1050–950 | 1100–1000 |

These are internal source correspondences, not independent validation of the
assigned periods. No offset, radiocarbon recalibration or harmonized interval is
supplied. The 780–1050 calendar-BP range is only an outer envelope: the three listed
intervals do not supply continuous support across the 850–950 BP gap. They do **not**
overlap the BOKE pilot's 2700–3200 calendar-BP support.

Method 128 is named **Archaeological period calendar years**, with abbreviation
`ArchPerCal`, while its description concerns pollen-zone comparison. That ambiguity prevents treating the label as a verified dating
procedure. Bibliography record 6606 is a source lead whose precise work and
edition remain unresolved; the captured record supplies neither DOI nor URL.
The bibliography is a comparative ceramic lead mentioning Sigtuna. That title
does not relocate Troitski to Sigtuna or Sweden and does not authenticate an exact
edition. These are limits on interpretation, not a reason to rewrite source
statements or admit Swedish model inputs.

This context does not establish a pollen-count denominator or an independently
verified age model. Measurement values were outside the selected projections.
Empty selected analysis-value, absolute-age, geochronology or dendrochronology
results do not prove that measurements or independent dates are absent from the
provider or the underlying study. The report makes no country, ecological-event
or LRA input admission.

## Scope and reproducibility

The earlier two-site operation remains a closed partial refusal. It observed
1,004 physical-sample identities before exhausting its page profile; it did not
establish source EOF. This distinct one-site capture used unchanged acquisition
caps and excluded the earlier request URLs. This result makes no downstream
completeness claim for site 2 or the other 124 review/unassigned roots. Their
classifications are not a request list or a requirement to collect or admit them.
Any further source-context work needs its own purpose and finite scope.
Completing this graph does not complete the two-site objective or the provider's
population.

[Verification](verification.json) records the exact source revision, closed
manifest and file digests, request/graph checks and the separate period-arithmetic
qualification. This public account contains summaries and hash provenance;
it does not redistribute source notes or full descriptions. A reader who already
holds an authorized copy of the complete capsule can reopen it with the
maintained API:

```python
from pathlib import Path
from bijux_pollenomics.collection.sources.sead.acquisition.context import read_sead_context

metadata = read_sead_context(
    Path("retained-sead-site-3441-context"),
    expected_manifest_sha256="24d18d4fa581d1ee9423dec61eb28bb68137d11306d81ad76823dfd7ec94432a",
)
assert metadata["sites"][0]["site_id"] == 3441
assert metadata["country_admission"] is False
assert metadata["ecological_event_admission"] is False
```

Readback consumes the caller's full local capsule, including its source text;
this public summary alone cannot reconstruct it. The API performs no provider
acquisition. The [captured source revision](https://github.com/bijux/bijux-pollenomics/tree/7df5a6dbbf235361d2969a11b50425a049436c6d)
is preserved independently of later library changes.

The [official SEAD provider](https://browser.sead.se/) and its
[bibliography record 6606](https://browser.sead.se/postgrest/tbl_biblio?biblio_id=eq.6606&select=biblio_id,title,year,doi,url)
are discovery leads, not authentication of an exact paper or edition. No source
license or scientific applicability is inferred from an accessible endpoint.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** One unassigned native Troitski context retains 20 physical samples, 59 repeated entity/date assertions, three period lookups and an exactly pinned complete selected nineteen-table context profile (sixteen queried EOF batches and three empty-dependency no-query tables); all 59 AD-note relationships match the numeric fields under a 1950 reference.

**Unsupported claim.** No Swedish or other country assignment, independent dating, authenticated period interpretation, pollen-count denominator, ecological event, LRA input admission or BOKE 2700–3200 calendar-BP applicability.

**Actual verification performed.** Finite acquisition completed 25 one-attempt requests. Separate saved-output byte/namespace/native-identity/EOF checks retained exact scalar/null correspondence; six source-pinned payloads supported 59 arithmetic/ownership checks and five refused semantic alterations. No qualification reran acquisition or models.

**Remaining input or review.** Method 128 name/description, bibliography 6606 exact work/edition, and the 50-year label/numeric convention remain unresolved. Source notes and full descriptions are not included in this public summary. Resolver: source-method and bibliographic maintainer Reopen when: An authenticated method/edition and explicit calendar convention establish the intended interpretation for this exact source packet.

**Cause category.** Source-context qualification with repeated assertions and unresolved calendar/method/bibliography meaning.

**Consequence.** The recorded Troitski point is not Sigtuna or a Swedish cohort merely because a bibliography title mentions Sigtuna; its 780–1050 calendar-BP fields do not overlap the BOKE 2700–3200 support.

**Precise next acceptance route.** Reopen an authorized complete capsule with the maintained public reader and exact manifest pin; separately authenticate source meaning and qualify target support before any country, event or numerical input admission.

**Negative or refused result.** The earlier two-site attempt remains refused after 1004 observed physical rows without EOF. Complete single-site context does not settle that wider scope, correct the 50-year difference or establish absence of counts or independent dates in unqueried measurement tables.

**Matched denominator.** One native site, 20 physical samples, 59 entity/date assertions, three period lookup rows, 59 datasets and one bibliography. Each physical sample has one distinct period; repeated entity assertions are not independent samples, dates or publications.

Retained evidence: [reports/science/chronology/sead/troitski-site-3441/verification.json](verification.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
