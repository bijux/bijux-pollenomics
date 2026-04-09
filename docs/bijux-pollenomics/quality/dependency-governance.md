---
title: Dependency Governance
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Dependency Governance

Dependency additions should be rare and easy to justify.

## Current Stance

- keep runtime dependencies small
- prefer standard-library solutions when they keep the code understandable
- treat new parsing, HTTP, or geospatial libraries as public review events

## Repository Context

Dependency checks are reinforced by repository quality and security targets, but
package docs should still explain why a new dependency is worth its maintenance
cost.

## Purpose

This page records how dependency growth should be governed for the runtime
package.
