# European pollen-productivity reference

Wieczorek, M. and Herzschuh, U. (2020), *Compilation of relative pollen
productivity (RPP) estimates and taxonomically harmonised RPP datasets for single
continents and Northern Hemisphere extratropics*, Earth System Science Data 12,
3515–3528. [Paper](https://doi.org/10.5194/essd-12-3515-2020);
[deposited dataset](https://doi.org/10.1594/PANGAEA.922661).
The paper and deposited data are licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
This attributed CSV extraction is a derived selection of the European columns.

[continental-europe.csv](continental-europe.csv) retains 55 source taxon rows
for each author dataset, including missing values. Each version contains 34
reported RPP estimates, 33 reported SE entries and 32 complete RPP/SE/fall-speed
triples. These counts describe table coverage, not independent study sites.
[source.json](source.json) records original filenames, URLs, exact hashes,
coverage and interpretation. Original workbooks and their readme are retained
in the configured shared pollen-productivity source directory; their public
URLs and hashes support exact retrieval without embedding raw workbooks here.

| Dataset | Betula RPP | Reported SE | n estimates | European Ulmus RPP / SE |
| --- | ---: | ---: | ---: | --- |
| v1 | 5.6725 | 0.33503914 | 8 | Missing / missing; n = 0 |
| v2 | 4.94 | 0.44296664 | 6 | Missing / missing; n = 0 |

Both deposited versions list fall speeds of 0.024 m/s for Betula and 0.032 m/s
for Ulmus. A fall speed alone does not supply pollen productivity. Blank values
remain missing; a zero count of source estimates is not zero productivity.
The CSV preserves original numeric strings, including binary64 decimal spellings,
original taxon spellings, worksheet names and per-field cell references. It does
not silently harmonise differences in source spelling between the two versions.

The separately attributed [LegacyVegetation 2025 tables](../legacyvegetation-2025/README.md)
provide additional original and synthesized parameter references. They preserve
their own uncertainty labels, duplicate rows and unresolved source discrepancies;
they do not replace this deposited compilation or form independent estimates
where the contributing studies overlap.

## Parameter use

Use these rows to compare published parameter sources and identify applicable
original studies. The reported SE describes the compiled mean and must retain
that identity. It is not automatically a between-study SD, and the combined
tables do not supply a cross-taxon covariance matrix. Selecting a Gaussian draw
scale from SE would be an explicit working assumption, not a recovery of a
population SD or calibrated field uncertainty.

The paper's Northern Hemisphere averages are intended for broad-scale
applications rather than site-specific vegetation composition. In particular,
its Northern Hemisphere Ulmus RPP comes from Chinese estimates; it cannot
silently fill the missing European entry. The original-study compilation
contains European Ulmus leads, but their model/reference/quality decisions must
be reviewed: the Kuneš et al. (2019) regional-model value is not in the selected
European combined set, and the chosen local-model row has no Ulmus estimate.

The current [Krageholm development calculation](../../../../reports/science/pollen-reconstruction/krageholm-regional-coupled/README.md)
retains LANDCLIM's separately attributed Betula 5.106 (SD label 0.303), Ulmus
1.27 (SD label 0.05), and original fall speeds. This reference intake supplies
new traceable parameter evidence; it does not replace those inputs or relabel
the completed numerical results. Physical basin admission, measured vegetation,
independent confirmation and qualified scientific review remain separate.

## Source consistency

The publisher's rounded Table 3 XLSX places 0.032 under the European Ulmus SE
column despite n = 0 and absent RPP. Both deposited workbooks put 0.032 in the
fall-speed column and leave Ulmus RPP/SE absent. The derived reference follows
the deposited cells and preserves the discrepancy in provenance.
