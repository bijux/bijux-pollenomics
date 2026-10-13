# Abborrtjärnen Rootsi and Neotoma source correspondence

The retained private `rootsi/ABB.xls` workbook has the same **107 numeric
sample-depth labels** as Neotoma/EPD dataset `19913`. Across **67 exact
shared taxon strings**, **2,183/2,183 explicit NISP count pairs** match,
representing 130,163 source count units in those explicit pairs. This matched
mass includes the source labels in the comparison and is not the declared
observed-pollen denominator. Another
**4,986** workbook positions have no Neotoma observation row; all workbook
values there are zero, but a missing Neotoma row is kept distinct from an
observed zero. The workbook and Neotoma each contain 94 taxon labels; 27
labels on each side do not match exactly. The [governed report](report.json)
retains the denominators and source hashes without copying the private
workbook or sample-level table into the repository.

The workbook's age labels **do not** numerically reproduce the Neotoma
sample-owned calibrated-BP ages: workbook minus Neotoma ranges from **-238
to +129**, and none of the 107 numbers is exactly equal. The workbook header
does not state an age unit or model. The separate author
[ABBO radiocarbon-control comparison](../abbo-age-controls/README.md)
validates six Neotoma control dates against PANGAEA, while the
[pollen-profile comparison](../abbo-profile/README.md) matches the Neotoma
pollen trajectory to a published ABBO profile. Neither result identifies
the Rootsi workbook's selected age model or resolves its historical-input
status, rights or sample-age uncertainty.

The separate [LandClim metadata core lead](../abbo-core-identity/README.md)
retains the source point, reported radius and differing chronology end labels
without transferring them to the Neotoma pollen core.

The workbook source is retained externally as
`landclim/rootsi-workbooks/rootsi/ABB.xls`, SHA-256
`205e7f77adde19b2c590d222acdd526d472e76ac22d0b8f27f7728acf451fa49`.
The [source-custody review](../../rootsi-landclim-overlap/README.md)
records its manifest. Historical basin geometry and a complete reviewed
taxon/PPE/count denominator remain unresolved. **No ABBO LRA sample is
admitted.**

Reproduce from the repository root into an absent local output directory:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.abborrtjarne_native_counts \
  --workbook ../bijux-pollenomics-data/landclim/rootsi-workbooks/rootsi/ABB.xls \
  --raw-part data/neotoma/raw/neotoma_pollen_dataset_downloads/part-004.json \
  --output artifacts/jobs/abbo-native-correspondence-replay
```

Compare its `report.json` with the governed report here. Keep the per-sample
CSV in the local run area while workbook reuse rights remain unresolved.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/abborrtjarnen-source-method.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/abborrtjarnen-source-method.md) (source SHA-256 `264420c81e18a6ee56b0b612e657f881fa26829a9cc060114d69b15d2491120f`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
