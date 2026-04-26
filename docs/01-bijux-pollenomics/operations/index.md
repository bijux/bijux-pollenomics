---
title: Operations
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Operations

This section explains how to install, run, troubleshoot, and release the
runtime package in the context of the tracked repository workflow.

Use it when the question is procedural rather than structural.

```mermaid
flowchart LR
    setup["installation and setup"]
    local["local development"]
    workflows["common workflows"]
    diagnostics["diagnostics and recovery"]
    release["release and deployment boundaries"]
    reader["reader question<br/>which procedure should I run?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class setup,page reader;
    class local,workflows,diagnostics,release positive;
    setup --> reader
    local --> reader
    workflows --> reader
    diagnostics --> reader
    release --> reader
```

## Start Here

- open [Installation and Setup](installation-and-setup.md) for environment and
  bootstrap expectations
- open [Common Workflows](common-workflows.md) for the main rebuild and verify
  paths
- open [Release and Versioning](release-and-versioning.md) when the question is
  about tags, package artifacts, or release evidence

## Pages In This Section

- [Installation and Setup](installation-and-setup.md)
- [Local Development](local-development.md)
- [Common Workflows](common-workflows.md)
- [Observability and Diagnostics](observability-and-diagnostics.md)
- [Performance and Scaling](performance-and-scaling.md)
- [Failure Recovery](failure-recovery.md)
- [Release and Versioning](release-and-versioning.md)
- [Security and Safety](security-and-safety.md)
- [Deployment Boundaries](deployment-boundaries.md)

## What This Section Should Answer

- how to bootstrap the supported environment
- how to separate verification from state-changing rebuild work
- how to recover from failures without widening the diff surface

## Purpose

This page organizes the operational procedures for running and releasing the
runtime package.
