---
title: Review Checklist
audience: reader
type: checklist
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Review Checklist

Use this as a fast but honest review pass before commit:

- identify which runtime boundary changed: commands, data, reporting, or docs
- inspect the tracked destinations that boundary owns
- check whether the repository story stayed pollenomics-first
- check whether non-aDNA source breadth stayed visible
- check whether atlas or country output language became stronger than the
  evidence reviews allow
- run the narrowest relevant tests before commit

If the change cannot survive this short review in plain language, it is usually
not ready for a broader build or a public claim.
