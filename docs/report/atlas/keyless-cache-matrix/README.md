# Keyless atlas cache and provider matrix

The [browser receipt](browser-receipt.json) records an actual local Chrome 155.0.8059.40 run on the current four-country, eight-source-site atlas candidate. Its [compact candidate identity](candidate-inputs.json) binds the deterministic build ID and 76 frozen input hashes. The verifier source is `packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/keyless-cache-matrix.mjs`; the receipt binds its SHA-256.

The local server served atlas files with `Cache-Control: public, max-age=3600`. Each viewport began after clearing the browser cache. Both tile hosts were blocked by the browser network domain. The run used the same page URL for cold and warm visits, then loaded a direct `#basemap=none` URL with browser offline mode enabled.

| Viewport | Cold local file requests | Warm local file requests | Blocked street/terrain tile requests per online visit | Offline No basemap file/tile requests | Rendered source sites | Runtime exceptions |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1440 × 900 | 17 | 0 | 24 / 24 | 0 / 0 | 8 | 0 |
| 390 × 900 | 17 | 0 | 12 / 12 | 0 / 0 | 8 | 0 |

Both online visits reached the announced No basemap fallback, retained all four country names and eight source sites, and sent no tile URL query or authorization header. The warm visits emitted browser cache events and made no local server requests. The offline visits rendered with no local server or tile requests; they did not emit a `Network.requestServedFromCache` event, so the receipt does not identify whether that delivery used HTTP cache or page restoration. The run exercised one browser engine and a local URL. It does not reproduce the user's earlier failing URL, extension state, public endpoint, or a different browser's cache. It also does not create governed ecological map layers.

To reproduce from the repository root with absent destinations under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.ci.atlas_browser.nordic_source_candidate \
  --repository . --destination artifacts/jobs/keyless-cache-matrix/replayed-candidate
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/keyless-cache-matrix.mjs \
  artifacts/jobs/keyless-cache-matrix/replayed-candidate \
  artifacts/jobs/keyless-cache-matrix/replayed-browser \
  '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
```

## Source-owned retained capture

The published observations now come from the immutable [source-view capture](../../../../data/atlas/source-view-capture/capture.json) on source candidate `fa79ae6eff0f344b5a2dbff2cc858f92746c1f67`, using Chrome 155.0.8059.40. The packet retains original generation, verifier, served-file, screenshot and download identities. Six successful browser observations belonged to an aggregate run that also contained two failed probes; two separately recorded successful successor probes supply the provider and modeled-panel observations. Those failures remain part of the execution history.

These report files are reproduced by guarded retained transport and explicit metadata projection. That operation executes no browser, estimator or R program, and grants no scientific, source-rights, ecological or cross-browser acceptance. Earlier public file identities remain in the capture certificate. The direct browser commands above start separately qualified new observations.

For this owner's retained projection, use an absent output under `artifacts/`:

```sh
mkdir -p artifacts/atlas-source-views
python -m bijux_pollenomics_dev.source_completion.atlas_browser.capture_projection \
  --repository . \
  --receipt configs/ci/report-capture-projections/atlas-source-views/keyless-cache-matrix-browser-receipt.json \
  --output artifacts/atlas-source-views/keyless-cache-matrix
```
