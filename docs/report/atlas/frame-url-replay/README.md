# Populated context frame URL replay

[The verification receipt](verification.json) binds two current production-rendered candidates to retained inputs and actual browser downloads. The modeled candidate contains 1,875 PANGAEA 937075 cell-window records across 25 declared windows and 47 source metrics. The signed native candidate reuses a retained synthetic paired LRA product: 18 source rows, four missing native statistics, and exact `calendar-bp1950-signed.v1` support. Neither candidate runs numerical estimation or grants scientific acceptance.

## Source and publication boundary

The [producer](../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/context_frame_candidate.py) authenticates the retained Nordic chunk inventory, reads the exact local normalized grid rows, and verifies that the current null-preserving publication projection equals every retained published feature. It then requires the static writer to preserve all selected published records exactly. The source manifest retains 628 high, 940 low, and 307 no-pollen-data features; every no-pollen estimate and standard-error field is null in the served publication and downloaded frames. No gaps are interpolated between source windows.

The native input is the retained `artifacts/v2/signed-calendar/browser-postcommit/candidate001/zero-crossing/presentation/product` plus its byte-bound display geometry. The producer checks their exact digests before rendering the current atlas and rechecks every consumed input afterward. The native view identity remains `c7276b4b90bd57750af6182cb65ae8674e349f332cc6f606bd23dcb19e13a6e8`; the original product manifest is `de45206119e4f2663fe1d24cb4b52a481f025fa8cf7561c5ac7a188c624c07e9`. Source native units, missing values, and geometry refusals retain their distinct meanings. This paired view has no posterior draw channel or draw selector; the receipt records that absence.

## Actual browser result

The [browser verifier](../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/frame-url-replay.mjs) passed at widths 1440 and 390, with zero runtime errors:

- 28 actual modeled GeoJSON downloads matched complete selected source cell-window records. Cases span the oldest and newest windows, Denmark and Finland filters, source land-cover type, source PFT `ISTS` with its unavailable definition, and exact-taxon metrics. Oldest full-country frame: 75 features, 48 no-pollen null records. The Denmark frame: six features, three null records. The Finland frame: 19 features, three null records. Newest full-country frame: 75 features, ten null records.
- 30 actual native JSON downloads matched the independently checked source view, complete selected rows, native units and DOM missingness. Selections include all 18 rows/four missing values, a regional subset with five rows/one missing value, a local zero-point Calendar BP window with eight rows/two missing values, and an explicit empty role selection. The fractional `[-0.25, 0.25]` and point `[0, 0]` windows retain their signed profile and exact view identity.
- 16 direct hash replays and 24 browser Back/Forward outcomes restored the complete frame/profile/selection and identical download bytes. Incoming hash transitions reinitialized the document once; no reload loop was observed.
- Two incompatible signed-profile URLs were visibly refused, retained their requested profile in the address, selected no native rows, and disabled download. Returning through browser history restored the valid empty selection and its exact export.

All modeled frames are labeled `context_only`, with interpolation and propagation disabled. The native outputs are synthetic exploratory views with `scientific_acceptance: not_evaluated` and `publication_authorized: false`. Accepted pollen propagation, posterior draw comparison, and a four-country accepted edge matrix are not asserted.

Five focused producer regressions passed in 0.62 seconds. Producer mypy, Ruff and formatting checks, browser verifier Node syntax, input hashes, served byte hashes, and report links passed.

## Reproduction

From the repository root, use an absent destination below `artifacts/` and the retained product and geometry inputs:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.ci.atlas_browser.context_frame_candidate \
  --repository . --destination artifacts/atlas-frame-url-replay/replay-candidate \
  --native-product artifacts/v2/signed-calendar/browser-postcommit/candidate001/zero-crossing/presentation/product \
  --native-geometry artifacts/v2/signed-calendar/browser-postcommit/candidate001/zero-crossing/presentation/display-geometry.json \
  --product-manifest-sha256 de45206119e4f2663fe1d24cb4b52a481f025fa8cf7561c5ac7a188c624c07e9 \
  --geometry-sha256 52afc5687e5ab39b6cf3445cdefb12096be050938b12f3cc9436b3da51b761bd
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/frame-url-replay.mjs \
  artifacts/atlas-frame-url-replay/replay-candidate artifacts/atlas-frame-url-replay/replay-browser \
  '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
```

The retained final artifacts are `artifacts/atlas-frame-url-replay/owned-candidate` and `artifacts/atlas-frame-url-replay/browser-owned`. Download files remain under the browser artifact directory, and the browser profile is removed after the observed terminal result. The receipt stores each download hash and source-supported selection.

## Scope

This result verifies populated modeled context and a signed synthetic native view through actual full-document, same-document URL and browser-history replay. It does not certify current real-data native LRA approval, posterior draw selection, full accessibility, performance, provider modes, deployment, or an accepted cross-border propagation edge. Those require separately admitted evidence and consumer checks.
