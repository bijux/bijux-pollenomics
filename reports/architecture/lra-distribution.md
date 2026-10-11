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

## What we built and observed

At clean product commit `46fcf43f5`, we built both wheels and installed them
from local wheel directories into a fresh CPython 3.11 environment with one
`bijux-pollenomics[lra]` command. The host loaded the installed engine from
`site-packages`, verified its `lra` entry point and analytical LOVE capability,
and the engine ran a deterministic REVEALS plus analytical LOVE example from
bundled inputs without R on `PATH` or `R_HOME`.

| Built wheel | Bytes | SHA-256 |
| --- | ---: | --- |
| `bijux_pollenomics-0.1.9.dev655-py3-none-any.whl` | 2,487,011 | `eb428cc0d8edbbc2c7060f847dd70c89d758402d1bf30b1f831eb1d0174d8eed` |
| `bijux_pollenomics_lra-0.1.9.dev655-py3-none-any.whl` | 261,194 | `2ddcd766eef56090b7786957b4bf88c29da6e05b679a49cda3bec8aece3991f3` |

The resulting environment had both `0.1.9.dev655` distributions and 16 other
dependencies. Its result manifest named the `python-numpy-scipy` backend,
installed version, original DISQOVER reference version `0.9.14` and archive
SHA-256 `ea496ae82807b52c9dd3d4b39b4dfa294bfac4068e20184ce56187bff70caf5c`.
In a second fresh environment, we installed only the base host wheel. It had
neither NumPy nor the engine package; `load_engine()` returned the declared
`LRARefusal` with the extra-install instruction. The base installed CLI still
exposed `run-lra` in its help.

These checks establish a local, built-wheel installation path on this
platform. We have not tested every operating system, final release versions or
the hosted release pipeline. The generated wheel and
run products were kept under `artifacts/jobs/lra-single-install/` during the
check; the hashes above preserve the identity used for this decision.

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
