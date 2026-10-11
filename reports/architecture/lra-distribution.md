# Why we kept the LRA engine separate

## Our decision

We kept `bijux-pollenomics-lra` as a separate, optional distribution and made
`bijux-pollenomics[lra]` the single install choice for users who need LRA. We
considered merging the engine into the host because the repository already
contains substantial LRA work. The built-package check showed that merging
would not simplify that user operation. Keeping the boundary also leaves the
base host free of NumPy, SciPy and pandas while the LRA engine has an explicit
version and extension contract.

The [host metadata](../../packages/bijux-pollenomics/pyproject.toml) declares
an Apache-2.0 runtime and an `lra` extra requiring
`bijux-pollenomics-lra>=0.1.5,<0.3`. The [engine metadata](../../packages/bijux-pollenomics-lra/pyproject.toml)
declares GPL-2.0-or-later, its numerical dependencies and the extension entry
point. The host's [discovery code](../../packages/bijux-pollenomics/src/bijux_pollenomics/analysis/lra/engine/discovery.py)
checks the installed engine's distribution, version, entry point and API
descriptor. Those are current package contracts, not a promise of a future
public release.

## What we verified

On 1 October 2026, we installed the host with its `lra` extra from locally
built `0.1.9.dev847` host and engine wheels at commit `14d999d43` into a fresh
CPython 3.11 environment. The installed host discovered the `0.1.9.dev847`
engine entry point from `site-packages`, then ran deterministic bundled REVEALS
and analytical LOVE examples with R absent from `PATH` and `R_HOME` empty. The
REVEALS sample shape was 2 × 3 × 21; the LOVE mean cover shape was 10 × 10.

In a second fresh environment we installed the base host wheel alone. NumPy,
SciPy, pandas and the engine were absent; loading LRA returned the declared
extra-install instruction. Both installed CLIs exposed `run-lra --help`. This
establishes one local install path on this platform. Public index availability,
release rights, other operating systems and final release versions remain
separate gates.

## Public index check on 30 September 2026

We checked the official PyPI [host project](https://pypi.org/project/bijux-pollenomics/)
and [engine project URL](https://pypi.org/project/bijux-pollenomics-lra/).
The host JSON endpoint returned published version `0.1.8` with only a `dev`
extra. Both the engine JSON endpoint and its simple-index endpoint returned
HTTP 404. This is a dated availability observation: the local built-wheel
proof does not yet give ordinary users a public PyPI route for
`bijux-pollenomics[lra]`. We did not publish either distribution. The release
candidate, source notices, installed help and rights review remain open gates
before a public one-command install can be claimed.

## Why we did not merge the distributions

A merged wheel would give us one artifact and version, but it would also put
the engine's numerical dependency set and GPL-derived code inside the
Apache-declared host. That change requires a qualified review of exact source
rights and redistribution terms, followed by an entry-point, API, installation
and release migration. The [Apache Software Foundation compatibility guidance](https://apache.org/licenses/GPL-compatibility.html)
distinguishes GPLv2 from GPLv3 compatibility; this report does not make a legal
determination. Package-size difference alone did not justify the migration.

We will revisit the split if a measured user or release problem remains after
the optional-extra path, and after the rights and migration work can be
specified and verified. Installing the engine does not qualify a pollen core
for LRA: chronology, basin geometry, denominator, PPE and source rights remain
scientific admission decisions in the [model-use report](../science/model-use.md).
