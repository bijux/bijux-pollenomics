---
title: Deployment Boundaries
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Deployment Boundaries

The package does not deploy a long-lived application. Its deployable unit is a
set of generated files plus a publishable Python distribution.

## What Gets Deployed

- Python package artifacts built from `packages/bijux-pollenomics/`
- the MkDocs site that exposes checked-in docs and `docs/report/` outputs

## What Does Not Get Deployed

- a runtime server for interactive data collection
- mutable remote state owned by this package

## Purpose

This page clarifies the package's deployment boundary so operators do not infer
service semantics that the repository does not provide.
