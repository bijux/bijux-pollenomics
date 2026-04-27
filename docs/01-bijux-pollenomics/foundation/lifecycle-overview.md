---
title: Lifecycle Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Lifecycle Overview

This package owns one tracked lifecycle from command entry to published output.
Each stage matters because it changes which file or surface becomes
authoritative for the next review question.

## Runtime Lifecycle

- commands enter through `cli.py` and `command_line/`
- collection and normalization run through `data_downloader/collector.py` and
  `data_downloader/pipeline/`
- repository-owned evidence state is written under `data/`
- reporting code turns that tracked state into bundles and atlas outputs under
  `docs/report/`

## Review Handoffs

- the data handbook explains why a source family looks the way it does
- the atlas pages explain what one visible publication layer can and cannot
  support
- the fieldwork pages explain the direct visit record behind one mapped point

## First Proof Check

- `src/bijux_pollenomics/command_line/`
- `src/bijux_pollenomics/data_downloader/pipeline/`
- `src/bijux_pollenomics/reporting/`
- `tests/regression/test_data_collector.py`
- `tests/regression/test_country_report.py`
