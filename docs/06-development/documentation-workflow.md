---
title: Documentation Workflow
audience: mixed
type: workflow
status: canonical
owner: bijux-pollen-docs
last_reviewed: 2026-03-23
---

# Documentation Workflow

The documentation system is now MkDocs-based and intentionally aligned with the broader Bijux project style.

## Commands

```bash
make docs
make docs-serve
```

`make docs` builds the site into `artifacts/docs/site/`.

`make docs-serve` is configured to serve the local site at `http://127.0.0.1:8000/` so homepage links and iframe paths resolve against the local root instead of the GitHub Pages project path.

The `make docs` and `make docs-serve` targets also set `NO_MKDOCS_2_WARNING=true` to suppress an upstream warning banner emitted by the installed Material theme package. That suppression only affects terminal noise; it does not change the generated site.

## GitHub Pages Deployment

The repository deploys documentation with [deploy-docs.yml](/Users/bijan/bijux/bijux-pollen/.github/workflows/deploy-docs.yml).

- pushes to `main` build the site and deploy it to GitHub Pages
- tags matching `v*` build the site as a release-quality validation step
- the deploy job itself runs only for `main`
- the workflow validates that `mkdocs.yml` still writes to `artifacts/docs/site` and keeps `strict: true`

## Documentation Rules

- the docs homepage should continue to lead with the shared Nordic map
- section index pages should explain how to read the section
- diagrams should clarify architecture or workflow, not decorate pages
- documentation should match the checked-in command surface and file layout exactly
- claims about current files, commands, counts, or layers should be verified against code or checked-in artifacts in the same change
- the seven canonical sections should carry the narrative documentation load; duplicate side-channel guide pages should not reappear
- when scope is limited, say so explicitly instead of implying future capability is already present

## Purpose

This page explains how docs are built and what quality bar they should meet.
