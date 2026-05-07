---
title: bijux-pollenomics
audience: reader
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# bijux-pollenomics Runtime Handbook

`bijux-pollenomics` is the runtime package that rebuilds the repository's
checked-in sample-first evidence surfaces. It does one durable job: collect
project, paper, supplement, sample, site, and coordinate evidence, normalize
it into tracked files, and publish reviewed country bundles plus the shared
Nordic atlas as downstream views.

<div class="bijux-quicklinks">
  <a class="md-button md-button--primary" href="interfaces/cli-surface/">Open the CLI surface</a>
  <a class="md-button" href="interfaces/artifact-contracts/">Open the artifact contracts</a>
  <a class="md-button" href="operations/installation-and-setup/">Open the install and rebuild path</a>
  <a class="md-button" href="quality/test-strategy/">Open test strategy</a>
</div>

## Runtime Loop

```mermaid
flowchart TB
    commands["CLI commands"]
    tracked["tracked sample, site, and coordinate files"]
    bundles["country bundles and atlas bundle"]
    review["tests and release checks"]

    commands --> tracked
    tracked --> bundles
    review --> commands
    review --> bundles
```

The runtime handbook is for readers who need to understand how a visible
publication surface is rebuilt. It is not an internal catalog of helpers.

## Start Here

- why this package exists and where it stops:
  [foundation](foundation/index.md)
- how commands, tracked files, and outputs connect:
  [architecture](architecture/index.md)
- which commands and files are part of the public contract:
  [interfaces](interfaces/index.md)
- how to install, rebuild, and verify:
  [operations](operations/index.md)
- how proof is layered and where current limits still sit:
  [quality](quality/index.md)

## What This Package Owns

- the operator-facing commands that collect tracked evidence and rebuild
  publication outputs
- the code paths that normalize source material into repository-owned artifacts
- the report and atlas publication logic that turns tracked files into review
  surfaces
- the candidate ranking logic that summarizes locality proximity against the
  checked-in atlas context layers

## What This Package Does Not Claim

- the repository-wide documentation, release, and workflow rules explained in
  the maintainer handbook
- the source-specific provenance caveats explained in the data reference
- the scientific interpretation of the mapped evidence beyond what the checked-in
  artifacts and documented limitations support
- claims that map-ready publication already equals full pollenomics analysis
