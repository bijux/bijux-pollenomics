# Published Table 1 and archived summer-green types

We checked the publisher's table directly against the pinned archive because
the two assign deciduous Quercus to different functional-type columns. We
retain both source versions and their differing claims.

The [publisher's machine-readable Table 1](https://essd.copernicus.org/articles/14/1581/2022/essd-14-1581-2022-t01.xlsx)
for Githumbi et al. (2022), *Earth System Science Data* 14, 1581–1619,
DOI [10.5194/essd-14-1581-2022](https://doi.org/10.5194/essd-14-1581-2022),
was downloaded on 28 September 2026. The 9,022-byte XLSX has SHA-256
`3e7579b3bb3db7a0fc194a9fbf2aacdbe56c6f5e8a24f22bdd4eed82221fa3e7`
and is retained in the external source-data store at
`landclim/publisher-paper/table-1.xlsx`. The article is CC BY 4.0. This
source is separate from the PANGAEA 937075 parameter CSV and output archive.

The XLSX first sheet has 31 taxon rows assigned to **12 PFT codes** and three
LCTs. Its nine `TBS` rows are Carpinus betulus, Carpinus orientalis, Castanea
sativa, Corylus avellana, Fagus sylvatica, Fraxinus, deciduous Quercus type,
Tilia and Ulmus. The `TBS` code begins at row 13 and continues through row 21;
rows 16, 18 and 19 contain Corylus, Fraxinus and deciduous Quercus. The table
contains no `ISTS` code. This independently confirms the paper's intended
nine-taxon TBS group, including deciduous Quercus.

The exact archived mean arithmetic differs: `TBS` contains six of those taxon
columns, while `ISTS` contains the three named above, across all 10,500
grid/window rows. The [numeric report](tbs-taxon-arithmetic/report.json) proves
that split for the pinned PANGAEA archive. The publisher table supplies no
archive-producing postprocessing source or version and no explanation for the
extra `ISTS` code. It therefore strengthens the paper/archive discrepancy;
it does not authorize relabeling `ISTS` or aggregating its standard errors by
sum.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Publisher Table 1 taxon/PFT assignments are checked against archived mean arithmetic.

**Unsupported claim.** An agreed biological deciduous-Quercus PFT classification across paper and archive.

**Actual verification performed.** Retained publisher XLSX and archived taxon arithmetic review are cited; index did not reread remote source.

**Remaining input or review.** Publisher Table 1 assigns deciduous Quercus to TBS while archived arithmetic places its mean in ISTS; the source-specific biological naming/producer route is unresolved. Resolver: LandClim table/archive source owner and qualified taxon reviewer Reopen when: Versioned Quercus concept crosswalk and archive transformation explain the two classifications.

**Cause category.** data|qualified review

**Consequence.** Preserve both published and archive claims without silently relabeling the output.

**Precise next acceptance route.** Versioned Quercus concept crosswalk and archive transformation explain the two classifications. Then update reports/science/publication-correspondence/pft-crosswalk/README.md.

**Negative or refused result.** Publisher assigns Quercus to TBS while archived mean split contributes it to ISTS.

**Matched denominator.** 31 parameter-table taxon rows; 12 PFT codes; nine paper TBS taxa with a three-taxon archived ISTS split.

Retained evidence: [reports/science/publication-correspondence/pft-crosswalk/tbs-taxon-arithmetic/report.json](tbs-taxon-arithmetic/report.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
