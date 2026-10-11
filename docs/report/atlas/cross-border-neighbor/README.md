# Cross-border neighbor context in a country view

The production atlas retains the neighboring endpoint of a governed cross-border edge when a country is selected. The retained point has a permanent country-labeled tooltip, reduced marker opacity, and a context label in its popup and detail card. Focal-country point counts, country chips, chronology counts, search summaries, and capture counts exclude the contextual point; the capture snapshot reports its count separately. Static chunk selection loads the required neighboring point country while leaving unrelated point countries and neighboring boundary chunks out.

## Measured browser result

The [controlled candidate producer](../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/cross_border_neighbor_candidate.py) rendered two fixture point ages through the production static atlas transport: an older Norway endpoint at 200 BP and a younger Sweden endpoint at 100 BP. The shared WGS84 helper measured their straight endpoint distance as 50.6723134140697 km. The candidate contains one fixture `NO→SE` relation, a 100-year lag, and four **schematic rectangles** for orientation. Its status is `controlled_cross_border_only`; scientific admission was not evaluated. The fixture relation is not a historical movement, route, or real source result.

The retained [baseline Brave receipt](../../../../artifacts/atlas-cross-border-neighbor/browser-baseline-country/receipt.json) showed the gap: the regional view had two points and one edge, while Sweden-only and Norway-only each lost the neighboring endpoint and edge. The final [Brave receipt](../../../../artifacts/atlas-cross-border-neighbor/browser-final-bound/receipt.json) passed 320 × 900 and 1440 × 900 in blocked-provider fallback and direct No basemap modes. Each selected Sweden or Norway view had one focal point, one visible label naming the other country, and one rendered cross-border edge. The unchecked neighbor country chip stayed at zero. Denmark-only had no points, context, or edge; the regional view retained two points and one edge. Direct No basemap requested zero provider tiles, and the browser reported zero runtime errors.

The [320 px Sweden screenshot](../../../../artifacts/atlas-cross-border-neighbor/browser-final-bound/320-tile-free-sweden.png) and [1440 px Sweden screenshot](../../../../artifacts/atlas-cross-border-neighbor/browser-final-bound/1440-tile-free-sweden.png) show the label and focal/context count split. The [browser verifier](../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/cross-border-neighbor.mjs) checks source and generated hashes, the controlled relation identity, the rendered edge and count split, label visibility inside the viewport, country chips, provider requests, and 16 screenshots. [Verification identity](verification.json) binds the final browser receipt, renderer, and verifier.

## Reproduction

From the repository root, use new destinations under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.ci.atlas_browser.cross_border_neighbor_candidate \
  --repository . --destination artifacts/atlas-cross-border-neighbor/candidate-repro
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/cross-border-neighbor.mjs \
  artifacts/atlas-cross-border-neighbor/candidate-repro \
  artifacts/atlas-cross-border-neighbor/browser-repro \
  '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
```

The affected browser semantics and static runtime selection passed 89 tests. Ruff check and format, selected mypy, Node syntax, and `git diff --check` passed.

## Scope

This result exercises one controlled relation and the local country-only display contract. The retained point is shown only when a selected governed edge names it and the point passes the active layer, chronology, signal, and coordinate filters. It does not establish scientific eligibility for real records, actual Nordic boundary admission, source coverage, the behavior of a large edge network, or a cross-browser accessibility result.
