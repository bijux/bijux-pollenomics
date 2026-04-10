---
title: publish
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-10
---

# publish

`publish.yml` handles tagged release publication for the primary package across
PyPI, GHCR, and GitHub Releases.

It delegates build work to the reusable release workflow and then publishes the
staged distribution artifacts to PyPI, the staged release bundle to GHCR, and
the staged release assets to the repository release page.

## Current Job Tree

- `build` creates the staged release bundle for `bijux-pollenomics`
- `publish_pypi` uploads the package distributions to PyPI
- `publish_ghcr` publishes the staged release bundle to GHCR as an OCI artifact
- `release` creates the repository GitHub Release and attaches the staged assets

## Purpose

This page records the role of the publish workflow.
