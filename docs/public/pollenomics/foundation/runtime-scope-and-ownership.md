---
title: Runtime Scope and Ownership
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-10
---

# Runtime Scope and Ownership

`bijux-pollenomics` exists to rebuild repository-owned evidence state. Its job
is not abstract scientific theory and it is not general-purpose workflow
policy. It owns the runtime loop that turns tracked inputs into tracked public
outputs.

That ownership boundary matters because this repository has several nearby
surfaces that sound similar but serve different audiences. The public runtime,
the data handbook, the atlas guide, and the maintainer toolkit should work
together without being mistaken for the same thing.

## Capability Map

- collect source families into governed `data/` trees
- normalize pollen, archaeology, boundary, and aDNA evidence into inspectable
  repository files
- publish country bundles, atlas layers, and repository truth reviews
- keep command defaults and output locations stable enough to review in one
  repository checkout

## Surface Map

- runtime commands
- tracked source-family and normalized evidence files
- tracked publication outputs
- repository truth and claim-audit surfaces

## Ownership Boundary

The runtime owns:

- command entrypoints and command defaults
- collection and normalization behavior
- publication behavior for `docs/report/`
- file and path contracts needed to rebuild checked-in state

The runtime does not own:

- repository-health policy that belongs in `bijux-pollenomics-dev`
- public provenance interpretation that belongs in
  `public/pollenomics-data`
- atlas interpretation guidance that belongs in `public/nordic-atlas`
- broader paper-grade pollenomics analysis that has not been implemented yet

## Dependencies And Adjacencies

The runtime sits between repository provenance and repository publication. It
depends on source-family inputs and feeds country bundles, atlas layers, and
review surfaces, but it should not blur those adjacent responsibilities into one
flat story.

## Domain Language

- `source family`: one governed upstream domain such as LandClim, Neotoma,
  SEAD, RAÄ, boundaries, AADR, or animal aDNA papers
- `normalized evidence`: tracked repository output derived from those sources
- `publication surface`: a downstream atlas, country bundle, or report surface
- `partial recovery`: a surface that is real and inspectable but still too thin
  for stronger scientific or release language

## Lifecycle

1. collect or refresh source-family state
2. normalize it into reviewable repository artifacts
3. publish downstream surfaces from that state
4. run validation that can block overclaims or drift

## Change Principles

- preserve provenance differences across source families
- prefer durable path and artifact contracts over convenience shortcuts
- keep pollenomics breadth visible while weaker aDNA recovery continues
- block stronger publication language when evidence depth is not there

## Why This Matters

If the ownership line gets blurry, the public guide stops being trustworthy.
It becomes harder to tell whether a claim is coming from tracked evidence,
presentation logic, or maintainer policy. A clear runtime boundary is what lets
the repository say, with some precision, which part of the system produced a
given output and which part merely explains it.

## Related Pages

- [repository scope and limits](repository-scope-and-limits.md)
- [pollenomics engine roadmap](pollenomics-engine-roadmap.md)
- [runtime system model](../architecture/runtime-system-model.md)
