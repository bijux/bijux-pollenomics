---
title: Execution Model
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Execution Model

The package executes as an explicit command-driven batch workflow.

## Runtime Shape

1. the root CLI parses arguments into one named subcommand
2. runtime dispatch resolves the matching handler
3. the handler loads defaults from `config.py` and option parsing helpers
4. collection or reporting code performs deterministic filesystem work
5. the command exits after writing reviewable files

## Consequences

- there is no long-lived process state between commands
- correctness is observed through tracked file outputs and command exit status
- operators can review each step separately: collection, report publishing, and
  docs build

## Purpose

This page explains the runtime model that underpins every public command.
