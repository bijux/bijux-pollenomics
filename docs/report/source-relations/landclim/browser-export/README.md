# LandClim modeled frame browser export

The [machine result](report.json) records a completed Chrome 157 download from the published [Nordic map](../../../regions/nordic/nordic_map.html) at [committed source abc002ad3](https://github.com/bijux/bijux-pollenomics/tree/abc002ad3c2f3d67d189723de475d6fb3629fa19). The browser selected the **0–100 BP** source window and the Denmark and Sweden country controls, then clicked **Download visible frame**. Chrome DevTools Protocol reported a completed download of `pangaea-937075-ol-0-100-bp.geojson` (237,793 bytes; SHA-256 `90d7ca58dfa0a6dc3f17a6a3d3ca12393929cb87aaf1b8314b74b3449d9327e6`), byte-identical to the historical export. The current observation and downloaded file are under `artifacts/verification/landclim-download-runtime/qualification/capture/`. The historical `555ef191` reference remains a baseline; this run does not recover the original Brave 154 raw/CDP custody.

The 32 downloaded cell/window features have the exact record IDs, parsed properties, and polygon coordinates of the [pinned normalized-to-map projection](../map-export-lineage/README.md). Denmark contributes 6 cells and Sweden 26. All 47 estimate keys and the matching 47 standard-error keys were compared for every feature. There are 1,363 numeric pairs and 141 null pairs; the three `no_pollen_data` cells account for all null pairs. Among numeric pairs, 408 estimates and 408 standard errors are genuinely zero. The normalized projection for each country matches the pinned country/window ledger digest. The browser's JSON serializer writes integral coordinates such as `8.0` as `8`, so the raw downloaded JSON is not byte-identical to the Python ledger serialization despite exact parsed numeric equality.

The export identifies PANGAEA dataset [937075](https://doi.pangaea.de/10.1594/PANGAEA.937075) and the [Githumbi et al. (2022) method](https://doi.org/10.5194/essd-14-1581-2022), percentage-cover units, and a published BP source window. Its selected metric is OL, a source land-cover type. The full map manifest has 31 exact-taxon, 13 source-PFT, and 3 source land-cover keys; ET, ST, and OL are land-cover types, while AL is a PFT component of OL. The export has no separate scenario field; the cited PANGAEA REVEALS reconstruction is its source identity, and no alternative scenario is asserted. Its evidence role is `context_only`, with interpolation and propagation disallowed. The values are modeled vegetation context, not measured vegetation observations.

The 32 exported polygons are one-degree squares centered exactly on `lonDD`/`latDD` in the corresponding published TW25 mean CSV. These polygons are derived map geometry; the archived source supplies grid centers, not polygon rings. [PANGAEA's geocode policy](https://wiki.pangaea.de/wiki/Geocode) describes geographic coordinates as WGS84 decimal degrees, and [RFC 7946 section 4](https://www.rfc-editor.org/rfc/rfc7946#section-4) assigns WGS84 longitude/latitude semantics to GeoJSON. The download and normalized GeoJSON have no explicit CRS member or source-to-polygon CRS declaration. This check therefore supports the coordinate interpretation and exact center-to-polygon derivation for the selected frame; it does not certify independent historical polygon authority or a separately declared CRS chain.

Replay from the repository root using an absent artifact destination:

```sh
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/landclim_export/capture.mjs \
  . artifacts/jobs/landclim-browser-export-replay \
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/landclim_export/reconcile.py \
  --repository . --artifact artifacts/jobs/landclim-browser-export-replay \
  --browser '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' \
  --output artifacts/jobs/landclim-browser-export-replay/reconciled-report.json
```

The reconciliation refuses changes in the pinned source/map identities, record IDs, parsed feature content, all estimate/SE values, source-center polygon derivation, window and country counts, citations, source class, evidence role, null semantics, or browser download completion event. A new browser run can produce different volatile event identifiers and should be compared by the semantic result and downloaded content hash.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Author/source lineage, transformations and distinct modeled products; chronology and historical run admission remain separate.

**Supported claim.** The sampled Chrome 157 download at source abc002ad3 matches its pinned 32-feature modeled LandClim projection and the historical export bytes exactly.

**Unsupported claim.** This selected-frame check does not qualify other browser/export scenarios or untested source/runtime changes; modeled REVEALS percentages are not observed vegetation.

**Actual verification performed.** Ran the maintained capture and full source/ledger reconciliation at source abc002ad3 with Chrome 157; recorded actual CDP and source identities and matched the historical export bytes exactly.

**Remaining input or review.** Original Brave 154 raw/CDP custody remains unrecovered; contributor lineage, geometry authority, source rights and scientific admission remain separate.

**Cause category.** Historical browser custody and derived modeled context.

**Consequence.** The completed event qualifies this current modeled-frame export; it does not restore original Brave custody or admit modeled context as observed vegetation.

**Precise next acceptance route.** Resolve original historical browser custody separately; invalidate and requalify this frame only when its relevant source or runtime identities change.

**Negative or refused result.** 3 no_pollen_data features retain 141 null metric pairs; historical browser evidence is refused as current qualification.

**Matched denominator.** 32 features: 6 DK/26 SE, 47 paired metrics, 1,363 numeric pairs/141 null pairs and 408 numerical zeros in each metric family.

- [Retained qualification evidence: docs/report/source-relations/landclim/browser-export/report.json](report.json) (SHA-256 `dabc41ef2daace7a363baac651f9c56b0940160bccd42e3749951301e1fc8a0c`).

- [Retained qualification evidence: docs/report/source-relations/landclim/map-export-lineage/report.json](../map-export-lineage/report.json) (SHA-256 `ed1b569142f8a137217c226e0abb90930a1870a8571a785ba580a11de35783d8`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
