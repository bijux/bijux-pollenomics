# Tibetanus point-age sensitivity

Two existing point-age sequences give different conditional pollen-based cover estimates when the same Tibetanus counts are pooled into the same time windows. This is a new reconstruction sensitivity analysis, separate from historical LandClim reproduction and from validating either chronology.

The analysis uses all 45 retained pollen samples for Neotoma site 28860, collection unit 39229 and dataset 53980. The first sequence is the recorded calibrated point ages of default chronology 38408. The alternative transfers the actual Arctic supplement Tibetanus TP ages at 45 uniquely matching sample depths, with a maximum permitted depth difference of 10⁻⁸ cm. It does not interpolate, refit laboratory controls, substitute a publication year for BP zero, or alter the original chronology. The source's 1995 collection-year surface control remains distinct from the sampled points.

The [2014 Arctic database article](https://cp.copernicus.org/articles/10/1605/2014/cp-10-1605-2014.pdf) defines Table 1's dates relative to AD 1950. Its rounded Tibetanus endpoints of 39 and 10,238 years agree with the supplement's actual TP extrema of 39.4 and 10,237.5. This supports a scoped AD 1950 interpretation of those source points; endpoint agreement does not establish calibration, age-model identity or chronological accuracy. Neotoma documents analysis-unit depths in centimetres in [section 12.2](https://open.neotomadb.org/manual/sample-related-tables-1.html).

The four parameter maps, integer pollen counts, sparse-zero and partition hypotheses, PPE values, fall speeds, and physical response factors remain those of the [Swedish parameter-transfer account](../swedish-parameter-transfer-scenarios/README.md). The reused baseline response assumes a static 100 m basin radius, 100 km regional extent and wind of 3 m/s. No new physical quadrature was needed. Conditional cover closes the mapped counts divided by their PPE and response factors; its denominator is the mapped taxon panel, not all reported pollen or measured vegetation area.

Twelve of the 45 age points change time-window membership. Both sequences retain all 45 samples without exclusion and occupy the same 23 windows, with changed pooled counts in 16 windows. All 43,851 reported pollen grains remain accounted for. The full occupied-window union is retained; this is not a census of all 25 possible windows.

| Parameter assumptions | Mapped / reported pollen NISP | Largest absolute cover change | Taxon and window |
| --- | ---: | ---: | --- |
| Literal parameter labels | 12,259 / 43,851 | 22.768 percentage points | Pinus sylvestris, 7,200–7,700 cal BP |
| Major parameter transfers | 38,384 / 43,851 | 15.618 percentage points | Pinus sylvestris, 7,200–7,700 cal BP |
| Shared birch PPE | 42,275 / 43,851 | 14.404 percentage points | Pinus sylvestris, 7,200–7,700 cal BP |
| Large-grass cereal proxy | 42,275 / 43,851 | 14.404 percentage points | Pinus sylvestris, 7,200–7,700 cal BP |

Each maximum is an alternative-minus-native decrease in conditional cover. Shared-birch and large-grass assumptions use the same Tibetanus transfer map and parameters, so they give identical Tibetanus results; no additional large-grass transfer applies in this core. Their effects in other cores remain separate.

The native-age branch exactly reproduced the original 92 baseline windows across the four maps: counts, cover, standard errors, counting covariance, assumed PPE covariance and total conditional covariance. The completed capture contains eight cases and 184 window results. Native execution exited zero in 25.688 seconds, within its declared 768 MiB limit at 396,115,968 bytes peak RSS; all 9,318 frozen source/runtime members remained unchanged and no owned processes survived. This establishes the finite execution and original-baseline comparison. A separate [read-only source/output review](execution/actual-source-output-review.json) checked all 92 native baseline windows against the original capture, all eight case memberships and 184 private support hashes, the count-window changes, and the identical shared-birch/large-grass Tibetanus results. This is source and saved-output verification; it does not supply an independent numerical oracle, refit the chronology or establish accuracy.

Two earlier source-comparison captures exited one: the first rejected the census status because it expected the wrong acceptance label; the second reached comparison but failed while encoding mixed numeric and text cell keys. Their exact native refusal records are retained. These are capture-control failures, not negative reconstruction fits. The corrected typed-cell source comparison and the eight chronology cases exited zero. No scientific case or sample was silently omitted.

Both age sequences remain point scenarios with unknown sample-age error bounds. Counting and assumed PPE delta standard errors do not include chronology uncertainty, taxonomy, basin-history uncertainty or ecological model discrepancy. A zero plug-in standard error at a zero observed or hypothesized count is not an interval establishing absence. Larger estimated cover changes do not identify which chronology is more accurate. Historical LandClim selection/preparation, taxonomic and sparse-zero assumptions, measured vegetation accuracy, and raw-source redistribution rights remain unresolved.

The [assumptions](assumptions/protocol.json), [aggregate report](report.json) and [exact native capture](execution/native-capture.json) belong to this account. Individual sample/depth/age associations and actual source-label masks remain in the separately retained local support capsule; they are not published as raw observations here.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-bound conditional reconstruction or exposed pollen development wrapper; own source assumptions and exact scored/refused populations must be preserved alongside account links.

**Supported claim.** The same 45 Tibetanus sample counts yield different conditional mapped-panel cover when native points versus depth-matched Arctic TP points allocate counts to the same declared windows. This is a source-bound point-age scenario sensitivity, not chronology validation.

**Unsupported claim.** Calibration or chronological accuracy of TP ages, a full 25-window source census, measured vegetation change/accuracy, historical LandClim identity or chronology uncertainty coverage from conditional counting/PPE SEs.

**Actual verification performed.** The reader, protocol and actual capture/source-output review were inspected. Retained native execution exits 0 for 8 cases/184 results, exactly reproducing 92 native-age baseline windows; later source/output review checks memberships, support hashes and changed pooled windows. It is explicitly not an independent numerical oracle, and this qualification reruns nothing.

**Remaining input or review.** Both scenarios have unknown sample-age error bounds. AD 1950 interpretation of TP endpoints is scoped source evidence, not calibration or age-model identity. Taxonomic/sparse-zero/partition assumptions, static 100 m geometry, historical selection, ecological validity and raw-source redistribution rights remain open.

**Cause category.** data | assumption | comparability | access/rights | qualified review

**Consequence.** Interpret cover differences within each mapped parameter panel, not as measured landscape change or proof of a better age model. Point scenarios and conditional delta SEs omit chronology, taxonomy, basin history and model discrepancy.

**Precise next acceptance route.** Qualify TP/native chronology and joint age uncertainties for the named sample support, preserve the full declared source window domain separately, and obtain authentic historical preparation or independent vegetation measurements for those stronger claims. Retain distinct taxon/sparse-zero and rights decisions.

**Negative or refused result.** 12/45 points migrate windows and 16/23 occupied windows change pooled counts. All 45 samples remain. Largest literal-map Pinus decrease is 22.768 percentage points; shared-birch and large-grass Tibetanus mappings are identical. Two earlier source-comparison failures were capture-control failures, not failed reconstruction cases.

**Matched denominator.** 45 samples,4 parameter maps ×2 age scenarios =8 cases,23 occupied windows each and 184 results; all 43,851 reported grains accounted for. Native baseline 92 windows are matched exactly. Literal/major/shared-birch/large-grass mapped totals are 12,259/38,384/42,275/42,275 of 43,851; occupied-window union is not all 25 possible windows.

Qualified authored reader SHA-256: `cdcd82af2bb123833cb37f6d20619cfaa08a74b4d0e97892d636577f668cb47d`.

- [Retained qualification evidence: docs/report/pollen-reconstruction/tibetanus-point-age-sensitivity/report.json](report.json) (SHA-256 `5abb9af22673ec7e93fb38642b2d5f7958bd002218a5edd4514e11ffa093e5fe`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/tibetanus-point-age-sensitivity/assumptions/protocol.json](assumptions/protocol.json) (SHA-256 `3943070ee7076b042279a8f0c4d534c4de0cf72cb05c2001379ae78ff86bb586`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/tibetanus-point-age-sensitivity/execution/native-capture.json](execution/native-capture.json) (SHA-256 `cb8111b4ee4d660a2633e967cf561af551a69ed5838df045af8dab87f90e0c0f`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/tibetanus-point-age-sensitivity/execution/actual-source-output-review.json](execution/actual-source-output-review.json) (SHA-256 `2625f8ce8d37f520db3078f925cbdf549273f8dd7065bb6bd28025426d19af8f`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
