# EMBSeCBIO source and fixed-model reconstruction

The supplied EMBSeCBIO files contain usable scientific evidence. Reading's 2017 release provides 1,380 sample metadata and categorical reconstruction rows. Reading's separate 2021 release provides 301,197 pollen records in 15 tables. After exact native-ID and strict metadata comparisons, 430 of the earlier rows qualify for a declared raw-count proof of concept. These are current-source candidates; corrected later data do not establish the original historical count bytes.

The publisher-cited 2022 method repository also contains a saved biome model, curated pollen percentages, extracted potential-vegetation labels and original comparison tables. We executed the published saved-model equation for all 5,765 released samples and all 242 model taxa. Independent scalar Python and native base R agree on every sample's predicted class and all 103,770 distance/score cells. This supplies concrete numerical reconstruction of the fixed model, with the input assumptions below.

## What the model calculates

For each biome `b`, the published calculation is:

```text
distance_b = sqrt(sum_t(((percentage_t - mean_bt) / (sample_sd_bt + 0.5))^2))
score_b = exp(-distance_b / 100)
```

The mean and sample standard deviation come directly from the saved `Train_dataset.csv`. The input is the published percentage value, without new renormalization. Source-absent model taxa receive zero under the declared source-compatible fill assumption. No ambiguous duplicate sample/taxon values or unsupported positive taxa were accepted. Prediction chooses the largest score, using the published class order `TUND, DESE, GRAM, XSHB, ENWD, WTSFS, CENF, CMIX, TEDE` for exact sample ties.

Adding 0.5 percentage points avoids division by a zero standard deviation. It does not represent measured error or a confidence interval. The equation contains a diagonal standardized distance, not estimated cross-taxon covariance. Scores are unnormalized exponential distances. They do not describe calibrated probabilities, continuous vegetation cover or pollen transport. This categorical biome calculation does not execute the Landscape Reconstruction Algorithm.

## Actual numerical verification

Native R 4.6 evaluates the equation independently of Python's `math.fsum` implementation. All 103,770 cells passed the previously fixed tolerances: distance absolute `1e-10` plus relative `1e-12`, score absolute `1e-13` plus relative `1e-12`; predictions matched exactly. Maximum absolute differences were `8.526512829121202e-14` for distance and `3.3306690738754696e-16` for score.

The first aggregate run is retained as failed. Its full Python calculation exited 0, while R's attempted Latin1-to-C-locale conversion produced invalid-input/EOF warnings and a finite-value refusal before the formula. The native-reader successor changed only the reader: original source bytes travel unchanged, with an ASCII preflight for native IDs, taxa, percentages and coordinates. Entity-name byte strings use a bijective Latin1 transport convention; this is not a claim that the original mixed byte strings are correctly encoded or repaired Unicode identities. The successful Python output was authenticated and reused. No source values, selection, equation, labels or tolerances were changed to obtain agreement.

The successor exited 0 in 2.227854 seconds. Its terminal receipt records unchanged custody for all 14,245 frozen source/runtime members, no process survivors and peak aggregate memory 275,415,040 bytes. This is an actual macOS Python 3.11/base-R 4.6 calculation. It does not reproduce the original R 4.0.2 package installation or stochastic training sequence.

## Categorical map diagnostics

These diagnostics compare predicted classes with released potential-natural-vegetation map labels. Entities are grouped by literal source entity-name byte tokens; the complete-cohort mode chooses the lexicographically first class when counts tie. This newly declared grouping differs from the published stochastic choice of one sample per location. Grouping by a name token does not authenticate a physical site or core.

| Complete declared population | Source samples | Eligible map-label samples | Entity-name groups | Dominant matches | Dominant or subdominant matches |
| --- | ---: | ---: | ---: | ---: | ---: |
| All curated samples | 5,765 | 5,521 | 5,297 | 3,445 / 5,297 (65.04%) | 3,956 / 5,297 (74.68%) |
| Published EMB coordinate window, `28 < latitude < 49.25`, `20 < longitude < 62` | 1,395 | 1,277 | 1,055 | 641 / 1,055 (60.76%) | 766 / 1,055 (72.61%) |
| Northern-Europe coordinate screen, `54 <= latitude <= 72`, `-25 <= longitude <= 32` | 946 | 878 | 878 | 586 / 878 (66.74%) | 682 / 878 (77.68%) |

Missing/unrecognized dominant labels and invalid coordinates account for the sample exclusions; every original sample and exclusion remains in the full derived report. The northern-Europe screen is a coordinate subset, not an authenticated Nordic country/core population or an independent accuracy experiment.

The source metric excludes entities whose prediction or dominant map class is TUND or CENF. Applying that same class rule changes the all-cohort denominator from 5,297 to 4,412, and the EMB denominator from 1,055 to 1,053. In the northern screen it removes 639 of 878 entities, leaving 239: dominant agreement becomes 191/239 (79.92%), composite agreement 200/239 (83.68%). These conditional fractions must retain the excluded 639 and cannot replace the broad 878-entity result.

The [PNV reference](https://zenodo.org/records/3631254) is itself a model of potential vegetation using climate, relief and compiled reference data, including Biome6000k, with a 2000–2017 reference period. Its categorical labels are not independent field measurements. Compatible native training IDs are now retained by the model-regeneration consumer below. Their exact historical identity and the evaluation exposure still require separate assessment; these map-label diagnostics do not establish untouched confirmation or independently measured vegetation accuracy.

## Original paper results remain separate

The original dominant table contains 917 cells in total with 570 diagonal matches (62.159%). The original composite table contains 917 with 679 matches (74.046%). The original subdominant table contains 565 with 113 matches (20%). Our complete EMB comparison contains 1,055 entities for dominant/composite and 659 with eligible subdominant labels. Every differing complete-cohort matrix cell is retained. The original MLmetrics function constructs `table(y_true, y_pred)`: source matrices use reference rows and prediction columns. The original comparison explicitly assumed the reversed orientation; that report is retained and a comparison-only corrected successor preserves the successful numerical evidence. Primary [MLmetrics implementation](https://github.com/yanyachen/MLmetrics/blob/83a403cc86da496c057f987847a3a05235c22b1a/R/Classification.R#L61-L64) and independently recalculated saved balanced accuracy both support the correction.


The saved EMB metric percentages use a different denominator from the full exported matrices. The source metric removes TUND/CENF predictions or dominant labels: removing two diagonal-zero entities leaves 915, giving dominant `570/915 = 62.29508%` and composite `679/915 = 74.20765%`. These saved percentages must not be described as the `570/917` or `679/917` full-matrix trace fractions. The independently checked source metric arithmetic does not recover the selected entity IDs.

The pinned source gives seed 2501 and the location-selection code. A finite native R consumer now executed eight declared compatibility scenarios, reusing the authenticated per-sample predictions. All four `RNGversion("4.0.2")` scenarios using Rejection sampling reproduced every cell of the original dominant, composite and subdominant tables in their correct reference-row/prediction-column orientation. Both C and en_US.UTF-8 collations and both current/legacy dplyr collation options were actually available and agreed. The four `RNGversion("3.5.0")` Rounding scenarios differed and remain retained negative outcomes.

The source procedure selected 4,398 unique coordinate locations globally, then retained 4,204 samples with nonmissing dominant labels. The strict EMB window contains 917 selected samples/entities. This gives exactly the original 917/570 dominant, 917/679 composite and 565/113 subdominant populations/diagonal counts. Removing the source's two TUND/CENF entities reproduces the original 915-denominator metrics: dominant accuracy 62.2950819672%, balanced accuracy 64.2197942775%; composite accuracy 74.2076502732%, balanced accuracy 77.3391474453%. The actual native consumer exited 0 in 3.820813 seconds, with unchanged custody for 14,236 frozen members and no survivors.

This is exact table-cell and metric reproduction under an explicitly declared current R 4.6/dplyr 1.2.1 source-seed compatibility scenario. This location-selection consumer does not authenticate the original R 4.0.2 installation/package custody. The separate archived-source training consumer below regenerates all published mean/SD parameters under declared compatibility profiles, with the actual random-state sequence and compatible training IDs retained. Complete raw-count-to-curated-percentage/PFT transformations remain a separate source consumer. The complete-cohort diagnostics above remain distinct from this recovered original-selection account.

The [2017 paper](https://onlinelibrary.wiley.com/doi/abs/10.1111/jbi.13128) describes 1,387 modern samples and 1,107 entities; the deposited CSVs contain 1,380/1,099. Literal map agreement in the CSVs is 255/586 for known EVM pairs and 209/1,033 for known FGAM pairs. These diagnostics retain their own denominators rather than adopting the paper's approximately 44% Europe or 33% overall as reproduced results. A source longitude of `27858333` and age `-336` relative to 1950 CE remain unresolved source defects.

## Sources, rights and remaining work

The user's two 2017 CSVs were independently byte-matched to official [Reading DOI 109](https://researchdata.reading.ac.uk/109/) downloads. The original ZIP's three members were checked against the supplied extracted files. The 2021 raw database was obtained from [Reading DOI 309](https://researchdata.reading.ac.uk/309/). Each deposit's own README states CC BY 4.0; later corrected records remain a distinct release.

The [publisher-cited model repository](https://github.com/esmeraldacs/Intra_biome_variation_method) was acquired at exact Git SHA `28949b77fb0e63035d6b80a5eadea1b3e868e30a`. All seven saved-model assets were checked against the pinned Git blob identities and lengths. Its tree contains no license file. The deposit licenses do not automatically settle redistribution of transformed combined EMB/SMPDS inputs or author code. Current analysis keeps source bytes private and records their identities; any public redistribution requires the precise source-use decision.

The next concrete consumers are an explicitly new raw-count/taxonomy reconstruction on the 430 qualified rows and a training/evaluation exposure assessment using the now-retained compatible training IDs. Neither permits invented measurements, chronology, basin radii, source permissions, reviewer answers or seed histories. Qualified scientific review, independent vegetation observations and untouched confirmation remain open. The accompanying review packet is prepared and unsent.

Independent numerical review separately checked 38 source vectors at Decimal precision 50 (684 outputs per language), all 103,770 R/Python cells, exact sample predictions, source-byte critical fields, cohort/modal arithmetic and original matrix/metric denominators. Its accepted scope excludes historical cohort, ecological calibration, source authority and qualified external endorsement. The review also retains 1,163 zero-SD model cells offset by 0.5, score sums approximately 2.04–8.42, 14 non-ASCII opaque entity tokens, two entity tokens spanning multiple coordinate pairs and 21 all-cohort/20 EMB mode ties resolved by the declared lexicographic rule. These observations reinforce the interpretation and identity limits above.

## Maintained publication

The maintained Python producer recomputes the saved equation, every native-R numerical comparison, complete-cohort categorical-map diagnostics and all original matrices on the retained source-seed selection. It consumes the exact private nine-file source capsule and its separately pinned snapshot manifest. The compact raw-source audit is a retained actual native capture; this producer does not claim to rescan all raw tables during each publication. Failed numerical/reader/publication predecessors and explicit compatibility counter-scenarios retain their own outcomes.

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.pollen_reconstruction.embsecbio_biome.publication \
  --repository . --source-root /path/to/private-scientific-source-store \
  --output artifacts/jobs/embsecbio-reconstruction/source-products
```

The current source-store parent must contain `embsecbio/published-biome-model-training`, with the independently pinned 17-file snapshot. The original `embsecbio/published-biome-model` nine-file snapshot remains separately preserved. Qualification establishes the exact input byte population, not redistribution permission or ecological approval. Generated products contain compact derived summaries, with private source vectors and native sample selections retained outside the product repository. Source-use rights, exact original runtime/training-ID identity, ecological and external-review limits remain visible alongside the parameter-regeneration result.

Two disjoint actual maintained publication writers completed source/model/refusal tests (13 passed), then reproduced all four compact products byte for byte. Their current candidate source/physical runtime custody remained unchanged. This publication replay is separate from the retained independent native mathematical capture and source-seed compatibility consumer.


## Published model training regeneration

The supplied modern percentages and PNV lookup also support regeneration of the published training model. Both declared archived-source Rejection compatibility profiles reproduce all 4,356 published mean/sample-standard-deviation cells, with maximum absolute difference below 1e-13. The native R capture uses archived themis constructor/prep/bake functions and recipes factor/constructor functions under current R 4.6. A fixed single-Dominant-column adapter replaces nonnumerical recipe selector dispatch; it preserves the actual source RNG force order. These are explicit compatibility profiles, rather than identification of the author's exact installed environment.

The original procedure selects 4,204 eligible location samples, downsamples to 970 samples with class target 113, and draws 678 training samples using the unchanged named seed 2468 and 70% per-class sampling. The commented seed 124 stays inactive. Default constructor draws produce identifier `downsample_R5Yuv` and seed 49714 in the Rejection profile. Native training IDs and parameter outputs remain in the qualified external source store. The published model is not substituted for the regenerated statistics.

Both older Rounding profiles retain 2,060 model-parameter mismatches, with maximum absolute difference about 9.63. The independent Python source-statistic consumer agrees with the native R mean and sample SD for every cell in all four scenarios. Negative profiles and the initial supervised startup failure are preserved alongside the successful successor.

The maintained `training-reconstruction.json` product recomputes the statistics directly from the admitted native sample IDs and original percentage values, compares the captured native and published parameters, and retains the four original profile scopes and numerical results. It does not rerun R sampling or install archived packages during report publication. The original nine-file fixed-model source snapshot remains preserved; the training publication uses a separately identified combined snapshot with those exact bytes and eight added native CSV inputs.

This establishes model-parameter regeneration under the declared assumptions. Original full runtime identity and original historical training-ID custody remain separate. Training/evaluation exposure should now be measured from the retained IDs; strict untouched confirmation and independent vegetation accuracy are not established by matching the saved model. PNV remains a model-derived reference, and source/code redistribution authority and external scientific review remain unresolved.
