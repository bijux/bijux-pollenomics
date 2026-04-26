---
title: bijux-pollenomics-dev
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-26
---

# bijux-pollenomics-dev

This section documents the repository-owned maintainer package.

Use it when the question is about maintainer-only tooling, schema governance,
release support, or documentation integrity rather than runtime behavior.

This package is where repository policy becomes executable helper code. The
important reader question is not just “what rules exist?” but “which helper
module enforces them, and what repository surface does that enforcement
protect?”

```mermaid
flowchart LR
    reader["reader question<br/>which helper surface owns this rule?"]
    dev["bijux-pollenomics-dev<br/>repository helper package"]
    quality["quality/ and api/<br/>gate enforcement and drift checks"]
    release["release/<br/>publication guards and version rules"]
    docs["docs/<br/>badge and docs integrity support"]
    trusted["trusted_process.py<br/>shared maintainer process rules"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class reader page;
    class dev,quality,release,docs,trusted positive;
    reader --> dev
    dev --> quality
    dev --> release
    dev --> docs
    dev --> trusted
```

## Start Here

- open [Package Overview](package-overview.md) for the maintainer package
  boundary
- open [Quality Gates](quality-gates.md) and [Security Gates](security-gates.md)
  for the enforced review surface
- open [Release Support](release-support.md) when changes touch publication or
  repository release evidence

## Pages In This Section

- [Package Overview](package-overview.md)
- [Scope and Non-Goals](scope-and-non-goals.md)
- [Module Map](module-map.md)
- [Operating Guidelines](operating-guidelines.md)
- [Quality Gates](quality-gates.md)
- [Security Gates](security-gates.md)
- [Schema Governance](schema-governance.md)
- [Release Support](release-support.md)
- [Documentation Integrity](documentation-integrity.md)

## Use This Section When

- the issue is implemented as helper code under
  `packages/bijux-pollenomics-dev/`
- you need to know which helper module or policy surface enforces a repository
  rule
- the concern is about schema drift, docs integrity, release support, security,
  or quality gates

## Do Not Use This Section When

- the real question is about runtime commands, data contracts, or atlas
  publication behavior
- the issue belongs to shared Make routing or GitHub Actions trigger logic
- you are looking for end-user behavior rather than repository-health helpers

## What This Section Clarifies

- which maintainer-only rules are encoded as Python helper modules rather than
  as Make routing or workflow YAML
- where API freeze, OpenAPI drift, release guards, license assets, and badge
  synchronization are actually enforced
- which repository-health behavior belongs in helper code because it needs
  executable policy rather than prose alone

## Concrete Anchors

- `packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/api/` for API
  freeze and drift enforcement
- `packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/docs/badge_sync.py`
  for managed docs badge synchronization
- `packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/release/` for
  release guards, version resolution, and license assets
- `packages/bijux-pollenomics-dev/tests/` for the proof that these maintainer
  helpers still enforce the intended rules

## Reader Takeaway

Use `bijux-pollenomics-dev` when repository-health behavior is implemented as
helper code. If the question is really about shared command routing or workflow
entrypoints, move sideways to `makes/` or `gh-workflows/` instead.
