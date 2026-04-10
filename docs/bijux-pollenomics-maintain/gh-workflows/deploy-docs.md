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

It also validates the docs output contract before publication.

It runs on `main` when docs-related files change and can also be started
manually. The job tree stays small on purpose: validate the docs contract,
build the site, validate the published assets, then deploy the Pages artifact.

## Purpose

Use this page to understand when documentation publication runs and which site
inputs it validates before deploy.
