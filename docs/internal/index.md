---
title: Internal Guide
audience: maintainer
type: index
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-07-22
---

# Internal Guide

The internal surface owns repository operation: validation policy, generated
state, workflow behavior, release evidence, and documentation integrity. It
does not redefine the scientific meaning published in the public data and
atlas guides.

## Start Here

<div class="bijux-quicklinks">
  <a class="md-button md-button--primary" href="maintain/">Open the maintainer handbook</a>
  <a class="md-button" href="pollenomics-dev/documentation-integrity/">Open documentation integrity</a>
  <a class="md-button" href="pollenomics-dev/quality-gates/">Open quality gates</a>
  <a class="md-button" href="pollenomics-dev/release-support/">Open release support</a>
</div>

## Ownership Map

| Concern | Owner | Governing entry point |
| --- | --- | --- |
| repository-wide maintenance | maintainer handbook | [Maintenance](maintain/index.md) |
| focused repository operations | `bijux-pollenomics-dev` | [Operator guide](pollenomics-dev/index.md) |
| documentation navigation and claim integrity | documentation integrity checks | [Documentation integrity](pollenomics-dev/documentation-integrity.md) |
| validation selection and proof | quality gates | [Quality gates](pollenomics-dev/quality-gates.md) |
| GitHub Actions and release evidence | release support | [Release support](pollenomics-dev/release-support.md) |
| Make target contracts | Make handbook | [Make system](maintain/makes/index.md) |

## Public And Internal Boundary

Public pages govern reader interpretation of sources, evidence, publications,
atlas features, and fieldwork. Internal pages govern how maintainers preserve
those contracts while changing code or generated state. An internal diagnostic
may block a release or reveal drift; it does not become the scientific
authority for a public record.

Readers evaluating a scientific or publication claim should return to the
[documentation home](../index.md) and follow the claim upstream through the
data system.
