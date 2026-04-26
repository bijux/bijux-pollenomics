---
title: Nordic Evidence Atlas
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Nordic Evidence Atlas

This page is the dedicated root row for the shared Nordic map publication.

Use it when the fastest path is to inspect the live publication surface before
reviewing source-specific tables, normalized outputs, or package internals.

```mermaid
flowchart LR
    atlas["Nordic Evidence Atlas<br/>interactive publication"]
    layers["visible layers<br/>AADR, pollen, archaeology, fieldwork, boundaries"]
    outputs["output reference<br/>checked-in atlas assets"]
    sources["source reference<br/>where each layer originates"]
    package["package handbook<br/>commands that rebuild publication"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    class atlas,page layers;
    class outputs,sources,package positive;
    atlas --> layers
    atlas --> outputs
    atlas --> sources
    atlas --> package
```

<div class="bijux-quicklinks">
  <a class="md-button md-button--primary" href="../report/nordic-atlas/nordic-atlas_map.html">Open the Nordic Evidence Atlas</a>
  <a class="md-button" href="../02-bijux-pollenomics-data/outputs/nordic-atlas/">Open atlas output reference</a>
  <a class="md-button" href="../04-fieldwork/">Open fieldwork row</a>
</div>

<div class="bijux-map-mobile-note">
  <strong>Phone view:</strong> Open the atlas in its own tab for full map
  controls.
</div>

<div class="bijux-map-frame">
  <iframe src="../report/nordic-atlas/nordic-atlas_map.html" title="Nordic Evidence Atlas"></iframe>
</div>

## What This Page Is For

- opening the current atlas quickly without navigating through output reference
  pages first
- checking the publication surface that readers will actually inspect
- branching into data, fieldwork, or package docs once a concrete atlas
  question appears

## What This Page Is Not For

- explaining every upstream data caveat in detail
- documenting rebuild commands or release automation
- replacing the output-reference pages that describe the checked-in atlas files

## Purpose

Provide a stable first-class docs row for the map publication so both top
navigation and side navigation expose the atlas directly.

## Stability

This page is canonical and should remain a direct wrapper around the checked-in
`docs/report/nordic-atlas/` publication output.
