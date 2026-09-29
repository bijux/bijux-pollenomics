# Reindeer author preprint Table S3

The [author bioRxiv supplement](https://www.biorxiv.org/content/10.1101/2023.09.21.558762v1.supplementary-material) labels its second spreadsheet `Table S3`. The workbook from the September 22, 2023 preprint is retained in the private source store at `adna/prjeb60484/biorxiv-preprint-2023-09-22/table-s3.xlsx` (60,061 bytes; SHA-256 `fe4066aecc10fb4573613ac1641756c80503cb4bf41c7bf9a49ab25aa2ecfe97`). Its private `source-manifest.json` records the exact download URL and version. This is an author preprint supplement; identity with the [published Molecular Ecology Appendix S1](https://onlinelibrary.wiley.com/action/downloadSupplement?doi=10.1111%2Fmec.17274&file=mec17274-sup-0001-Appendix+S1.zip) is unverified.

The workbook has one sheet. Rows 3–20 contain 18 distinct ancient specimen IDs, each matching exactly one ENA alias in the governed `PRJEB60484` sample master; rows 21–110 contain 90 modern specimens. The age-range column G agrees with all 17 currently admitted ancient intervals. The remaining specimen, `R20` (row 20), has `0–450 BP`, agreeing with the published primary article's Table 1 and the author preprint's Table 1. The later [Scientific Reports supplementary Table S1](https://doi.org/10.1038/s41598-024-54296-2) reports `41–252 BP` for its `R20*` row. These are different source versions with a real age disagreement. The governed R20 chronology remains unresolved pending an explicit source-specific chronology decision; the newly found workbook does not make the later interval disappear.

| Source fact | Workbook row | Current implication |
| --- | ---: | --- |
| `B20` collection area is `Edgeøya` | 5 | More specific locality evidence than the current broad `E-Svalbard` Table 1 description; not yet admitted into generated locality records. |
| `R20` collection area is `Wijdfjorden`, age range `0–450 BP` | 20 | Confirms primary/preprint age version; no chronology selection made. |
| `M68`, `R36`, `R25a`, `R29a`, `MB60`, `R20` have `NA` median | 15–20 | Do not attribute the medians in later secondary rows to the preprint. |

The workbook gives UTM easting and northing, but no UTM zone. It provides no source-qualified WGS84 point, so no coordinate is projected from these values. Its first-published field and 90 modern rows are source evidence, not additional ancient project samples. The private workbook should be included in the governed source library only after its distribution rights and producer integration are resolved; the existing published PDF and secondary workbook remain separate source roles.
