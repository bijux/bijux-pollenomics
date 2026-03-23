---
title: Troubleshoot Early Problems
audience: mixed
type: troubleshooting
status: canonical
owner: bijux-pollen-docs
last_reviewed: 2026-03-23
---

# Troubleshoot Early Problems

## `make install` fails

Check:

- `python3.11 --version`
- whether `.venv/` is in a broken partial state

If needed:

```bash
make clean
make install
```

## `make data-prep` is slow

This is expected when RAÄ density is being rebuilt, because the current workflow calculates visible Swedish archaeology coverage from repeated RAÄ WFS count queries.

## `make docs` fails

Check:

- missing Markdown pages referenced in navigation
- broken relative links
- files moved without updating `mkdocs.yml`

## The map opens but some layers are missing

Check:

- whether `make data-prep` completed successfully
- whether `report-multi-country-map` ran after the last data refresh
- whether the copied files exist under `docs/report/nordic/`

## Purpose

This page captures the most likely first-run problems before deeper architecture or reference material is needed.
