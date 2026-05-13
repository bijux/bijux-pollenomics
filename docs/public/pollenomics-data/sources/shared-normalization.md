---
title: Shared Normalization
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-10
---

# Shared Normalization

Different source families enter the repository in very different shapes, but
they still need a shared normalization discipline if they are going to appear
together without collapsing into one shapeless export.

Normalization is the repository's way of translating unlike inputs into
repository-owned evidence artifacts that can be compared, reviewed, and
published responsibly. It is not a cosmetic formatting pass. It is the point
where raw source material becomes something the repository can stand behind.

## What Shared Normalization Means

Shared normalization does not force every source to have identical fields. It
means the repository gives each family a predictable stage where the material
is converted into repository-owned evidence artifacts with known roles.

That discipline is what makes it possible to compare:

- source capture versus public publication
- one domain against another
- visible points against the narrower evidence files that support them

## What Normalization Must Not Do

Normalization should make unlike families legible together, but it should not
pretend that unlike evidence becomes identical evidence.

It must not:

- flatten away source-specific limits
- invent certainty that was not present upstream
- hide the difference between context layers and direct sample-backed evidence

If it did those things, the repository would look cleaner while becoming less
honest.

## Why Readers Benefit

Readers usually notice normalization only when it is missing. Without it, a
mixed repository turns into a pile of raw tables, ad hoc exports, and public
pages that cannot be compared honestly.

With it, readers can move across source families and still understand what is
direct evidence, what is context, what is sample-backed, and what is a broader
framing layer.

## Where The Repository-Owned Records Live

Normalized family outputs live in paths such as:

- `data/landclim/normalized/`
- `data/neotoma/normalized/`
- `data/sead/normalized/`

The public publication side then builds from those repository-owned surfaces
into atlas, regional, and country outputs.
