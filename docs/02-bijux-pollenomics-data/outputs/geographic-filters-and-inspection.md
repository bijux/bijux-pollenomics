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

- [world map](../../report/world/world_map.html)
- [Europe-plus map](../../report/regions/europe-plus/europe-plus_map.html)
- [Nordic map](../../report/regions/nordic/nordic_map.html)
- [publication geography registry](../../report/publication_geography_registry.md)
- [publication geography subset validation](../../report/publication_geography_subset_validation.md)

## What Readers Should Be Able To Inspect

- which countries are active in one scope
- which point layers remain visible after geography filtering
- whether animal points belong to the world surface only or to narrower derived views
- whether a country bundle is derived from the world surface directly or through a regional parent

The point of the inspection surface is not decoration. It is to keep geography
selection auditable for readers who did not write the code.
