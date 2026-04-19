---
title: State and Persistence
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# State and Persistence

Persistent state in `bijux-pollenomics` is primarily file state.

## Durable State

- tracked source files under `data/<source>/raw/`
- normalized outputs under `data/<source>/normalized/`
- published report bundles under `docs/report/`
- frozen API contracts under `apis/bijux-pollenomics/v1/`

## Non-Durable State

- virtual environments and build artifacts under `artifacts/`
- command-local in-memory objects used during collection and reporting

## Review Implication

Because the runtime persists through files rather than a service database,
state-changing commands must be evaluated through their filesystem diffs. If a
change alters persistent outputs, the docs and review story should say why.

## Purpose

This page explains where runtime state lives and how it should be reviewed.
