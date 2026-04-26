---
title: bijux-pollenomics
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# bijux-pollenomics Runtime Handbook

`bijux-pollenomics` is the repository's runtime package for collecting tracked
Nordic evidence layers and publishing reviewable report bundles from them.

Open this handbook when the question is about the package boundary rather than
the repository as a whole: what code belongs in the runtime, which contracts
are public, how data and reports move through the package, and which quality
rules protect that behavior.

The package's full job is to collect source material, normalize it into
governed repository files, publish atlas and country bundles, and keep the
command and file contracts stable enough that reviewers can inspect the whole
loop from the repository alone.

<div class="bijux-callout"><strong>Think in one runtime loop.</strong> The package collects and normalizes tracked evidence, turns that material into checked-in report bundles, and keeps the CLI and file contracts stable enough to review from the repository alone.</div>

<div class="bijux-panel-grid">
  <div class="bijux-panel"><h3>Foundation</h3><p>Start here to understand what the runtime owns, which language stays stable, and where package boundaries stop.</p></div>
  <div class="bijux-panel"><h3>Interfaces</h3><p>Open this section for commands, defaults, data layouts, output bundles, and other reader-visible contracts.</p></div>
  <div class="bijux-panel"><h3>Operations</h3><p>Open this section for safe rebuilds, review-shaped reruns, publication procedure, and failure recovery.</p></div>
</div>

<div class="bijux-quicklinks">
  <a class="md-button md-button--primary" href="https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/entrypoints-and-examples/">Open command entrypoints</a>
  <a class="md-button" href="https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/common-workflows/">Open common workflows</a>
  <a class="md-button" href="https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/test-strategy/">Open test strategy</a>
</div>

## Start Here

- open [Foundation](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/) if the main question is what the
  runtime owns and where that boundary stops
- open [Interfaces](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/) if you need the public command,
  configuration, tracked-file, or output-bundle contract
- open [Operations](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/) if the immediate need is a repeatable
  rebuild, diagnostic, or release workflow
- open [Quality](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/) if you need the proof bar for a runtime
  change or for a visible atlas diff

## Open This Package When

- you need the shortest honest description of what the runtime package owns
- you are changing CLI, data collection, report publishing, or package
  contracts
- you need one stable page that routes from visible publication behavior back
  to the code and proof that support it

## Open Another Package When

- the real question is already about source provenance rather than runtime
  behavior
- the real question is repository-wide automation rather than package behavior
- the real question is one atlas point or field visit rather than the runtime
  loop that published it

## Pages In This Package

- [Foundation](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/)
- [Architecture](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/architecture/)
- [Interfaces](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/)
- [Operations](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/)
- [Quality](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/)

## What This Package Owns

- the operator-facing commands that collect tracked evidence and rebuild
  publication outputs
- the code paths that normalize source material into repository-owned artifacts
- the report and atlas publication logic that turns tracked files into review
  surfaces

## What This Package Does Not Own

- the repository-wide documentation, release, and workflow rules explained in
  the maintainer handbook
- the source-specific provenance caveats explained in the data reference
- the scientific interpretation of the mapped evidence beyond what the checked-in
  artifacts and documented limitations support

## Concrete Anchors

- `packages/bijux-pollenomics/src/bijux_pollenomics/cli.py` and
  `packages/bijux-pollenomics/src/bijux_pollenomics/command_line/` for the
  command entry surface
- `packages/bijux-pollenomics/src/bijux_pollenomics/data_downloader/` for
  collection, normalization, and tracked data layout behavior
- `packages/bijux-pollenomics/src/bijux_pollenomics/reporting/` for country
  bundles, atlas output, and publication logic
- `packages/bijux-pollenomics/tests/` for unit, regression, and end-to-end
  proof that the runtime loop still holds

## Bottom Line

Open this package when the question is how `bijux-pollenomics` turns source
material into checked-in evidence outputs.
If the answer depends on provenance detail, repository automation, or
scientific interpretation rather than that runtime loop, another handbook owns
the question.
