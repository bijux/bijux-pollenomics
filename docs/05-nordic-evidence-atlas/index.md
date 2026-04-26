---
title: Nordic Evidence Atlas
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Nordic Evidence Atlas

The Nordic Evidence Atlas is the shared Nordic map publication.

Open this page when the fastest path is to inspect what readers actually see
before reviewing source-specific tables, normalized outputs, or package
internals.

The atlas is not just an image or a convenience link. It is the main public
evidence surface of the repository. This page helps readers move
from a visible layer, point, or polygon to the exact source, output, fieldwork,
or runtime explanation that can support or limit what they think they are
seeing.

```mermaid
flowchart LR
    reader["reader question<br/>what does this visible layer actually mean?"]
    atlas["Nordic Evidence Atlas<br/>interactive publication"]
    layers["visible layers<br/>AADR, pollen, archaeology, fieldwork, boundaries"]
    outputs["output reference<br/>checked-in atlas assets"]
    sources["source reference<br/>where each layer originates"]
    fieldwork["fieldwork row<br/>direct visit context"]
    package["runtime handbook<br/>commands that rebuild publication"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    class reader page;
    class layers,outputs,sources,fieldwork,package positive;
    atlas --> layers
    layers --> reader
    reader --> outputs
    reader --> sources
    reader --> fieldwork
    reader --> package
```

<div class="bijux-quicklinks">
  <a class="md-button md-button--primary" href="https://bijux.io/bijux-pollenomics/report/nordic-atlas/nordic-atlas_map.html">Open the Nordic Evidence Atlas</a>
  <a class="md-button" href="https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/outputs/nordic-atlas/">Open atlas output reference</a>
  <a class="md-button" href="https://bijux.io/bijux-pollenomics/04-fieldwork/">Open fieldwork row</a>
</div>

<div class="bijux-map-mobile-note">
  <strong>Phone view:</strong> Open the atlas in its own tab for full map
  controls.
</div>

<div class="bijux-map-frame">
  <iframe src="https://bijux.io/bijux-pollenomics/report/nordic-atlas/nordic-atlas_map.html" title="Nordic Evidence Atlas"></iframe>
</div>

## Start Here

- open the atlas first when you need to inspect what a reader actually sees on
  the publication surface
- move to [atlas output reference](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/outputs/nordic-atlas/)
  when the question is about generated files, checked-in assets, or publication
  packaging
- move to [data reference](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/sources/) when the real
  question is where a visible layer or record originates
- move to [fieldwork](https://bijux.io/bijux-pollenomics/04-fieldwork/) when a point appears to represent a
  documented visit and you need direct local context
- move to [runtime handbook](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/) when the question is how
  the atlas was rebuilt, validated, or packaged

## Use This Page When

- opening the current atlas quickly without navigating through output reference
  pages first
- checking the publication surface that readers will actually inspect
- branching into data, fieldwork, or package docs once a concrete atlas
  question appears

## Do Not Use This Page When

- explaining every upstream data caveat in detail
- documenting rebuild commands or release automation
- replacing the output-reference pages that describe the checked-in atlas files
- assuming the map alone is sufficient evidence without checking source or
  fieldwork context

## Concrete Anchors

- `docs/report/nordic-atlas/nordic-atlas_map.html` for the checked-in map
  publication itself
- `docs/report/nordic-atlas/_map_assets/` for the shipped atlas asset bundle
- [atlas output reference](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/outputs/nordic-atlas/)
  for publication files and generated atlas components
- [data reference](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/sources/) and
  [fieldwork](https://bijux.io/bijux-pollenomics/04-fieldwork/) for the two main routes from a visible map
  element back to supporting evidence

## Reader Takeaway

The atlas is the fastest way to see the published evidence surface, not the
only place where meaning lives. A trustworthy read usually starts here and then
branches outward into source, output, fieldwork, or runtime docs depending on
what the visible map element is actually claiming.

## Purpose

Open this page when you need direct access to the map publication and the
nearest routes into the source, output, fieldwork, or runtime docs behind it.

## Stability

This page is canonical and should remain a direct wrapper around the checked-in
`docs/report/nordic-atlas/` publication output.
