---
title: Dependency Governance
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Dependency Governance

Dependency additions should be rare and easy to justify.

## Current Stance

- keep runtime dependencies small
- prefer standard-library solutions when they keep the code understandable
- treat new parsing, HTTP, or geospatial libraries as public review events

## First Proof Check

- current dependency list
- repository quality and security targets
- the exact runtime surface that needs the new library
