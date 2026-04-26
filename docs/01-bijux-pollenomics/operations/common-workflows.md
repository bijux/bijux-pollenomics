---
title: Common Workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Common Workflows

Most package work falls into a short list of repeatable workflows.

```mermaid
flowchart TD
    verify["make check"]
    collect["make data-prep or collect-data"]
    reports["make reports or publish-reports"]
    intent["choose the workflow that matches intent"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class verify,page intent;
    class collect,reports positive;
    verify --> intent
    collect --> intent
    reports --> intent
```

## Verify The Current State

Run `make check` when the goal is to validate code, docs, API, packaging, and
shared repository contracts without refreshing tracked scientific outputs.

## Refresh Tracked Data

Run `make data-prep` or the equivalent `bijux-pollenomics collect-data ...`
command when upstream source material or normalization logic needs a deliberate
refresh.

## Refresh Published Artifacts

Run `make reports` or `bijux-pollenomics publish-reports ...` when country
bundles or the atlas need regeneration from current tracked inputs.

## Reader Takeaway

The main operational discipline is choosing the narrowest workflow that matches
the goal. Broad commands are not safer just because they feel more complete.

