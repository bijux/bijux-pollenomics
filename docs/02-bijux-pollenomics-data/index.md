---
title: bijux-pollenomics-data
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# bijux-pollenomics-data

`bijux-pollenomics-data` is the handbook root for tracked source inputs,
normalized datasets, field documentation, and publication-facing output
references.

Use this section when the question is about where a layer comes from, what file
family it lands in, how its provenance is preserved, or which migration hazards
exist when the data layout changes.

This section is the reader route from visible atlas layers back to the tracked
files and source families that support them. It should help a reader move from
"what am I looking at?" to "where did this come from, what was normalized, and
which checked-in outputs can I inspect?"

<div class="bijux-callout"><strong>Follow the data from source to publication.</strong> This branch is where to verify source selection, normalization rules, output families, and the field evidence that anchors visible atlas points back to real collection work.</div>

<div class="bijux-panel-grid">
  <div class="bijux-panel"><h3>Sources</h3><p>Start here when the question is about upstream origin, refresh policy, coordinate handling, or source-specific caveats.</p></div>
  <div class="bijux-panel"><h3>Outputs</h3><p>Use this branch to inspect normalized file families, report bundles, and the Nordic atlas publication surfaces.</p></div>
  <div class="bijux-panel"><h3>Fieldwork</h3><p>Use this branch when a visible point or media artifact needs to be tied back to one concrete collection visit.</p></div>
</div>

<div class="bijux-quicklinks">
  <a class="md-button md-button--primary" href="outputs/nordic-atlas/">Open atlas outputs</a>
  <a class="md-button" href="sources/source-comparison/">Compare source families</a>
  <a class="md-button" href="../04-fieldwork/lyngsjon-lake-fieldwork/">Open fieldwork record</a>
</div>

```mermaid
flowchart LR
    source["upstream source families"]
    normalize["tracked normalization rules"]
    outputs["checked-in outputs and reports"]
    field["fieldwork evidence"]
    atlas["visible atlas layers"]
    reader["reader question<br/>where did this layer come from?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    class source,page reader;
    class normalize,outputs,field,atlas positive;
    source --> normalize --> outputs --> atlas --> reader
    field --> atlas
```

## Main Paths

- [Foundation](foundation/index.md)
- [Sources](sources/index.md)
- [Outputs](outputs/index.md)
- [Fieldwork](../04-fieldwork/index.md)

## Use This Section When

- you need to trace one atlas or report layer back to its source family
- you need to understand what was normalized before publication
- the question is about tracked data provenance rather than package code or
  repository automation

## Do Not Start Here When

- the real question is about runtime commands, tests, or release tooling
- you already know the source family and only need one package behavior page
- the question is about one field visit rather than the wider tracked data tree

## What Readers Usually Need First

- upstream origin and provenance rules: [Sources](sources/index.md)
- exact file families and publication bundles: [Outputs](outputs/index.md)
- checked-in field evidence and media: [Fieldwork](../04-fieldwork/index.md)
- layout and migration constraints: [Foundation](foundation/index.md)

## Reader Takeaway

This section should help a reader move from a visible publication surface back
to the tracked evidence behind it. It is where data provenance becomes legible,
not where package runtime behavior or maintainer automation is explained.

## Purpose

Use this page to choose the right data-reference branch before reviewing one
source family or one output contract in detail.
