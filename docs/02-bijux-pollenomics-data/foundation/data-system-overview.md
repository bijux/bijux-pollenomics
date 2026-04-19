---
title: Data System Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Data System Overview

The pollenomics data system is a tracked file tree that separates source intake,
normalized evidence layers, and publication outputs.

## Core Shape

- `data/` holds source-owned raw and normalized material
- `docs/report/` holds publication bundles derived from that tracked context
- `apis/` holds frozen API contracts that describe public-facing behavior around
  those outputs

## Why This Shape Exists

The repository needs to prove where evidence layers came from and what the
current publication state was at one commit. A file-oriented system makes that
history reviewable in Git instead of requiring hidden external state.

## Purpose

This page gives the shortest explanation of the repository's data architecture.
