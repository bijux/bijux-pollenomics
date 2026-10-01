# LandClim model cells in the Nordic map

The [machine result](report.json) reconciles the governed temporal grid with all six published Nordic map node shards that contain LandClim features. All 2,515 LandClim I, II and Marquer features match the map transport after the production projection replaces `no_pollen_data` model placeholders with null. The LandClim II subset has 1,875 cell/window features, each carrying 47 paired estimate and standard-error metric keys. The [country/window ledger](rows.csv) records 100 slices across Denmark, Finland, Norway and Sweden, with 73,696 numeric estimate/SE pairs and 14,429 null pairs. Every slice has an ordered full-feature digest, source bounds, and quality counts. The pinned LandClim II raw archive matches its governed receipt.

The published map's export selector uses the exact source window and active country set. Its GeoJSON serializer carries the selected features, source metric, model DOI, method citation, evidence role and non-interpolation rule. This result checks the published selector and serializer bindings plus exact static transport data; it does not claim an executed browser download. The model is the published PANGAEA 937075 REVEALS reconstruction, expressed as percentage cover. ET, ST and OL remain source land-cover types; AL is a source plant functional type within OL, not another disjoint land-cover class. The 25 BP windows are model windows, not physical pollen sample ages.

The normalized GeoJSON and download contract have no explicit CRS declaration. The result therefore does not certify the CRS part of WP07-LANDCLIM. The 79 Rootsi matches are metadata candidates; their exact grid/window contribution and historical input identity are unresolved. The reviewed Swedish Neotoma same-name leads have zero admitted physical site identities. SEAD records are context, with no source-to-model-cell contributor identity established here. None of these overlaps is independent vegetation corroboration or measured vegetation truth.

Replay from the repository root with the development environment:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.landclim_map_export_lineage \
  --repository . --output artifacts/jobs/landclim-map-export-lineage/check
cmp artifacts/jobs/landclim-map-export-lineage/check/report.json docs/report/source-relations/landclim/map-export-lineage/report.json
cmp artifacts/jobs/landclim-map-export-lineage/check/rows.csv docs/report/source-relations/landclim/map-export-lineage/rows.csv
```

The output destination must not already exist. The producer refuses changed map shards, model manifest, window/country quality counts, metric keys, paired numeric/null posture, source archive custody, or the published download selector contract.
