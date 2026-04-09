---
title: Artifact Contracts
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Artifact Contracts

Published artifacts are part of the package contract because they are checked in
and reviewed like code.

## Main Artifact Families

- country bundles under `docs/report/<country-slug>/`
- the shared atlas under `docs/report/nordic-atlas/`
- report summaries and map payloads produced by the reporting package

## Contract Anchors

- `reporting/bundles/paths.py`
- `reporting/rendering/`
- `reporting/map_document/`

## Review Rule

If an output path, slug, or file family changes, treat it as an interface change
and update docs plus tests together with the code.

## Purpose

This page records the stable publication artifact surface owned by the package.
