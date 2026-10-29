# LandClim II author-example correspondence

The [row-level ledger](paper-correspondence.csv), [generated report](REPORT.md), and [numerical summary](report.json) compare the installed LRA publication profile with an independent exact author-R replay on the 17 author sites in grids 512 and 562. All 14,074 supported fractional cover and standard-error values pass the declared source tolerances. Maximum absolute residuals are 1.83881e-13 for means and 7.15331e-14 for standard errors. The 25-bin source profile has unavailable site-bins, which the report counts separately.

The [source and output manifest](manifest.json) records the producer and the original retained run. The original CSV was newline-normalized for the repository; the generated Markdown and JSON retain their original bytes. The current producer writes LF line endings directly. Replaying from the retained original candidate and author-R reference reproduces all three governed files byte for byte. An [independent R/native execution](../landclim-example-reexecution/README.md) produced the same row-level CSV and generated Markdown. Its JSON differs only in the reference receipt digest because that R execution has a new receipt.

Replay the governed correspondence from the original candidate and author-R reference retained in the private source store:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.author_example_correspondence \
  --run ../bijux-pollenomics-data/landclim/two-grid-process/run/run001 \
  --reference ../bijux-pollenomics-data/landclim/author-reference/reference \
  --output artifacts/jobs/author-example-correspondence/replay
```

This is two author grids, not the complete historical paper input set or a vegetation validation.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Published-product versus released-author-example correspondence, not authenticated original input reconstruction.

**Supported claim.** The released author-R/current-source-Python two-grid calculation agrees on every supported mean/SE cell within original tolerances; original source support and raw missing-value representations are retained.

**Unsupported claim.** This is not historical 1,128-input reconstruction, agreement with the PANGAEA published estimates, a resolved PFT transformation, independent measured vegetation accuracy or native R certification of new scenarios.

**Actual verification performed.** The original author R and current source Python stages genuinely completed on commit e282e08d796528488b438edd3ea661fb94b97b5d. Their original third-observer refusal and whole-job exit1 remain unchanged. The complete saved-source observer on 2784d4eae839e4a4e43f80ec77fd26bd0172aff0 passed; the separate maintained correspondence writer on e1ca9def55e7cd3e68ac6f20270059e743373251 returned0, while its original observer and aggregate returned1. The corrected saved-ledger observer genuinely passed with terminal 71d5f761f80e074d30fb1b13c4c0d53a3d34c86f9d5fa3dfa9e045bfb1ffbf45, rejoining every one of 14,074 ordered mean/SE cells to original R/current Python and the complete source support. Published reexecution report SHA256 4deb4e836c9ef8b81d5c29809bc2df7aed4d9dadef208f1cd866466e17d8b99f; ledger SHA256 1380633da596cfa0a51ec94ef885a7e94eecc617e37d78d0ed7c4f22121f5029. All184 available and241 unavailable site-bins remain source-bound. Original R off-support zero placeholders remain excluded; Python off-support values remain missing. Original mean/SE tolerances,1000 exact shared bootstrap draws and all17 source sites remain retained. Historical9dd1 raw proof is unavailable and is not used. No new math is executed for publication and no full1128study, independent vegetation, Nordic, source-rights, human or official release acceptance is asserted. Actual numerical calls used current source modules. Legacy raw installed-LRA wording and installed_lra column vocabulary do not establish installed-distribution execution, and independent installed-distribution receipts are not used as this run's numerical proof. This website reading route executes no numerical producer.

**Remaining input or review.** Historical count/chronology revisions, complete paper cohort, source-use rights and the 11/12/13 PFT/ISTS discrepancy remain open; the author and archive time axes have only one exact shared interval. Independent measured vegetation and external review remain separate.

**Cause category.** data | comparability | assumption | qualified review

**Consequence.** Use numerical parity as a control for this prepared source example. Missing site/bins remain unavailable, not observed zero; shared author inputs and code lineage do not become independent ecological evidence.

**Precise next acceptance route.** Authenticate a named historical grid/window production snapshot and taxon/PFT transformation, then compare that exact source closure. Preserve the existing two-grid tolerance/missing-mask evidence and qualify any new measured-target or release claim separately.

**Negative or refused result.** Original numerical whole1 and earlier observer1 remain literal; later saved-source and saved-ledger observers passed separately. Source-unavailable R zero placeholders and Python missing values are excluded, never observations. No full study, measured vegetation, rights, human or official release acceptance.

**Matched denominator.** 17 sites in2 grids:9+8,25bins,31taxa;184/425 supported site-bins,241 missing;43/50 supported regional bins;14,074 supported mean/SE pairs,77 original R CSVs,1000 exact shared bootstrap draws.

- [Retained qualification evidence: docs/report/publication-replay/landclim-author-example-correspondence/report.json](report.json) (SHA-256 `efcfce2e75ea4c98367e22bd8f0d4d28e123776b52436bef2e966f615f4b16bc`).

- [Retained qualification evidence: docs/report/publication-replay/landclim-author-example-correspondence/paper-correspondence.csv](paper-correspondence.csv) (SHA-256 `1380633da596cfa0a51ec94ef885a7e94eecc617e37d78d0ed7c4f22121f5029`).

- [Retained qualification evidence: docs/report/publication-replay/landclim-author-example-correspondence/manifest.json](manifest.json) (SHA-256 `ac3b206e20bbf8a2eda6382a5efc0f78b6a7d87c7851233adb4a28504550fcef`).

- [Retained qualification evidence: reports/science/publication-correspondence/author-grid-retained-source.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence/author-grid-retained-source.json) (SHA-256 `550701277e3e1b6a5146751cab32a731b98f31d54cd6666a762c83310f592919`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
