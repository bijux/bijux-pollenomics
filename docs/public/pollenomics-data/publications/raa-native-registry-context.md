---
title: Conditional native registry cells in Atlas
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-11-17
---

# Conditional native registry cells in Atlas

The optional `raa-native-registry-cells` layer shows **qualifying retained
registry UUIDs per original one-degree SWEREF 99 cell**. It is separate from the
[historical RAÄ WFS display cells](../sources/raa.md) and uses the conditional
[native POINT consumer](../sources/raa-native-point-grid.md). The layers have
different source populations and must not be added together or treated as
interchangeable estimates.

This is a display-only context layer, initially disabled. It assigns no country
and has no supported ancient chronology. It does not contribute observations,
candidate rankings, propagation edges or accepted archaeological events. A count
is not a number of sites, people, primary geometry occurrences or records per
square kilometre. Sparse absent cells are not measured archaeological zeros.

## Conditional population and exclusions

The producer keeps exact native `Fornlämning` UUID owners with exactly one raw
primary POINT occurrence and exactly one valid, supported POINT. One valid point
plus a second null occurrence is excluded. Uncertainty geometry is a separate
role and does not provide a location. The complete source population remains
partitioned into included, unselected class, no point, multiple raw points,
unsupported sole point and unsupported projection/location dispositions.

Atlas consumes only the already qualified `report.json` and `cell-counts.csv`.
It requires independently supplied file SHA256 pins and an administrative source
record containing the original whole-source SHA256, byte count, capture time,
download URL and rights statement. It checks the report against that source
identity and reconciles the full source, selected and excluded populations with
the complete CSV numerator. The producer's native profile hash remains a
**producer binding**, not an independent metadata-profile reconstruction.

These checks qualify a captured aggregate epoch. They do not reopen or freshly
verify the national GeoPackage, reproduce its acquisition, admit its empirical
accuracy, or promote an arbitrary report's own hashes into source authority.
The private UUID ledger and individual coordinates are never inputs to this
Atlas connection.

## Native cell and display footprint

The original count grid is EPSG:4619 longitude/latitude, with mathematical-floor
cell ownership and a one-degree interval on each axis. Its cell identity, full
native bounds and UUID count remain unchanged in downloads and on the map.

GeoJSON display coordinates use longitude/latitude WGS84 as required by
[RFC 7946 section 4](https://www.rfc-editor.org/rfc/rfc7946.html#section-4).
The explicit display operation is **EPSG:1879, SWEREF99 to WGS84 (1)**, using
always-XY order, offline operation selection and no ballpark fallback. A changed
or unavailable operation refuses publication. This operation is numerically a
no-op in the qualified PROJ implementation; recording the operation is not a
silent relabeling of the native grid. Its stated one-metre operation accuracy is
not a bound on native-coordinate or total display accuracy.

[Lantmäteriet distinguishes SWEREF 99 from contemporary global reference
frames](https://www2.lantmateriet.se/en/geodata/gps-geodesy-and-swepos/swedish-reference-systems/).
A higher-accuracy dynamic transformation would need the appropriate frame,
coordinate epoch and motion information. The capture date is not a coordinate
epoch, and this layer invents none.

A synthetic cell rectangle may extend beyond the declared projection-support
rectangle even though its contributing points qualified. Only its **display
footprint** is intersected with the frozen operation-support rectangle before
the explicit transformation. A partial footprint retains the original full-cell
ID, bounds and count, and its popup says that the count is not prorated. This is
not country clipping, observation rebinning, extrapolation or an estimate for
the clipped area. A wholly unsupported or nonfinite footprint refuses the
publication; cells are never silently dropped.

The context metadata separately records all mapped cells and full-cell UUIDs,
partial-footprint cells and their full-cell UUIDs, and any withheld account.
The complete original CSV remains byte-identical. Country and time controls do
not reclassify these country-unassigned, untimed counts. The layer is explicitly
eligible only for Nordic and custom map scopes, and its own toggle remains
disabled by default.

## Bounded public derivative

The source-specific owner is `reporting.context.raa_native`. Capture uses the
existing descriptor-bound selected-file reader with a 64 KiB report limit and a
16 KiB CSV limit; the private ledger is not enumerated or read. Two independent
file pins are required before decoding either aggregate. The snapshot contains
native immutable bytes and survives closure of its original input handles.

An explicit `native_registry_context` keyword connects the snapshot to
`build_context_layers`, including when `context_root=None`. It does not trigger
implicit source lookup, native SQL, provider requests or legacy RAÄ admission.
The existing callback publication owner retains exclusive candidates, complete
namespace checks and prior/refused recovery. Four public files are attached
under `context/raa-native-registry`:

| File | Meaning |
| --- | --- |
| `cell-counts.csv` | Complete original sparse native cell counts, unchanged |
| `context.json` | Source epoch, input pins, selection, full denominators and exclusions, native grid, display operation and partial-footprint accounting |
| `cells.geojson` | Synthetic display footprints with original full-cell IDs, bounds and counts |
| `publication_manifest.json` | Exact public member sizes and SHA256 identities |

The ordinary Atlas polygon transport, authenticated current-selection export,
legend, popup and count palette display this context. Exports preserve the
original count unit, grid and partial-footprint fields; downloading a selected
public row is not analytical selection or scientific admission. No UUID ledger
link or source-store route is exposed.

Actual retained-result rendering still requires a separately reviewed finite
input/code/output scope and portable browser qualification. Generated producer,
publication and browser tests establish software behavior; they do not declare
all RAÄ or Atlas work complete.
