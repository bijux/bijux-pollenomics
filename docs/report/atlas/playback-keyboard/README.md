# BP playback keyboard navigation

The production atlas now keeps keyboard focus on an enabled chronology step when a manual step reaches either BP boundary. At the oldest frame, focus moves from the disabled Older button to Newer; at the youngest frame, it moves from the disabled Newer button to Older.

## Measured browser result

The [controlled candidate producer](../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/playback_keyboard_candidate.py) rendered three explicit fixture point ages (0, 150, and 300 BP) through the production map document. The point records are controlled fixture data, and the four country outlines are schematic rectangles. The inline transport says `inline_test_fixture`; no source chronology or boundary geometry received scientific admission.

The [Brave receipt](../../../../artifacts/atlas-playback-keyboard/browser-final-reverse/receipt.json) passed four local scenarios at 320 × 900 and 1440 × 900, each in blocked-provider fallback and direct No basemap mode. At both widths, Tab reached the enabled Older, chronology status, and playback controls with visible focus, viewport clearance, and center hits. Shift+Tab crossed the same controls in reverse. Enter and Space stepped through [0, 100], [100, 200], and [200, 300] BP; focus transferred to the enabled opposite step at both boundaries. Enter started playback at [200, 300] BP, Space paused it without advancing for 1.1 seconds, and Space resumed the 200 → 100 → 0 BP sequence. The playback button retained visible focus and returned `aria-pressed=false` on completion.

The browser recorded zero runtime errors. Direct No basemap issued zero provider tile requests; the blocked-provider runs requested tiles and ended with No basemap. The [320 px playback screenshot](../../../../artifacts/atlas-playback-keyboard/browser-final-reverse/320-tile-free-playing.png) shows the focus ring and the fixture map. The [browser verifier](../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/playback-keyboard.mjs) checks the candidate source and output hashes, served files, focus geometry, keyboard actions, BP windows, provider requests, and eight screenshot hashes. [Verification identity](verification.json) binds the retained receipt and current renderer/verifier.

## Reproduction

From the repository root, use new destinations under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.ci.atlas_browser.playback_keyboard_candidate \
  --repository . --destination artifacts/atlas-playback-keyboard/candidate-repro
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/playback-keyboard.mjs \
  artifacts/atlas-playback-keyboard/candidate-repro \
  artifacts/atlas-playback-keyboard/browser-repro \
  '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
```

The affected browser semantics suite passed 84 tests. Ruff check and format passed for both new Python files; Node syntax passed for the browser verifier.

## Scope

This is a local keyboard and focus check for an explicit fixture BP chronology. It does not establish source age comparability, real Nordic boundary admission, screen-reader output, reduced-motion behavior, or a cross-browser accessibility result.
