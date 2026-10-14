# Nordic observed pollen on the 31 author taxonomy targets

The detailed source and score narrative is maintained in the
[root research report](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/denmark-finland-norway-author-pollen.md).
The [input manifest](input-manifest.json), [coverage ledger](coverage.csv),
[score table](scores.csv) and [governed report](report.json) remain at this
producer-owned path. This page preserves earlier website citations.

The ten prepared source products can be reproduced with the qualified
`bijux_pollenomics_dev.source_completion.nordic.author_target_preparation` CLI.
It consumes the retained 193-file author snapshot in its external source store
and the governed Neotoma/Swedish source inputs. The repository descriptor is
`configs/ci/qualified-report-sources/landclim-author-snapshot.json`.

Preparation binds the complete snapshot before reading and immediately before
publishing an absent destination beneath repository `artifacts/`. It preserves
the 31 author targets, 81 Nordic sites, 5,432 samples, 1,637 site bins and each
country's exclusion from its own training profiles. All nine compressed matrices
and the source input manifest belong to this preparation owner. Prediction and
scoring remain separate producers; preparation performs no prediction, model
fit or solver execution. Snapshot qualification authenticates custody and
identity; it grants neither source-use rights nor scientific admission.

```sh
python -m bijux_pollenomics_dev.source_completion.nordic.author_target_preparation \
  --repository "$REPOSITORY" \
  --source-root "$SOURCE_STORE" \
  --source-descriptor configs/ci/qualified-report-sources/landclim-author-snapshot.json \
  --output "$REPOSITORY/artifacts/author-target-preparation"
```


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Named Nordic source/development wrapper; its own source denominator remains separate from canonical study/account limits.

**Supported claim.** This reader retains the relationship to the31-author-target Nordic study and documents a separate source-snapshot preparation boundary; preparation writes ten source products without prediction or scoring.

**Unsupported claim.** Prepared custody does not establish source-use rights, LRA readiness, historical LandClim authenticity, measured vegetation skill or independent confirmation.

**Actual verification performed.** Read the citation/preparation body, current result, source input manifest and three compressed metadata products. Reconciled 81 sites, 5,432 samples and 1,637 candidate site bins with nine compressed output bindings plus the manifest. No preparation, prediction, scoring, fitting or source-acquisition consumer was rerun.

**Remaining input or review.** The external193-file author snapshot needs its qualified source route and scientific/rights review; prediction and scoring remain independently owned consumers.

**Cause category.** Source preparation boundary and retained study citation.

**Consequence.** A complete prepared matrix cannot be counted as another fit, score or scientifically admitted cohort.

**Precise next acceptance route.** Run the qualified author-target preparation against the exact external descriptor, then use separately frozen country-excluded prediction and scoring consumers for any computational reproduction.

**Negative or refused result.** All current scientific/source-rights refusals remain; preparation admits no target to LRA and evaluates no predictor.

**Matched denominator.** Preparation:31targets,81Nordic sites,5,432 samples,1,637 site bins and ten products (nine compressed matrices plus input manifest). These are not ten scientific experiments.

Qualified authored reader SHA-256: `cc17fa2a995961d6fd5703a4c156250fb85839e035ecfdcc4c1a60c764e21e3e`.

- [Retained qualification evidence: docs/report/regions/nordic/author-target-pollen/report.json](report.json) (SHA-256 `4a5845c1adc4cd510e396c4698963d7f1102db9f170713f7c5007e32dbe77db3`).

- [Retained qualification evidence: docs/report/regions/nordic/author-target-pollen/inputs/metadata-DK.json.gz](inputs/metadata-DK.json.gz) (SHA-256 `2f33131a93644d2c645cbc5cade1f9df75abd70d66386de50cdd8a12d2ed38a9`).

- [Retained qualification evidence: docs/report/regions/nordic/author-target-pollen/inputs/metadata-FI.json.gz](inputs/metadata-FI.json.gz) (SHA-256 `4f88132d091289e6fbc58215abf8f2a294b579ec1c0bb80d472841866e11e71c`).

- [Retained qualification evidence: docs/report/regions/nordic/author-target-pollen/inputs/metadata-NO.json.gz](inputs/metadata-NO.json.gz) (SHA-256 `f1a2f8d408cdfbd8c46bde9e1ca9f1bae5e1acb14881247fe62c62d4620b3371`).

- [Retained qualification evidence: docs/report/regions/nordic/author-target-pollen/input-manifest.json](input-manifest.json) (SHA-256 `86645e8d2f29f60c6c206cb9b594030e7ec01d6b568009eb1e6dec3fc3481500`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

- [Canonical scientific account: reports/science/nordic-pollen-study.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/nordic-pollen-study.md) (source SHA-256 `59626da8437e802b57d1d5bd397bbed003860dd870c114f2b4be7eaed43323f4`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
