# Atlas provider fallback and mobile controls

The retained Nordic source atlas remains usable when both keyless tile providers fail and when a shared URL selects **No basemap** directly. The [verification receipt](verification.json) binds the [candidate generation](candidate-generation.json), [browser run](browser-receipt.json), verifier, [screenshots and four downloaded source records](observations/) by SHA-256. The candidate contains eight exact Neotoma and SEAD source sites across Denmark, Finland, Norway, and Sweden. Its source graph and detail records match the retained inputs; it adds no accepted classification or propagation edge.

## Observed browser behavior

Local headless Brave was run at 1440 × 900 and 390 × 900. Both OpenStreetMap and OpenTopoMap tile hosts were deliberately blocked. At each width, the atlas attempted the street provider, then the terrain provider, and settled on No basemap with an announced degraded status. The observed requests used neither URL query parameters nor authorization headers. Direct `#basemap=none` requested zero provider tiles. All eight source sites, coordinate readout, scale, Legend control, and source detail remained available in both modes.

At 390 px, screenshot inspection found that the status panel covered the collapsed Legend button and scale. The [mobile map styles](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/assets/document.html) now place both above the status panel and give the Legend toggle a 44 px height. The final browser run verified each control's center was visible in both degraded and direct No basemap modes. The current [mobile tile-free screenshot](observations/390-tile-free.png) and the other three viewport screenshots are retained with the [browser receipt](browser-receipt.json).

In each of four width/mode combinations, keyboard search selected Neotoma site 12, drawer tab keys reached source chronology, and the displayed chronology retained context-only and refused claims. Clearing the drawer returned focus to Search. Keyboard activation reached Help through the basemap status control; its dialog exposed `aria-modal` and Escape returned focus to Help. The actual Download action produced a source record whose six source tables and provenance, source semantics, and temporal support matched the [retained source export](../source-export/downloads/neotoma-site-12.pollen-series.json). Its 270 chronology claims and 2,580 pollen observations remained source-native; interpolation was disabled.

The [browser verifier](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/provider-accessibility.mjs) produced four passing keyboard routes, four equal source downloads, two automatic provider fallbacks, two direct No basemap runs, and zero runtime errors. The current selection passed 139 map document and browser semantics tests and 12 atlas browser candidate producer regressions.

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
