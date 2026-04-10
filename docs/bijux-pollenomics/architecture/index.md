---
title: Architecture
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Architecture

This section explains how `bijux-pollenomics` is divided structurally across
CLI parsing, data collection, spatial helpers, and report publishing.

Use it when the question is about module seams, dependency direction, and how
tracked outputs are produced from the package internals.

## Start Here

- open [Module Map](module-map.md) for the shortest code-level tour
- open [Execution Model](execution-model.md) when you need to trace collection
  and publication flow
- open [Integration Seams](integration-seams.md) when the boundary between
  collectors, helpers, and report builders is the real question

## Pages In This Section

- [Module Map](module-map.md)
- [Dependency Direction](dependency-direction.md)
- [Execution Model](execution-model.md)
- [State and Persistence](state-and-persistence.md)
- [Integration Seams](integration-seams.md)
- [Error Model](error-model.md)
- [Extensibility Model](extensibility-model.md)
- [Code Navigation](code-navigation.md)
- [Architecture Risks](architecture-risks.md)

## Purpose

This page organizes the structural explanations for the runtime package.
