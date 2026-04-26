---
title: Security Gates
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-26
---

# Security Gates

Security support here is narrow and practical.

## Current Gates

- `trusted_process.py` requires absolute executables for repository-owned
  subprocess calls
- `quality/deptry_scan.py` helps keep dependency review consistent across
  packages
- publication guards stop accidental prerelease or dirty-version publication

## Boundary

This package does not act as a full application security layer. It protects the
repository’s maintenance flows from obvious drift and unsafe publication paths.
