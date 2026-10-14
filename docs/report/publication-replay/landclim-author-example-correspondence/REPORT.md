# ESSD LandClim author-example correspondence

The installed LRA publication profile was recomputed on the retained author inputs and compared cell by cell with an independent exact author-R replay. The source revision is `57ead2e2fcc493d099be4e5a3092fc396e1c3d3a`. Values are fractional cover and fractional standard error.

Across 17 site examples in grids 512 and 562, 14,074 supported mean/SE values have zero missing or extra keys. The maximum absolute mean residual is 1.83881e-13; the maximum absolute SE residual is 7.15331e-14. All pass the source comparison's prospective mean (`atol=1e-11`, `rtol=1e-10`) and SE (`atol=5e-8`, `rtol=1e-9`) tolerances. The CSV gives each reference value, recomputed value, signed residual, and status; the JSON gives per-site and regional maximum/median residuals and support counts.

This checks two author examples, not the 1,128-row historical reconstruction or the PANGAEA published estimate table. The source bins retain their documented 50 BP difference from the paper, and 12-PFT paper / 11-description dataset / populated ISTS output semantics remain unresolved. No independent measured vegetation accuracy is evaluated.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Published-product versus released-author-example correspondence, not authenticated original input reconstruction.

**Supported claim.** The installed publication profile agrees within predeclared tolerances with an exact author-R replay on the retained 17-site two-grid example, preserving available support, missing masks and fractional mean/SE units.

**Unsupported claim.** This is not historical 1,128-input reconstruction, agreement with the PANGAEA published estimates, a resolved PFT transformation, independent measured vegetation accuracy or native R certification of new scenarios.

**Actual verification performed.** The generated summary and exact report/CSV were inspected, including supported keys and declared tolerance outcomes. All 14,074 retained mean/SE values pass the original mean 1e-11+1e-10 relative and SE 5e-8+1e-9 relative criteria. This qualification runs no R, native REVEALS or new numerical comparison.

**Remaining input or review.** Historical count/chronology revisions, complete paper cohort, source-use rights and the 11/12/13 PFT/ISTS discrepancy remain open; the author and archive time axes have only one exact shared interval. Independent measured vegetation and external review remain separate.

**Cause category.** data | comparability | assumption | qualified review

**Consequence.** Use numerical parity as a control for this prepared source example. Missing site/bins remain unavailable, not observed zero; shared author inputs and code lineage do not become independent ecological evidence.

**Precise next acceptance route.** Authenticate a named historical grid/window production snapshot and taxon/PFT transformation, then compare that exact source closure. Preserve the existing two-grid tolerance/missing-mask evidence and qualify any new measured-target or release claim separately.

**Negative or refused result.** No missing/extra keys among supported comparisons; the unavailable site-bins and seven unsupported regional bins in grid 512 remain excluded. Archive modeled-product differences and unresolved functional-type semantics are not removed by source-example parity.

**Matched denominator.** 17 sites: grid 512 has nine, grid 562 eight; 25 bins/31 taxa. Available site-bins are 97/225 and 87/200; regional support 18/25 and 25/25. The 14,074 paired mean/SE values have maximum residuals 1.83881e-13/7.15331e-14 fraction. Two examples are not 1,128 authenticated historical records.

Qualified authored reader SHA-256: `07565129d2d5aac5de919cc822997e2c79419c2585b66c600f158f9411fb57ef`.

- [Retained qualification evidence: docs/report/publication-replay/landclim-author-example-correspondence/report.json](report.json) (SHA-256 `a9bbb131a8094a2c0b1efaa83b6afba09f3f59f6e20257934d73a470de36fc9f`).

- [Retained qualification evidence: docs/report/publication-replay/landclim-author-example-correspondence/paper-correspondence.csv](paper-correspondence.csv) (SHA-256 `9c574919c250b9fe386154b72266869b290365ee9afe5d8a270250ed01c211d8`).

- [Retained qualification evidence: docs/report/publication-replay/landclim-author-example-correspondence/manifest.json](manifest.json) (SHA-256 `da0c47d31334b3789d856a0b7e624b57f5bd85231201e9fbb97c955856259793`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md) (source SHA-256 `ffcac6cb938189c61113cf92453c4ee1c79fcd9a69305d4bf15fec387bbca898`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
