# Retained Neotoma drawer navigation

Evidence `atlas-retained-neotoma-detail-navigation` verifies actual source-owned
drawer content for Ageröds Mosse (`neotoma:site:12`) and Bergakyllen
(`neotoma:site:3009`). The [receipt](verification.json) retains authenticated
source/producer hashes, the generated candidate identity, served browser bytes,
browser assertions, source chronology dispositions and check results.

The bounded candidate uses the current production renderer with unchanged details
from the retained Nordic atlas. The producer verifies each source chunk against
the atlas inventory, preserves both detail records, and checks its consumed input
hashes again before finishing. The materialized detail records also match the
source record hashes exactly. It does not acquire data or recompute science.

| Source site | Samples | Chronology claims | Literal pollen observations |
|---|---:|---:|---:|
| Ageröds Mosse | 135 | 270 | 2,580 |
| Bergakyllen | 28 | 56 | 523 |

Ageröds Mosse retains 131 comparable calibrated claims, four refused calibrated
claims and 135 contextual uncalibrated claims. Bergakyllen retains 28 comparable
calibrated claims and 28 contextual uncalibrated claims. The site aggregate age
ranges remain context; they do not provide continuous numerical time support.
No reviewed pollen sum, taxon classification or propagation eligibility is added.

The actual Brave/Chromium receipt has 34 assertion entries at 1440 and 390 pixel
widths: 32 passed checks and two recorded keyboard routes, with zero runtime
errors. It used keyboard search, drawer tab navigation,
sample paging, chronology/composition/provenance inspection, next/previous source
record navigation, and Escape/Clear focus return. It compared every displayed
cell of the first source pollen observation with its literal source values,
including identifiers, count, native `NISP` unit, null denominator and denominator
status. No-basemap mode was active and tile provider requests were blocked.

The browser records its route through Chromium's keyboard-focusable overflow
tables before reaching sample paging. The default synthetic profile independently
passed its existing 30 browser assertions with the extended verifier. Three source
candidate regressions and two synthetic fixture regressions passed. Earlier
collection/verifier diagnostics remain identified in the receipt. The original
[synthetic drawer evidence](../detail-focus/README.md) retains its original verifier
identity and has not been rewritten as a new pass.

## Reproduce

Run from the repository root with the installed Python environment and an installed
Chromium browser. Set `PYTHONDONTWRITEBYTECODE=1` and set `OMP_NUM_THREADS`,
`OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS` and
`VECLIB_MAXIMUM_THREADS` to `1`. Select an absent artifact candidate destination
and a fresh browser output directory.

```sh
.venv/bin/python -m bijux_pollenomics_dev.ci.atlas_browser.source_detail_candidate --repository . --destination artifacts/atlas-source-detail/replay-candidate
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/detail-focus.mjs artifacts/atlas-source-detail/replay-candidate artifacts/atlas-source-detail/browser-replay '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser' artifacts/atlas-source-detail/replay-candidate/expectations.json
```

The producer is
[`source_detail_candidate.py`](../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/source_detail_candidate.py);
the consumer is
[`detail-focus.mjs`](../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/detail-focus.mjs).
Run package checks separately because their test packages share the `tests` name:

```sh
.venv/bin/python -m pytest packages/bijux-pollenomics-dev/tests/atlas_browser/test_source_detail_candidate.py --basetemp=artifacts/atlas-source-detail/source-tests -o cache_dir=artifacts/atlas-source-detail/pytest-cache -q
.venv/bin/python -m pytest packages/bijux-pollenomics/tests/unit/reporting/map_document/browser_semantics/test_detail_focus.py --basetemp=artifacts/atlas-source-detail/drawer-tests -o cache_dir=artifacts/atlas-source-detail/pytest-cache -q
```

This result covers two retained Swedish source contexts. It does not certify the
full atlas, SEAD record navigation, four-country coverage, palette simulations,
screen-reader behavior, 200% zoom, performance, deployment or release readiness.
