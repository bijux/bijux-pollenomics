---
title: Common Workflows
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Common Workflows

## Fresh Checkout

1. run `make install`
2. confirm the console script with
   `artifacts/root/check-venv/bin/bijux-pollenomics --version`
3. run `make check` or the narrower validation targets you need

## Data Refresh Review

1. run `make data-prep`
2. inspect `data/collection_summary.json`
3. inspect the changed source-family subtrees under `data/`

## Publication Review

1. run `make reports`
2. inspect `docs/report/published_reports_summary.json`
3. inspect `docs/report/nordic-atlas/`
4. inspect `docs/report/repository_truth_posture.md`

## Full Local Rebuild

1. run `make app-state`
2. inspect the `data/`, `docs/report/`, and docs-site changes separately
3. finish with the relevant targeted tests before committing
