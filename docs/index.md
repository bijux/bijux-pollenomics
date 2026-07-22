---
title: Bijux Pollenomics
audience: reader
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-07-22
---

# Bijux Pollenomics

`bijux-pollenomics` connects curated evidence to public maps and reports about
pollen, palaeoenvironmental context, archaeology, hydrography, fieldwork, and
ancient DNA. Every publication belongs to a traceable chain: source capture,
normalization, evidence review, release qualification, and derived output.

The site is useful in both directions. Start with a map or country report to
understand the published result, or start with a source family and follow its
records forward to see what the repository is prepared to claim.

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

[![bijux-pollenomics docs](https://img.shields.io/badge/docs-bijux--pollenomics-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-pollenomics/public/pollenomics/)
[![pollenomics docs](https://img.shields.io/badge/docs-pollenomics-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-pollenomics/public/pollenomics/)
<!-- bijux-pollenomics-badges:generated:end -->

## Start Here

<div class="bijux-quicklinks">
  <a class="md-button md-button--primary" href="public/pollenomics/">Open the product guide</a>
  <a class="md-button" href="public/pollenomics-data/">Open the data guide</a>
  <a class="md-button" href="report/">Open the report portal</a>
  <a class="md-button" href="report/how-to-read/">How to read the report tree</a>
  <a class="md-button" href="public/nordic-atlas/">Open the atlas guide</a>
  <a class="md-button" href="public/fieldwork/">Open the fieldwork record</a>
</div>

## From Source To Public Claim

```mermaid
flowchart LR
    Source["source dataset, paper, or supplement"] --> Capture["versioned capture"]
    Capture --> Normalize["repository-owned records"]
    Normalize --> Evidence["identity, place, time, and coordinate evidence"]
    Evidence --> Gate{"publication gate"}
    Gate -->|qualified| Reports["reports and atlas layers"]
    Gate -->|blocked| Review["visible caveat or recovery queue"]
    Reports --> Reader["inspectable public claim"]
```

Source files are never promoted merely because they can be plotted. The
publication gate evaluates the evidence appropriate to each family. Boundary
geometry can frame a map without becoming scientific evidence; pollen and
archaeology layers retain their own temporal semantics; and animal aDNA needs
sample-level support before an exact point or chronology can be asserted.

## Evidence Surfaces

| Surface | What it preserves | Where to begin |
| --- | --- | --- |
| Source families | upstream identity, acquisition, version, license, and refresh posture | [Sources](public/pollenomics-data/sources/index.md) |
| Curated evidence | normalized records plus locality, chronology, coordinate, and ambiguity decisions | [Evidence](public/pollenomics-data/evidence/index.md) |
| Publications | derived world, regional, country, and lake views | [Publications](public/pollenomics-data/publications/index.md) |
| Atlas interpretation | layer meaning, point posture, filters, and visible limits | [Nordic atlas](public/nordic-atlas/index.md) |
| Field observations | a dated, situated record from Lyngsjön Lake | [Fieldwork](public/fieldwork/index.md) |

## What Is Strong Today

- the repository already publishes tracked pollen, archaeology, boundary, and
  fieldwork context as reviewable files plus public report surfaces
- world, Europe-plus, Nordic, and country bundles are one publication family,
  not disconnected products
- the Sweden lake ranking packet and optional Nordic lake overlays now make
  lake prioritization visible without hiding the underlying evidence packet

## What Is Still Constrained

- animal aDNA extraction and the strongest claims that depend on deeper sample
  recovery remain less mature than the rest of the repository
- visible map proximity still does not substitute for chronology review, source
  posture, or field verification
- lake ranking surfaces are decision-support outputs, not bathymetry or coring
  plans

## Choose A Route

- use the [product guide](public/pollenomics/index.md) when you need the
  overall answer: what the repository is for and how the outputs fit together
- use the [data guide](public/pollenomics-data/index.md) when you need the
  evidence answer: what is in scope, how it is governed, and what remains weak
- use the [report portal](report/index.md) when you want the checked-in public
  outputs first
- use the [Nordic atlas guide](public/nordic-atlas/index.md) when you need map
  behavior, filters, point posture, and overlay caveats
- use the [fieldwork record](public/fieldwork/index.md) when you want one real
  visited location instead of a generalized public summary

Choose the route that matches the claim you need to evaluate. Publications
provide orientation; evidence and source pages provide the narrower support
needed for scientific or operational decisions.

## Fieldwork Record

The fieldwork section is intentionally narrow. It anchors one mapped point to a
real visit without pretending that field media replaces curated sample, paper,
or supplement evidence.

<div class="bijux-quicklinks">
  <a class="md-button md-button--primary" href="https://bijux.io/bijux-pollenomics/public/fieldwork/lyngsjon-lake-fieldwork/">Open the fieldwork page</a>
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

- what the runtime rebuilds: [product guide](public/pollenomics/index.md)
- what this repository publishes and where its limits are:
  [documentation home](index.md)
- what the tracked data system and source families are:
  [data guide](public/pollenomics-data/index.md)
- how the publication tree is organized: [report portal](report/index.md)
- how the map points, filters, and honesty surfaces work:
  [Nordic atlas guide](public/nordic-atlas/index.md)
