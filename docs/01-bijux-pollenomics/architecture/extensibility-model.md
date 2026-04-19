---
title: Extensibility Model
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Extensibility Model

The package is designed to add new sources and reporting refinements by
extending named registries and stable file contracts rather than by inserting
special cases everywhere.

## Expected Extension Paths

- add new source integrations through `data_downloader.sources` and source
  registry wiring
- add new staging or summary behavior through `data_downloader.pipeline`
- add new report artifacts through `reporting.bundles`, `reporting.rendering`,
  and related context helpers

## Guardrails

- new extensions should still land in deterministic tracked paths
- source-specific behavior should stay source-scoped rather than becoming a
  cross-package shortcut
- extension work should update docs and tests at the same time as code

## Purpose

This page explains how the package is expected to grow without losing shape.
