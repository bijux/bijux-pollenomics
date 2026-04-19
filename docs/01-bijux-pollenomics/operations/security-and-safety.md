---
title: Security and Safety
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Security and Safety

Security in `bijux-pollenomics` is mostly about trusted execution and safe
handling of fetched content.

## Current Safety Anchors

- source files are collected through explicit supported-source paths
- XML handling uses `defusedxml`
- repository checks include security and dependency review targets
- tracked outputs make suspicious changes easier to inspect in review

## Operational Caution

Some collection paths interact with mutable external services. Treat upstream
inputs as untrusted and prefer explicit local review of resulting tracked diffs
before assuming a refresh is safe to publish.

## Purpose

This page records the practical security stance of the runtime package.
