---
title: Make System Contracts
audience: maintainer
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-05-08
---

# Make System Contracts

The `makes/` tree is command routing, not a bag of convenience aliases. Its
job is to give maintainers stable entrypoints into install, verify, publish,
and package surfaces.

## Main Files

- `makes/root.mk` for top-level entrypoint routing
- `makes/env.mk` for environment conventions
- `makes/packages.mk` and `makes/packages/*.mk` for package-specific dispatch
- `makes/publish.mk` for publication-oriented commands
- `makes/bijux-py/*.mk` for shared Python packaging and API contracts

## Repository Layout And Entry Points

- `Makefile` is the main root entrypoint
- `makes/README.md` explains the shared command-routing posture
- package-specific `.mk` files should explain why a target belongs to that
  owner rather than duplicating root logic

## Authoring And CI Pressure

- authoring rules should keep target intent explicit
- CI targets should mirror local verification boundaries closely enough to
  debug failures without reading every workflow first
- environment targets should make the `artifacts/` and editable-venv posture
  obvious

## Contract Rule

Each `make` target should answer one of three questions clearly:

- does it verify repository state without rewriting tracked outputs?
- does it rebuild governed tracked outputs under `data/` or `docs/report/`?
- does it publish or package release artifacts?

If a target hides that boundary, the maintainer surface is getting weaker.
