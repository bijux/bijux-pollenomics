# Engine architecture

The host imports `bijux_pollenomics_lra.api`; translated DISQOVER helper names are
implementation details, absent from the public root facade. The host owns input
admission, chronology/taxa decisions, spatial validation, CLI and product registry.

| Domain | Responsibility |
| --- | --- |
| `models` | Typed configuration, result structures, validation and errors |
| `dispersal` | Deposition factors, source-compatible rounding and LOESS curves |
| `reconstruction` | Regional REVEALS, analytical LOVE, optimized LOVE, draws and forward deposition |
| `optimization` | Explicit bounded solver and candidate replay diagnostics |
| `workflows` | Regional/local execution, coupled stages and exact-coordinate series |
| `provenance` | Stable input identity, backend/runtime and scientific manifests |
| `outputs` | Numerical result serialization and checksum inventories |
| `resources` | Pinned model assets, examples and engine schemas |

Calculations never write host products or load host collection modules. Numerical
legacy writer flags refuse writes; callers use result serialization explicitly.
Result classes defer importing serializers until `.write()` so numerical imports
do not pull artifact work into reconstruction. Live R tools live under
`tests/reference/lra_oracle` and are excluded from runtime wheels. Installed
metadata exposes `bijux_pollenomics.extensions:lra` with target
`bijux_pollenomics_lra.api:extension_descriptor`; there is no engine console script.

Every source function's original path/hash and disposition is retained in
`adoption-manifest.json`; `architecture-migration.json` maps its domain owner.
Original installer, setuptools releases, generated metadata, broad aliases,
standalone CLI and host-specific envelope logic are excluded. Historical source
contract notes under `reference/` describe the received prototype and do not
supersede the supported facade or these module boundaries.

Versions follow host tags using Hatchling and hatch-vcs. The wheel includes
model/schema assets and GPL notices; the source archive additionally includes
exact DISQOVER source and independent oracle/test tooling. No compiler is required
by the current Python backend. Native migration must preserve the facade, numerical
profile, uncertainty, refusal behavior and source attribution.
