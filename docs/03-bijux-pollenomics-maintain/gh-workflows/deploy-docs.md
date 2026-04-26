---
title: deploy-docs
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-26
---

# deploy-docs

`deploy-docs.yml` builds and publishes the documentation site.

## What It Does

- resolves docs build configuration from repo vars and `.github/docs-deploy.env`
- sets up Python, uv, Node, or Rust only when the repo surface requires them
- discovers install, build, and verify commands from repository targets
- builds the site and publishes a deployable artifact when the event permits it

## Boundary

This workflow owns site publication behavior. It does not define handbook
content quality; the docs pages and local docs targets still own that.
