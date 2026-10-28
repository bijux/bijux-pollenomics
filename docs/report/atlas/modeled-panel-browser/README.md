# Modeled panel browser verification

The retained PANGAEA 937075 atlas candidate rendered 1,875 source cell-window records and the committed 400-row country/window/metric panel inventory without numerical recomputation. The candidate is a source-bound browser fixture. Its modeled vegetation values remain context only; this check grants no scientific admission or publication authorization.

An actual Chrome 155.0.8059.40 session downloaded 16 visible GeoJSON frames at 320 and 1440 px. Each viewport exercised all four metrics in direct No basemap with Denmark's `11200-11700 BP` source window and blocked-provider fallback with Sweden's `0-100 BP` window. The browser selected the source land-cover family for ET, ST, and OL, and the source plant-functional-type family for AL. AL retains its source code `AL` and its definition, agricultural land/cereals within open land; it is not a fourth disjoint land-cover class.

Every downloaded frame had exactly the source records for its selected country and published window. Per-record estimates and source standard errors, panel minimum and maximum values, modeled and no-pollen counts, source labels, and source classes agreed with the committed panel CSV. No-pollen records remained null across all estimate and standard-error fields. The downloaded frames stated `context_only`, with interpolation and propagation disabled. All 16 comparisons passed with no browser runtime errors. The [desktop screenshot](observations/1440-no_basemap.png) and [example source frame](observations/downloads/1440-no_basemap-ET/pangaea-937075-et-11200-11700-bp.geojson) are retained with the other observations and bound by the verification receipt.

The [verification receipt](verification.json) binds the [browser receipt](browser-receipt.json), [candidate generation record](candidate-generation.json), producer and verifier, source input hashes, served file hashes, download hashes, and screenshots. The producer read 272 source and renderer inputs. The browser served 11 candidate files and blocked 288 tile requests.

The retained Chrome 155.0.8059.40 replay passed with zero runtime errors. The earlier two candidate producer regressions remain a separately scoped source check. This browser sample covers two country/window pairs and four metrics at both widths and map modes. The retained CSV carries all 400 country/window/metric rows; this receipt does not claim that every panel row was navigated in the browser.

## Reproduction

From the repository root, use absent destinations under `artifacts/`:

```sh
.venv/bin/python -m bijux_pollenomics_dev.ci.atlas_browser.modeled_panel_candidate --repository . --destination artifacts/modeled-panel-candidate
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/modeled-panel-browser.mjs artifacts/modeled-panel-candidate docs/report/regions/nordic/landclim-modeled-panels/panels.csv artifacts/modeled-panel-browser '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
```

## Source-owned retained capture

The published observations now come from the immutable [source-view capture](../source-files/capture.json) on source candidate `fa79ae6eff0f344b5a2dbff2cc858f92746c1f67`, using Chrome 155.0.8059.40. The packet retains original generation, verifier, served-file, screenshot and download identities. Six successful browser observations belonged to an aggregate run that also contained two failed probes; two separately recorded successful successor probes supply the provider and modeled-panel observations. Those failures remain part of the execution history.

These report files are reproduced by guarded retained transport and explicit metadata projection. That operation executes no browser, estimator or R program, and grants no scientific, source-rights, ecological or cross-browser acceptance. Earlier public file identities remain in the capture certificate. The direct browser commands above start separately qualified new observations.

For this owner's retained projection, use an absent output under `artifacts/`:

```sh
mkdir -p artifacts/atlas-source-views
python -m bijux_pollenomics_dev.source_completion.atlas_browser.capture_projection \
  --repository . \
  --receipt configs/ci/report-capture-projections/atlas-source-views/modeled-panel-browser-browser-evidence.json \
  --output artifacts/atlas-source-views/modeled-panel-browser
```
