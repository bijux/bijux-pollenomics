---
title: Fieldwork
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Fieldwork

Fieldwork is the checked-in evidence layer for real sampling visits.

Open this section when a map point or normalized source record needs direct
on-site collection context.

This section is intentionally narrow. It does not try to replace the atlas, the
data reference, or a full field-log system. Its job is to preserve the direct
human record behind a documented visit: where the team went, when sampling
happened, and which media artifacts support that record.

```mermaid
flowchart LR
    reader["reader question<br/>what really happened at this place?"]
    atlas["atlas point or visible field marker"]
    record["fieldwork page<br/>visit facts, media, local context"]
    facts["date, place, and collection context"]
    media["photos, video, and supporting artifacts"]
    data["data reference<br/>source-derived interpretation"]
    boundary["boundary<br/>a visit record is narrow evidence"]
    planner["future return visits<br/>repeatable local context"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    class reader page;
    class atlas,record,facts,media,data,planner positive;
    class boundary caution;
    atlas --> record
    record --> facts
    record --> media
    record --> data
    record --> planner
    record --> boundary
    record --> reader
```

The [Nordic Evidence Atlas](https://bijux.io/bijux-pollenomics/report/nordic-atlas/nordic-atlas_map.html)
remains the main decision surface for comparing mapped evidence layers. This
section lets readers follow one visible atlas point back to a real visit
instead of treating every layer as equally abstract.

## Start Here

- open [Lyngsjön Lake Fieldwork](https://bijux.io/bijux-pollenomics/04-fieldwork/lyngsjon-lake-fieldwork/) for the
  current documented visit record
- open the [Nordic Evidence Atlas](https://bijux.io/bijux-pollenomics/report/nordic-atlas/nordic-atlas_map.html)
  when the question starts from a visible map layer and you need to confirm
  whether fieldwork supports it
- open [data reference](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/) when the question is
  really about source provenance or normalization rather than on-site context
- open [Nordic Evidence Atlas](https://bijux.io/bijux-pollenomics/05-nordic-evidence-atlas/) when the wider
  question is how one visit sits among the full visible evidence stack

## Pages In Fieldwork

- [Lyngsjön Lake Fieldwork](https://bijux.io/bijux-pollenomics/04-fieldwork/lyngsjon-lake-fieldwork/)

## Open This Section When

- confirming that a mapped fieldwork point refers to a documented visit
- checking the exact date, location, and media attached to that visit
- distinguishing direct field evidence from source-derived atlas layers
- preparing repeat visits or local interpretation with the original visit
  context in view

## Choose Another Section When

- inferring that every atlas point has matching field documentation
- treating one visit as proof of regional sampling completeness
- replacing the data reference when the real question is provenance or
  normalization
- expecting maintainers' workflow or publication instructions

## Concrete Anchors

- `docs/gallery/2026-02-26-data-collection.JPG` and
  `docs/gallery/2026-02-26-data-collection.mp4` for the current checked-in
  field media
- [Lyngsjön Lake Fieldwork](https://bijux.io/bijux-pollenomics/04-fieldwork/lyngsjon-lake-fieldwork/) for the canonical
  visit record
- [Nordic Evidence Atlas](https://bijux.io/bijux-pollenomics/05-nordic-evidence-atlas/) for the wider
  publication surface that this row supports without replacing
- [data reference](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/) for provenance and
  normalization questions that exceed one visit record

## Reader Takeaway

Fieldwork pages answer a narrow but important question with integrity:
what exactly happened at this place on this date, and what direct artifacts
support that statement. They do not quietly expand into claims about the
whole atlas or the full regional evidence base.

