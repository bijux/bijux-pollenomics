# Map keyboard navigation

The [map document](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/assets/document.html) now removes the closed controls drawer and the invisible mobile scrim from the Tab order. The drawer starts inert and its inert state follows its collapsed state. The scrim remains a pointer dismissal surface but stays hidden from the accessibility tree; the drawer provides a Close button and Escape return path.

## Measured behavior

The retained [baseline browser receipt](evidence/baseline/receipt.json) recorded 31–32 Tab entries at 320 px. Eighteen entries focused controls in the translated, offscreen drawer; the invisible scrim was another Tab stop. The final [browser receipt](evidence/selected/receipt.json) passed four local headless Brave scenarios at 320 × 900 and 1440 × 900, each in blocked-provider fallback and direct No basemap mode. The 320 px route now has 12–13 entries, with no offscreen drawer or scrim stops. Every interactive stop on the tested route has a visible focus outline, is within the viewport, and passes a center hit test. North remains an informational image labeled “North is up” and is absent from the Tab route.

Actual Tab and Shift+Tab move between Fit active and Search in both directions. Enter expands the Legend and Space collapses it while focus stays on its button. Enter on Leaflet zoom + raises the map zoom by one; Enter on zoom − returns it to its prior value after the zoom transition. The attribution link receives visible keyboard focus. Enter and Space on Basemap open the controls drawer and move focus to the active No basemap button. At 320 px that button is in the viewport after the drawer transition; Tab reaches Reset view and Shift+Tab returns to No basemap. Help opens as a modal from the drawer: Tab and Shift+Tab wrap between its Close and Return buttons, and Escape returns to Help. At 320 px a further Escape closes the drawer and restores the Basemap opener. The browser reported no runtime errors. Direct No basemap requested zero provider tiles.

The focused [attribution screenshot](evidence/selected/320-tile-free-attribution-focus.png) and [Help dialog screenshot](evidence/selected/320-tile-free-help-dialog.png) show the visible focus state. The [browser verifier](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/map-keyboard-navigation.mjs) records all key routes, focus outlines, viewports, hit tests, drawer and dialog states, and network requests. The [verification summary](verification.json) binds 61 producer input hashes, 11 generated output hashes, six served file hashes, the renderer and verifier hashes, and 12 screenshot hashes.

## Reproduction

From the repository root, use new destinations under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.ci.atlas_browser.boundary_orientation_candidate \
  --repository . --destination artifacts/atlas-map-keyboard-navigation/candidate-repro
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/map-keyboard-navigation.mjs \
  artifacts/atlas-map-keyboard-navigation/candidate-repro \
  artifacts/atlas-map-keyboard-navigation/browser-repro \
  '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
```

The affected browser semantics selection passed 83 tests. Ruff check and format passed for the focused test, and Node syntax passed for the verifier.

## Scope

This controlled candidate has no BP chronology. Its playback controls are visibly disabled with “No BP chronology available”; playback keyboard activation was not exercised. The Leaflet attribution link was focused and visually checked but not opened. The four outlines are **controlled schematic rectangles**, not admitted Nordic boundary geometry or scientific evidence. This local Brave result is not a screen-reader, contrast, or full browser matrix audit.

The [retained browser evidence manifest](evidence/manifest.json) records the
original process-file hashes and identifies diagnostic path rebasing.
