---
title: Documentation Integrity
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-10
---

# Documentation Integrity

Docs integrity in this repository depends on strict MkDocs builds, published
site asset support, and maintenance discipline that keeps docs aligned with the
real runtime and workflow surfaces.

## Current Documentation Surfaces

- `mkdocs.yml`
- `docs/hooks/publish_site_assets.py`
- `bijux_pollenomics_dev.docs.site_assets`

## Why The Hook Exists

The repository keeps browser icon sources under `docs/assets/site-icons/` so
they stay versioned with the rest of the docs theme. Browsers still expect
those files at the published site root, so `publish_site_assets.py` copies the
checked-in sources into the build output after MkDocs finishes.

That means docs integrity here is not only about Markdown and navigation. It
also includes the root asset contract that makes the generated atlas and report
pages render with the expected icons when they are opened directly.

## Purpose

This page explains where repository documentation integrity support lives.
