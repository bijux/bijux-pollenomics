# Amsoldingersee publication-input source review

LandClim II metadata row 1059 identifies `Amsoldingersee`, source code `E#69`,
23 pollen samples, and an author chronology. The row lies outside the 17
author-prepared examples. Its `NR` restriction label is a workbook value, not a
per-dataset redistribution decision.

The [source-bound report](report.json) replays a 21 September 2026 Neotoma API
capture from private source custody. Site 2973 has three current pollen
datasets: 3873 (`AMSOPO1`, 23 sample IDs), 3874 (`AMSOPO2`, 24), and 3875
(`AMSOPO3`, 52). Dataset 3873 matches the workbook sample **count** but its
chronology response has zero records. The other two return radiocarbon-year
age information. None of the three dataset, download or chronology responses
contains `E#69`. A site-name, coordinate or sample-count match cannot identify
the paper's historical core, count revision or age model.

**One selected publication row remains unrecovered; zero of three candidate
cores is reproduction-ready.** The missing inputs are an author or ALPADABA
`E#69`-to-core mapping, the exact historical 23-sample count revision, the
author age-depth output, and the taxon-to-PFT transformation. No R input,
vegetation accuracy or source-use permission is inferred from this review.
The [full 1,128-row inventory](../landclim-study-inputs/README.md) retains the
broader denominator; this review resolves the refusal evidence for one row
without changing its admission status.

The [source-input manifest](https://github.com/bijux/bijux-pollenomics/blob/main/data/landclim/review/amsoldingersee-source-inputs.json)
binds the 11 consumed raw API responses, their two acquisition receipts and
the selected publication row. Historical run plans, logs and a superseded
public-note check are not inputs to this source decision.

To replay into an absent artifact directory with the private source store:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.landclim_amsoldingersee_recovery \
  --repository . \
  --source-root /path/to/private/landclim/amsoldingersee-source-review \
  --output artifacts/jobs/landclim-amsoldingersee-source-review/replay
```

The producer checks all 14 consumed private files against the source manifest, all 11
HTTP response hashes and status records, the exact author example metadata,
and the observed candidate fields before writing the report. The raw API
responses remain outside the repository.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Published-product versus released-author-example correspondence, not authenticated original input reconstruction.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md) (source SHA-256 `ffcac6cb938189c61113cf92453c4ee1c79fcd9a69305d4bf15fec387bbca898`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
