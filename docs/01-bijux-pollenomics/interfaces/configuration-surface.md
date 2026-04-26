---
title: Configuration Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Configuration Surface

Configuration is centered on explicit defaults rather than on hidden discovery.

```mermaid
flowchart LR
    config["config.py defaults"]
    parser["parser option helpers"]
    commands["runtime commands"]
    artifacts["paths, names, and published outputs"]
    review["default change review"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class config,page review;
    class parser,commands,artifacts positive;
    config --> parser --> commands --> artifacts
    artifacts --> review
```

## Primary Defaults

- `DEFAULT_AADR_VERSION = "v66"`
- `DEFAULT_ATLAS_SLUG = "nordic-atlas"`
- `DEFAULT_ATLAS_TITLE = "Nordic Evidence Atlas"`
- `DEFAULT_PUBLISHED_COUNTRIES = ("Sweden", "Norway", "Finland", "Denmark")`
- default roots for `data/`, `data/aadr/`, and `docs/report/`

## Location

These defaults live in `packages/bijux-pollenomics/src/bijux_pollenomics/config.py`
and are reused by parser helpers under `command_line/parsing/options.py`.

## Review Rule

Changing a default is a public contract change because it can alter tracked
paths, published artifact names, and operator expectations.

## Reader Takeaway

Defaults are part of the interface because they shape file locations, atlas
identity, and the command outcomes readers expect to reproduce.

