---
title: Execution Model
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Execution Model

The package executes as an explicit command-driven batch workflow.

```mermaid
flowchart LR
    parse["parse command"]
    resolve["resolve handler"]
    defaults["load defaults"]
    work["perform collection or reporting work"]
    write["write reviewable files"]
    exit["exit command"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class parse,page resolve;
    class defaults,work,write,exit positive;
    parse --> resolve --> defaults --> work --> write --> exit
```

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

## Bottom Line

This runtime does not hide behavior behind a long-lived application process.
Each command is a bounded batch run whose result is legible from the
files it writes and the exit status it returns.

