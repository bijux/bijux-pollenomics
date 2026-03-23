---
title: Neotoma
audience: mixed
type: explanation
status: canonical
owner: bijux-pollen-docs
last_reviewed: 2026-03-23
---

# Neotoma

`data/neotoma/` contains Nordic pollen and paleoecology site data normalized from the Neotoma API.

## What It Produces

- a raw API snapshot under `data/neotoma/raw/neotoma_pollen_sites.json`
- normalized CSV and GeoJSON outputs under `data/neotoma/normalized/`

## Why It Matters

Neotoma is the strongest pollen-oriented source in the current pipeline and is the clearest bridge from aDNA evidence toward pollenomic site interpretation.

## Acquisition Command

```bash
PYTHONPATH=src .venv/bin/python -m bijux_pollen.cli collect-data neotoma --output-root data
```

## Normalization Rule

The repository reduces Neotoma geometries to representative points for map use, then assigns those points to Nordic countries using the tracked boundary layer.

## Purpose

This page explains how Neotoma enters the repository and why it is part of the shared Nordic evidence surface.
