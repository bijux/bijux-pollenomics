# National RAÄ native population reconciliation

The retained national GeoPackage contains **764,383 distinct remains UUIDs**,
with **3,286,090 native rows across seven tables**. All native ownership relations
resolve, and an independent SQL aggregation reproduces every table population,
every field's null/non-null, numeric-zero and empty-text counts, and all five
category distributions. This establishes national source accounting. It does
not identify the historical WFS records or admit an archaeological chronology.

The complete compact population result is [report.json](report.json). The
[full geometry payload result](geometry.json) separately accounts for all
1,603,446 native geometry occurrences and independently checks 39,641,674
coordinate pairs; its structural and CRS scope is described below. It extends the
existing [finite lead support](../../../docs/report/source-relations/raa/native-lead-support/report.json),
which examined 21,467 distinct remains around four coordinate leads. The new
question is national identity, class and missingness reconciliation, including
all source rows rather than another local distance study. It reuses the
maintained source-row ownership audit; no raw national row inventory, source
copy or new download was created.

## Inputs and source dates

The source identity is the existing
[national capture descriptor](../../../data/raa/raw/national_geopackage_source.json):
`raa/lamningar-v1/lamningar_sverige.gpkg`, 2,291,224,576 bytes, SHA-256
`96bbe197a84c70b64f047873ded15ce5df568198dc0794870a782decb82fed0b`.
The descriptor records capture at `2026-09-13T01:14:04.983494+00:00` and HTTP
Last-Modified `2026-09-12 04:14:41 GMT`. The original bytes remain in the shared
private source store, opened read-only and immutable, with source hash and
stat identity checked before and after the scan. Source SQL views and
extensions were not executed.

The historical comparison uses the retained
[WFS layer summary](../../../data/raa/normalized/sweden_archaeology_layer.json),
feature type `arkreg_v1.0:publicerade_lamningar_centrumpunkt`. Its last Git
change is `03bdcf2302d88b9a8122ea1e70b09852f318e6da` (31 March 2026).
That is repository provenance, **not a WFS capture or provider timestamp**.
The historical summary supplies neither a jointly bound source date nor the
complete per-feature identity population. This comparison cannot attribute a
net difference to specific additions, removals, reclassification or time.

The existing descriptor records dataset-level Public Domain terms from the
RAÄ product description version 3.0 (2 February 2026). This execution makes no
new rights decision and does not extend those terms to separately linked media,
land access or fieldwork.

## Native population and geometry scope

| Native table | Source rows | Ownership |
| --- | ---: | --- |
| `lamning` | 764,383 | unique, valid UUIDs; each links to one native remains row |
| `ingaendelamning` | 143,795 | unique native nested IDs; links to a remains row |
| `egenskap` | 774,466 | direct or nested native ownership resolves |
| `point` | 531,617 | native remains ownership resolves |
| `linestring` | 81,434 | native remains ownership resolves |
| `polygon` | 226,012 | native remains ownership resolves |
| `lämningar_sverige_lägesosäkerhet` | 764,383 | separate positional-uncertainty geometry role; native ownership resolves |

There are zero duplicate valid remains UUIDs and zero duplicate native nested
IDs. Every source row is retained in the accounting denominator; no invalid or
orphan owner rows occurred in this capture. Those are observed results for this
source, rather than assumptions enforced by dropping difficult records.

The population census source profile binds the inspected GeoPackage application/version, table
columns and geometry/CRS declarations. All **1,603,446 geometry blobs** have
supported container headers. Of these, **839,063** are point/line/polygon source
occurrences and **764,383** are positional-uncertainty occurrences. These are
geometry rows, not independent remains or archaeological events. The maintained
ownership reader checks headers, declared EPSG:3006 and original byte identity;
it does **not** certify complete geometry payloads, topology, exact spatial
intersections, center-point equivalence, survey completeness or palaeolandscape
support. The separate existing finite geometry study retains its own scope.

## Native classes and the historical WFS aggregate

| Native `antikvariskbedomning` value | Source rows |
| --- | ---: |
| `Ej kulturhistorisk lämning` | 6,709 |
| `Fornlämning` | 318,818 |
| `Ingen antikvarisk bedömning` | 62,292 |
| `Möjlig fornlämning` | 98,921 |
| `Övrig kulturhistorisk lämning` | 277,643 |
| Total | 764,383 |

| Declared comparison | National native rows | Historical declared WFS hits | Native minus historical |
| --- | ---: | ---: | ---: |
| All remains | 764,383 | 761,917 | +2,466 |
| `Fornlämning` | 318,818 | 318,265 | +553 |
| `Fornlämning` or `Möjlig fornlämning` | 417,739 | 416,913 | +826 |

The class strings are source-native labels. No period-to-age conversion or
scientific archaeological classification is inferred. Equal wording does not
establish equivalent selection predicates between the native tables and WFS.
The historical one-degree density cell sum of 339,412 remains separately
unreconciled with its national declared `Fornlämning` count of 318,265. This
national scan neither changes that density surface nor turns it into a
partition of the new population.

The result also retains native `lamningstyp`, actuality, damage and investigation
status distributions. Source values such as `Okänd` remain explicit text
categories, distinct from nulls, empty strings and numeric zero. In particular,
499,229 rows have damage status `Okänd`, and 479,148 have investigation status
`Okänd`; neither is an observed absence of damage or investigation. The 1,536
rows marked `Utgår på grund av felregistrering` and 2,063 marked
`Överförd till annan lämning` remain in the national inventory denominator.
A later claim-specific selection must declare its treatment of these statuses.

## Execution and independent check

The actual national execution used committed consumed source
`657c8358f9f2234b58a1155e0e2906cd58e23eba` on 26 October 2026:

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv/bin/python -B \
  -m bijux_pollenomics_dev.source_completion.archaeology.national_population \
  --repository /Users/bijan/bijux/bijux-pollenomics \
  --source /Users/bijan/bijux/-bijux-pollenomics-data/raa/lamningar-v1/lamningar_sverige.gpkg \
  --output /Users/bijan/bijux/bijux-pollenomics/artifacts/raa-reconciliation/national-population
```

The owned execution session `50719` terminated with exit code **0**. It completed
in **49.112 seconds**, below its 600-second SQLite wall budget, and wrote a
22,551-byte report. Other workers had disjoint edits; the source consumer and
its inputs were committed and stable throughout. This is a consumed-source
scientific result, not a clean whole-repository release qualification.

The independent check uses SQLite aggregation directly over the seven native
base tables, without the Python ownership reader's counting loop. It compares
all field populations, including null/zero/empty distinctions, and exact native
category bins. All agree. It shares the same source file and is an independent
computational check, not independent archaeological corroboration.

The configured archaeology test suite passed **35 tests**; the final focused
population tests passed **5 tests**, strict configured mypy passed both changed
Python files, and configured Ruff check/format passed. Controls include duplicate
UUIDs, ambiguous nested ownership, an orphan geometry reference, missing versus
empty status, numeric zero, source-null geometry, changed SQL categories and
population, a negative historical difference, and equal totals without inferred
record equivalence. Earlier setup/type-check failures and their correction are
retained under `artifacts/raa-reconciliation/check-failures.txt`.

## Complete payload and CRS qualification

The full retained source was also passed through the maintained
`iter_geometry_documents` consumer. All **1,603,446 geometry occurrences** have
complete, nonempty standard 2D payloads under that reader's contract. A separate
NumPy traversal independently agrees on every accepted occurrence's coordinate,
line-component, ring, polygon and empty-polygon counts, zero-coordinate counts,
finite XY extrema, ring closure, declared binary type/dimensions, and any source
envelope. Table/fid identities and the complete native populations are matched
against separate raw-table cursors. No geometry was dropped or repaired.

| Native geometry role/table | Occurrences | Coordinate pairs | Line components | Polygon components | Rings |
| --- | ---: | ---: | ---: | ---: | ---: |
| Remains `point` | 531,617 | 531,617 | 0 | 0 | 0 |
| Remains `linestring` | 81,434 | 658,246 | 81,434 | 0 | 0 |
| Remains `polygon` | 226,012 | 4,826,397 | 0 | 226,012 | 226,369 |
| Positional uncertainty `lämningar_sverige_lägesosäkerhet` | 764,383 | 33,625,414 | 0 | 770,020 | 773,905 |
| Total | 1,603,446 | 39,641,674 | 81,434 | 996,032 | 1,000,274 |

Thus **6,016,260 coordinate pairs** belong to the native remains geometry
occurrences and **33,625,414** to the separate positional-uncertainty role.
Multiple polygons or rings within a payload do not become independent remains,
events or measurements. There are no source-null, empty, invalid or unsupported
payloads in this capture and no reader/oracle disagreement. Every maintained
status cross-count is `structurally_valid_nonempty:accepted_nonempty`; the
private refusal stream is empty. These are observed outcomes, not a rule that
invalid or refused rows would be excluded from the accounting.

The native source WKT agrees with EPSG:3006. The WKT lists northing before
easting, while GeoPackage binary transport explicitly uses XY: easting then
northing. The consumer preserves that distinction and performs no coordinate
transformation. The header and WKB have separately interpreted byte-order flags;
optional envelopes and canonical empty-point handling follow the
[OGC GeoPackage 1.4 geometry encoding specification](https://www.geopackage.org/spec140/index.html#_geometry_encoding).
The fixtures exercise both byte orders, mixed empty/nonempty polygon components,
nonfinite coordinates, non-2D types, malformed rings/lines, wrong source envelopes
and CRS, source-null versus zero, output bounds, and a saved independent
ring-count mismatch that must fail rather than acquire acceptance.

The numerical result establishes standard binary structure, finite coordinate
content and the declared CRS. It does not establish topology, coordinate
accuracy, country assignment, center-point equivalence, historical basin
geometry, archaeological time or scientific suitability. No area, representative
point, field ranking or density replacement is derived.

The final actual command used committed consumed source
`31635dea0ee3a2d05e8800f7e2b843512192d6c7`:

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv/bin/python -B \
  -m bijux_pollenomics_dev.source_completion.archaeology.national_geometry \
  --repository /Users/bijan/bijux/bijux-pollenomics \
  --source /Users/bijan/bijux/-bijux-pollenomics-data/raa/lamningar-v1/lamningar_sverige.gpkg \
  --output /Users/bijan/bijux/bijux-pollenomics/artifacts/raa-reconciliation/national-geometry-runtime
```

The owned session `54257` terminated with exit code **0** in **74.593 seconds**.
Its 5,333-byte [geometry.json](geometry.json) records NumPy **2.4.6**, pyproj
**3.7.2** and PROJ **9.5.1**. The scan was bounded to 1,200 seconds, a 100 KiB
compact report and a 16 MiB private refusal stream. It reused the existing
environment and original raw source directly, with committed consumed source
held stable during disjoint work elsewhere in the checkout.

The same-input numerical execution at source
`9a9875c3432246aec7de2b98be2e97283d913d43`, session `33256`, also exited **0**
in **74.942 seconds**. Its output remains under
`artifacts/raa-reconciliation/national-geometry/`. Inspection found an inherited
CRS metadata field referring to versions in the original API's manifest,
although this consumer writes a compact report. The corrected consumer records
actual versions in its report. Every scientific/source field agrees exactly
between these executions after excluding elapsed time and that explicit
runtime-metadata correction. The original result is not a numerical failure.

Configured verification passed **60 archaeology tests** for the payload
consumer and shared native fixture, followed by **25 geometry tests** after the
runtime-metadata correction. Strict mypy passed the five affected Python paths
and the corrected consumer; configured Ruff check/format passed. The NumPy
comparison is an independent computational method on the same source, not
independent archaeological corroboration or qualified human review.

## Remaining acceptance

This is a scoped source-accounting contribution to RAÄ preservation and
landscape-context work. The historical WFS feature inventory with native
identities, exact query predicates and capture/source dates is still needed for
individual population reconciliation. The complete 2D payload/declared-CRS
accounting is now established; qualified spatial/archaeological
interpretation, source-bound chronology and the actual intended downstream
selection remain separate. Canonical source adoption, historical-density
equivalence, chronology admission, scientific-event admission and field
permission remain false. No whole science outcome or original umbrella clause
is closed by this national census alone.
