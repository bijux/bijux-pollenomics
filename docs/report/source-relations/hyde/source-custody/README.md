# HYDE source declarations and Nordic window custody

The [custody receipt](receipt.json) binds 12 compact historical files to exact
private copies under `hyde/` in the external source store. Six are the original
file-hash and archive-member inventories, NetCDF declaration inventory, and
source-conflict/process receipts. Six are the three base/lower/upper native
source-index windows and their manifests. The copied bytes were checked against
their original v2/v3 artifact files before this receipt was written.

The historical hash inventory records 1,574 local HYDE 3.5 files totaling
66,393,709,629 bytes and 7,730 archive members. This custody move authenticates
the **compact retained records**, not a fresh full-data rehash of the 66 GB
release. The native release remains outside Git at the caller's chosen source
root. `file-inventory-report.json` explicitly calls the source inventory
hashed but not scientifically admitted.

The two selected artifact directories that held the four-file hash inventory
and six source-index window files were retired after exact original/private
hash checks, no live consumer or open-handle finding, and the private-root
integration test. Other HYDE artifact directories and the native source release
were outside this retirement.

The real three-scenario regression now reads these private copies via one
declared directory. From the repository root, with the external source store
available, run:

```sh
BIJUX_RUN_HYDE_NORDIC_REAL_INTEGRATION=1 \
BIJUX_HYDE_SOURCE_CUSTODY_ROOT=/path/to/private/source/store/hyde \
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
.venv/bin/python -m pytest -q \
  packages/bijux-pollenomics-dev/tests/source_completion/test_hyde_nordic_window.py \
  -k real_retained_windows_match_the_pinned_three_scenario_profile \
  -o cache_dir=artifacts/jobs/hyde-source-custody/pytest-cache
```

This source-index bundle does not assign country membership, reconcile the
conflicting license/version claims, define formal CRS or calendar conversion,
or measure vegetation. The [country cropland result](../../../regions/nordic/hyde-country-cropland/README.md)
is a separate bounded modeled-source comparison.
