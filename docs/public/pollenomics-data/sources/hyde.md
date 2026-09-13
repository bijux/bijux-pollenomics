---
title: HYDE 3.5
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-09-13
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

## Inspected local release

The September 2026 local inventory contains 1,574 dataset files totaling
66,393,709,629 bytes, including 1,159 ZIP archives and 48 NetCDF files across
base, lower and upper scenarios. File hashing and an occurrence-preserving
inventory of 7,730 archive members provide custody evidence. Duplicate archive
names remain distinguishable by member position; extraction must not silently
choose the last occurrence. Finder metadata is outside this dataset-file count.

Release declarations conflict. The supplied Yoda metadata and `License.txt`
state CC BY-NC 4.0, while the README and NetCDF attributes state CC BY 3.0.
All 48 NetCDF files retain `HYDE3.4` and `HYDE3.4 test netCDF` attributes inside
the supplied 3.5 release. Coverage prose also differs between 2023, 2024 and
2025. Preserve these source claims until their interpretation is established.
No distribution permission or release equivalence is inferred from the most
favorable declaration.

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
