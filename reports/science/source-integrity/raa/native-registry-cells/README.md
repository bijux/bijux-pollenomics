# Conditional native RAÄ registry cells

[Open the portable map](atlas/native-registry-index.html), or inspect the exact
[native count CSV](atlas/context/raa-native-registry/cell-counts.csv),
[display footprints](atlas/context/raa-native-registry/cells.geojson),
[context and source identity](atlas/context/raa-native-registry/context.json), and
[public buffer manifest](atlas/context/raa-native-registry/publication_manifest.json).

This closed publication contains **212,516 qualifying retained registry UUIDs in
121 original one-degree SWEREF 99 cells**. Its unit is a conditional registry UUID
count per cell. It makes no archaeological-event, ancient-population, vegetation
accuracy or area-density claim. It assigns no country and has no supported
ancient chronology. The 24-file portable tree is byte-identical to the accepted
17 November 2026 static publication; copying it did not render or reproject data.

**Retained UI limitation.** Generated browser checks of the retained map interface found
that a centered polygon-context notice can obscure cells. This byte-preserved
map may require ordinary map dragging to move cells out from behind the notice.
The CSV and GeoJSON expose the complete counts directly. A separately repaired
interface does not change these retained bytes; actual browser qualification of
this publication remains pending.

## Use the local map

The layer is initially disabled. Enable **Retained registry UUIDs per 1° SWEREF99
cell** (`raa-native-registry-cells`) in the map's layer controls. This standalone
context map contains zero scientific records; enabling its context does not
create scientific countries, dates or observations. Country and time filters do
not reclassify these country-unassigned, untimed counts.

Download or retain the complete `atlas/` directory, including its relative
software assets. GitHub displays HTML as a file rather than running the local
application. Open `native-registry-index.html` locally, or serve only this public
directory if the browser's local-file policy prevents loading:

```sh
python -m http.server 8765 --bind 127.0.0.1 \
  --directory reports/science/source-integrity/raa/native-registry-cells/atlas
```

Then visit `http://127.0.0.1:8765/native-registry-index.html`. The directory contains
no GeoPackage, private UUID ledger or source store. Static bytes, publication
integrity and aggregate conservation are qualified. Actual browser interactions,
mobile behavior and current-selection downloads remain pending their separate
qualification; this account did not execute a browser. The direct CSV link above
already identifies the complete original aggregate. This publication does not
automatically enable a layer in the current full Nordic Atlas.

## Population and conserved exclusions

The source capture contains 764,383 native `lamning.uuid` owners. Selection uses
the exact native `antikvariskbedomning = Fornlämning` value. A selected UUID is
included only with **one raw primary POINT occurrence and one valid, supported
POINT**. One valid occurrence plus a second null occurrence is multiple, even if
there is only one usable coordinate. Identical coordinates do not merge two raw
occurrences. Uncertainty geometry never supplies a point location. Non-POINT geometry validity
is outside this qualification.

| Disjoint source disposition | UUIDs |
| --- | ---: |
| unselected native class | 445,565 |
| selected class, no primary POINT occurrence | 104,609 |
| selected class, multiple raw primary POINT occurrences | 1,693 |
| selected class, unsupported sole POINT | 0 |
| selected class, unsupported projection or location | 0 |
| included in the native grid | 212,516 |
| **complete source population** | **764,383** |

The selected class has 318,818 UUIDs; the excluded source population is 551,867.
The public context also records 531,617 raw and 531,617 valid POINT occurrences
across the source. Those occurrence totals are a different unit from included
UUID owners. Zero unsupported cases is an observed disposition in this capture,
not a zero uncertainty or a claim about uncaptured sources. Unoccupied cells are
not exported and are not measured archaeological zeros.

## Native grid and approximate display

The native consumer interprets declared EPSG:3006 X/Y as easting/northing metres
and uses an explicit always-XY inverse projection to geographic SWEREF 99
(EPSG:4619). Cell ownership is mathematical floor with origin `(0, 0)`, one-degree
steps, west/south-inclusive and east/north-exclusive edges, without snapping or
an epsilon. Degree cells have different physical areas at different latitudes.
Counts cannot be read as counts per square kilometre.

The GeoJSON contains synthetic display footprints. It uses the separately
recorded **EPSG:1879** SWEREF 99 to WGS84 display operation, always-XY, offline and
without a ballpark fallback. Its stated one-metre operation accuracy is not measured
native-coordinate accuracy. The coordinate epoch remains unknown; the source
capture date supplies no coordinate epoch or contemporary reference-frame claim.

Only display rectangles are clipped to the frozen operation-support bounds
`[10.03, 54.96, 24.17, 69.07]`. This is not a country boundary or a new membership
predicate. All 121 cells and 212,516 UUIDs remain accounted: 116 complete display
footprints and five partial footprints. The five partial cells retain these
**whole original-cell counts**, without prorating to the visible area:

| Native west longitude | Native south latitude | Full-cell UUID count |
| ---: | ---: | ---: |
| 10 | 57 | 1 |
| 10 | 58 | 14 |
| 24 | 65 | 58 |
| 24 | 66 | 1 |
| 20 | 69 | 22 |
| **five partial footprints** | | **96** |

No cell or UUID was withheld. A partial footprint does not establish where its
individual contributing UUIDs lie inside that cell. The complete CSV remains
1,275 bytes with SHA-256
`84abcdd93101830b284d18c2e9d4dc91eff40f7b12489ec2fcfdcc3d7bc124ae`.

## Source, rights and verification scope

Source: **Riksantikvarieämbetet, Kulturhistoriska lämningar**, retained national
GeoPackage captured at `2026-09-13T01:14:04.983494+00:00`, 2,291,224,576 bytes,
SHA-256 `96bbe197a84c70b64f047873ded15ce5df568198dc0794870a782decb82fed0b`.
The recorded [source download URL](https://pub.raa.se/nedladdning/datauttag/lamningar_v1/l%c3%a4mningar_sverige.gpkg)
and [official product catalogue](https://catalog.raa.se/store/1/resource/217)
identify the source. No new download was performed for this account.

The retained rights decision cites product description v3.0, dated 2 February
2026: the dataset is declared Public Domain without an access restriction;
source and capture-date attribution accompany redistribution. Separately linked
media fall outside that decision. This account preserves the captured rights
statement rather than asserting a newly checked provider policy. Vendored map
software retains its separate upstream copyright and licensing conditions.
The [software notices](notices/README.md) retain the exact Leaflet 1.9.4 BSD
2-Clause and Leaflet.markercluster 1.5.3 MIT notices. All ten vendored UI files
match those versioned upstream distributions. Keep `notices/` alongside `atlas/`
when redistributing this publication.

The earlier national computation reconciled a private disposition ledger for
all 764,383 UUIDs. This map publication consumed only two independently pinned
qualified aggregates, `report.json` and `cell-counts.csv`, totalling 8,024 bytes;
it did not reopen that national source or ledger. The four curated public
buffers preserve a **producer profile binding**, not an independent public
reconstruction of the native SQL profile, UUID membership or source accuracy.
The original 6,749-byte report remains private audit metadata. Its hash in
`context.json` is provenance, not a public file or a dependency to download here.

The actual static publication used source revision
`a60fe253baf28d8c5d6c52ee1fc8595c39478d4a`. It exited successfully after 15.3757
seconds, recording four aggregate opens and 16,048 conservative reserved bytes,
with no unexpected denials or forbidden events. Reserved bytes are accounting,
not measured physical I/O. The frozen public tree contains 24 files and
1,114,838 bytes. The closed freeze SHA-256 is
`842cbbce48eae5c222624ad852f46e1785aee796a7efea626a905a31cc148004`;
the separate closed-result review SHA-256 is
`aabee286c4c5e768f5ec8ad433c56200de89af6bf958828b557b6e65003485cb`.
That review independently reconciled the public buffers and static transport
without running JavaScript or repeating the national computation.

## Reuse the maintained workflow

For viewing, copying the complete byte-qualified `atlas/` tree is sufficient.
Regeneration requires separately qualified native inputs or the independently
pinned aggregate pair; the public buffers alone cannot recreate the private
source profile or national UUID ledger. A fresh national reconstruction starts
from the declared source identity and the maintained
[native POINT consumer and finite profile](../../../../../docs/public/pollenomics-data/sources/raa-native-point-grid.md).
Its explicit source hash, byte count and limits remain necessary.

The existing [Atlas publication route](../../../../../docs/public/pollenomics-data/publications/raa-native-registry-context.md)
captures the qualified aggregate pair into an immutable snapshot, writes four
curated public buffers and passes the snapshot explicitly as
`native_registry_context` to the existing context-layer and static-map owners.
This account copies their completed result; it introduces no alternate SQL,
projection, renderer or numerical engine.

The retained 106-cell historical WFS surface sums to 339,412 and has a different,
unreconciled query denominator. It is not equivalent to these conditional native
counts. Neither surface establishes survey completeness, archaeological-event
frequency, vegetation accuracy or canonical adoption of a source release.
Continue to [RAÄ source guidance](../../../../../docs/public/pollenomics-data/sources/raa.md)
for the two separate source and publication contracts.
