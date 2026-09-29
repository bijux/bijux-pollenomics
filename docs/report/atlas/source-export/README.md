# Source pollen downloads and shared record links

Evidence `atlas-source-pollen-export-url` verifies actual source-record downloads
and URL replay for Ageröds Mosse (`neotoma:site:12`) and Bergakyllen
(`neotoma:site:3009`). The [receipt](verification.json) binds the source inputs,
current renderer, browser consumer, served files and measured downloads.

The drawer provides **Download pollen/time-series records** when its complete
sample, chronology and observation tables are available with literal source
value/unit/sample fields and chronology comparability. Generic model composition
tables do not enable this source download. The JSON download
preserves source sample/observation identifiers, values, native units, null
denominators, chronology alternatives/refusals and provenance. Collection units,
datasets and source-variable tables travel with the record. It exports the
complete selected record; a map time window is metadata and does not silently
remove source rows. No chronology interpolation or continuous support is added.

The URL now carries the exact layer, feature, record and selected drawer tab.
Reloading a shared record link restores that identity and tab. If current filters
exclude it, the drawer stays closed and the atlas reports that the shared record
is unavailable. The drawer also provides a copy-link control, with an address-bar
fallback when clipboard access is unavailable. Clipboard platform integration was
not included in the measured download/URL checks.

## Retained downloads

These files are the current desktop browser downloads, with byte hashes in the [verification receipt](verification.json):

| Source record | Samples | Chronology claims | Pollen observations | Download |
|---|---:|---:|---:|---|
| Ageröds Mosse | 135 | 270 | 2,580 | [Source record JSON](downloads/neotoma-site-12.pollen-series.json) |
| Bergakyllen | 28 | 56 | 523 | [Source record JSON](downloads/neotoma-site-3009.pollen-series.json) |

All six decoded source tables were compared with the authenticated retained atlas
tables. The downloaded chronology census preserves Ageröds Mosse's 131 comparable
calibrated, four refused calibrated and 135 contextual uncalibrated claims, and
Bergakyllen's 28 comparable calibrated and 28 contextual uncalibrated claims.
Null denominators and literal `NISP`/other source units remain unchanged.

Download selection metadata includes the local verification URL. Those URLs
identify the measured local browser context; reproduce the candidate to use a
current local link. Width-specific selection metadata explains why desktop and
narrow download hashes differ, while the source tables remain equal.

## Verification and replay

The actual Brave/Chromium consumer passed at 1440 and 390 pixel widths with zero
runtime errors. It completed six downloads: selected record, shared-link reload
of the same record, and next record at each width. The restored downloads were
byte-identical to their original selections. Four URL outcomes cover successful
record/tab restoration and refusal to restore a record excluded by filters at
both widths. Twelve current candidate producer regressions passed.

The current verifier completed all six downloads and four URL outcomes with zero runtime errors.

Run from the repository root with the installed Python environment and Chromium
browser. Set `PYTHONDONTWRITEBYTECODE=1` and set `OMP_NUM_THREADS`,
`OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS` and
`VECLIB_MAXIMUM_THREADS` to `1`. Use an absent candidate destination and a fresh
browser output directory.

```sh
.venv/bin/python -m bijux_pollenomics_dev.ci.atlas_browser.source_detail_candidate --repository . --destination artifacts/atlas-source-export/replay-candidate
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/source-export.mjs artifacts/atlas-source-export/replay-candidate artifacts/atlas-source-export/browser-replay '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
```

The product logic is
[`source-record-export.js`](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/assets/source-record-export.js),
and the browser consumer is
[`source-export.mjs`](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/source-export.mjs).
This result covers two retained Swedish source contexts. It does not certify SEAD
navigation, four-country coverage, time-series diagrams, approved pollen sums or
taxa mappings, propagation, full accessibility/provider/performance gates, or
deployment/release readiness. The governed Nordic atlas now includes the source download controls.
