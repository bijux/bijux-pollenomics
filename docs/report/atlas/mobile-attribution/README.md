# Mobile map attribution clearance

The [map document](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/assets/document.html) places Leaflet’s attribution and zoom controls in a clear lane below the North indicator on narrow screens. The mobile rule applies to the shared Leaflet control container in both blocked-provider fallback and direct No basemap mode. It keeps the attribution link visible and clickable without covering the scale, Legend, North indicator, or status panel.

## Measured behavior

Before the change, the retained [baseline browser receipt](evidence/baseline/receipt.json) placed the attribution at x=329–390, y=883–900 in the 390 × 900 blocked-provider scenario. The status panel spanned x=8–382, y=750–892, and the attribution center hit the status panel. The baseline run intentionally failed that visibility assertion.

The final [browser receipt](evidence/selected/receipt.json) passed four local headless Brave scenarios at 1440 × 900 and 390 × 900. At 390 px in both modes, the attribution spans x=321–382, y=302–319; its center and Leaflet link center are hit-visible. Zoom + and − occupy x=338–372, y=228–292 and are hit-visible. The North indicator ends at y=220; the Legend is at y=671–715, scale at y=706–724, and status begins at y=750. The verifier measured no attribution overlap with those controls or the top bar. The blocked-provider path observed 12 street and 12 terrain requests at 390 px before No basemap; direct No basemap made zero provider tile requests. The four controlled outlines and matching Legend cues remained visible, with no browser runtime errors.

The [verification summary](verification.json) binds 61 producer input hashes, 11 generated output hashes, six served file hashes, the renderer and browser verifier hashes, and four screenshot hashes. The [browser verifier](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/mobile-attribution.mjs) records measured DOM rectangles, hit targets, network requests, and browser facts. Its screenshots are retained under `artifacts/atlas-mobile-attribution/browser-zoom-verified/`.

## Reproduction

From the repository root, use new destinations under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.ci.atlas_browser.boundary_orientation_candidate \
  --repository . --destination artifacts/atlas-mobile-attribution/candidate-repro
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/mobile-attribution.mjs \
  artifacts/atlas-mobile-attribution/candidate-repro \
  artifacts/atlas-mobile-attribution/browser-repro \
  '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
```

The affected browser semantics selection passed 80 tests; the focused test passed after formatting. Ruff check and format passed for the focused test, and Node syntax passed for the verifier.

## Scope

The four outlines are **controlled schematic rectangles**, not admitted Nordic boundary geometry or scientific evidence. This result covers the local Brave desktop and mobile fallback and direct No basemap scenarios; it does not establish provider availability or terms, a full browser matrix, or a full accessibility audit. At 1440 px, the status panel still covers the zoom + and − center points. That separate desktop control defect is recorded in the final receipt and remains open.

The [retained browser evidence manifest](evidence/manifest.json) records the
original process-file hashes and identifies diagnostic path rebasing.
