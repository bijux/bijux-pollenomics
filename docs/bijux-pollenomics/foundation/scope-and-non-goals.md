---
title: Scope and Non-Goals
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Scope and Non-Goals

`bijux-pollenomics` is scoped to deterministic collection and publication work.
It should make tracked evidence layers and report bundles reproducible from one
repository state.

## In Scope

- downloading or refreshing supported source datasets
- normalizing those sources into stable, reviewable files
- publishing country report bundles and the Nordic Evidence Atlas
- exposing configuration defaults that keep those workflows explicit

## Out of Scope

- genotype processing beyond public AADR metadata files
- lake-intersection analysis and ranking logic
- automated field recommendation or site-selection decisions
- mutable hosted application behavior that depends on server state

## Review Rule

If a proposed change increases scientific ambition or product breadth without
also preserving deterministic file outputs and clear review boundaries, it does
not belong in this package yet.

## Purpose

This page records the package boundary in terms of what work it should and
should not absorb.
