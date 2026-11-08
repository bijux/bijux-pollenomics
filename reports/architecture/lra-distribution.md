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

## Installed host and optional engine

Accepted source `07b9a9a53cfc34822da1c520d41ba26f6629cde9` was qualified on
8 November 2026 as `0.1.9.dev2607`, using CPython 3.11.13 on macOS ARM64.
The host and engine each produced a wheel and sdist; both standalone sdist
rebuilds retained their version with enclosing Git discovery blocked. All six
archives passed Twine, metadata, legal-file and path checks. Every wheel RECORD
entry passed; 1,481 host and 71 engine files matched accepted Git blobs, and
the engine included its declared SCM-generated version file. Direct/sdist-rebuilt
wheel payloads were byte-identical. Host metadata remained Apache-2.0; the
optional engine retained GPL-2.0-or-later.

Two fresh noneditable environments separated the base host from optional LRA.
The base environment was subsequently reinstalled directly from the host sdist.
All probes ran under `python -I` from a neutral directory, with production
imports confined to the corresponding installed prefix and no editable packages.

| Installed consumer | Elapsed process seconds | Peak RSS bytes | Verified module origins |
| --- | ---: | ---: | ---: |
| Base host wheel | 8.39 | 78,757,888 | 1,050 |
| Base host sdist | 3.13 | 73,465,856 | 1,050 |
| Host and optional LRA wheels | 33.45 | 216,727,552 | 2,030 |

Each probe refused five oversized JSON-float count totals with
`invalid_count_denominator`, including local counts, and refused a changed
source digest before output. Both base paths had no engine, NumPy, SciPy or
pandas and returned `lra_extension_missing` for valid synthetic LRA input. The
optional path discovered the installed extension and produced two synthetic
REVEALS products: integer and integral-float counts yielded two byte-identical
CSV pairs, and both products reopened through their manifests. The installed
[Neotoma site-evidence API](../../packages/bijux-pollenomics/src/bijux_pollenomics/analysis/lra/materialization/api.py)
preserved nine synthetic source values and their types, exposed the conflicting
provider area definitions, selected no unit and admitted zero samples. The
[request](../../packages/bijux-pollenomics/tests/unit/analysis/lra/support.py) and
[source](../../packages/bijux-pollenomics/tests/unit/analysis/lra/materialization/support.py)
helpers supplied declared synthetic controls; their production calls imported
the installed packages. Both environments passed dependency checks and CLI
version, help and `run-lra --help`; R and Rscript were absent from the probe PATH.

Builds used the declared Hatchling bounds, Hatchling 1.33.0, hatch-vcs 0.5.0
and build 1.4.2. The existing
[locked dependency exporter](../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/dependency_audit.py)
provided nine base and seventeen optional pins, including target markers;
compatible cached payloads were reused and missing wheels downloaded into the
owned cache. The native commands below use the selected package, archive,
interpreter and output locations; `$probe` denotes the retained isolated harness.

```sh
python -m build --no-isolation --wheel --sdist --outdir "$dist" "$package"
python -m build --no-isolation --wheel --outdir "$rebuilt" "$unpacked_sdist"
uv pip install --offline --no-deps --python "$python" "$wheel"
uv pip install --offline --reinstall --no-deps --python "$base_python" \
  --build-constraints "$build_constraints" "$host_sdist"
python -I "$probe" "$role" "$label" "$source" "$output"
```

The build, rebuild and initial-install drivers used 180-second per-subprocess
deadlines; CLI calls had 30 seconds. The direct sdist installation and final
consumers had no imposed process-wide deadline. The table records observed
consumer elapsed time and RSS, without asserting a memory quota. An independent
readback authenticated the archives, captured import origins and both serialized
products without rerunning the producer. Optional
engine execution after a direct sdist installation was not separately tested;
its rebuilt wheel equivalence is the narrower result. This qualification adds
no physical cohort, native R comparison, public index or release claim; both
synthetic products retain `not_evaluated` scientific acceptance.

The same accepted source also supplied the Apache-2.0 `pollenomics` compatibility
wheel. An offline dependency-resolving installation reused the completed base-sdist
environment after its recorded host probes. All eight package payload files matched
Git, the wheel and installed bytes; fourteen wheel RECORD entries, legal files,
Twine and the resulting dependency check passed. An isolated 3.51-second probe
(72,105,984 bytes peak RSS) confirmed twenty shared top-level exports and nested
API/type identity, six console/module version-and-help calls, and an oversized-count
CLI refusal with exit 2 and `invalid_count_denominator`. The public alias API also
preserved that count refusal and `lra_extension_missing` for valid base input,
without creating outputs. All checked imports resolved inside the installed prefix;
the engine, NumPy, SciPy and pandas remained absent. CLI refusals preserve
machine-readable JSON on stdout. This adds no compatibility-sdist,
optional-engine, native-R, physical-cohort or public-release qualification.

## Direct source-distribution installations

Both the base host and optional engine work when installed directly from their
source archives at accepted source
[`0cf34c42`](https://github.com/bijux/bijux-pollenomics/commit/0cf34c42cc6f982ada3b6518ee01f663715f861e).
The two archives have version `0.1.9.dev2725`. This qualification uses CPython
3.11.13 on macOS ARM64 and extends the earlier result to optional-engine
execution after direct sdist installation and the later goat-reference consumer.

Two noneditable prefixes separate the base host from host plus LRA. Installed
production imports are confined to those prefixes; probes use `python -I -B`
from an isolated artifact working directory, with source fixtures and governed
data opened explicitly. The base retains no engine, NumPy, pandas or SciPy.

| Installed runtime | Seconds | Observed peak RSS | Run output |
| --- | ---: | ---: | ---: |
| Base host from sdist | 6.34 | 90.2 MiB | 522.7 KiB |
| Host and optional engine from sdists | 37.89 | 206.0 MiB | 776.5 KiB |

Each probe has a prospective 60-second deadline, a 512 MiB completed-process
RSS check and an 8 MiB output bound; these are not an OS memory quota. CLI
calls retain their 30-second limit, and build/install process groups have
180-second deadlines. The earlier uncapped observations keep their original
scope.

The installed goat API reproduces the complete typed four-row governed master,
including all five reported paper references, both Direkli records and the
unresolved Blagotin wording. All four identities remain ambiguous with zero
final identities. Controlled count cases preserve the exact JSON integer
`9007199254740993` and refuse its excessive denominator through API and CLI;
the five floating-count cases and changed-source digest remain refused without
outputs. Nine synthetic provider-style Neotoma cases preserve literal values,
types and conflicting unit definitions, with no selected unit or admission.
The optional engine produces and reopens two synthetic REVEALS products;
integer and integral-float inputs yield two identical numerical CSV pairs.
Their scientific acceptance remains `not_evaluated`.

Independent readback verifies both archive identities and versions, all 1,481
host and 71 engine source files against accepted Git, 1,492/82 installed RECORD
entries and exact package-owned licence/notice bytes. The engine's declared
generated version file is the sole source-payload exception. Builds reuse the
unchanged locked dependency and build pins; the temporary Hatch version output
is restored to its exact prior bytes, mode and timestamp.

Archive origin is authenticated by the exact local URI and actual frozen archive
bytes. Supplied direct-URL hashes are checked, while the
[standard permits absent hash metadata](https://packaging.python.org/en/latest/specifications/direct-url-data-structure/#archive-urls).
An over-strict metadata-reader refusal and a refused hash-fragment invocation
remain separate retained outcomes. The archives were built once; the successful
probes reuse the original successful installations.

These are installed-runtime, governed-source and synthetic numerical checks.
They add no physical cohort, new scientific acceptance, native-R comparison,
compatibility-sdist qualification or public release.

## Earlier installed API checks

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

At `d30a0ee545abc3a35514e0a9c9f4698c1686e8c1`, engine version
`0.1.9.dev1821`, the direct wheel, source archive and independently rebuilt
wheel passed three checks of the exact new measured-panel counting module
bytes. The two existing private environments installed the corresponding
engine wheels with `--no-deps`, passed dependency checks and ran isolated
joint-region probes from their own `site-packages`. Both probes checked exact
binomial tails, inverses, corners and coordinate extrema, zero projected
Betula/Ulmus effort, the excluded pure-Fraxinus limit, empty regions and four
input refusals. All eight commands passed in 9.10 seconds with 4.14 MB of
outputs. Builds used temporary PEP 517 isolation and the existing offline
backend cache; the shared scientific environment, host and facade were
unchanged. This qualifies the installed mathematical API without rerunning R
or a real cohort, and grants no hosted or complete release qualification.

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
