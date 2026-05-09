---
title: Bijux Pollenomics
audience: reader
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# Bijux Pollenomics

`bijux-pollenomics` publishes public evidence surfaces about Nordic pollenomics,
environmental context, archaeology, boundaries, fieldwork, and animal ancient
DNA. This site is split on purpose:

- the public route explains what readers can inspect and trust today
- the internal route explains how maintainers keep the repository honest

Start on the public side unless you are actively maintaining the repository.

<!-- bijux-pollenomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-pollenomics/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-pollenomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-pollenomics/actions/workflows/verify.yml/badge.svg?branch=main)](https://github.com/bijux/bijux-pollenomics/actions/workflows/verify.yml?query=branch%3Amain)
[![Release PyPI](https://img.shields.io/badge/release-pypi%20workflow-2563EB?logo=githubactions&logoColor=white)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-pypi.yml)
[![Release GHCR](https://img.shields.io/badge/release-ghcr%20workflow-2563EB?logo=githubactions&logoColor=white)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-ghcr.yml)
[![Release GitHub](https://img.shields.io/badge/release-github%20workflow-2563EB?logo=githubactions&logoColor=white)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-github.yml)
[![Docs](https://github.com/bijux/bijux-pollenomics/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/deploy-docs.yml)
[![Release](https://img.shields.io/github/v/release/bijux/bijux-pollenomics?display_name=tag&label=release)](https://github.com/bijux/bijux-pollenomics/releases)
[![GHCR packages](https://img.shields.io/badge/ghcr-2%20packages-181717?logo=github)](https://github.com/bijux?tab=packages&repo_name=bijux-pollenomics)
[![Published packages](https://img.shields.io/badge/published%20packages-2-2563EB)](https://github.com/bijux/bijux-pollenomics/tree/main/packages)

[![bijux-pollenomics](https://img.shields.io/pypi/v/bijux-pollenomics?label=bijux--pollenomics&logo=pypi)](https://pypi.org/project/bijux-pollenomics/)
[![pollenomics](https://img.shields.io/pypi/v/pollenomics?label=pollenomics&logo=pypi)](https://pypi.org/project/pollenomics/)

[![bijux-pollenomics](https://img.shields.io/badge/bijux--pollenomics-ghcr-181717?logo=github)](https://github.com/bijux/bijux-pollenomics/pkgs/container/bijux-pollenomics%2Fbijux-pollenomics)
[![pollenomics](https://img.shields.io/badge/pollenomics-ghcr-181717?logo=github)](https://github.com/bijux/bijux-pollenomics/pkgs/container/bijux-pollenomics%2Fpollenomics)

[![bijux-pollenomics docs](https://img.shields.io/badge/docs-bijux--pollenomics-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/)
[![pollenomics docs](https://img.shields.io/badge/docs-pollenomics-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/)
<!-- bijux-pollenomics-badges:generated:end -->

## Start Here

<div class="bijux-quicklinks">
  <a class="md-button md-button--primary" href="public/">Open the public guide</a>
  <a class="md-button" href="01-bijux-pollenomics/">Open the product guide</a>
  <a class="md-button" href="02-bijux-pollenomics-data/">Open the data guide</a>
  <a class="md-button" href="report/">Open the report portal</a>
  <a class="md-button" href="report/how-to-read.md">How to read the report tree</a>
  <a class="md-button" href="05-nordic-evidence-atlas/">Open the atlas guide</a>
  <a class="md-button" href="04-fieldwork/">Open the fieldwork record</a>
  <a class="md-button" href="internal/">Open the internal guide</a>
</div>

Read the site in this order:

```mermaid
flowchart TB
    pollen["pollen and environmental source families"]
    context["archaeology, boundary, and fieldwork context"]
    samples["sample-backed ancient DNA context"]
    reports["country bundles and atlas evidence tables"]
    atlas["visible atlas point or country surface"]
    review["reader checks traceability and limits"]

    pollen --> reports
    context --> reports
    samples --> reports
    reports --> atlas
    atlas --> review
```

## Public Surface

- public guide: [public/index.md](public/index.md)
- product guide: [01-bijux-pollenomics](01-bijux-pollenomics/index.md)
- data guide: [02-bijux-pollenomics-data](02-bijux-pollenomics-data/index.md)
- report portal: [report/index.md](report/index.md)
- Nordic atlas guide: [05-nordic-evidence-atlas](05-nordic-evidence-atlas/index.md)
- fieldwork record: [04-fieldwork](04-fieldwork/index.md)

The public side should explain the repository without assuming that the reader
already knows the codebase, package layout, or build system.

## Internal Surface

The internal side is for maintainers. It explains release checks, documentation
integrity, GitHub workflows, and repository health rules.

- internal guide: [internal/index.md](internal/index.md)
- maintainer handbook: [03-bijux-pollenomics-maintain](03-bijux-pollenomics-maintain/index.md)

## Fieldwork Record

The fieldwork section is intentionally narrow. It anchors one mapped point to a
real visit without pretending that field media replaces curated sample, paper,
or supplement evidence.

<div class="bijux-quicklinks">
  <a class="md-button md-button--primary" href="https://bijux.io/bijux-pollenomics/04-fieldwork/lyngsjon-lake-fieldwork/">Open the fieldwork page</a>
  <a class="md-button" href="gallery/2026-02-26-data-collection.mp4">Open the field video</a>
</div>

<div class="bijux-media-grid">
  <figure class="bijux-media-card">
    <img src="gallery/2026-02-26-data-collection.JPG" alt="Field sampling at Lyngsjön Lake on 2026-02-26." loading="lazy">
    <figcaption>Lyngsjön Lake, southwest of Kristianstad, during winter field collection on 2026-02-26.</figcaption>
  </figure>
</div>

## What The Repository Does Not Claim

- that map proximity alone establishes scientific weight
- that every visible layer has identical provenance quality
- that a project list alone is enough to justify a mapped point
- that unresolved or region-only geography should be published like exact site evidence
- that the current narrow animal aDNA atlas candidate surface means the repository is already scientifically broad
- that the repository is already the full cross-evidence pollenomics engine

## Read By Question

- what the runtime rebuilds: [01-bijux-pollenomics](01-bijux-pollenomics/index.md)
- what this repository does and where its limits are:
  [public guide](public/index.md)
- what the tracked data system and source families are: [02-bijux-pollenomics-data](02-bijux-pollenomics-data/index.md)
- how the publication tree is organized for readers: [report portal](report/index.md)
- how the map points, filters, and honesty surfaces work: [05-nordic-evidence-atlas](05-nordic-evidence-atlas/index.md)
- how repository maintenance works: [internal guide](internal/index.md)
