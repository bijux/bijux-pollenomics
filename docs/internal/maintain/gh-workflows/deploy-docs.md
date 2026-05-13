---
title: Docs Deployment
audience: maintainer
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-05-07
---

# Docs Deployment

`deploy-docs.yml` builds the strict MkDocs site and publishes it only when the
repository keeps a coherent docs surface.

The workflow follows the shared Bijux docs contract, uses `mkdocs.shared.yml`,
and treats broken docs publication as a release problem rather than as a
cosmetic failure.
