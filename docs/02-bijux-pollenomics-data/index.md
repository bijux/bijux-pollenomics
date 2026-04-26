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
flowchart TB
    sources["source families"]
    rules["selection and normalization rules"]
    tree["tracked data tree"]
    outputs["normalized output families"]
    reports["country bundles"]
    atlas["Nordic atlas"]
    fieldwork["direct visit record"]
    reader["visible layer question"]

    sources --> rules
    rules --> tree
    tree --> outputs
    outputs --> reports
    outputs --> atlas
    fieldwork --> atlas
    atlas --> reader
    reports --> reader
```

This handbook is the evidence map behind the public site. It keeps three
questions separate: what the repository accepted from upstream sources, how
that material was narrowed into tracked files, and which checked-in outputs
carry those files into reader-facing reports or the atlas. That separation is
the difference between a persuasive documentation surface and a list of file
paths.

The data handbook should make one thing obvious immediately: visible atlas
layers and country reports are downstream proof surfaces, not primary evidence.
If readers cannot see that chain on this page, they will assume the site is
telling them stories rather than showing its tracked basis.

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

## Design Pressure

The easy failure is to document source pages, normalized trees, and published
surfaces as separate inventories without keeping the evidence chain legible
from one reader question to the next.

## Boundary Test

If a question is really about runtime commands, repository automation, or the
meaning of one published atlas point, this handbook should route the reader out
instead of answering too broadly.
