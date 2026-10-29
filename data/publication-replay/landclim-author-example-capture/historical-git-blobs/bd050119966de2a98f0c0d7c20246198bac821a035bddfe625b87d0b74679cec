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

**Supported claim.** The installed publication profile agrees within predeclared tolerances with an exact author-R replay on the retained 17-site two-grid example, preserving available support, missing masks and fractional mean/SE units.

**Unsupported claim.** This is not historical 1,128-input reconstruction, agreement with the PANGAEA published estimates, a resolved PFT transformation, independent measured vegetation accuracy or native R certification of new scenarios.

**Actual verification performed.** The narrative explains the row-level ledger, retained receipt and independent reexecution; its report/CSV/manifest bytes were inspected. All 14,074 retained mean/SE values pass the original mean 1e-11+1e-10 relative and SE 5e-8+1e-9 relative criteria. This qualification runs no R, native REVEALS or new numerical comparison.

**Remaining input or review.** Historical count/chronology revisions, complete paper cohort, source-use rights and the 11/12/13 PFT/ISTS discrepancy remain open; the author and archive time axes have only one exact shared interval. Independent measured vegetation and external review remain separate.

**Cause category.** data | comparability | assumption | qualified review

**Consequence.** Use numerical parity as a control for this prepared source example. Missing site/bins remain unavailable, not observed zero; shared author inputs and code lineage do not become independent ecological evidence.

**Precise next acceptance route.** Authenticate a named historical grid/window production snapshot and taxon/PFT transformation, then compare that exact source closure. Preserve the existing two-grid tolerance/missing-mask evidence and qualify any new measured-target or release claim separately.

**Negative or refused result.** No missing/extra keys among supported comparisons; the unavailable site-bins and seven unsupported regional bins in grid 512 remain excluded. Archive modeled-product differences and unresolved functional-type semantics are not removed by source-example parity.

**Matched denominator.** 17 sites: grid 512 has nine, grid 562 eight; 25 bins/31 taxa. Available site-bins are 97/225 and 87/200; regional support 18/25 and 25/25. The 14,074 paired mean/SE values have maximum residuals 1.83881e-13/7.15331e-14 fraction. Two examples are not 1,128 authenticated historical records.

Qualified authored reader SHA-256: `8a9c336a3b951739a97a01982ea94e5a4159d11514e0c531f0884f48481634cf`.

- [Retained qualification evidence: docs/report/publication-replay/landclim-author-example-correspondence/report.json](report.json) (SHA-256 `a9bbb131a8094a2c0b1efaa83b6afba09f3f59f6e20257934d73a470de36fc9f`).

- [Retained qualification evidence: docs/report/publication-replay/landclim-author-example-correspondence/paper-correspondence.csv](paper-correspondence.csv) (SHA-256 `9c574919c250b9fe386154b72266869b290365ee9afe5d8a270250ed01c211d8`).

- [Retained qualification evidence: docs/report/publication-replay/landclim-author-example-correspondence/manifest.json](manifest.json) (SHA-256 `da0c47d31334b3789d856a0b7e624b57f5bd85231201e9fbb97c955856259793`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md) (source SHA-256 `ffcac6cb938189c61113cf92453c4ee1c79fcd9a69305d4bf15fec387bbca898`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
