---
title: Bijux Pollenomics
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Bijux Pollenomics

`bijux-pollenomics` is a static, reviewable evidence workspace. The repository collects tracked Nordic source data, normalizes it into stable files, and publishes those files as country bundles plus one shared interactive atlas.

Start here with the checked-in Nordic Evidence Atlas. It is the fastest way to
see what this repository actually publishes: AADR sample points, LandClim
pollen sequences and REVEALS grid cells, Neotoma pollen sites, SEAD sites,
Swedish archaeology density from RAÄ, fieldwork media, and Nordic country
boundaries.

Use this page to trace what the repository publishes today, where the visible
layers come from, which code rebuilds them, and where the documentation stops
making claims.

<!-- bijux-pollenomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-pollenomics/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-pollenomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-pollenomics/actions/workflows/verify.yml/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/verify.yml)
[![Release PyPI](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-pypi.yml/badge.svg?event=workflow_dispatch)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-pypi.yml?query=event%3Aworkflow_dispatch)
[![Release GHCR](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-ghcr.yml/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-ghcr.yml)
[![Release GitHub](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-github.yml/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-github.yml)
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

<div class="bijux-callout">
  <strong>Start with the atlas, then branch by question.</strong> Use the rest of the site to verify what the repository publishes, where each visible layer originates, which commands rebuild it, and which limits remain deliberate.
</div>

<div class="bijux-panel-grid">
  <div class="bijux-panel">
    <h3>What the repository shows</h3>
    <p>Which files are checked in, which source families feed the atlas, which commands rebuild the published outputs, and which repository boundaries are intentionally held.</p>
  </div>
  <div class="bijux-panel">
    <h3>What still needs skepticism</h3>
    <p>That spatial proximity implies scientific weight, that the current layers are complete, or that mutable upstream services will behave identically forever.</p>
  </div>
</div>

<div class="bijux-quicklinks">
  <a class="md-button md-button--primary" href="https://bijux.io/bijux-pollenomics/05-nordic-evidence-atlas/">Open the Nordic Evidence Atlas</a>
  <a class="md-button" href="https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/">Open the package handbook</a>
  <a class="md-button" href="https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/">Open the data reference</a>
  <a class="md-button" href="https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/">Open the maintainer handbook</a>
</div>

<div class="bijux-map-mobile-note">
  <strong>Phone view:</strong> Open the atlas in its own tab for panning, layer toggles, and map controls. The inline embed stays available on larger screens where the full layer stack fits.
  <div class="bijux-quicklinks">
    <a class="md-button md-button--primary" href="https://bijux.io/bijux-pollenomics/05-nordic-evidence-atlas/">Open the Nordic Evidence Atlas</a>
  </div>
</div>

<div class="bijux-map-frame">
  <iframe src="report/nordic-atlas/nordic-atlas_map.html" title="Nordic Evidence Atlas"></iframe>
</div>

## Start Here

Open the path that matches what you need right now:

- understanding the runtime package boundary, command loop, and public
  contracts: open
  [bijux-pollenomics](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/)
- checking what each tracked dataset contributes, how it is normalized, and
  where it lands: open
  [bijux-pollenomics-data](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/)
- reviewing CI, release, docs, and make-system maintenance rules: open
  [bijux-pollenomics-maintain](https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/)
- inspecting the current visible publication first: open the
  [Nordic Evidence Atlas](https://bijux.io/bijux-pollenomics/05-nordic-evidence-atlas/)
  and the checked-in `docs/report/` bundles

## Fieldwork Evidence

The website now also carries checked-in field media from the Lyngsjön Lake sampling visit on 2026-02-26. That material anchors one atlas point to a real collection day on the lake ice rather than to database outputs alone.

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

## What You Can Verify Here

Start from the visible atlas, then open the exact supporting explanation you
need:

- what the repository produces today and why
- how the tracked data categories are collected and normalized
- how reports and the shared map are generated
- how the runtime package is divided by responsibility
- how maintainers verify and review long-lived changes

## Published Handbooks

- [bijux-pollenomics](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/)
- [bijux-pollenomics-data](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/)
- [bijux-pollenomics-maintain](https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/)

## Current Issues and Migration Notes

- package limits and active risks: [Known Limitations](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/known-limitations/)
- data-tree migration issues: [Migration Issues](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/foundation/migration-issues/)
- package risk tracking: [Risk Register](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/risk-register/)

## Concrete Anchors

- `docs/report/nordic-atlas/nordic-atlas_map.html` for the visible publication
  surface most readers will inspect first
- `data/` for the tracked normalized evidence tree that feeds the atlas
- `packages/bijux-pollenomics/src/bijux_pollenomics/` for the runtime code that
  collects, normalizes, and publishes
- `packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/` and `makes/` for
  the repository-health surfaces that protect release, docs, and verification

## Core Point

Start here when the visible atlas is the shortest path into the repository. If
a claim about the atlas cannot be backed by source provenance, runtime
contracts, tracked outputs, or maintainer proof, this repository should say so
directly rather than implying certainty it does not have.
