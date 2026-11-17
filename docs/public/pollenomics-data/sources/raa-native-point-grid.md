---
title: Native RAÄ POINT grid counts
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-11-17
---

# Native RAÄ POINT grid counts

The source-owned `collection.sources.raa.point_grid` consumer produces a private
UUID ledger, a sparse one-degree count CSV and a compact conservation report.
Its unit is **qualifying native registry UUIDs per declared cell**. The
implementation is tested with generated GeoPackages and official projection
controls; these software checks are not a new execution or qualification of the
retained national source.

## Conditional population

A record must have the exact native `lamning.antikvariskbedomning` value
`Fornlämning`, exactly one raw primary `point` occurrence and exactly one valid,
finite, supported native POINT. The source identity is `lamning.uuid`, joined to
`point.lamning_uuid`. Source fields are not renamed to historical WFS identities
or classes. Other primary geometries do not create additional records or point
occurrences. Positional-uncertainty geometry is a separate counted role and never
supplies a point location.

The private ledger assigns each source UUID one disposition, in this order:

1. unselected exact native class;
2. no primary point occurrence;
3. multiple raw primary point occurrences;
4. unsupported, null, empty or nonfinite sole point;
5. unsupported projection or location; or
6. included grid cell.

One valid POINT plus a null second occurrence remains excluded as multiple raw
occurrences. Identical coordinates do not collapse two source occurrences.
Duplicate UUIDs, orphan geometry owners, changed source bytes, an unsupported
native profile or conflicting CRS declarations refuse the input. A resource
limit refuses the operation; it does not silently drop a source row. Native
non-BLOB geometry storage is accounted without decoding arbitrary text payloads.

## Frame and cells

Source EPSG:3006 binary X/Y means easting/northing in metres. An explicit
always-XY inverse projection produces SWEREF 99 geographic longitude/latitude
(EPSG:4619). The report records the operation, library versions, PROJ database
identity and supported EPSG:3006 area-of-use rectangle. That rectangle is a
location-support condition, not country containment. No contemporary WGS84,
epoch-motion or native positional-accuracy qualification follows.

The one-degree grid has longitude/latitude origin `(0, 0)`. Mathematical floor
assigns coordinates to west/south-inclusive and east/north-exclusive cells,
without snapping or epsilon. An exact `(15, 60)` belongs to the cell with west
longitude 15 and south latitude 60. A value immediately below either edge belongs
to the preceding cell. Lantmäteriet's [fifteen official SWEREF 99 projection
controls](https://www.lantmateriet.se/contentassets/a7ddfc3b7821498da8b55cd3f71b5150/kontrollpunkter_sweref99tm.pdf)
verify both projection directions at the published precision. Rounded projected
controls are tested separately from exact numerical grid edges.

## Private product and execution

Call `materialize_raa_native_point_grid` with an explicit source path, complete
source SHA256 and byte count, absent destination and `NativePointGridLimits`.
The limits declare positive native integer ceilings for UUID rows, total
geometry rows, each point blob and total output bytes. There is no implicit
national-source lookup. The maintained read-only SQLite owner authenticates the
original source before rows and retains custody through publication. Only
primary POINT blobs are decoded; other geometry roles receive ownership checks.

The output directory is private (mode 0700) and contains exactly:

| File | Meaning |
| --- | --- |
| `uuid-dispositions.ndjson` | Private source UUID/fid/class, raw and valid point counts, separate uncertainty count, disposition and conditional coordinates/cell |
| `cell-counts.csv` | Sparse occupied cells and included UUID counts |
| `report.json` | Source/profile identity, selection, exclusions, denominators, conservation, projection/grid and software/file provenance |

Public sharing is limited to aggregate counts and provenance. The UUID ledger
and coordinates remain private. Original captured-source terms and source/date
attribution still apply; this projection does not change licences or grant field
access. An existing destination or foreign candidate is never overwritten.
Refused private publication evidence is retained for its owner.

Before a retained-source execution, separately qualify the exact source, finite
read/write/resource budget and independent same-source reconciliation. This
consumer does not replace the [106 historical WFS display cells](raa.md), adopt
a canonical source release, assign a country, interpret administrative dates as
ancient chronology or admit archaeological events. Sparse missing cells are not
measured zeros for archaeological activity, and counts per degree cell are not
counts per square kilometre or human-population estimates.

The optional [native registry Atlas context](../publications/raa-native-registry-context.md)
consumes only independently pinned aggregate buffers. It preserves the native
cell/count unit while recording a separate approximate WGS84 display operation
and any partial synthetic footprint; the UUID ledger remains private.
