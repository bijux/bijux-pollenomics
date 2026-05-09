---
title: Filters and Popups
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# Filters and Popups

The public map should make geography filtering understandable instead of
silently burying it in code. World, Europe-plus, Nordic, and country views are
all governed by explicit scope rules.

## What Readers Should Be Able To Inspect

- which countries are active in one scope
- which point layers remain visible after geography filtering
- why Nordic-only context overlays disappear when a reader moves back to world or Europe-plus
- whether animal points belong to the world surface only or to narrower derived views
- whether a country bundle is derived from the world surface directly or through a regional parent

The point of the inspection surface is not decoration. It is to keep geography
selection auditable for readers who did not write the code.

## Nordic Atlas Filters And Popups

The Nordic atlas inherits these filtering rules from the wider publication
geography contract. Popups should expose why a point is visible, not hide the
selection logic behind front-end convenience.
