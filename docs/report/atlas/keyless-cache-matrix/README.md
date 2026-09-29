# Keyless atlas cache and provider matrix

The [browser receipt](browser-receipt.json) records an actual local Brave run on the current four-country, eight-source-site atlas candidate. Its [compact candidate identity](candidate-inputs.json) binds the deterministic build ID and 75/75 live input hashes. The verifier source is `packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/keyless-cache-matrix.mjs`; the receipt binds its SHA-256.

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
