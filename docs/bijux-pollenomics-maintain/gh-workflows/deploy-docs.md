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

It also validates the docs output contract before publication. In
`bijux-pollenomics`, that contract includes the root-level browser icons copied
by `docs/hooks/publish_site_assets.py` after the MkDocs build finishes.

It runs on `main` when docs-related files change and can also be started
manually. The job tree stays small on purpose: validate the docs contract,
build the site, validate the published assets, then deploy the Pages artifact.

## Asset Publication Rule

The checked-in icon sources live under `docs/assets/site-icons/`, but published
browsers probe for `favicon.ico` and Apple touch icons at the site root. The
deploy workflow therefore depends on the post-build hook to copy:

- `favicon.ico`
- `apple-touch-icon.png`
- `apple-touch-icon-precomposed.png`

The hook is repository-specific because these atlas and report pages are also
published directly from the docs site root. It is not a generic MkDocs concern.

## Purpose

Use this page to understand when documentation publication runs and which site
inputs it validates before deploy.
