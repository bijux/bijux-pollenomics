# Reindeer author preprint Table S3

The [author bioRxiv supplement](https://www.biorxiv.org/content/10.1101/2023.09.21.558762v1.supplementary-material) labels its second spreadsheet `Table S3`. The workbook from the September 22, 2023 preprint is [retained in the governed source library](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/data/adna/governance/source_library/papers/10.1111-mec.17274/supplementary/author-preprint-table-s3.xlsx) (60,061 bytes; SHA-256 `fe4066aecc10fb4573613ac1641756c80503cb4bf41c7bf9a49ab25aa2ecfe97`). Its [receipt](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/data/adna/governance/source_library/papers/10.1111-mec.17274/supplementary/author-preprint-table-s3.xlsx.metadata.json) records the exact download URL, version and bioRxiv API's `cc_by` license declaration. This is an author preprint supplement; the separate [published Appendix S1 correspondence](reindeer-published-appendix.md) identifies its added rows and changed fields. Direct publisher byte parity for the user-supplied published archive remains unverified.

The workbook has one sheet. Rows 3–20 contain 18 distinct ancient specimen IDs, each matching exactly one ENA alias in the governed `PRJEB60484` sample master; rows 21–110 contain 90 modern specimens. The age-range column G agrees with all 18 admitted ancient intervals. `R20` (row 20) has `0–450 BP`, agreeing with the published primary article's Table 1 and the author preprint's Table 1. The later [Scientific Reports supplementary Table S1](https://doi.org/10.1038/s41598-024-54296-2) reports `41–252 BP` for its `R20*` row. For this archive project's sample chronology, the published primary article's wider interval is selected. The later narrower interval is retained as an alternative and is contained by the selected range. The canonical `225 BP` midpoint used by interval consumers is derived from 0–450; no source median is attributed to the primary article.

| Source fact | Workbook row | Current implication |
| --- | ---: | --- |
| `B20` collection area is `Edgeøya` | 5 | Source-backed island locality is admitted into the generated sample master and locality records; no point coordinate is inferred. |
| `R20` collection area is `Wijdfjorden`, age range `0–450 BP` | 20 | Confirms the selected primary-project interval; the secondary 41–252 BP range remains a distinct version. |
| `M68`, `R36`, `R25a`, `R29a`, `MB60`, `R20` have `NA` median | 15–20 | Do not attribute the medians in later secondary rows to the preprint. |

The workbook gives UTM easting and northing, but no UTM zone. It provides no source-qualified WGS84 point, so no coordinate is projected from these values. Its first-published field and 90 modern rows are source evidence, not additional ancient project samples. The governed producer checks the exact workbook bytes, receipt, 18 ancient IDs and their age intervals before using B20 row 5. The existing published PDF and secondary workbook remain separate source roles.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native DNA specimen/publication/chronology scope and unsupported ecological or pollen extension.

**Supported claim.** The preprint Table S3 source supports eighteen ancient reindeer interval/alias correspondences in its own revision.

**Unsupported claim.** A preprint is not byte-equivalent to the final appendix; unzoned UTM coordinates and derived midpoints are not source points or medians.

**Actual verification performed.** Read the supplement account against the retained published-appendix correspondence and current animal chronology account; no workbook reread or reprojection.

**Remaining input or review.** Final-publication revision correspondence, sample coordinates with CRS/zone, and missing source medians remain separately qualified questions.

**Cause category.** Source revisions and coordinate/date roles are not interchangeable.

**Consequence.** The primary R20 interval stays 0–450 BP and a 225 BP midpoint remains derived.

**Precise next acceptance route.** Retain each revision and obtain source-owned coordinate and final-table bindings before changing sample point/date fields.

**Negative or refused result.** B20 is locality-only; six ancient rows lack medians; 90 modern rows do not enlarge the ancient cohort.

**Matched denominator.** 18 ancient rows 3–20 versus 90 modern rows 21–110; all 18 primary intervals correspond, with R20 secondary 41–252 BP retained separately.

Qualified authored reader SHA-256: `1463fd6f3dc930d477fe78cd242543f5f1728b77cd4b5ae5ff74d848a3312bab`.

- [Retained qualification evidence: reports/science/reindeer-appendix-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/reindeer-appendix-correspondence.md) (SHA-256 `57d8dfbf72caf3741d04231feb20cd89b044a2e55661aefff0909ab5ddaa779a`).

- [Retained qualification evidence: reports/science/animal-sample-chronology.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-sample-chronology.md) (SHA-256 `0f4b689193ff2e872be0155dc77e48be083f917812248c6b29cb6b364c390545`).

- [Canonical scientific account: reports/science/reindeer-appendix-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/reindeer-appendix-correspondence.md) (source SHA-256 `57d8dfbf72caf3741d04231feb20cd89b044a2e55661aefff0909ab5ddaa779a`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
