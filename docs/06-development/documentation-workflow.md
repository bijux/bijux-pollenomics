---
title: Documentation Workflow
audience: mixed
type: workflow
status: canonical
owner: bijux-pollen-docs
last_reviewed: 2026-03-23
---

# Documentation Workflow

The documentation system is now MkDocs-based and intentionally aligned with the broader Bijux project style.

## Commands

```bash
make docs
make docs-serve
```

## Documentation Rules

- the docs homepage should continue to lead with the shared Nordic map
- section index pages should explain how to read the section
- diagrams should clarify architecture or workflow, not decorate pages
- documentation should match the checked-in command surface and file layout exactly
- claims about current files, commands, counts, or layers should be verified against code or checked-in artifacts in the same change
- the seven canonical sections should carry the narrative documentation load; duplicate side-channel guide pages should not reappear
- when scope is limited, say so explicitly instead of implying future capability is already present

## Purpose

This page explains how docs are built and what quality bar they should meet.
