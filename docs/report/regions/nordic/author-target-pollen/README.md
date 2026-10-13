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

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

- [Canonical scientific account: reports/science/nordic-pollen-study.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/nordic-pollen-study.md) (source SHA-256 `59626da8437e802b57d1d5bd397bbed003860dd870c114f2b4be7eaed43323f4`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
