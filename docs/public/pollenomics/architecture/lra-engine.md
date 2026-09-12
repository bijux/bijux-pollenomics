---
title: LRA Engine Integration
audience: contributor
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-09-12
---

# LRA engine integration

`bijux-pollenomics-lra` owns numerical REVEALS, analytical and optimized LOVE,
coupled reconstruction, exact-coordinate series and forward pollen deposition.
The canonical host owns source admission, chronology, taxa, experiment splits,
commands and product publication. The extension imports neither the host nor its
development toolkit. Its implementation is Python, NumPy and SciPy.

The supported Python facade is `bijux_pollenomics_lra.api`. Installed metadata
registers group `bijux_pollenomics.extensions`, name `lra`, target
`bijux_pollenomics_lra.api:extension_descriptor`. Loading checks installed identity
and compatibility; missing dependencies and incompatible implementations are
observable refusals. There is no standalone engine command or automatic fallback.

| Engine domain | Responsibility |
| --- | --- |
| `models` | Configuration, results, validated dimensions and errors |
| `dispersal` | Deposition factors and source-compatible LOESS curves |
| `reconstruction` | Regional/local equations, draws and forward observation model |
| `optimization` | Bounded solver, replay and convergence diagnostics |
| `workflows` | Stage composition and coordinate pairing |
| `provenance` | Input, backend and scientific content identity |
| `outputs` | Numerical serialization and byte checksums |
| `resources` | Versioned models, schemas and examples |

Tests mirror those responsibilities. Exact-source R tooling lives under
`tests/reference` and does not ship in the runtime wheel. The numerical core does
not write products. Result serialization is explicit; the host decides whether
an output is scientifically eligible for release.

The adopted calculations retain the explicitly named DISQOVER 0.9.14 source
profile. Source geometry conventions, analytical estimates outside physical
fractions, uncertainty omissions and optimizer failure are observable. A numeric
pairing coordinate is not a canonical source ID or an automatically inferred age.
Publication-specific multi-site aggregation requires its own verified profile.

Pollen and vegetation validation have different targets and scores. Holding every
target pollen sample out requires a spatial predictor and a forward observation
model; LOVE itself needs local pollen. Grouped folds and dependency closure guard
the training boundary. Synthetic recovery and R parity establish numerical
behavior; they do not establish ecological accuracy or qualified review.

Hatch/VCS, the workspace lock, Make/tox, test discovery and CI govern the package.
Its GPL license and source attribution are package-owned. Repository license
synchronization must not replace them with the host's Apache license. The
distribution is excluded from the public release matrix pending scientific,
distribution and release acceptance. Local build evidence is not publication.

A bounded C++ objective experiment agreed numerically with Python and R but did
not meet its predefined performance thresholds against prepared NumPy. That
kernel remains Python. This finding does not establish that every possible
native optimization is unsuitable; further native adoption requires measured
benefit, binding safety and platform evidence through the same Python facade.

## Host boundary

The host facade is `bijux_pollenomics.analysis.lra.api`; its `inputs`, `engine`,
`execution` and `outputs` packages have distinct owners and mirrored unit tests.
The CLI delegates to the same service. `validate-lra-input` verifies a declared
request and installed configuration; `run-lra` executes it and publishes a new
local exploratory bundle. Neither command grants source or scientific approval.

The request records sample/site identities separately from exact numeric pairing
coordinates. All source age intervals remain typed BP support. An explicit
`declared_bin_stationarity` decision identifies common time bins containing the
full support of every paired sample; matching a numeric key alone cannot
establish chronological compatibility. This is a declared modeling assumption,
not a chronology review verdict. Included/excluded sample identities must be
disjoint and unique.

Geometry records use metres and square metres, with explicit source references.
The optimized profile consumes terrestrial-to-ring area ratios; it needs
regional rings beyond the separately declared local `max_ring`. The analytical
profile does not apply partial terrestrial masks and refuses them. Arithmetic
checks do not independently verify source geometry. The optimized source
objective uses nominal PPE; its nested method manifest retains that source
limitation even when other stages draw PPE uncertainty.

Products retain source-file hashes, explicit omissions, numerical units, actual
installed engine identity, code/resource inventories, diagnostic files and
separate operational/scientific hashes. Source and code changes during a run
refuse publication. Before/after file inventories are mutation checks; they do
not attest Python objects already loaded in a long-lived process. Certification
uses fresh installed processes and pinned dependencies.

Directory publication requires an atomic no-replace operation on the destination
filesystem. The Linux and macOS paths use their native exclusive-rename
primitives; Windows uses its nonreplacing rename behavior. Unsupported systems
or filesystems refuse publication instead of falling back to a racy existence
check. Failed staging directories remain available for diagnosis. Local macOS
execution evidence does not certify the other operating systems.

The primitive contracts are documented by the
[Linux rename manual](https://www.man7.org/linux/man-pages/man2/renameat2.2.html)
and [Apple's rename flag definitions](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/sys/stdio.h).
