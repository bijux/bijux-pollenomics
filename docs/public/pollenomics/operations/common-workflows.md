---
title: Common Workflows
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Common Workflows

This page groups the rebuild paths by question, not by internal subsystem. The
idea is simple: choose the smallest workflow that answers your question, then
stop there.

## Fresh Checkout

1. run `make install`
2. confirm the console script with
   `artifacts/root/check-venv/bin/bijux-pollenomics --version`
3. run `make check` or the narrower validation targets you need

Use this path when you first want to prove that the repository is runnable.

## Data Refresh Review

1. run `make data-prep`
2. inspect `data/collection_summary.json`
3. inspect the changed source-family subtrees under `data/`

Use this path when the question is whether upstream evidence changed and how
that change was normalized.

## Publication Review

1. run `make reports`
2. inspect `docs/report/published_reports_summary.json`
3. inspect `docs/report/world/`
4. inspect `docs/report/repository_truth_posture.md`

Use this path when the question is what the repository now says in public.

## Full Local Rebuild

1. run `make app-state`
2. inspect the `data/`, `docs/report/`, and docs-site changes separately
3. finish with the relevant targeted tests before committing

Use this broader path only when your task genuinely spans source refresh,
publication, and docs surfaces together.
