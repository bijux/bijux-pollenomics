---
title: Make System Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-10
---

# Make System Overview

The repository make system is the shared command language for maintainer work.

It starts at `Makefile`, delegates to `makes/root.mk`, and then pulls in
repository fragments, reusable `bijux-py` contracts, package dispatch, and
per-package bindings.

