---
title: Maintainer Handbook
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-10
---

# Maintainer Handbook

`bijux-pollenomics-maintain` is the handbook root for repository-owned
maintenance work.

This section exists so repository health stays inspectable. Quality gates,
schema drift checks, docs integrity checks, release support, and workflow
contracts should be readable from checked-in docs instead of being rediscovered
through CI logs and shell glue.

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

## Sections In This Handbook

- [bijux-pollenomics-dev](bijux-pollenomics-dev/index.md)
- [makes](makes/index.md)
- [gh-workflows](gh-workflows/index.md)

## What Readers Usually Need First

- release, schema, and docs integrity rules: [bijux-pollenomics-dev](bijux-pollenomics-dev/index.md)
- command routing and repository automation: [makes](makes/index.md)
- CI, publish, and docs deployment behavior: [gh-workflows](gh-workflows/index.md)

## Purpose

Use this page to choose the maintenance branch that owns the current repository
health question.
