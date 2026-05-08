---
title: Failure Recovery
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Failure Recovery

When a rebuild fails, recover by boundary rather than rerunning the whole
repository blindly.

## Failure Questions

- did command parsing fail before any tracked state changed?
- did collection or normalization fail inside one source family?
- did publication fail while writing `docs/report/` outputs?
- did a truth or contract check block an overclaim?

## Recovery Route

1. inspect the narrowest command you ran
2. inspect the governed root it should have touched: `data/` or `docs/report/`
3. rerun the narrowest relevant tests
4. only rerun `make app-state` once the broken boundary is understood

## High-Risk Cases

- partial aDNA refreshes that appear to improve counts without improving
  sample-owned evidence
- docs rewrites that narrow `01`, `02`, or `03` while keeping pages green
- report output changes that make atlas posture sound stronger than the support
  reviews justify
