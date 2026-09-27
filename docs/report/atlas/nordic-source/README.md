# Nordic retained source navigation

[The verification receipt](verification.json) records a passing browser replay of eight exact retained source sites across Denmark, Finland, Norway, and Sweden. The current production renderer serves a bounded candidate; its source graphs and detail records are authenticated against the retained [Nordic atlas](../../regions/nordic/nordic_map.html) and remain exactly equal after serialization.

## Selected records and scientific posture

| Country | Neotoma site | Chronology claims | SEAD site | Chronology claims |
| --- | --- | ---: | --- | ---: |
| Denmark | 27349, Harreskov | 38 unresolved | 3797 | 12 context only, refused |
| Finland | 2966 | 46 comparable, 92 context only | 5070 | 1 context only, refused |
| Norway | 26128 | 54 comparable, 110 context only, 1 refused | 5119 | 1 context only, 1 unresolved; both refused |
| Sweden | 12, Ageröds Mosse | 131 comparable, 135 context only, 4 refused | 6468 | Unavailable: `sead_site_numeric_chronology_not_available` |

These are geographic source contexts. Site age extrema do not establish continuous pollen support. All retained classification and relation refusals remain visible. The retained SEAD acquisition release and propagation status remain refused; this replay does not upgrade source admission or scientific approval.

## Browser result

Brave Chromium at widths 1440 and 390 passed 12 country-filter outcomes, 16 exact record URL/navigation outcomes, and 16 chronology-display outcomes, with zero runtime errors. Each single-country selection contains exactly two source sites; all-country selection contains eight. Selecting none hides all sites and the drawer, and restoring all recovers eight.

Every cell of all 626 retained chronology rows was compared independently with the rendered table across all pages at each width: 1,252 row comparisons. The checks include nested source age values, source relation paths, source-native identifiers, alternate chronology statuses, refusal reasons, uncertainty nulls, and numeric nulls. The unresolved Swedish SEAD site shows its original unavailable reason. Source build identities and classification/relation refusals remain visible when switching tabs. Keyboard activation of Next reaches the other selected source in the focal country and writes its exact record identity to the URL.

The browser receipt preserves actual served byte hashes and verifier identity. The producer receipt preserves original source build, source provenance, selected feature/detail hashes, and every consumed input byte hash. Source graph/detail equality and input integrity were checked after generation. Seven focused producer regressions passed in 0.52 seconds; selected Ruff checks and Node syntax checks passed.

## Reproduction

From the repository root, use an absent destination below `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.ci.atlas_browser.nordic_source_candidate \
  --repository . --destination artifacts/atlas-nordic-source/replay-candidate
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/nordic-country.mjs \
  artifacts/atlas-nordic-source/replay-candidate artifacts/atlas-nordic-source/replay-browser \
  '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
```

The [producer](../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/nordic_source_candidate.py) and [browser verifier](../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/nordic-country.mjs) use existing local dependencies. The retained run used `artifacts/atlas-nordic-source/frozen-candidate` and `artifacts/atlas-nordic-source/browser-frozen`. The browser profile is removed after its observed terminal result.

## Scope of this evidence

This result verifies four-country retained source display, full-document shared record URL loading, country filter denominators, source inspection, and context/refusal navigation. It does not certify complete four-country acquisition, same-document hash/history replay, performance, full accessibility, provider modes, deployment, or continuous time-series support.

The candidate contains zero accepted propagation edges. Cross-border endpoint context, ordered country-pair edge filters, edge-matrix denominators, eligible pair generation, independent scientific signal comparison, and partition deduplication require source-supported accepted edge evidence and remain unverified here.
