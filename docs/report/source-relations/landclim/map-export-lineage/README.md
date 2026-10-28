# LandClim model cells in the Nordic map

The [machine result](report.json) reconciles the governed temporal grid with all six published Nordic map node shards that contain LandClim features. All 2,515 LandClim I, II and Marquer features match the map transport after the production projection replaces `no_pollen_data` model placeholders with null. The LandClim II subset has 1,875 cell/window features, each carrying 47 paired estimate and standard-error metric keys. The [country/window ledger](rows.csv) records 100 slices across Denmark, Finland, Norway and Sweden, with 73,696 numeric estimate/SE pairs and 14,429 null pairs. Every slice has an ordered full-feature digest, source bounds, and quality counts. The pinned LandClim II raw archive matches its governed receipt.

The published map's export selector uses the exact source window and active country set. Its GeoJSON serializer carries the selected features, source metric, model DOI, method citation, evidence role and non-interpolation rule. This result checks the published selector and serializer bindings plus exact static transport data; it does not claim an executed browser download. The model is the published PANGAEA 937075 REVEALS reconstruction, expressed as percentage cover. ET, ST and OL remain source land-cover types; AL is a source plant functional type within OL, not another disjoint land-cover class. The 25 BP windows are model windows, not physical pollen sample ages.

The source archive has 75 stable `lonDD`/`latDD` centers in each of its 25 mean files. All 1,875 normalized LandClim II polygons are exactly one-degree squares around those centers. [PANGAEA's geocode policy](https://wiki.pangaea.de/wiki/Geocode) defines geographic longitude/latitude as WGS84 decimal degrees, and [RFC 7946](https://www.rfc-editor.org/rfc/rfc7946#section-4) gives GeoJSON longitude/latitude the corresponding CRS84 semantics. This is our source-to-derived-coordinate interpretation; the archive CSV and normalized GeoJSON carry no file-level CRS declaration, and the source provides centers rather than historical polygon rings. The 79 Rootsi matches are metadata candidates; their exact grid/window contribution and historical input identity are unresolved. The reviewed Swedish Neotoma same-name leads have zero admitted physical site identities. SEAD records are context, with no source-to-model-cell contributor identity established here. None of these overlaps is independent vegetation corroboration or measured vegetation truth.

We separately [executed the browser download](../browser-export/README.md) for Denmark and Sweden at 0–100 BP. That bounded check reconciles all 32 downloaded cells and every estimate/standard-error pair to this lineage.

Replay from the repository root with the development environment:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.landclim_map_export_lineage \
  --repository . --output artifacts/jobs/landclim-map-export-lineage/check
cmp artifacts/jobs/landclim-map-export-lineage/check/report.json docs/report/source-relations/landclim/map-export-lineage/report.json
cmp artifacts/jobs/landclim-map-export-lineage/check/rows.csv docs/report/source-relations/landclim/map-export-lineage/rows.csv
```

The output destination must not already exist. The producer refuses changed map shards, model manifest, window/country quality counts, metric keys, paired numeric/null posture, source archive custody, or the published download selector contract.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Author/source lineage, transformations and distinct modeled products; chronology and historical run admission remain separate.

**Supported claim.** The source-to-static lineage preserves published LandClim modeled values and source metric families through map transport.

**Unsupported claim.** Transport parity does not prove raw pollen contributors, independent vegetation truth, explicit source polygon CRS or a fresh browser download.

**Actual verification performed.** Read the current lineage JSON and row ledger, distinguishing refreshed map/shard custody from the retained historical browser capture; no model rerun.

**Remaining input or review.** Exact grid/window contributors, source-core identities and any current browser outcome remain separately required.

**Cause category.** Derived modeled context and incomplete contributor/geometry authority.

**Consequence.** LandClim estimates/SE remain context-only and cannot certify Rootsi/Neotoma predictions independently.

**Precise next acceptance route.** Recover the authentic selected core-to-grid/window contribution ledger and qualify geometry/use; rerun browser only for a current UI claim.

**Negative or refused result.** 79 Rootsi candidates have unresolved contributor identity; 0 Swedish same-name physical identities are admitted.

**Matched denominator.** 2,515 full source features; LandClim II 1,875 cell-windows=75 centers×25 windows; 47 metrics yield 73,696 numeric/14,429 null pairs across 100 country-window slices.

- [Retained qualification evidence: docs/report/source-relations/landclim/map-export-lineage/report.json](report.json) (SHA-256 `d620dab202ff00693e8b31b8fc18f0fa5b6d7dcfee8b95b0ef59e05e60e074ca`).

- [Retained qualification evidence: docs/report/source-relations/landclim/map-export-lineage/rows.csv](rows.csv) (SHA-256 `fefa4a3a3462e1d9cdf36109ebb3b53e01fc44843206b2ae3ccc07ea8acfa5e5`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
