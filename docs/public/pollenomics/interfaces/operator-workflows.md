---
title: Operator Workflows
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Operator Workflows

The runtime has three honest operator workflows: verify the checkout, rebuild
tracked data, or publish downstream outputs. Mixing those without saying which
one you are doing is how review gets muddy.

This page translates the command surface into practical intent. The goal is not
to list every command again. The goal is to help a reader choose the right
class of workflow before they start rewriting tracked state.

## The Three Questions

Before running anything, ask which question you are actually trying to answer:

- is the checkout healthy
- did the evidence tree change
- what public output does the repository now publish

Those three questions sound close together, but they create different diffs,
different review burdens, and different kinds of public risk.

## Verify Only

- `make install`
- `make lock-check`
- `make lint`
- `make test`
- `make test-generated-artifacts`
- `make test-all`
- `make docs`

Use this path when you need proof that the checkout is healthy without
rewriting tracked state.

`make test` is the faster default check path. `make test-generated-artifacts`
isolates the generated-publication contract lane. `make test-all` is the full
local verification gate when nothing should be skipped.

## Refresh Data

- `make data-prep`
- inspect `data/collection_summary.json`
- inspect source-family roots under `data/`

Use this path when the goal is collection or normalization review.

## Publish Outputs

- `make reports`
- inspect `docs/report/published_reports_summary.json`
- inspect `docs/report/repository_truth_posture.md`

Use this path when the goal is country bundles, atlas layers, or public review
surfaces.

## How To Choose Cleanly

- choose verify if you want confidence without changing the repository story
- choose refresh if you expect upstream evidence movement
- choose publish if the output question is public wording, report structure, or
  visible atlas behavior
- do not treat publish as a substitute for refresh; it only tells the truth
  about whatever evidence state already exists

## Why These Three Paths Stay Separate

They answer different questions:

- verify asks whether the checkout is healthy
- refresh asks whether upstream evidence changed
- publish asks what the repository now says in public

Keeping those questions separate makes review faster and the resulting diffs
more honest.
