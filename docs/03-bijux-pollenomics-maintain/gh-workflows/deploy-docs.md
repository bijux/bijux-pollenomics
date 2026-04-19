---
title: deploy-docs
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-10
---

# deploy-docs

`deploy-docs.yml` builds the strict MkDocs site and publishes the built output
to the docs repository when credentials are available.

The workflow follows the shared Bijux docs contract. This repository keeps site
icons under `docs/assets/site-icons/` and uses the standard MkDocs theme
configuration surface from `mkdocs.shared.yml`.

It runs on `main` when docs-related files change and can also be started
manually. The job tree stays small on purpose: build the strict site, validate
the deploy artifact, then publish to Pages.

## Trigger Surface

The workflow should run when either authored docs inputs or the shared docs
shell changes. That includes `docs/**`, `mkdocs.yml`, and
`mkdocs.shared.yml`, because the shared MkDocs config changes site behavior
even when no Markdown page changes.

## Purpose

Use this page to understand when documentation publication runs and which site
inputs it validates before deploy.
