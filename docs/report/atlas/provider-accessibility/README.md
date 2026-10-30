# Atlas provider fallback and mobile controls

The retained Nordic source atlas remains usable when both keyless tile providers fail and when a shared URL selects **No basemap** directly. The [verification receipt](verification.json) binds the [candidate generation](candidate-generation.json), [browser run](browser-receipt.json), verifier, [mobile screenshot](observations/390-tile-free.png) and [example downloaded source record](observations/390-tile-free-source/neotoma-site-12.pollen-series.json) by SHA-256. The candidate contains eight exact Neotoma and SEAD source sites across Denmark, Finland, Norway, and Sweden. Its source graph and detail records match the retained inputs; it adds no accepted classification or propagation edge.

## Observed browser behavior

Local headless Chrome 155.0.8059.40 was run at 1440 × 900 and 390 × 900. Both OpenStreetMap and OpenTopoMap tile hosts were deliberately blocked. At each width, the atlas attempted the street provider, then the terrain provider, and settled on No basemap with an announced degraded status. The observed requests used neither URL query parameters nor authorization headers. Direct `#basemap=none` requested zero provider tiles. All eight source sites, coordinate readout, scale, Legend control, and source detail remained available in both modes.

At 390 px, screenshot inspection found that the status panel covered the collapsed Legend button and scale. The [mobile map styles](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/assets/document.html) now place both above the status panel and give the Legend toggle a 44 px height. The final browser run verified each control's center was visible in both degraded and direct No basemap modes. The current [mobile tile-free screenshot](observations/390-tile-free.png) and the other three viewport screenshots are retained with the [browser receipt](browser-receipt.json).

In each of four width/mode combinations, keyboard search selected Neotoma site 12, drawer tab keys reached source chronology, and the displayed chronology retained context-only and refused claims. Clearing the drawer returned focus to Search. Keyboard activation reached Help through the basemap status control; its dialog exposed `aria-modal` and Escape returned focus to Help. The actual Download action produced a source record whose six source tables and provenance, source semantics, and temporal support matched the [retained source export](../source-export/downloads/neotoma-site-12.pollen-series.json). Its 270 chronology claims and 2,580 pollen observations remained source-native; interpolation was disabled.

The [browser verifier](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/provider-accessibility.mjs) produced four passing keyboard routes, four equal source downloads, two automatic provider fallbacks, two direct No basemap runs, and zero runtime errors. The earlier selection passed 139 map document/browser semantics tests and 12 candidate producer regressions; those are separate from the native capture retained here.

## Reproduction

From the repository root, use absent destinations under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.ci.atlas_browser.nordic_source_candidate \
  --repository . --destination artifacts/atlas-provider-accessibility/candidate-clearance
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/provider-accessibility.mjs \
  artifacts/atlas-provider-accessibility/candidate-clearance \
  artifacts/atlas-provider-accessibility/browser-clearance \
  '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
```

## Scope

This is a local two-viewport provider failure and keyboard interaction check for the retained point-source candidate. It does not establish provider service availability or terms, a cross-browser accessibility or contrast audit, country-boundary behavior, or scientific approval. The source chronology's unavailable, context-only, and refused states remain explicit.

The separate [cold, warm and offline browser matrix](../keyless-cache-matrix/README.md) records current four-country source candidate behavior under explicit cache and provider network conditions. It leaves the user's original failing URL and browser context open for diagnosis.

## Source-owned retained capture

The published observations now come from the immutable [source-view capture](../source-files/capture.json) on source candidate `fa79ae6eff0f344b5a2dbff2cc858f92746c1f67`, using Chrome 155.0.8059.40. The packet retains original generation, verifier, served-file, screenshot and download identities. Six successful browser observations belonged to an aggregate run that also contained two failed probes; two separately recorded successful successor probes supply the provider and modeled-panel observations. Those failures remain part of the execution history.

These report files are reproduced by guarded retained transport and explicit metadata projection. That operation executes no browser, estimator or R program, and grants no scientific, source-rights, ecological or cross-browser acceptance. Earlier public file identities remain in the capture certificate. The direct browser commands above start separately qualified new observations.

For this owner's retained projection, use an absent output under `artifacts/`:

```sh
mkdir -p artifacts/atlas-source-views
python -m bijux_pollenomics_dev.source_completion.atlas_browser.capture_projection \
  --repository . \
  --receipt configs/ci/report-capture-projections/atlas-source-views/provider-accessibility-browser-evidence.json \
  --output artifacts/atlas-source-views/provider-accessibility
```

## Local deterministic provider matrix and native controller

The maintained [matrix runner](https://github.com/bijux/bijux-pollenomics/blob/main/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/runner.py), invoked with `--plan <scope-plan.json> --provider-failure-matrix-only`, passed the following direct local map cases. Each scope covered HTTP 401, 403, 404, 429 with and without `Retry-After`, timeout, aborted connection, offline mode, corrupt tile decode and both providers unavailable. Provider replies were intercepted locally; this did not contact or qualify a live tile service.

| Direct map | Checked source commit | Passing cases |
| --- | --- | --- |
| Nordic | `b25d0fbf9f667819e1a08da64634240644a6580d` | 10/10 |
| World | `d39810f76c78ea575c830b05fad5df6e9c6e986b` | 10/10 |
| Europe | `d39810f76c78ea575c830b05fad5df6e9c6e986b` | 10/10 |

The Nordic result is reused only for its unchanged movable time-control branch. World and Europe exercised a finite preset before moving time, then restored the original full preset, country selection, time and counts. The [failure scenarios and interception policy](https://github.com/bijux/bijux-pollenomics/blob/main/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/provider-failures.mjs) checked bounded provider failover, usable map controls and unchanged scientific payload identities. All provider transactions were observed through teardown without allowing live requests; request URLs and headers and visible DOM were checked for credentials. Static scientific assets were unchanged before and after both later runs. Earlier failed runs remain failures in the local execution record.

The real local Nordic docs wrapper also passed all ten distinct provider cases at source `aa9275093828875894fcdf5b139017425fe7ac5f`, with 100 passing assertions in 28.885 seconds and 5.9 MB of bounded outputs. Chrome 155.0.8059.80 loaded `public/nordic-atlas/index.html` and its actual `report/regions/nordic/nordic_map.html` iframe; both retained identities matched the existing [embedded-report owner](https://github.com/bijux/bijux-pollenomics/blob/main/configs/docs/maps/report-owner.json), including the child's `v66` build. The [wrapper adapter](https://github.com/bijux/bijux-pollenomics/blob/main/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/wrapper-runtime.mjs) reused the provider assertions in the child execution context while checking the parent navigation and iframe remained usable. All 871 local served requests completed without a server error; there were no escaped external requests or runtime errors. Initial failover transactions were bounded and had no duplicate URLs, all later provider requests were accounted for through teardown, and the owned browser, server and profile closed. The direct-map results above were reused without rerunning them.

A separate [current-loader contract](https://github.com/bijux/bijux-pollenomics/blob/main/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/selection-runtime.mjs) passed seven controlled executable assertions at the same source. It executed the maintained selection controller and exact loader, payload-validation and acceptance functions with delayed responses: an obsolete request was aborted, its waiter refused, reselecting the original asset created a fresh request, and the old completion could neither replace the current operation nor admit a stale chunk. Build/version mismatches and HTTP, byte-count and transport-integrity failures produced actionable refusals. These are controlled contracts for current JavaScript; the retained wrapper does not contain that newer selection controller, and neither result establishes whole-atlas performance.

To repeat these checks with the already qualified local site, use an absent wrapper output directory. This reuses existing site assets and acquires or regenerates no scientific inputs:

```sh
mkdir -p artifacts/provider-failures/reproduction
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/wrapper-runtime.mjs \
  . artifacts/qualification/current-configs/site \
  artifacts/provider-failures/reproduction/nordic-wrapper \
  '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/selection-runtime.mjs .
```

At the same `d39810f76` source, a controlled synthetic signed-native bundle passed actual HTTP and `file:` browser use with the existing [signed-calendar oracle](https://github.com/bijux/bijux-pollenomics/blob/main/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/signed-native-lra.mjs) and [selection/export oracle](https://github.com/bijux/bijux-pollenomics/blob/main/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/native-lra.mjs). Its synchronous local controller loaded before use: the 18,936-byte external script matched the packaged source, with executed file-mode bytes independently read through the browser debugger. The 516,475-byte HTML remained below the unchanged 524,288-byte limit. All 41 bundle manifest members remained unchanged. Both modes preserved 18 native rows and three missing values, fractional bounds across zero, the zero instant, invalid-bound refusal and restoration, selected-role filtering and the bytes of an actual downloaded selection. Neither mode produced runtime errors or remote requests.

The first combined run recorded an overall failure because file-mode Resource Timing did not expose the controller, after the HTTP functional checks passed. That observation failure was retained. A file-only repeat passed with positive debugger script identity instead; it did not relax the signed-control or export assertions. These results qualify these local consumers only. The local retained Nordic wrapper is now covered as described above. Other wrappers, hosted execution, performance of the whole current atlas, broader browser/release gates, scientific acceptance and publication authorization remain open; the synthetic bundle supplies no new ecological result or uncertainty claim.
