---
title: Common Workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Common Workflows

Most package work falls into a short list of repeatable workflows.

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

## Purpose

This page records the package workflows operators use most often.
