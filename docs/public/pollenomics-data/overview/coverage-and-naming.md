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

## Naming Encodes Authority

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

## Reading Counts Safely

Before comparing two counts, confirm that they share the same unit, scope,
version, and evidence stage. Project counts cannot be compared directly with
sample counts; source sites cannot be compared directly with published
features; and an excluded record remains evidence even though it is absent
from a map.
