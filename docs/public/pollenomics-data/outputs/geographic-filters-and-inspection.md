---
title: Geographic Filters and Inspection
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# Geographic Filters and Inspection

The public map should make geography filtering understandable instead of
silently burying it in code. World, Europe-plus, Nordic, and country views are
all governed by explicit scope rules.

## Reader Anchors

- [world map](../../../report/world/world_map.html)
- [world map publication contract](../../../report/world/world_map_publication_contract.md)
- [Europe-plus map](../../../report/regions/europe-plus/europe-plus_map.html)
- [Europe-plus map publication contract](../../../report/regions/europe-plus/europe-plus_map_publication_contract.md)
- [Nordic map](../../../report/regions/nordic/nordic_map.html)
- [Nordic map publication contract](../../../report/regions/nordic/nordic_map_publication_contract.md)
- [Nordic point traceability](../../../report/regions/nordic/nordic_point_traceability.md)
- [publication geography registry](../../../report/publication_geography_registry.md)
- [publication geography subset validation](../../../report/publication_geography_subset_validation.md)

## What Readers Should Be Able To Inspect

- which countries are active in one scope
- which point layers remain visible after geography filtering
- why Nordic-only context overlays disappear when a reader moves back to world or Europe-plus
- whether animal points belong to the world surface only or to narrower derived views
- whether a country bundle is derived from the world surface directly or through a regional parent

The point of the inspection surface is not decoration. It is to keep geography
selection auditable for readers who did not write the code.

## Nordic Atlas Filters And Popups

The Nordic atlas inherits these filtering rules from the wider publication
geography contract. Popups should expose why a point is visible, not hide the
selection logic behind front-end convenience.

Readers should still be able to answer:

- why a point is visible in Nordic scope but not in a broader or narrower surface
- which publication scope owns the point currently on screen
- which traceability document backs the popup claims
- whether a filter is hiding rows because of geography, evidence weakness, or release posture

## Nordic Reader Anchors

- [Nordic evidence atlas](../../nordic-atlas/index.md)
- [Nordic evidence surface](../../../report/regions/nordic/README.md)
- [Nordic map publication contract](../../../report/regions/nordic/nordic_map_publication_contract.md)
- [publication geography registry](../../../report/publication_geography_registry.md)
