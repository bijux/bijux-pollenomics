# Desktop map zoom clearance

The [map document](../../../../packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/assets/document.html) places Leaflet’s zoom and attribution controls below the North indicator on desktop screens. The 390 px rule keeps its own position below North. This keeps zoom + and − clickable in blocked-provider fallback and direct No basemap mode without covering attribution, North, the top bar, Legend, scale, or status.

## Measured behavior

The retained [baseline browser receipt](../../../../artifacts/atlas-desktop-zoom-controls/browser-obscured/receipt.json) failed at 1440 × 900. Zoom controls spanned x=1396–1430, y=809–873; the status panel spanned x=333–1424, y=817–876. Both button centers hit the status panel.

The final [browser receipt](../../../../artifacts/atlas-desktop-zoom-controls/browser-clearance/receipt.json) passed four local headless Brave scenarios at 1440 × 900 and 390 × 900. At 1440 px in both modes, zoom controls now span y=72–136 and attribution spans y=146–163. Both zoom buttons and the attribution link pass center hit tests. The verifier found no zoom overlap with attribution, North, the top bar, Legend, scale, or status. At 390 px, the previously verified positions remain: zoom y=228–292 and attribution y=302–319, with their center targets visible. Blocked-provider fallback observed street and terrain requests before No basemap; direct No basemap made zero provider tile requests. Four controlled outlines and matching Legend cues remained visible, with no browser runtime errors.

The [verification summary](verification.json) binds 61 producer input hashes, 11 generated output hashes, six served file hashes, the renderer and [browser verifier](../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/desktop-zoom-controls.mjs) hashes, and four screenshot hashes. Screenshots are retained under `artifacts/atlas-desktop-zoom-controls/browser-clearance/`.

## Reproduction

From the repository root, use new destinations under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.ci.atlas_browser.boundary_orientation_candidate \
  --repository . --destination artifacts/atlas-desktop-zoom-controls/candidate-repro
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/desktop-zoom-controls.mjs \
  artifacts/atlas-desktop-zoom-controls/candidate-repro \
  artifacts/atlas-desktop-zoom-controls/browser-repro \
  '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
```

The affected browser semantics selection passed 81 tests. Ruff check and format passed for the new focused test, and Node syntax passed for the verifier.

## Scope

The four outlines are **controlled schematic rectangles**, not admitted Nordic boundary geometry or scientific evidence. This result covers the local Brave desktop and mobile fallback and direct No basemap scenarios. It does not establish provider service availability or terms, a full browser matrix, or a full accessibility audit.
