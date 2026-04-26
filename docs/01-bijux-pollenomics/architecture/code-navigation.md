---
title: Code Navigation
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Code Navigation

Open the following path when you need to trace behavior quickly.

```mermaid
flowchart TD
    question["question type"]
    cli["CLI and parsing"]
    dispatch["dispatch and handlers"]
    source["source collection"]
    report["report publishing"]
    tests["tests"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class question,page cli;
    class dispatch,source,report,tests positive;
    question --> cli
    question --> dispatch
    question --> source
    question --> report
    question --> tests
```

## Start Points By Question

- command syntax or default flags: start in `cli.py` and
  `command_line/parsing/`
- command dispatch behavior: read `command_line/runtime/dispatch.py` and
  `handlers.py`
- source collection behavior: read `data_downloader/api.py`, `collector.py`,
  and `pipeline/`
- source-specific quirks: move into `data_downloader/sources/<source>/`
- report publishing behavior: read `reporting/service.py`, `reporting/api.py`,
  and `reporting/bundles/`
- rendered output shape: inspect `reporting/rendering/` and
  `reporting/map_document/`

## Test Navigation

- unit behavior: `tests/unit/`
- output regression checks: `tests/regression/`
- CLI behavior: `tests/e2e/test_cli.py`

## Bottom Line

This page is for fast orientation, not for architectural argument. It helps
you reach the right directory quickly when you already know the kind of
behavior you are trying to inspect.

