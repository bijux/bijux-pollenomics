# ESSD LandClim author-example correspondence

The installed LRA publication profile was recomputed on the retained author inputs and compared cell by cell with an independent exact author-R replay. The source revision is `57ead2e2fcc493d099be4e5a3092fc396e1c3d3a`. Values are fractional cover and fractional standard error.

Across 17 site examples in grids 512 and 562, 14,074 supported mean/SE values have zero missing or extra keys. The maximum absolute mean residual is 1.83881e-13; the maximum absolute SE residual is 7.15331e-14. All pass the source comparison's prospective mean (`atol=1e-11`, `rtol=1e-10`) and SE (`atol=5e-8`, `rtol=1e-9`) tolerances. The CSV gives each reference value, recomputed value, signed residual, and status; the JSON gives per-site and regional maximum/median residuals and support counts.

This checks two author examples, not the 1,128-row historical reconstruction or the PANGAEA published estimate table. The source bins retain their documented 50 BP difference from the paper, and 12-PFT paper / 11-description dataset / populated ISTS output semantics remain unresolved. No independent measured vegetation accuracy is evaluated.
