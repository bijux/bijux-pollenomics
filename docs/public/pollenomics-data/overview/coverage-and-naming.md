---
title: Coverage and Naming
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-07-22
---

# Coverage And Naming

Coverage is multidimensional. A source can be geographically broad but
temporally sparse, contain many project records but few recovered samples, or
support normalization without supporting publication. One count cannot
represent all of those conditions.

## Coverage Dimensions

| Dimension | Question | Example measure |
| --- | --- | --- |
| acquisition | Was the intended source material captured? | expected and recovered files, projects, papers, or supplements |
| extraction | Were usable records recovered from the capture? | extracted samples or sites versus supported expectations |
| evidence | Are identity, locality, chronology, and coordinates supported? | resolved, qualified, unresolved, and conflicting records |
| geographic | Which places are represented? | countries, regions, sites, or registered lakes |
| temporal | Which time spans and precision classes are represented? | numeric intervals, contextual labels, unresolved chronology |
| publication | Which records satisfy a named product contract? | admitted, qualified, excluded, and deferred members |

Coverage claims name both the dimension and denominator. “Twelve projects
tracked” is not equivalent to “all samples recovered,” and “four countries
published” is not equivalent to balanced source coverage across those
countries.

The resulting coverage description is a vector rather than a single score:

```text
(acquired, extracted, evidenced, geolocated, dated, admitted, published)
```

Each element has its own observation unit and denominator. Keeping those
elements separate exposes where apparent abundance becomes an evidence
bottleneck—for example, many captured rows but few supported numeric
chronologies, or many governed samples but few exact-point admissions.

## Coverage Rule

Every coverage statement names five things: the observation unit, governing
scope, source version, lifecycle stage, and denominator basis. If any of the
five is unknown, report the known counts and the unresolved denominator rather
than converting uncertainty into a percentage.

Coverage is evaluated at the boundary claimed. Capture coverage cannot stand
in for extraction coverage; extraction cannot stand in for supported
localities or chronologies; and product membership cannot stand in for source
completeness. Cross-family totals remain separate unless a comparison contract
defines a common observation unit and eligible population.

## Denominator Contract

Every coverage statement should resolve this tuple:

```text
observation unit + governing scope + source version + lifecycle stage + denominator basis
```

For example, “admitted sample points from AADR v66 within the Nordic product
scope” is interpretable only when the bundle names those members and the
denominator explains whether excluded, unresolved, and out-of-scope samples
are counted separately. Without that basis, a percentage can appear precise
while comparing different populations.

Use explicit states for the denominator:

- **known and admitted** — satisfies the named product contract;
- **known and qualified** — visible under a narrower claim;
- **known and excluded** — evaluated but outside the contract;
- **known and unresolved** — tracked but missing a required decision or fact;
- **not assessed** — belongs to the declared population but has not been
  evaluated;
- **outside scope** — not part of the denominator for this question.

Unknown is not zero, and absence from a product is not evidence of absence in
the source or historical record.

## Coverage At A Glance

| Statement | Valid denominator | Misleading substitute |
| --- | --- | --- |
| source acquisition coverage | declared upstream objects expected for the named release | all objects that might exist upstream |
| sample recovery coverage | source samples expected from captured material | number of downloaded files |
| chronology coverage | governed records assessed for chronology | only records already carrying numeric bounds |
| point-publication coverage | candidates evaluated under the named point contract | every record with a place name |
| country publication coverage | product members evaluated inside the declared geography | all repository records mentioning the country |

The denominator includes known exclusions and unresolved records when they
belong to the evaluated population. Reporting only admitted rows turns a
fitness result into a circular success rate.

## Naming Rules

Names identify ownership and scope; they must not imply evidence that the
artifact does not contain. Apply these rules to governed records and published
descendants:

- use stable repository identifiers for joins and retain source-native keys;
- include family, geography, species, version, scenario, or evidence posture
  when it changes the population a reader would infer;
- keep display names and aliases as properties rather than identity;
- reserve lifecycle terms for stages that are materially present;
- treat `final` as final for one declared contract, never as universal
  scientific finality;
- name refusals, gaps, conflicts, and exclusions by the decision they record,
  not as undifferentiated errors.

### Lifecycle Names Encode Authority

| Name component | Meaning |
| --- | --- |
| `raw` or source capture | acquired material before repository interpretation |
| `normalized` | repository-owned representation with source linkage |
| `review`, `audit`, `ledger`, or `queue` | evaluation, conflict, exclusion, or unresolved work |
| `candidate` | record evaluated for a use but not automatically published |
| `final` | admitted input for a declared downstream contract, not universal scientific finality |
| `report`, `map`, `bundle`, or `summary` | derived presentation or publication surface |

A broad name must not conceal a narrow scope. Country, region, version,
species, scenario, and evidence posture belong in the artifact identity when
they materially constrain interpretation.

## Identity And Display Names

Stable identifiers join evidence; display names help readers. A site, sample,
project, source record, and product feature may share words while remaining
different objects. Preserve their identifiers independently and record any
alias or normalized label as a property rather than using it as the join key.

Coordinates are not names. Two records at the same rounded point need not be
the same object, and one record with revised coordinates need not be a new
object. Likewise, a species label, country name, or paper title can change
without changing the governed identity it describes.

## Reading Counts Safely

Before comparing two counts, confirm that they share the same unit, scope,
version, and evidence stage. Project counts cannot be compared directly with
sample counts; source sites cannot be compared directly with published
features; and an excluded record remains evidence even though it is absent
from a map.

When a count changes, compare member identifiers first. Then classify each
addition, removal, and modification by source, normalization, curation,
admission, or scope. Aggregate arithmetic can confirm the result but cannot
explain it.

## Compare Releases By Membership

A release comparison separates four changes:

| Change | Meaning |
| --- | --- |
| added identity | a governed object entered the declared population |
| removed identity | an object left the population, with an exclusion or source reason |
| changed evidence | the object remained, but an owned fact or qualification changed |
| changed admission | the evidence remained, but product membership or role changed |

This separation prevents a corrected coordinate from appearing as a new
sample, a stricter admission rule from appearing as source loss, or a display
name change from appearing as scientific turnover. Counts summarize the
membership diff; stable identifiers and decision records explain it.
