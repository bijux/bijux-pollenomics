---
title: Reports
audience: mixed
type: index
status: canonical
owner: bijux-pollen-docs
last_reviewed: 2026-03-23
---

# Reports

This section explains the browser-facing and file-facing outputs generated from the tracked `data/` tree.

## Pages in This Section

- [Country reports](country-reports.md)
- [Shared Nordic map](shared-nordic-map.md)
- [Published artifacts](published-artifacts.md)

```mermaid
flowchart TD
    Data[data/] --> CountryReports[Per-country reports]
    Data --> SharedMap[Shared Nordic map]
    CountryReports --> Review[Human review]
    SharedMap --> Review
```

## Canonical Status

This section is the canonical source for report and map documentation inside the docs site. It replaces the older narrative content that previously lived in separate `docs/report/...` guide pages.

## Purpose

This page organizes the output-side documentation for `bijux-pollen`.
