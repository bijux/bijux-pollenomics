# LandClim II author method and example input profile

The [method crosswalk](method_crosswalk.csv), [example input identities](example_inputs.csv), and [machine report](report.json) compare the retained author source with the named native LandClim II profile. The producer verifies the private author snapshot manifest and all 193 listed members by SHA-256, then checks the historical R function, wrapper, 17 raw and prepared example inputs, 31-taxon PPE and covariance axes, 25 time bins, and the [tracked two-grid comparison receipts](reference/report.json). The three compact comparison receipts are pinned by exact SHA-256 and retained beside this report so replay does not require a historical job directory. The private inputs remain external. Source redistribution rights remain uncleared.

The original wrapper calls the 30 October 2016 `REVEALS` release with GPM neutral, 3 m/s wind and 100,000 m regional extent. The retained native profile names the same source revision and parameters. The example spans grid 512 with nine sites and grid 562 with eight sites; all 17 site metadata rows use source model code 2 (lake). Each raw and prepared input has a private snapshot hash in the example ledger. The retained original-R receipt and native comparison report passed for these two grids. This report reads those receipts; it does not rerun either implementation or claim full-study reproduction.

The crosswalk marks the differences that matter when interpreting those results: missing site/bin support is masked in native inputs, while the original R function replaces `NA` values inside available matrices with zero; the source wrapper writes cover and SE in percent, while native run outputs use fractions; and the source multisite bootstrap does not propagate PPE covariance. The author example's 25 bins do not establish every historical chronology for the paper's 1,128 sequences. Both source and native retain the historical lake gamma expression's unresolved author comment.

## PFT classification remains blocked

The [paper](https://essd.copernicus.org/articles/14/1581/2022/) describes 12 PFTs; the [PANGAEA dataset description](https://doi.org/10.1594/PANGAEA.937075) describes 11. Their 2026-09-21 page bytes are now bound by the [provider-description custody](../../maintenance/artifact-retention/landclim-provider-description-custody.json); the capture does not identify the archive-producing grouping rule. The content-bound PANGAEA parameter CSV has 12 nonblank PFT codes for its 31 taxa. All 50 mean/SE CSV members in the pinned PANGAEA result archive share a header with **13 PFT-position columns** between the 31 taxa and three LCT columns. `ISTS` is present in the output headers and absent from that parameter table. Without the version-specific grouping and column crosswalk, none of 11, 12, or 13 is admitted as a universal classification count.

## Reproduce

From an installed development environment at the repository root, point to an intact external author snapshot and an absent output directory:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  -m bijux_pollenomics_dev.essd_reproduction.method_profile \
  --repository . \
  --private-root /path/to/landclim/author-reference \
  --output artifacts/jobs/landclim-method-profile/replay
```

The comparison refuses a changed snapshot member, original function signature, example grid membership, native method parameters, or PANGAEA table/output header. Whole-paper historical input identity, per-sequence rights, PFT classification, and independent measured-vegetation accuracy remain outside this two-grid result.

The focused test module runs its publisher-table and corrupted-snapshot checks in ordinary CI. To run all five checks, including private input identities and byte replay, set `BIJUX_LANDCLIM_AUTHOR_REFERENCE` to the external author snapshot directory:

```sh
BIJUX_LANDCLIM_AUTHOR_REFERENCE=/path/to/landclim/author-reference \
  PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/pytest -q \
  -o cache_dir=artifacts/jobs/landclim-method-profile/pytest-cache \
  --basetemp=artifacts/jobs/landclim-method-profile/pytest-private \
  packages/bijux-pollenomics-dev/tests/essd_reproduction/test_method_profile.py
```
