---
title: Sweden Lake Priorities
audience: reader
type: explainer
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-06-28
---

# Sweden Lake Priorities

The Nordic atlas now carries optional Sweden lake ranking overlays so readers
can inspect the strongest lake candidates without leaving the shared map.
These layers stay **off by default** because they are a ranked interpretation
surface, not a base evidence surface. The governing packet still lives in the
Sweden report tree, and the atlas overlay should only help readers inspect the
same ranked packet in geographic context.

Use this page when you need to understand what the Sweden lake overlays are
actually ranking, what they are not ranking, and how far those scores should be
trusted before field planning.

## What The Overlay Shows

The public Sweden lake packet currently ranks **6,763** registry-backed lake
candidates. The Nordic atlas exposes the following optional overlays:

- aggregate top 40
- consensus top 40
- 10 km top 40
- 20 km top 40
- 30 km top 40
- 40 km top 40
- 50 km top 40
- fieldwork shortlist top 20

The fieldwork shortlist remains top 20 because that is the governed public
shortlist published by the Sweden packet today. The other scenario layers now
expose the top 40 rows directly on the map.

## How Ranking Works

The candidate pool comes from the Sweden lake registry published through SMHI
SVAR. Each lake uses one representative point derived from the official lake
polygon rather than a pollen-site centroid. Only lakes with at least one human
aDNA locality within 50 km remain in the ranked set.

Aggregate ranking blends the five radius scenarios with these weights:

| Radius scenario | Weight |
| --- | ---: |
| 10 km | 0.35 |
| 20 km | 0.27 |
| 30 km | 0.18 |
| 40 km | 0.12 |
| 50 km | 0.08 |

Inside each scenario, the public packet weights evidence families like this:

| Evidence component | Weight |
| --- | ---: |
| Human aDNA signal | 0.59 |
| Direct pollen signal | 0.14 |
| Nearby pollen signal | 0.07 |
| Lake sampling fit | 0.07 |
| Archaeology signal | 0.07 |
| Domesticated animal signal | 0.04 |
| Evidence diversity signal | 0.02 |

The decision rule is intentionally conservative:

- human aDNA locality and sample coverage decide the ranking first
- direct pollen support is the next tie-break
- broader pollen and archaeology context come after that
- sampling fit and blended score resolve later ties

The consensus overlay is different from the aggregate overlay. It lifts lakes
that recur across multiple scenario top slices, then breaks ties by the mean
scenario rank and finally by aggregate rank.

## What These Scores Do Not Include

The public ranking is useful, but it is deliberately narrower than a full site
selection workflow. It does not currently ship:

- governed bathymetry or coring-depth surfaces
- shoreline access, permits, or landowner logistics
- a field-confirmed judgment that one lake is already ready for sampling
- a claim that the highest-scoring row is the best scientific target under all
  practical constraints

## What Lake Properties Are Public

Each mapped lake row currently ships these reader-facing properties:

- registry-backed coordinates
- aggregate rank and aggregate score
- scenario rank and scenario score
- lake registry identifier
- lake area in square kilometers
- sampling posture and sampling fit
- duplicate-name and coordinate-spread diagnostics
- supporting scenario-presence counts

This is enough to compare evidence density against basic lake suitability, but
it is **not** a full limnology packet. The current public packet does **not**
ship governed depth, width, bathymetry, coring logistics, or access-permit
surfaces. Where a row says `compact_lake_candidate`, `small_lake_review`, or
`sampling_lake_candidate`, that is a ranking posture, not a substitute for
field bathymetry or basin-shape verification.

## Current High-Ranking Lakes

The public atlas page should let readers see concrete examples quickly, so the
table below mirrors the top of the current aggregate registry packet.

| Aggregate rank | Lake | Aggregate score | Scenario top-20 presence | Area km² | Sampling posture |
| ---: | --- | ---: | ---: | ---: | --- |
| 1 | Bergsjön | 0.5947 | 4 | 0.063346 | `compact_lake_candidate` |
| 2 | Hulesjön | 0.5875 | 3 | 0.037617 | `small_lake_review` |
| 3 | Sjötorpasjön | 0.5862 | 7 | 0.603122 | `sampling_lake_candidate` |
| 4 | Hornborgasjön | 0.5037 | 6 | 27.925549 | `sampling_lake_candidate` |
| 5 | Skårsjön | 0.4818 | 3 | 0.021492 | `small_lake_review` |
| 6 | Rösjön | 0.4651 | 6 | 0.956929 | `sampling_lake_candidate` |
| 7 | Bjärsjön | 0.4573 | 6 | 0.132579 | `compact_lake_candidate` |
| 8 | Tresjö | 0.4433 | 3 | 0.104225 | `compact_lake_candidate` |
| 9 | Vartoftasjön | 0.4186 | 4 | 0.154654 | `sampling_lake_candidate` |
| 10 | Alasjön | 0.4053 | 4 | 0.191045 | `sampling_lake_candidate` |
| 11 | Ullstorpasjön | 0.3983 | 4 | 0.290248 | `sampling_lake_candidate` |
| 12 | Häckebergasjön | 0.3859 | 3 | 0.758596 | `sampling_lake_candidate` |

Readers who need the full ranked set should use the CSV and markdown artifacts
below instead of treating this table as the entire packet.

## How To Read The Layers

- Use the aggregate layer when you want the strongest blended ranking.
- Use the consensus layer when you want lakes that stay near the top across
  multiple ranking scenarios.
- Use the radius layers when you want to inspect how nearby evidence density
  changes as the search window expands.
- Use the fieldwork shortlist when you want the current public set that already
  leans toward sampling practicality and reduced identity ambiguity.

When a lake looks promising on the map, the next step should be the report
packet, not a stronger claim. The atlas helps you inspect the ranking in
geographic context; the governing evidence still lives in the Sweden report
artifacts linked below.

## Governing References

- [Nordic atlas landing page](../index.md)
- [Open the Nordic evidence surface](../../../report/regions/nordic/nordic_map.html)
- [Sweden lake evidence richness markdown](../../../report/countries/sweden/sweden_lake_evidence_richness_v66.md)
- [Sweden lake evidence registry CSV](../../../report/countries/sweden/sweden_lake_evidence_richness_v66_registry.csv)
- [Sweden lake evidence scenarios CSV](../../../report/countries/sweden/sweden_lake_evidence_richness_v66_scenarios.csv)
- [Sweden lake evidence bands CSV](../../../report/countries/sweden/sweden_lake_evidence_richness_v66_bands.csv)
- [Sweden lake fieldwork preparation markdown](../../../report/countries/sweden/sweden_lake_fieldwork_preparation_v66.md)
- [How filters and popups work](../../pollenomics-data/publications/filters-and-popups.md)
- [Current map limits and audits](../../pollenomics-data/publications/limits.md)
