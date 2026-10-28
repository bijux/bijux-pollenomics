# ESSD LandClim author-example correspondence

The installed LRA publication profile was recomputed on the retained author inputs and compared cell by cell with an independent exact author-R replay. The source revision is `57ead2e2fcc493d099be4e5a3092fc396e1c3d3a`. Values are fractional cover and fractional standard error.

Across 17 site examples in grids 512 and 562, 14,074 supported mean/SE values have zero missing or extra keys. The maximum absolute mean residual is 1.83881e-13; the maximum absolute SE residual is 7.15331e-14. All pass the source comparison's prospective mean (`atol=1e-11`, `rtol=1e-10`) and SE (`atol=5e-8`, `rtol=1e-9`) tolerances. The CSV gives each reference value, recomputed value, signed residual, and status; the JSON gives per-site and regional maximum/median residuals and support counts.

This checks two author examples, not the 1,128-row historical reconstruction or the PANGAEA published estimate table. The source bins retain their documented 50 BP difference from the paper, and 12-PFT paper / 11-description dataset / populated ISTS output semantics remain unresolved. No independent measured vegetation accuracy is evaluated.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Published-product versus released-author-example correspondence, not authenticated original input reconstruction.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
