---
title: Artifact Contracts
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Artifact Contracts

Published artifacts are part of the package contract because they are checked in
and reviewed like code. Readers do not experience these files as incidental
build leftovers. They experience them as the actual atlas and country-report
surface that the runtime promises to keep reproducible.

```mermaid
flowchart LR
    reporting["reporting bundle logic"]
    country["country bundle file families"]
    atlas["shared atlas file families"]
    summaries["summary, payload, and map assets"]
    review["reader question<br/>which published files are stable contracts?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class reporting,page review;
    class country,atlas,summaries positive;
    reporting --> country --> review
    reporting --> atlas --> review
    reporting --> summaries --> review
```

## Main Artifact Families

- country bundles under `docs/report/<country-slug>/`
- the shared atlas under `docs/report/nordic-atlas/`
- report summaries and map payloads produced by the reporting package

## Stable Path Anchors

- `reporting/bundles/paths.py` defines the named path families for country and
  atlas bundles
- country bundles include `README.md`, sample and locality CSV files, sample
  GeoJSON, sample Markdown, and summary JSON outputs
- atlas bundles include `README.md`, the map HTML document, sample GeoJSON, and
  summary JSON outputs
- bundled map assets copied by the rendering layer are part of the publication
  surface because broken assets break the published reader experience

## Contract Anchors

- `reporting/bundles/paths.py`
- `reporting/rendering/`
- `reporting/map_document/`

## Open This Page When

- a change alters output paths, slugs, file names, or report bundle contents
- reviewers need to know whether a docs/report diff is a contract change
- a renderer or publisher change may affect the files the website consumes

## Open Another Page When

- the real concern is command syntax rather than published file outputs
- you need package ownership or module layout before judging the contract
- the question is only about how to run the workflow, not what it must emit

## Review Rule

If an output path, slug, or file family changes, treat it as an interface change
and update docs plus tests together with the code.

## Proof Expectations

- pair artifact-surface changes with the narrowest relevant tests, usually
  `tests/unit/test_reporting_artifacts.py` or the regression bundle tests
- treat map asset completeness as part of the contract, not just cosmetic
  packaging
- explain intentional artifact changes in docs before expecting reviewers to
  infer the new publication shape from generated diffs alone

## Core Point

Artifact contracts matter because the website and repository review process both
consume these files directly. Breaking them is not an internal refactor.

