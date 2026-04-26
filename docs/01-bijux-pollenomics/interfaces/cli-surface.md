---
title: CLI Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# CLI Surface

The CLI is the primary public interface for `bijux-pollenomics`.

```mermaid
flowchart LR
    cli["bijux-pollenomics CLI"]
    collect["collect-data"]
    country["report-country"]
    atlas["report-multi-country-map"]
    publish["publish-reports"]
    outputs["tracked data and docs/report outputs"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class cli,page outputs;
    class collect,country,atlas,publish positive;
    cli --> collect --> outputs
    cli --> country --> outputs
    cli --> atlas --> outputs
    cli --> publish --> outputs
```

## Supported Commands

- `collect-data <sources...>` collects tracked datasets into `data/`
- `report-country <country>` publishes one country bundle from AADR metadata
- `report-multi-country-map <countries...>` builds the shared atlas for a
  chosen country set
- `publish-reports` regenerates the checked-in publication bundle set using the
  repository defaults

## Shared Options

- `--version` selects the AADR version directory and defaults to `v66`
- `--aadr-root` defaults to `data/aadr`
- `--output-root` defaults to `data` for collection or `docs/report` for
  report publishing
- `--context-root` defaults to `data`
- `--name` and `--title` control the atlas slug and display title

## Core Point

These commands are not merely convenience wrappers. They are the stable
operator surface for rewriting tracked repository state in a reviewable way.

