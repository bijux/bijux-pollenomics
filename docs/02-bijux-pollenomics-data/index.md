---
title: bijux-pollenomics-data
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# bijux-pollenomics-data

`bijux-pollenomics-data` is the provenance and output handbook for the tracked
evidence tree. Open it when the real question is where a visible layer came
from, what was normalized, which file family became authoritative, or how a
layout change would ripple through the repository.

<div class="bijux-callout"><strong>Follow the evidence from source to tracked file to published surface.</strong> This branch explains source selection, normalization rules, output families, and the narrow fieldwork record that anchors one visible map point to a real visit.</div>

<div class="bijux-quicklinks">
  <a class="md-button md-button--primary" href="https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/outputs/nordic-atlas/">Open atlas outputs</a>
  <a class="md-button" href="https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/sources/source-comparison/">Compare source families</a>
  <a class="md-button" href="https://bijux.io/bijux-pollenomics/04-fieldwork/lyngsjon-lake-fieldwork/">Open fieldwork record</a>
</div>

## Evidence Route

```mermaid
flowchart LR
    Sources["source families"] --> Rules["selection and normalization rules"]
    Rules --> Tree["tracked data tree"]
    Tree --> Outputs["normalized output families"]
    Outputs --> Reports["country bundles"]
    Outputs --> Atlas["Nordic atlas"]
    Fieldwork["direct visit record"] --> Atlas
    Atlas --> Reader["visible layer question"]
    Reports --> Reader

    class Sources,Fieldwork anchor;
    class Rules action;
    class Tree,Outputs page;
    class Reports,Atlas positive;
    class Reader caution;

    classDef page fill:#eef6ff,stroke:#2563eb,color:#153145,stroke-width:2px;
    classDef positive fill:#eefbf3,stroke:#16a34a,color:#173622,stroke-width:2px;
    classDef caution fill:#fff1f2,stroke:#dc2626,color:#6b1d1d,stroke-width:2px;
    classDef anchor fill:#f4f0ff,stroke:#7c3aed,color:#47207f,stroke-width:2px;
    classDef action fill:#fff4da,stroke:#d97706,color:#6b3410,stroke-width:2px;
```

This handbook is the evidence map behind the public site. It keeps three
questions separate: what the repository accepted from upstream sources, how
that material was narrowed into tracked files, and which checked-in outputs
carry those files into reader-facing reports or the atlas. That separation is
the difference between a persuasive documentation surface and a list of file
paths.

## Section Pages

- [Foundation](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/foundation/)
- [Sources](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/sources/)
- [Outputs](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/outputs/)
- [Fieldwork](https://bijux.io/bijux-pollenomics/04-fieldwork/)

## Start Here

- upstream origin, caveats, and refresh limits: [Sources](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/sources/)
- exact file families and publication bundles: [Outputs](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/outputs/)
- tracked tree rules and migration cost: [Foundation](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/foundation/)
- one direct visit record behind a mapped point: [Fieldwork](https://bijux.io/bijux-pollenomics/04-fieldwork/)

## What This Handbook Settles

- where a visible layer came from
- what normalization happened before publication
- which tracked files support the atlas or country bundles
- which layout changes would create wide migration cost

## First Proof Check

- `data/`
- `docs/report/`
- `docs/04-fieldwork/`

## Boundary Test

If a question is really about runtime commands, repository automation, or the
meaning of one published atlas point, this handbook should route the reader out
instead of answering too broadly.
