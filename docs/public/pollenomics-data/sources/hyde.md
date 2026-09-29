---
title: HYDE 3.5
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-09-24
---

# HYDE 3.5

HYDE is registered as external modeled land-use context. Its quantities may
support comparisons with LANDCLIM or LRA at explicitly matched spatial and
temporal support. They do not supply independently measured vegetation truth,
pollen observations, or evidence of propagation. Cropland is not cereal pollen,
and land outside agriculture is not automatically forest.

## Local storage and preparation

Keep the native dataset in a separate local data directory. Native ZIP archives,
NetCDF files and large prepared grids are not tracked in the product Git
repository. The preparation contract requires an explicit local source root and compact
provenance products in a caller-selected destination. Repository
contracts under `data/hyde/3.5` name small inventories, review receipts and
manifests; they do not require copying the native dataset into Git.

The existing declared-grid adapter supports bounded, explicitly labeled
interchange fixtures and pre-normalized candidates. It preserves quantities,
units, masks, missing values and temporal conventions. It is separate from native
release verification. Source identity, family lifecycle, capability and
spatiotemporal registries expose HYDE's pending admission. Unknown native cell
and country totals remain null; placing JSON files at expected paths cannot
turn them into accepted source evidence.

## Prepare and verify an external inventory

Use the installed host package to prepare a new compact inventory directory:

```python
from pathlib import Path

from bijux_pollenomics.collection.sources.hyde.local import (
    prepare_local_hyde_inventory,
    read_local_hyde_inventory,
    replay_local_hyde_inventory,
)

source = Path("/path/to/external/HYDE-3.5")
destination = Path("/path/to/external/manifests/hyde-custody-001")
product = prepare_local_hyde_inventory(source, destination)
print(product.manifest_sha256)
print(product.dataset_file_count, product.dataset_byte_count)

retained = read_local_hyde_inventory(
    destination, expected_manifest_sha256=product.manifest_sha256
)
replay_local_hyde_inventory(retained, source)
```

The destination must be new and separate from the source tree. Preparation
streams file hashes and inventories ZIP/ZIP64 central directories without
extracting grids. It writes four JSON files containing file identities, archive
occurrences, bounded original metadata bytes and a manifest. It imports no
NetCDF decoder and gives opaque `.nc` files no scientific interpretation.

Save the returned manifest SHA separately as the expected identity for later
inspection. Retained inspection authenticates the compact files; full replay
also requires the recorded producer source version, rereads the external dataset,
and compares its bytes and archive metadata. Retained inspection can read a
historical producer receipt; it does not attest to code already loaded into a
long-lived process. Replay therefore performs another full source read. A relocated identical
source tree remains usable because the manifest stores relative source paths.
A changed source requires a new custody product. Ancillary Finder metadata has
its own denominator and does not change the separate dataset inventory hash.

## Read a native source-index window

After creating an inventory, select an exact archive occurrence from that
inventory. For the inspected local delivery, this example retains four source
cells from the year-2000 base cropland member:

```python
from bijux_pollenomics.collection.sources.hyde.ascii import (
    AsciiWindowSelection,
    prepare_hyde_ascii_window,
    read_hyde_ascii_window,
)

selection = AsciiWindowSelection(
    archive_path="original/gbc2025_7apr_base/zip/2000AD_lu.zip",
    member_index=0,
    expected_member_name="cropland2000AD.asc",
    row_start=227,
    row_stop=228,
    column_start=2487,
    column_stop=2491,
)
window = prepare_hyde_ascii_window(
    destination,
    expected_custody_manifest_sha256=product.manifest_sha256,
    source_root=source,
    selection=selection,
    destination=Path("/path/to/external/prepared/cropland-window-001"),
)
retained_window = read_hyde_ascii_window(
    window.directory, expected_manifest_sha256=window.manifest_sha256
)
print(retained_window.source_tokens)
print(retained_window.missing_mask)
```

Rows and columns are zero-based source indices with exclusive stop bounds.
The archive ordinal distinguishes repeated names. The producer verifies the
selected archive hash and streams the complete selected member through EOF,
checking its size and CRC while retaining its SHA and only the requested cells.
It neither extracts archives nor rescans the full release for each window.
Repeated windows in one member each incur that member verification cost.

Two compact JSON files preserve the original six header lines, numeric tokens,
missingness and source indices. Missing cells remain distinct from numeric zero.
The native `0.0833333` step is retained literally. A source-index preview does
not assign CRS, area, variable units or calendar meaning; a later geographical
adapter must explicitly join those declarations to the existing grid contract.
The retained reader authenticates pinned bytes and internal consistency, rather
than re-executing the original source read.

`bijux_pollenomics.collection.sources.hyde.ascii.geometry.native_axis_geometry`
can derive exact decimal source-axis edges from a retained window and the
archive SHA-256 in its authenticated parent manifest. It uses the source's
literal `xllcorner`, `yllcorner` and `cellsize`; rows run north to south.
Because the native step is `0.0833333`, the calculated global east/north edges
are `179.9998560` and `89.9999280`, rather than rounded longitude/latitude
limits. The result carries archive, member, window and native scenario labels,
plus separate missing, nonmissing and zero counts. It explicitly leaves CRS,
variable units and calendar support unset, and marks country projection and
public release as unavailable.

The private source-axis envelope for the inspected base 2000AD cropland member
contains 72,576 selected cells: 29,217 missing, 43,359 nonmissing and 15,307
numeric zeros. Its source-axis window edges are west `3.9999264`, east
`31.9999152`, south `53.9999424` and north `71.9999352` in undeclared native
coordinate units. These are source-index geometry and mask counts, not a
country overlay, area estimate, admitted Nordic subset or vegetation truth.

Installed-package checks cover seven identical windows in each of base, lower
and upper cropland for 2000AD: 117 selected cells agree exactly with independent
native reads, including edge orientation, missingness, zeros and member hashes.
These scenarios are not pointwise bounds: the inspected lower scenario exceeds
base at source row 230, column 2479. This preview evidence is distinct from
scientific admission or a vegetation reconstruction test.

The private Nordic-intent bundle extends that byte-bound source-index coverage
to the same 72,576 positions in each of the base, lower and upper scenario
members: 72,576 unique positions and 217,728 scenario-token instances. Each
scenario has 29,217 missing and 43,359 nonmissing cells; the source-native
numeric-zero counts are 15,307 for base, 15,158 for lower and 15,332 for upper.
The bundle authenticates each child window and its exact archive and member
identity, binds their common custody-manifest identity, and authenticates four
compact declaration parents. It preserves raw tokens, missingness, numeric
zeros, literal header values and native-axis edges without computing scenario
totals, means, extrema, areas, fractions or cross-scenario comparisons. The
names `lower` and `upper` remain source labels; they are not interpreted as
pointwise ordering or confidence bounds.

Sweden, Denmark, Norway and Finland are recorded as requested country intents,
not as derived partitions of this rectangular source-axis window. Each country
row therefore retains null selected-cell, nonmissing-cell, cell-area and value
quantities, with country projection explicitly not materialized. The bundle
does not assign remainder cells to an invented unassigned country and does not
advance HYDE's refused country-ledger entries.

## Country accounting

The country ledger includes all eleven registered families across six partitions
(Sweden, Denmark, Norway, Finland, unassigned and outside) and three distinct
dimensions: source-reported, governed assignment and publication. Its 18 HYDE
cells retain null quantities and blocked/refused status because no governed
native country projection has been admitted. The recorded assignment policy is
explicitly not applied; no country snapshot or boundary digest is invented.
External archive custody remains available independently of that refusal.

The release also supplies source-reported country cropland tables. A bounded
[Nordic country result](../../../report/regions/nordic/hyde-country-cropland/README.md)
now reads the release's ISO-code workbook and base/lower/upper `cropland_c.txt`
tables at seven native CE year labels. It records modeled cropland area in km²
for Denmark, Finland, Norway and Sweden without projecting grid cells. This
source-reported quantity is separate from the generic count-only country ledger:
it does not change that ledger's refused grid assignment or publication cells,
or establish a matched pollen comparison.

For cropland at seven selected CE labels, a separate
[native ISO-grid reconciliation](../../../report/regions/nordic/hyde-country-cropland/grid-conservation/README.md)
now reproduces all 84 four-country/year/scenario source totals from native
grids to within 0.000001 km². This is a bounded internal source-consistency
result, not a general release, calendar, rights or scientific model admission.

## Inspected local release

The September 2026 local inventory contains 1,574 dataset files totaling
66,393,709,629 bytes, including 1,159 ZIP archives and 48 NetCDF files across
base, lower and upper scenarios. File hashing and an occurrence-preserving
inventory of 7,730 archive members provide custody evidence. Duplicate archive
names remain distinguishable by member position; extraction must not silently
choose the last occurrence. Finder metadata is outside this dataset-file count.

Release declarations conflict. The supplied Yoda metadata and `License.txt`
state CC BY-NC 4.0, while the README and NetCDF attributes state CC BY 3.0.
The exact local metadata and license text have SHA-256 identities
`44dacada9b1b9ade1886bf0f2a26277a2b964afbff46f9ee64c17069f7b57b3a`
and `3711f963c05d0be80d53e5923308a6dee31b203da23435c9cfb7c7b6e4dd5e19`.
[Utrecht University's Yoda license workflow](https://utrechtuniversity.github.io/yoda/administration/installing-licenses.html)
explains that a standard license named in package metadata is included as
`License.txt` when copied to its vault. This supports treating the two CC
BY-NC declarations as one package-level instruction, while leaving the
conflicting embedded declarations and provider intent unresolved. The public
[HYDE 3.5 dataset link](https://landuse.sites.uu.nl/datasets/) identifies the
2025 release but does not settle this file-level conflict.
All 48 NetCDF files retain `HYDE3.4` and `HYDE3.4 test netCDF` attributes inside
the supplied 3.5 release. Coverage prose also differs between 2023, 2024 and
2025. Preserve these source claims until their interpretation is established.
No distribution permission or release equivalence is inferred from the most
favorable declaration.

The host can now reconstruct a refusal-only declaration inventory from four
pinned compact parents: the 1,574-file custody inventory and report, the 48-file
NetCDF header inventory, and the conflict report. It requires the exact 16
variables in each of the base, lower and upper scenarios and retains raw axes,
spacing, orientation, dimensions, units, fill values, time/calendar labels,
source hashes and provider claims. It does not open native value arrays. The
inventory is reconstructed from those authenticated parents rather than trusted
through a detached canonical-product authority. Its typed reopen reconstructs
the inventory from the same four parents and accepts only byte-exact canonical
output from that reconstruction. Native admission, rights, CRS, canonical BP
conversion, confidence-bound semantics, publication, independent vegetation
truth and scientific acceptance all remain false or unevaluated.

A local comparison of year-2000 cropland in all three scenarios finds equal
ASCII/NetCDF missing masks and identical values after conversion to the source
NetCDF float32 representation. This is evidence for those three slices only.
It does not resolve the release metadata or certify other variables and years.
The source's rounded angular step and float32 coordinates remain explicit.

## Comparison requirements

Native preparation must preserve the variable and scenario inventories,
source grid edges and orientation, actual cell and land areas, masks, and
source-native time labels. Area, population, density and fractions are distinct
quantities. Lower and upper scenarios are not automatically confidence
intervals. Calendar conversion must resolve `0AD` and the NetCDF `365_day`
calendar before producing canonical BP values or matching LRA time windows.

Native geographical, chronological and scientific admission remains refused
by the current registration. Qualified review, comparable category mappings,
country/region reconciliation and a shared-input audit are required before a
matched comparison can be admitted. HYDE-assisted model configurations must
retain a pollen-only comparison and cannot reuse their HYDE predictors as
independent validation labels.
