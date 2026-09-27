# Atlas detail keyboard verification

Evidence `atlas-detail-focus-desktop-narrow` verifies the production drawer with a
synthetic golden record at 1440 and 390 pixel widths. The retained
[receipt](verification.json) contains browser identity, the
SHA-256 of every served file, producer sources, verifier identity, commands and
selected check results.

The drawer now moves focus to Overview when evidence opens. Left/Right wrap the
tab list; Home/End select its first/last tab. Only the selected tab is in the Tab
sequence, and it labels the evidence panel. Asynchronous detail loading and tab
selection preserve focus. Table pagination keeps focus on the same control, or
the panel when the control becomes disabled. Escape and Clear return focus to
the opening control; search selections return to Search because the results close
when the drawer opens. If the opening element is removed or hidden, the map is
the focus destination.

The actual Brave/Chromium browser passed 30 assertions with no runtime errors.
It opened evidence by keyboard, inspected sample pages, chronology, composition
and provenance, navigated to an unavailable record and back, and closed using
Escape and Clear. Network tile providers were blocked and the no-basemap mode
was selected. The affected rendering and browser semantics regressions passed
73 tests. Python lint/format checks and JavaScript syntax also passed.

The fixture has two points and one detailed record. Its 26 sample rows exercise
the 25-row pagination boundary. Its synthetic source locator, chronology and
composition values test preservation of evidence details; they are not admitted
scientific observations. Earlier verifier failures and their diagnosed causes
remain recorded in the receipt.

## Reproduce

Run from the repository root with the installed Python environment and a locally
installed Chromium browser. Set `PYTHONDONTWRITEBYTECODE=1` and set
`OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`,
`NUMEXPR_NUM_THREADS` and `VECLIB_MAXIMUM_THREADS` to `1`.

```sh
.venv/bin/python -m pytest packages/bijux-pollenomics/tests/unit/reporting/map_document/browser_semantics/test_detail_focus.py --basetemp=artifacts/atlas-detail-focus/pytest-tmp -o cache_dir=artifacts/atlas-detail-focus/pytest-cache -q
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/detail-focus.mjs artifacts/atlas-detail-focus/pytest-tmp/test_detail_focus_candidate_ex0 artifacts/atlas-detail-focus/browser-replay '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
```

The test materializes the candidate through the production renderer and static
asset producer. The consumer serves its files locally, sends actual browser key
events, records assertions and served hashes, and removes its browser profile.
Use a fresh browser output directory to retain separate replay receipts.

This result certifies drawer keyboard behavior for the declared fixture. It does
not certify accepted-source golden record navigation, the full provider matrix,
palette simulations, screen-reader behavior, 200% zoom, performance or release
readiness. The committed atlas HTML still needs regeneration through its governed
publication producer before this behavior is available in that retained atlas.
