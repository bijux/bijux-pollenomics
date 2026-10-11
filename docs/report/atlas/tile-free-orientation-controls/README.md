# Orientation and coordinates without map tiles

The atlas now displays an ↑ N indicator and keeps Center coordinates visible in the narrow status panel. The [map document](../../../../packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/assets/document.html) gives the indicator an accessible name, places the Basemap status button on a full mobile row, and keeps the Legend and scale above the taller status panel. The 390 px Legend and Basemap buttons each retain a 44 px touch target.

The [verification receipt](verification.json) binds the controlled candidate's selected source files, generated document and local assets, served files, browser verifier, and four screenshots by SHA-256. The four outlines are **schematic rectangles**. They exercise the production renderer but are not admitted Nordic boundary geometry or scientific evidence.

## Observed behavior

Local headless Brave was run at 1440 × 900 and 390 × 900. In each viewport, blocking the keyless street and terrain tile hosts led to No basemap; opening `#basemap=none` directly requested zero provider tiles. All four schematic outlines and corresponding visible country Legend cues remained on the map. Their northward and eastward screen order matched the controlled geometry.

At 390 px in both modes, the ↑ N indicator was visible and named “North is up,” without covering the top bar. The Center value matched the map snapshot and was visibly reachable at its center. The scale ended at pixel 724, while the status panel began at pixel 750, leaving 26 px of clearance. The Legend button was 44 px high, the Basemap status button was 44 px high, and both passed center hit tests. The status announced degraded No basemap and the browser reported zero runtime errors. [The browser verifier](../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/tile-free-orientation-controls.mjs) records each measured rectangle and control state.

The affected browser semantics selection passed 79 tests. The two focused files passed Ruff check and format; Node syntax passed for the browser verifier. The retained final browser receipt and screenshots are under `artifacts/atlas-tile-free-orientation-controls/browser-clearance/`.

## Reproduction

From the repository root, use absent destinations below `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.ci.atlas_browser.boundary_orientation_candidate \
  --repository . --destination artifacts/atlas-tile-free-orientation-controls/candidate-repro
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/tile-free-orientation-controls.mjs \
  artifacts/atlas-tile-free-orientation-controls/candidate-repro \
  artifacts/atlas-tile-free-orientation-controls/browser-repro \
  '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
```

## Scope

This result covers visible north orientation and Center coordinates in the tested desktop and mobile fallback and direct No basemap modes. It does not establish national boundary accuracy, provider service availability or terms, a full browser matrix, or a full accessibility and contrast audit. The controlled candidate contains no evidence points and makes no scientific admission claim.
