---
title: bijux-pollenomics
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# bijux-pollenomics

`bijux-pollenomics` is the repository's runtime package for collecting tracked
Nordic evidence layers and publishing reviewable report bundles from them.

Start here when the question is about the package boundary rather than the
repository as a whole: what code belongs in the runtime, which contracts are
public, how data and reports move through the package, and which quality rules
protect that behavior.

<div class="bijux-callout"><strong>Think in one runtime loop.</strong> The package collects and normalizes tracked evidence, turns that material into checked-in report bundles, and keeps the CLI and file contracts stable enough to review from the repository alone.</div>

<div class="bijux-panel-grid">
  <div class="bijux-panel"><h3>Foundation</h3><p>Use this branch to understand what the runtime owns, which language stays stable, and where package boundaries stop.</p></div>
  <div class="bijux-panel"><h3>Interfaces</h3><p>Use this branch for CLI, configuration, API, and file contracts when you need exact public surfaces.</p></div>
  <div class="bijux-panel"><h3>Operations</h3><p>Use this branch for installation, rebuild workflows, release rules, and failure recovery during package work.</p></div>
</div>

<div class="bijux-quicklinks">
  <a class="md-button md-button--primary" href="interfaces/entrypoints-and-examples/">Open command entrypoints</a>
  <a class="md-button" href="operations/common-workflows/">Open common workflows</a>
  <a class="md-button" href="quality/test-strategy/">Open test strategy</a>
</div>

## Read This Section When

- you need the shortest honest description of what the runtime package owns
- you are changing CLI, data collection, report publishing, or package
  contracts
- you want package-level docs that mirror the structure used in sister Bijux
  repositories

## Main Paths

- [Foundation](foundation/index.md)
- [Architecture](architecture/index.md)
- [Interfaces](interfaces/index.md)
- [Operations](operations/index.md)
- [Quality](quality/index.md)

## What Readers Usually Need First

- package ownership and scope: [Foundation](foundation/index.md)
- command, configuration, and file contracts: [Interfaces](interfaces/index.md)
- local rebuild and release steps: [Operations](operations/index.md)
- review expectations and validation depth: [Quality](quality/index.md)

## Purpose

Use this page to choose the right package branch before dropping into
module-level implementation details.

## Stability

Keep it aligned with `packages/bijux-pollenomics/`, its public CLI, its tracked
artifacts, and the review rules that protect them.
