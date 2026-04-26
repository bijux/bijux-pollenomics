---
title: Maintainer Handbook
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-26
---

# Maintainer Handbook

`bijux-pollenomics-maintain` is the handbook root for repository-owned
maintenance work.

This section exists so repository health stays inspectable. Quality gates,
schema drift checks, docs integrity checks, release support, and workflow
contracts should be readable from checked-in docs instead of being rediscovered
through CI logs and shell glue.

If someone opens only this page, they should be able to answer one routing
question quickly: is this problem enforced by maintainer helper code, by shared
Make entrypoints, or by GitHub automation?

<div class="bijux-callout"><strong>Use maintenance docs for repository truth, not folklore.</strong> This branch is where to check the exact make entrypoints, workflow fan-out, release support, and maintainer package rules that keep the repository stable over time.</div>

<div class="bijux-panel-grid">
  <div class="bijux-panel"><h3>Maintainer Package</h3><p>Use this branch for maintainer-only tooling, schema governance, release support, and documentation integrity rules.</p></div>
  <div class="bijux-panel"><h3>Make System</h3><p>Use this branch to understand repository entrypoints, package dispatch, CI targets, and which commands rewrite tracked state.</p></div>
  <div class="bijux-panel"><h3>GitHub Workflows</h3><p>Use this branch for verify, publish, docs deployment, and reusable workflow job trees.</p></div>
</div>

<div class="bijux-quicklinks">
  <a class="md-button md-button--primary" href="gh-workflows/index/">Open workflow docs</a>
  <a class="md-button" href="makes/root-entrypoints/">Open make entrypoints</a>
  <a class="md-button" href="bijux-pollenomics-dev/release-support/">Open release support</a>
</div>

```mermaid
flowchart LR
    reader["reader question<br/>which repository-health layer owns this rule?"]
    dev["bijux-pollenomics-dev<br/>helper code and policy checks"]
    makes["makes<br/>shared command surfaces"]
    workflows["gh-workflows<br/>GitHub Actions contracts"]
    package["runtime and data docs<br/>owned product behavior"]
    health["repository health<br/>release, docs, quality, automation"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class reader page;
    class dev,makes,workflows,health positive;
    class package caution;
    reader --> health
    health --> dev
    health --> makes
    health --> workflows
    health -.hands product behavior back to.-> package
```

## Start Here

- open [bijux-pollenomics-dev](bijux-pollenomics-dev/index.md) when repository
  health is enforced by helper code, release guards, docs integrity, or schema
  checks
- open [makes](makes/index.md) when the issue starts from a repository command
  or from CI target routing
- open [gh-workflows](gh-workflows/index.md) when the issue starts from a
  GitHub event, failed check suite, or publication trigger

## Sections In This Handbook

- [bijux-pollenomics-dev](bijux-pollenomics-dev/index.md)
- [makes](makes/index.md)
- [gh-workflows](gh-workflows/index.md)

## Use This Handbook When

- the question is about repository automation, verification, release support,
  docs integrity, or workflow fan-out
- you need to know which shared surface owns a repository-health rule
- the answer should stay above one product package boundary

## Do Not Start Here When

- the real question is about runtime behavior, data provenance, or atlas
  publication semantics
- you already know the issue belongs to one package API, CLI, or contract
- you are trying to understand product behavior rather than repository health

## What This Handbook Clarifies

- which repository-health questions belong to helper code, Make routing, or
  workflow automation
- where release and docs integrity rules are enforced before a product package
  ever changes
- when a repository-health page should hand the reader back to runtime, data,
  fieldwork, or atlas docs instead of trying to answer a product question

## Concrete Anchors

- `packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/` for repository
  helper code
- `makes/root.mk`, `makes/packages.mk`, and `makes/publish.mk` for shared
  command routing
- `.github/workflows/` for GitHub-triggered verification and publication
  surfaces

## Reader Takeaway

This handbook should make repository-health work explicit and reviewable. It is
not a shadow product layer, and it should route readers back to the runtime or
data docs as soon as the question becomes user-facing behavior.
