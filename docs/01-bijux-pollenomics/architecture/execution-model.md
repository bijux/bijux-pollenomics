---
title: Execution Model
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Execution Model

The package executes as an explicit command-driven batch workflow. One command
becomes one bounded run that either rewrites tracked files clearly or fails
before leaving ambiguous state behind.

## Runtime Shape

1. the root CLI parses arguments into one named subcommand
2. runtime dispatch resolves the matching handler
3. the handler loads defaults from `config.py` and option parsing helpers
4. collection or reporting code performs deterministic filesystem work
5. the command exits after writing reviewable files

## First Proof Check

- `src/bijux_pollenomics/cli.py`
- `src/bijux_pollenomics/command_line/runtime/`
- `src/bijux_pollenomics/data_downloader/collector.py`
- `src/bijux_pollenomics/reporting/service.py`
- `tests/e2e/test_cli.py`
