---
title: Bijux Pollenomics
audience: reader
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# Bijux Pollenomics

`bijux-pollenomics` is a checked-in pollenomics and environmental evidence
repository with ancient DNA, archaeology, and map products as contextual
surfaces. It gathers pollen-context layers, environmental archaeology context,
boundary geometry, fieldwork material, paper-backed sample evidence, and public
report outputs into one repository that a reader can inspect directly.

The central public question is broader than one atlas layer: which tracked data
families does this repository really own, how strong is each one today, and
which files support the current Nordic outputs without pretending that thin
animal aDNA extraction already equals the whole pollenomics engine?

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
  <a class="md-button md-button--primary" href="https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/">Open the data system guide</a>
  <a class="md-button" href="https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/sources/source-comparison/">Open the source comparison</a>
  <a class="md-button" href="https://bijux.io/bijux-pollenomics/05-nordic-evidence-atlas/">Open the Nordic Evidence Atlas</a>
  <a class="md-button" href="https://bijux.io/bijux-pollenomics/report/nordic-atlas/nordic-atlas_map.html">Open the shipped atlas bundle</a>
  <a class="md-button" href="https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/outputs/published-reports/">Open the country output reference</a>
  <a class="md-button" href="https://bijux.io/bijux-pollenomics/report/repository_truth_posture.md">Open the repository truth packet</a>
  <a class="md-button" href="https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/">Open the runtime handbook</a>
  <a class="md-button" href="https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/">Open the maintainer handbook</a>
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

## What The Repository Publishes

- tracked source trees for pollen, environmental archaeology, boundaries, and
  ancient DNA under `data/`
- one shared atlas view under [`docs/report/nordic-atlas/`](report/nordic-atlas/nordic-atlas_map.html)
- checked country bundles under [`docs/report/`](report/published_reports_summary.json)
- reader-facing data-system pages that explain the source families rather than
  only the current aDNA slice
- public truth and progress packets under [`docs/report/`](report/published_reports_summary.json)

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
- that the current thin animal aDNA atlas candidate set means the repository is already scientifically broad
- that the repository is already the full cross-evidence pollenomics engine

## Read By Question

- what the runtime rebuilds: [01-bijux-pollenomics](01-bijux-pollenomics/index.md)
- what the tracked data system and source families are: [02-bijux-pollenomics-data](02-bijux-pollenomics-data/index.md)
- how the map points are built and filtered: [05-nordic-evidence-atlas](05-nordic-evidence-atlas/index.md)
- how release and docs integrity are enforced: [03-bijux-pollenomics-maintain](03-bijux-pollenomics-maintain/index.md)
