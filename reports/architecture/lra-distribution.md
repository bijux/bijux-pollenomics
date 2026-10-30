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

On 23 October 2026, we built the host, compatibility facade and engine at
commit `b25d0fbf9f667819e1a08da64634240644a6580d`, each version
`0.1.9.dev1760`. Standard isolated PEP 517 builds produced three wheels and
three source distributions. We rebuilt each source distribution into a wheel
without access to the enclosing Git repository. All nine archives passed the
maintained distribution checks, including metadata, confined paths and wheel
RECORD integrity.

We used two fresh, noneditable CPython 3.11.13 environments: one for direct
wheels and one for wheels rebuilt from source distributions. In each environment,
we first installed the base host and facade. NumPy, SciPy, pandas and the engine
were absent; loading LRA returned the declared extra-install instruction.
Both CLIs exposed their version, help and `run-lra --help`.

We then installed the host's `lra` extra and the local engine wheel together
in each environment. Dependency checks passed. Isolated Python probes verified
the installed distribution origins in `site-packages`, engine version, entry
point and descriptor before running bundled REVEALS and analytical LOVE with
R absent from `PATH` and `R_HOME` empty. REVEALS produced samples of shape
2 × 3 × 21, retaining the supplied three-decimal percentage rounding allowance.
LOVE produced a 10 × 10 mean table: seven unsupported rings remained NaN and
three supported rings retained 16 negative values without clipping.

All 32 build, install, dependency and consumer commands passed. This establishes
two local distribution paths on this platform, including an independent source
archive rebuild. It does not establish public index availability, release rights,
other operating systems, ecological accuracy or final release versions. The
separate native R comparison uses the shared editable environment; this wheel
check does not establish an R comparison of the newly installed wheels.

We subsequently qualified the changed host report asset at commit
`2f9e86a826ae5cde8eb501f4cab4dcb7783a7d8a`, host version `0.1.9.dev1774`.
We built its wheel and source archive, independently rebuilt the source
archive without enclosing Git discovery, and passed all three archive checks.
We reused the two private installation environments, removed the engine from
each, installed the corresponding host wheel and ran the saved signed-report
consumer in isolated Python. Both paths retained 18 model rows and three
missing values, authenticated all 41 report files, and loaded the exact
18,936-byte packaged controller. The 516,475-byte HTML remained below the
524,288-byte budget. All ten commands passed in 9.991 seconds. This affected
host check did not repeat numerical-engine parity or establish browser or
scientific acceptance; the synthetic report retains `not_evaluated`.

We also qualified the new internal common-cover likelihood at commit
`a790c29a371b90f686a727a5761b44d0405ac77b`, engine version `0.1.9.dev1787`.
Its direct wheel, source archive and independently rebuilt wheel passed the
three archive checks. Both existing private environments installed the new
engine, passed dependency checks and imported it from their own `site-packages`
in isolated Python. A known common-cover example and an independent scalar
root solution agreed; saturated floating information and an unmeasured taxon
retained their refusals. The first analytic probe requested tighter cover error
than the default score stopping rule guaranteed and failed by 1.66 × 10⁻¹¹.
Both installed paths met the unchanged 10⁻¹² analytic bound after explicitly
requesting tighter solver stopping tolerances. This point-fit package check
adds no uncertainty, real-cohort, historical-method or release qualification;
the shared development environment and earlier R results were not rerun.

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
