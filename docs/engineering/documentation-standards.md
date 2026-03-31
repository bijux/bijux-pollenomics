---
title: Documentation Standards
audience: mixed
type: workflow
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# Documentation Standards

The documentation system is MkDocs-based and intentionally aligned with the repository’s checked-in outputs and the map-first reading model.

## Commands

```bash
make docs
make docs-serve
```

`make docs` builds the site into `artifacts/docs/site/`.

`make docs-serve` is configured to serve the local site at `http://127.0.0.1:8000/` so homepage links and iframe paths resolve against the local root instead of the GitHub Pages project path.

The `make docs` and `make docs-serve` targets also set `NO_MKDOCS_2_WARNING=true` to suppress an upstream warning banner emitted by the installed Material theme package. That suppression only affects terminal noise; it does not change the generated site.

The site theme is intentionally configured to avoid remote Google font dependencies and to keep the local docs build closer to the checked-in visual language used by the shared map.

## GitHub Pages Deployment

The repository deploys documentation with `.github/workflows/deploy-docs.yml`.

- pushes to `main` build the site and deploy it to GitHub Pages
- manual dispatch can build the same site without waiting for a push
- the deploy job itself runs only for `main`
- the workflow validates that `mkdocs.yml` still writes to `artifacts/docs/site` and keeps `strict: true`

## Documentation Rules

- the docs homepage should continue to lead with the shared Nordic map
- the docs site should avoid generic styling defaults when a small amount of local CSS can make provenance-heavy pages easier to read
- section index pages should explain how to read the section
- diagrams should clarify architecture or workflow, not decorate pages
- documentation should match the checked-in command surface and file layout exactly
- claims about current files, commands, counts, or layers should be verified against code or checked-in artifacts in the same change
- the named documentation sections should carry the narrative documentation load; duplicate side-channel guide pages should not reappear
- when scope is limited, say so explicitly instead of implying future capability is already present

## Naming Rule

- file and directory names should describe durable documentation intent, not temporary sequencing
- section names should reflect reader needs such as `foundation`, `workflows`, or `reference`, not authoring order
- page titles should stay valid even if the project grows for several years without another restructure

## Change Rule

When a documentation refactor moves pages or renames sections, update:

1. `mkdocs.yml`
2. internal links
3. section index pages
4. any workflow or reference page that names the old path directly

## Purpose

This page explains how docs are built and what quality bar they should meet.
