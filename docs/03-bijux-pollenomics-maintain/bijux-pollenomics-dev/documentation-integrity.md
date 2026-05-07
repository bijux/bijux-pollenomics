---
title: Documentation Integrity
audience: maintainer
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-05-07
---

# Documentation Integrity

Documentation integrity means the public site still builds, the key reader
links still resolve, and the docs surface does not drift away from the checked
outputs it claims to describe.

The documentation workflow relies on strict MkDocs builds and link-focused
regression checks. It also checks package-facing badge surfaces and theme-owned
assets such as `docs/assets/site-icons/`.

This page exists because docs are a release surface, not decoration. It should
stay tied to the shared Bijux docs theme contract and to the tracked public
evidence paths.
