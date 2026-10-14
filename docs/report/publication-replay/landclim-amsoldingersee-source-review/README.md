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

**Supported claim.** One named historical metadata row is compared with three current Neotoma pollen cores; the retained capture demonstrates a precise unrecovered historical identity rather than an admitted source match.

**Unsupported claim.** Equal sample count, approximate location, site name or NR workbook label does not authenticate historical count bytes, author age model, a legal redistribution decision, LRA reproduction or vegetation accuracy.

**Actual verification performed.** The authored review and retained candidate/source-hash report were inspected and bound. Its maintained reader authenticates 14 private inputs including 11 raw HTTP responses and two acquisition receipts. This qualification makes no new API request, model calculation, native R run or independent source authentication.

**Remaining input or review.** The E#69-to-core mapping, exact historical 23-sample count revision, author age-depth output, taxon-to-PFT transformation and sequence-specific source-use decision remain missing. Qualified historical and scientific review is required.

**Cause category.** data | comparability | access/rights | qualified review

**Consequence.** Keep the matching 23-sample candidate as a lead, not a closed historical input. The unresolved row stays in the full 1,128-row inventory; its three candidates are not three admitted historical cores.

**Precise next acceptance route.** Obtain an authenticated author or ALPADABA E#69 bridge, exact historical counts/chronology and transformation with an intended-use rights decision; replay that named row before extending to other publication rows.

**Negative or refused result.** No candidate response contains E#69. Dataset 3873 has 23 samples but zero chronology records; datasets 3874/3875 have 24/52 samples and radiocarbon-year information. None of the three candidates is reproduction-ready.

**Matched denominator.** One metadata row 1059 outside the 17 author examples; one current site 2973, three candidates 3873/3874/3875, 23/24/52 native sample IDs; 11 response bodies and 14 consumed private inputs; zero of three admitted candidates.

Qualified authored reader SHA-256: `ad0098d692f5a2d30a8447adc5e73a50984c9ca8e3b45be9f18ecdd0d085e2f0`.

- [Retained qualification evidence: docs/report/publication-replay/landclim-amsoldingersee-source-review/report.json](report.json) (SHA-256 `eb1d20e578c9bdbdb12ffbeab3eba87522cc98006de7c8919bac2bc29683d1a7`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md) (source SHA-256 `ffcac6cb938189c61113cf92453c4ee1c79fcd9a69305d4bf15fec387bbca898`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
