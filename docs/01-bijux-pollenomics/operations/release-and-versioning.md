---
title: Release and Versioning
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Release and Versioning

The package version and published scientific outputs are related but not the
same artifact boundary.

```mermaid
flowchart LR
    tags["repository tags"]
    version["package version via hatch-vcs"]
    package["package release artifacts"]
    outputs["tracked scientific outputs"]
    docs["docs deployment"]
    review["reviewed pull request to main"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class tags,page review;
    class version,package,outputs,docs positive;
    tags --> version --> package
    outputs --> review --> docs
```

## Version Anchors

- `tool.hatch.version` in `packages/bijux-pollenomics/pyproject.toml`
- installed package metadata resolved by `importlib.metadata`
- AADR input version defaults in `config.py`
- split release workflows:
  `release-artifacts.yml`, `release-pypi.yml`, `release-ghcr.yml`,
  and `release-github.yml`

## Version Source

Package versions are derived from repository tags through `hatch-vcs`, with a
checked-in fallback for source trees that are not inside a Git tag context.
That keeps local builds, CI builds, and published releases on one versioning
model instead of mixing static file versions with tag-driven publication.

## Release Rule

Do not treat a source refresh as invisible package state. When output-shaping
changes are intentional, the package docs and review trail should explain both
the runtime change and the resulting tracked artifact diff.

## Docs Deployment Trigger

`deploy-docs` runs on pushes to `main`/`master` (and `v*` tags), so docs
publication should be routed through a reviewed pull request that merges a real
docs or docs-tooling change into `main`.

## Reader Takeaway

Package versioning and data-output refreshes move together in review, but they
are not the same artifact. The docs should keep that distinction explicit.

## Purpose

This page records the release surfaces that govern package versioning and
publication.
