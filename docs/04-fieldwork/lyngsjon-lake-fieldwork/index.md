---
title: Lyngsjön Lake Fieldwork
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Lyngsjön Lake Fieldwork

This page documents the field sampling visit that appears in the Nordic
Evidence Atlas as a dedicated point layer entry.

It is evidence of one documented field visit, not a substitute for the broader
source-derived layers in the atlas. Its role is to connect the atlas to a real
checked-in collection event with media that lives in this repository.

```mermaid
flowchart TD
    lake["Lyngsjön Lake visit<br/>2026-02-26"]
    media["checked-in media<br/>photo and video"]
    atlas["atlas point<br/>Fieldwork documentation"]
    context["reader context<br/>one visit tied to one map point"]
    limit["boundary<br/>does not generalize to all evidence layers"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    class lake,page media;
    class atlas,context positive;
    class limit caution;
    lake --> media
    lake --> atlas
    media --> context
    atlas --> context
    context --> limit
```

## Site

- lake: Lyngsjön Lake
- country: Sweden
- regional description: southwest of Kristianstad
- sampling date: 2026-02-26
- map coordinates used in the atlas: `55.9319529, 14.0659044`

## Why It Is Published

The repository already publishes database-derived evidence layers. This
fieldwork material adds direct checked-in documentation that the team went to
the sampling location and collected data on the lake ice.

That makes the atlas more legible for readers who want to connect one visible
map point to a real collection day rather than to a database row alone.

[Open the Nordic Evidence Atlas](https://bijux.io/bijux-pollenomics/report/nordic-atlas/nordic-atlas_map.html){ .md-button .md-button--primary }
[Open the field video](https://bijux.io/bijux-pollenomics/gallery/2026-02-26-data-collection.mp4){ .md-button }
[Open the field photo](https://bijux.io/bijux-pollenomics/gallery/2026-02-26-data-collection.JPG){ .md-button }

![Field sampling at Lyngsjön Lake on 2026-02-26.](../../gallery/2026-02-26-data-collection.JPG){ loading=lazy }

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline>
    <source src="../../gallery/2026-02-26-data-collection.mp4" type="video/mp4">
    <a href="../../gallery/2026-02-26-data-collection.mp4">Open the field video.</a>
  </video>
  <figcaption>Field documentation from Lyngsjön Lake during winter sampling on 2026-02-26. Playback starts with sound off by default.</figcaption>
</figure>

## Atlas Integration

The atlas publishes this location as `Fieldwork documentation`.

- point title: `Lyngsjön Lake field sampling`
- popup media actions: direct photo and video links
- country filter: Sweden
- layer group: environmental context

## Interpretation Boundary

The point is useful because it ties the atlas to a specific checked-in
collection event. It does not turn the atlas into a field-log system, and it
does not imply that every mapped evidence point has matching field media.

## What A Reader Can Safely Conclude

- a documented visit happened at the published location on `2026-02-26`
- the repository keeps direct media for that visit under `docs/gallery/`
- the atlas can point to repository-owned field evidence, not only upstream
  database records

## What A Reader Should Not Infer

- that this visit alone is representative of regional pollen evidence
- that atlas proximity implies analytical significance by itself
- that future field pages will always use identical media or structure

## Purpose

This page shows how the checked-in field media connects to the atlas and what
that fieldwork evidence does and does not represent.
