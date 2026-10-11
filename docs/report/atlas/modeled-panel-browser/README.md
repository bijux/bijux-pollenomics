# Modeled panel browser verification

The retained PANGAEA 937075 atlas candidate rendered 1,875 source cell-window records and the committed 400-row country/window/metric panel inventory without numerical recomputation. The candidate is a source-bound browser fixture. Its modeled vegetation values remain context only; this check grants no scientific admission or publication authorization.

An actual Brave session downloaded 16 visible GeoJSON frames at 320 and 1440 px. Each viewport exercised all four metrics in direct No basemap with Denmark's `11200-11700 BP` source window and blocked-provider fallback with Sweden's `0-100 BP` window. The browser selected the source land-cover family for ET, ST, and OL, and the source plant-functional-type family for AL. AL retains its source code `AL` and its definition, agricultural land/cereals within open land; it is not a fourth disjoint land-cover class.

Every downloaded frame had exactly the source records for its selected country and published window. Per-record estimates and source standard errors, panel minimum and maximum values, modeled and no-pollen counts, source labels, and source classes agreed with the committed panel CSV. No-pollen records remained null across all estimate and standard-error fields. The downloaded frames stated `context_only`, with interpolation and propagation disabled. All 16 comparisons passed with no browser runtime errors. The four screenshots and 16 downloaded frames are retained in [observations](observations/).

The [verification receipt](verification.json) binds the [browser receipt](browser-receipt.json), [candidate generation record](candidate-generation.json), producer and verifier, source input hashes, served file hashes, download hashes, and screenshots. The producer read 267 source and renderer inputs. The browser served 11 candidate files and blocked 288 tile requests.

Focused checks: two candidate producer tests passed, and the current Brave replay passed with zero runtime errors. This browser sample covers two country/window pairs and four metrics at both widths and map modes. The retained CSV carries all 400 country/window/metric rows; this receipt does not claim that every panel row was navigated in the browser.

## Reproduction

From the repository root, use absent destinations under `artifacts/`:

```sh
.venv/bin/python -m bijux_pollenomics_dev.ci.atlas_browser.modeled_panel_candidate --repository . --destination artifacts/modeled-panel-candidate
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/modeled-panel-browser.mjs artifacts/modeled-panel-candidate docs/report/regions/nordic/landclim-modeled-panels/panels.csv artifacts/modeled-panel-browser '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
```
