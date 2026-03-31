---
title: Architecture
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-23
---

# Architecture

This section explains how the repository is put together and where responsibilities live.

## Pages in This Section

- [System overview](system-overview.md)
- [Data collection flow](data-collection-flow.md)
- [Codebase layout and ownership](codebase-layout-and-ownership.md)

## Core Boundary

```mermaid
flowchart LR
    Downloader[data_downloader] --> DataTree[data/]
    DataTree --> Reporting[reporting/]
    Reporting --> DocsReport[docs/report/]
    DocsReport --> MkDocs[documentation site]
```

## Purpose

This page organizes the architecture explanations for the repository.
