---
title: Common Workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Common Workflows

Most runtime work falls into a short list of repeatable workflows. The main
discipline is choosing the narrowest workflow that matches the goal.

## Verify The Current State

Run `make check` when the goal is to validate code, docs, API, packaging, and
shared repository contracts without refreshing tracked scientific outputs.

## Refresh Tracked Data

Run `make data-prep` or the equivalent `bijux-pollenomics collect-data ...`
command when upstream source material or normalization logic needs a deliberate
refresh.

## Refresh Published Artifacts

Run `make reports` or `bijux-pollenomics publish-reports ...` when country
bundles or the atlas need regeneration from current tracked inputs.

## First Proof Check

- `make check`
- `make data-prep`
- `make reports`
- `bijux-pollenomics collect-data ...`
- `bijux-pollenomics publish-reports ...`
