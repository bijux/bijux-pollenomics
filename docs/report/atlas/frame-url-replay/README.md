# Populated context frame URL replay

[The verification receipt](verification.json) binds two current production-rendered candidates to retained inputs and actual browser downloads. The modeled candidate contains 1,875 PANGAEA 937075 cell-window records across 25 declared windows and 47 source metrics. The signed native candidate reuses a retained synthetic paired LRA product: 18 source rows, four missing native statistics, and exact `calendar-bp1950-signed.v1` support. Neither candidate runs numerical estimation or grants scientific acceptance.

## Source and publication boundary

The [producer](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/context_frame_candidate.py) authenticates the retained Nordic chunk inventory, reads the exact local normalized grid rows, and verifies that the current null-preserving publication projection equals every retained published feature. It then requires the static writer to preserve all selected published records exactly. The source manifest retains 628 high, 940 low, and 307 no-pollen-data features; every no-pollen estimate and standard-error field is null in the served publication and downloaded frames. No gaps are interpolated between source windows.

The signed synthetic native input is retained under the [native product manifest](reference/native-product/manifest.json)
with [display geometry](reference/display-geometry.json). The producer checks
their exact digests before rendering the current atlas and rechecks every
consumed input afterward. The native view identity remains
`c7276b4b90bd57750af6182cb65ae8674e349f332cc6f606bd23dcb19e13a6e8`;
the original product manifest is
`de45206119e4f2663fe1d24cb4b52a481f025fa8cf7561c5ac7a188c624c07e9`.
Source native units, missing values, and geometry refusals retain their
distinct meanings. This paired view has no posterior draw channel or draw
selector; the receipt records that absence.

## Actual browser result

The [browser verifier](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/frame-url-replay.mjs) passed at widths 1440 and 390, with zero runtime errors:

- 28 actual modeled GeoJSON downloads matched complete selected source cell-window records. Cases span the oldest and newest windows, Denmark and Finland filters, source land-cover type, source PFT `ISTS` with its unavailable definition, and exact-taxon metrics. Oldest full-country frame: 75 features, 48 no-pollen null records. The Denmark frame: six features, three null records. The Finland frame: 19 features, three null records. Newest full-country frame: 75 features, ten null records.
- 30 actual native JSON downloads matched the independently checked source view, complete selected rows, native units and DOM missingness. Selections include all 18 rows/four missing values, a regional subset with five rows/one missing value, a local zero-point Calendar BP window with eight rows/two missing values, and an explicit empty role selection. The fractional `[-0.25, 0.25]` and point `[0, 0]` windows retain their signed profile and exact view identity.
- 16 direct hash replays and 24 browser Back/Forward outcomes restored the complete frame/profile/selection and identical download bytes. Incoming hash transitions reinitialized the document once; no reload loop was observed.
- Two incompatible signed-profile URLs were visibly refused, retained their requested profile in the address, selected no native rows, and disabled download. Returning through browser history restored the valid empty selection and its exact export.

All modeled frames are labeled `context_only`, with interpolation and propagation disabled. The native outputs are synthetic exploratory views with `scientific_acceptance: not_evaluated` and `publication_authorized: false`. Accepted pollen propagation, posterior draw comparison, and a four-country accepted edge matrix are not asserted.

Twelve earlier atlas browser candidate producer regressions remain historical source checks. The current browser verifier passed with zero runtime errors; the receipt binds the input and served byte hashes.

## Original numerical source custody

The retained [request](reference/native-product/request.json) declares a synthetic,
exploratory calculation with seed 7, one deterministic REVEALS iteration and one
analytical LOVE repeat. Its [scientific manifest](reference/native-product/scientific_manifest.json)
names the Python/NumPy/SciPy backend, disqover 0.9.14 compatibility and engine
version `0.1.9.dev37`. These identities describe the retained calculation;
the atlas frame producer reuses its results.

All 24 retained reference files agree with their recorded SHA256 identities.
The 11 numerical CSV files also agree with the original product manifest and
the nested checksum lengths and hashes.
The retained primary means are:

| Retained stage | Native unit | Alnus | Betula |
| --- | --- | --- | --- |
| Regional REVEALS | percent | 60.0 | 40.0 |
| Local analytical LOVE | fraction | 0.9315214003755345 | 0.06847859962446534 |

The regional and local standard-deviation cells are empty for both taxa. Those
four missing statistics remain unavailable. Local `cover_q10.csv` and
`cover_q90.csv` are byte-identical to `cover_mean.csv` in this deterministic
one-repeat product; they do not establish a calibrated uncertainty interval.
Chronology, basin geometry, parameter domain, spatial model and PPE covariance
remain explicitly omitted uncertainty channels in the request.

The declared host version identifies reachable source revision
[`1f01c1bb8ff1d3d423f20202cfd72195ea6057d8`](https://github.com/bijux/bijux-pollenomics/tree/1f01c1bb8ff1d3d423f20202cfd72195ea6057d8).
At that revision, exact Git bodies independently match 92 of the product's
93 recorded code/resource SHA256 identities: 48 engine files, 43 host adapter
files and the host publication file `core/owned_tree.py`. The remaining engine
identity is the generated `_build_version.py`, recorded as
`d26d7669ad664274e59725c164db5c803b340331ecc29807dd255d2f9b20721f`;
its original bytes or an exact authenticated derivation remain unbound.

The original request also names `raw_snapshot.txt`, `chronology.txt`,
`geometry.txt`, `taxa.txt`, `parameters.txt`, `dependency_lock.txt` and
`decision.txt`. Their original hash-bound bodies remain unavailable at the
report product's declared relative paths; absence from every possible custody
location has not been established. The original numerical invocation and
terminal are also unbound. The source correspondence and retained results
therefore advance custody evidence while the original numerical-producer
criterion remains unresolved. A new calculation would carry its own execution
identity and could not retrospectively certify this product. Scientific
acceptance remains `not_evaluated`, with no empirical vegetation accuracy or
publication authorization established.

## Reproduction

From the repository root, use an absent destination below `artifacts/` and the retained product and geometry inputs:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.ci.atlas_browser.context_frame_candidate \
  --repository . --destination artifacts/atlas-frame-url-replay/replay-candidate \
  --native-product docs/report/atlas/frame-url-replay/reference/native-product \
  --native-geometry docs/report/atlas/frame-url-replay/reference/display-geometry.json \
  --product-manifest-sha256 de45206119e4f2663fe1d24cb4b52a481f025fa8cf7561c5ac7a188c624c07e9 \
  --geometry-sha256 52afc5687e5ab39b6cf3445cdefb12096be050938b12f3cc9436b3da51b761bd
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/frame-url-replay.mjs \
  artifacts/atlas-frame-url-replay/replay-candidate artifacts/atlas-frame-url-replay/replay-browser \
  '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
```

Candidate and browser output directories are disposable reproduction products. The receipt stores each download hash and source-supported selection. This report retains the signed synthetic product and request needed to render the browser candidate. The request names seven evidence text files by hash, but their original bytes are not retained here; the exact synthetic LRA computation cannot be rerun from this report alone.

## Scope

This result verifies populated modeled context and a signed synthetic native view through actual full-document, same-document URL and browser-history replay. It does not certify current real-data native LRA approval, posterior draw selection, full accessibility, performance, provider modes, deployment, or an accepted cross-border propagation edge. Those require separately admitted evidence and consumer checks.

## Source-owned retained capture

The published observations now come from the immutable [source-view capture](../source-files/capture.json) on source candidate `fa79ae6eff0f344b5a2dbff2cc858f92746c1f67`, using Chrome 155.0.8059.40. The packet retains original generation, verifier, served-file, screenshot and download identities. Six successful browser observations belonged to an aggregate run that also contained two failed probes; two separately recorded successful successor probes supply the provider and modeled-panel observations. Those failures remain part of the execution history.

These report files are reproduced by guarded retained transport and explicit metadata projection. That operation executes no browser, estimator or R program, and grants no scientific, source-rights, ecological or cross-browser acceptance. Earlier public file identities remain in the capture certificate. The direct browser commands above start separately qualified new observations.

For this owner's retained projection, use an absent output under `artifacts/`:

```sh
mkdir -p artifacts/atlas-source-views
python -m bijux_pollenomics_dev.source_completion.atlas_browser.capture_projection \
  --repository . \
  --receipt configs/ci/report-capture-projections/atlas-source-views/frame-url-replay-browser-verification.json \
  --output artifacts/atlas-source-views/frame-url-replay
```
