# Narrow viewport map controls

The [map document](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/assets/document.html) now gives the North indicator and Leaflet controls a lower lane at widths up to 360 px. At 320 px the top bar wraps to 210 px high; the previous North position covered the playback button. The narrow rule moves North below that bar and keeps zoom and attribution below North.

## Measured behavior

The retained [baseline browser receipt](evidence/baseline/receipt.json) and [diagnostic screenshot](evidence/baseline/320-diagnostic.png) show the 320 × 900 blocked-provider page before the change: the top bar ended at y=218, its playback button ended at y=209, and North spanned y=176–220 over the button.

The final [browser receipt](evidence/selected/receipt.json) passed ten local headless Brave scenarios: blocked-provider fallback and direct No basemap at 320, 360, 361, 390, and 1440 px, all 900 px high. At 320 px, North spans y=230–274, zoom y=282–346, and attribution y=356–373. North no longer overlaps the top bar; zoom + and − and the attribution link pass center hit tests. All seven visible top bar buttons, Basemap and Legend buttons, and the Center readout pass center hit tests. The document width is exactly 320 px without horizontal overflow. In blocked-provider fallback the status starts at y=746, clear of the scale ending at y=724 and Legend ending at y=715. Direct No basemap starts status at y=750 and requests zero provider tiles. Both modes keep four controlled outlines and matching Legend cues visible, with no browser runtime errors.

At the breakpoint, North starts at y=230 for 360 px and y=176 for 361 px; both positions clear the top bar. The 390 px and 1440 px control lanes retain their previous measured positions. [The browser verifier](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/narrow-viewport-controls.mjs) records rectangles, hit targets, tile requests, and screenshots for every scenario. The [verification summary](verification.json) binds 61 producer input hashes, 11 generated output hashes, six served file hashes, the renderer and verifier hashes, ten final screenshot hashes, and the baseline screenshot hash.

## Reproduction

From the repository root, use new destinations under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.ci.atlas_browser.boundary_orientation_candidate \
  --repository . --destination artifacts/atlas-narrow-viewport-controls/candidate-repro
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/narrow-viewport-controls.mjs \
  artifacts/atlas-narrow-viewport-controls/candidate-repro \
  artifacts/atlas-narrow-viewport-controls/browser-repro \
  '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
```

The affected browser semantics selection passed 82 tests. Ruff check and format passed for the focused test, and Node syntax passed for the verifier.

## Scope

The four outlines are **controlled schematic rectangles**, not admitted Nordic boundary geometry or scientific evidence. This result covers the local Brave widths and modes listed above. It does not establish provider service availability or terms, a full browser matrix, or a full accessibility audit.

The [retained browser evidence manifest](evidence/manifest.json) records the
original process-file hashes and identifies diagnostic path rebasing.
