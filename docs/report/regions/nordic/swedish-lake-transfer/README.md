# Three-lake Swedish observed-pollen transfer

Our research account at `reports/science/sweden-lake-transfer.md` explains
the decision, scores and limits. This governed page retains the
source-bound predictions, tables and reproduction commands.

The [locked protocol](protocol.json) selected Gilltjärnen, Lake Avegöl and Flinkasjön from Neotoma/EPD **using site, collection-unit, dataset and age metadata before target counts were read**. Each is one lake site with one source pollen dataset and one core. The source-default calibrated-age rule selects **268 of 273** samples; the five other source samples remain outside this study. The selected samples span **63 site by 500 BP bins**.

The [input manifest](input-manifest.json) binds the Neotoma relational snapshot, the authors' 10,788-row taxonomy lookup, the 31-target axis and the previously retained 81-site DK/FI/NO training profiles. Training excludes every Swedish target site. The predictor read only [training](inputs/training-SE.json.gz) and [target metadata](inputs/metadata-SE.json.gz); the separately retained [sealed outcomes](sealed-outcomes/outcomes-SE.json.gz) were opened only after the [predictions](predictions/predictions-SE.json.gz) and their [freeze receipt](prediction-freeze.json) had been committed at `135250049`.

The [producer at prediction freeze](reference/prediction-producer.py.txt) is
retained byte for byte from that commit, SHA-256
`3c4321f729c5ea4cc53172b3ebf0a22b782f0e873ae88ad67225b43a0ad01b62`.
Later style, typing and CLI-documentation edits changed the live producer's
file hash. The verifier authenticates the frozen prediction against the
retained producer bytes. We separately ran the current producer's prepare,
predict and score commands on the same source inputs: its input manifest,
three prepared files, prediction file and five score products all matched
their governed counterparts byte for byte. The prediction SHA-256 remained
`eb10b5e7225cef3c51b544c1a25cebc264d9b5ab10477d9c4216b83a38bad909`.

| Target lake | Selected samples | Scored bins | Native pollen NISP | Assigned to 31 targets | Author excluded | Unmapped |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Gilltjärnen | 100 | 23 | 59,073 | 57,697 | 1,374 | 2 |
| Lake Avegöl | 62 | 15 | 67,949 | 67,178 | 740 | 31 |
| Flinkasjön | 106 | 25 | 111,775 | 106,240 | 1,711 | 3,824 |
| **Total** | **268** | **63** | **238,797** | **231,115** | **3,825** | **3,857** |

All 63 bins received the three fixed baseline predictions and have positive assigned pollen counts, yielding **189 matched score rows** and zero training-support refusals. The [coverage](coverage.csv), [site scores](site-scores.csv), [all bin scores](scores.csv) and [taxon diagnostics](taxon-diagnostics.csv) retain their denominators.

| Fixed method | Equal-site mean absolute fraction error | Equal-site Hellinger distance |
| --- | ---: | ---: |
| Inverse distance squared | 0.017334 | 0.286757 |
| Nearest site | 0.017932 | 0.288872 |
| Training mean | 0.020682 | 0.333694 |

Inverse distance squared has the lowest three-site mean error in this declared comparison, but nearest site has the lower error at Lake Avegöl. Only three lake groups support the equal-site aggregate, and prior Nordic outcomes informed the fixed study design. This is **development evidence for direct observed-pollen subcomposition**, not a confirmatory estimate, LRA reconstruction, full-pollen or vegetation prediction, or a country-wide Swedish skill claim. Basin geometry, PPE, independent vegetation truth and unresolved source periods remain separate admission questions.

## Reproduce

From the repository root, with the retained external author-reference capsule:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_lake_transfer prepare \
  --repository . --author-source-root /path/to/landclim/author-reference \
  --output artifacts/jobs/swedish-lake-transfer/replay-prepared
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_lake_transfer predict \
  --prepared artifacts/jobs/swedish-lake-transfer/replay-prepared \
  --output artifacts/jobs/swedish-lake-transfer/replay-predictions
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_lake_transfer score \
  --prepared artifacts/jobs/swedish-lake-transfer/replay-prepared \
  --predictions docs/report/regions/nordic/swedish-lake-transfer/predictions \
  --output artifacts/jobs/swedish-lake-transfer/replay-scored
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/regions/nordic/swedish-lake-transfer/verify.py
```

The score command must use the committed prediction file. The [report manifest](manifest.json) binds retained evidence bytes, and `verify.py` checks the freeze, current Neotoma relational source identity, source denominator, score coverage and site-macro arithmetic. If that published source changes, this comparison requires a reviewed refresh before it can pass. The private author lookup is authenticated by digest and is not copied here.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Named Nordic source/development wrapper; its own source denominator remains separate from canonical study/account limits.

**Supported claim.** The retained three-lake development study chooses targets from metadata, freezes predictions before opening separate outcomes and compares three fixed observed-pollen predictors on the31-target count subcomposition.

**Unsupported claim.** Three source groups and prior Nordic design exposure do not establish independent confirmation, a Swedish population skill estimate, LRA vegetation reconstruction or measured ecological accuracy.

**Actual verification performed.** Read this reader's scientific narrative and its retained machine account and checked the physical evidence identity. This qualification reran no producer, predictor, numerical oracle, browser or source-acquisition consumer. A separate replay at commit 65d4752111915e1157315004d59603469af2d644 completed six maintained prepare, predict and score commands and two independent observers, all with exit 0. Common, inner and outer run results were 0. All ten native products per study family matched the retained bytes exactly. Only four preparation files per family receive retained source admission. Nine protocol, historical freeze, reference-text and verification files remain unresolved under their original study owners; no historical production or freeze certificate is inferred. Both protocols used the exact training-SE input. The original owner recipes incorrectly declared training-DK; those recipes and this correction remain explicit in the capsule and witness. The authored capsule preserves the original public source and controls and all 66,481 input identities. Runtime, private taxonomy lookup, relational inputs and 4,356 bytecode payloads remain omitted. The original generic outer receipt mentions EMPD2; its text is preserved, and the actual Swedish plan and eight command receipts establish the execution scope. These previously exposed direct-pollen development results do not establish untouched confirmation, ecological or field accuracy, vegetation truth, acquisition or reuse rights, human acceptance or LRA admission. Authoring the capsule is not a new native retention execution.

**Remaining input or review.** Basin/parameter/source-period decisions and independent vegetation truth remain separate; frozen historical producer identity must not be silently rewritten as current.

**Cause category.** Metadata-selected development transfer with historical freeze custody.

**Consequence.** Lowest aggregate error in these lakes does not establish uniform site superiority or justify outcome-selected changes to the fixed study.

**Precise next acceptance route.** Replay source preparation and the current predictor separately, score the exact committed frozen prediction and verify all matched numeric products before making a current-source correspondence claim.

**Negative or refused result.** Fiveof273source samples remain age-excluded; nearest site beatsIDWatLakeAvegöl despiteIDWhaving the lower three-site aggregate.

**Matched denominator.** Three lakes/cores,268of273samples,63bins,31targets and189score rows;238,797native NISP=231,115assigned+3,825excluded+3,857unmapped; equal-siteIDWMAE0.0173343.

Qualified authored reader SHA-256: `9f7aad3f21bb204744b3ecf9f29a7604e57f56bc82fe9afd84f7a723bceec6c6`.

- [Retained qualification evidence: docs/report/regions/nordic/swedish-lake-transfer/report.json](report.json) (SHA-256 `9e70b542d843466cbb2933a6d0c9cbb7c5c4ae6ddfc9fd4e8f8a73ab42d4789c`).

- [Retained qualification evidence: reports/science/source-lineage/swedish-direct-pollen-preparation.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-lineage/swedish-direct-pollen-preparation.json) (SHA-256 `a64dfad19cfc41eae4d4e6c810b2078076a2b3d3c2088fbe11dff6a024d095aa`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

- [Canonical scientific account: reports/science/nordic-pollen-study.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/nordic-pollen-study.md) (source SHA-256 `59626da8437e802b57d1d5bd397bbed003860dd870c114f2b4be7eaed43323f4`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
