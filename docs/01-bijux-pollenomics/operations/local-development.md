---
title: Local Development
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Local Development

Local development should keep verification and rewrite operations separate.

```mermaid
flowchart LR
    verify["safe verification loop"]
    rewrite["explicit rewrite loop"]
    review["review tracked diffs"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class verify,page review;
    class rewrite caution;
    verify --> review
    rewrite --> review
```

## Safe Default Loop

```bash
make lock-check
make lint
make test
make docs
make package-verify
```

## Rewrite Loop

Use explicit rewrite targets only when the intent is to refresh tracked outputs:

- `make data-prep`
- `make reports`
- `make app-state`

## Open This Page When

- deciding whether the task is verification-only or intended to rewrite tracked
  repository state
- teaching a new maintainer the default local working rhythm

