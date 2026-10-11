# Controlled boundary orientation browser result

This result exercises the production atlas renderer with four **schematic rectangles** labeled Denmark, Finland, Norway, and Sweden. The rectangles are controlled browser geometry. They are not national borders, source observations, or scientifically admitted Nordic boundary data. The candidate contains no evidence points or accepted propagation edges.

The [verification receipt](verification.json) binds the candidate's geometry, selected source inputs, rendered files, browser verifier, served files, and four screenshots by SHA-256. Its producer uses the [production map renderer](../../../../packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/render.py) and existing local Leaflet assets. The [controlled producer](../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/boundary_orientation_candidate.py) labels scientific admission as `not_evaluated`.

## Browser observations

In local headless Brave at 1440 × 900 and 390 × 900, both keyless tile hosts were blocked. In each viewport, street and terrain failures led to No basemap. Opening directly with `#basemap=none` requested zero provider tiles. Each of the four runs rendered four nonzero SVG outlines, whose stroke colors matched four visible country Legend cues. The schematic northern rectangles appeared above the southern rectangles, and eastern rectangles appeared to the right. This confirms north-up placement of the rendered outlines in these runs. The scale was visible at its center and the basemap status described the degraded state.

The renderer has **no visible north arrow or compass** in these runs. The Center value was visible in the desktop status panel; the current narrow layout hides that status field, although the value remains in the document. This result therefore does not close the explicit north-orientation indicator or mobile coordinate-visibility requirements. The controlled geometry also cannot establish national boundary accuracy, country-boundary source admission, provider availability, or accessibility across browsers.

The [browser verifier](../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/boundary-orientation.mjs) checks the rendered path boxes and country cues, tile requests, scale, and status. The final screenshots and raw browser receipt are under `artifacts/atlas-boundary-orientation/browser-coordinate-visibility/`.

## Reproduction

From the repository root, use absent destinations below `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.ci.atlas_browser.boundary_orientation_candidate \
  --repository . --destination artifacts/atlas-boundary-orientation/candidate-final
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/boundary-orientation.mjs \
  artifacts/atlas-boundary-orientation/candidate-final \
  artifacts/atlas-boundary-orientation/browser-coordinate-visibility \
  '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
```
