---
title: verify
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-19
---

# verify

`verify.yml` is the main repository verification workflow.

It runs repository checks first and then fans out into package-level checks for
`bijux-pollenomics`, `pollenomics`, and `bijux-pollenomics-dev`.

The job tree is intentionally split. `repository` runs shared automation
contracts first, `package` fans out by package through `ci-package.yml`, and
each reusable package run splits again into package-scoped `tests`, `checks`,
and `lint` jobs.

## Purpose

Use this page to understand when verification runs and how it branches from
repository checks into package-level jobs.
