# LandClim II published-window correspondence

The retained Python REVEALS publication-profile output for author grids 512 and 562 is compared with the pinned PANGAEA 937075 June 2021 mean and standard-error members. The author bin labeled 225 spans 100–350 BP, exactly the published TW2 window. The 31 taxon axes use the authenticated author crosswalk; recomputed fractions are explicitly multiplied by 100 to match published percentage cover. All 62 grid/taxon keys and all mean/SE values pair without missing or extra keys.

- Grid 512: 6 author sites in this bin; maximum/median absolute mean residual 9.1979/0.0214 percentage points; maximum/median absolute SE residual 3.2162/0.0114 percentage points. Largest mean discrepancy: Cyperaceae; largest SE discrepancy: Cyperaceae.
- Grid 562: 5 author sites in this bin; maximum/median absolute mean residual 10.5527/0.0322 percentage points; maximum/median absolute SE residual 4.2581/0.0145 percentage points. Largest mean discrepancy: Calluna.vulgaris; largest SE discrepancy: Calluna.vulgaris.

These are candidate-minus-archive residuals, with no fitted or declared pass tolerance. Matching keys, bin bounds and units do not establish matching historical raw-input cohorts: the local author example uses the pinned 2016 source revision while the archive is a June 2021 published product. The other author bins differ from the published time bounds and are excluded. Functional-type columns, including the unresolved ISTS mapping, are excluded. This is a numerical published-product correspondence on one window, not whole-paper reproduction or measured vegetation accuracy.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Published-product versus released-author-example correspondence, not authenticated original input reconstruction.

**Supported claim.** The exact common 100–350 BP window pairs all 31 taxon mean/SE axes in two author grids against the pinned June 2021 PANGAEA modeled-product archive, with explicit fraction-to-percentage conversion and all residuals retained.

**Unsupported claim.** Paired keys/time support do not establish matching historical raw cohorts, other 24 windows, functional-type identity, statistical equivalence, whole-paper reproduction or independent measured vegetation accuracy.

**Actual verification performed.** The generated grid-level residual summary was checked against its machine report and row ledger. The retained correspondence has 62 mean and 62 SE pairs with no missing/extra keys and no pass tolerance. This qualification runs no LRA model, R program or numerical comparator.

**Remaining input or review.** Historical 2016 author versus 2021 archive source selection, count revisions, chronology, taxon/PFT transformation and intended-use decisions remain unresolved; the other 24 intervals have different bounds. Independent vegetation observations and qualified review are separate.

**Cause category.** data | comparability | assumption | qualified review

**Consequence.** Large candidate-minus-archive gaps are descriptive cross-revision model differences, not failed source-parity tests or independent field error. Their presence cannot be removed by matching taxon keys or normalizing output.

**Precise next acceptance route.** Authenticate a named historical source cohort/chronology/transformation for the shared window and replay it against the archive; retain all residuals and declare any later comparison criterion before inspecting new outcomes.

**Negative or refused result.** Maximum mean gaps 9.19787/10.55270 pp and SE gaps 3.21615/4.25814 pp remain. Twenty-four nonmatching intervals and unresolved PFT columns are excluded rather than silently matched; no pass tolerance is assigned to archive correspondence.

**Matched denominator.** TW2=[100,350)BP, two grids ×31 taxa =62 keys,62 mean+62 SE =124 values. Six author sites contribute in grid 512 and five in 562. This is one exact interval of 25, not the full 1,128-record study.

Qualified authored reader SHA-256: `2b4dfc764723667748dea2928635d7ba93c76d8d8efd39236ef9feced15d0074`.

- [Retained qualification evidence: docs/report/publication-replay/landclim-published-window-correspondence/report.json](report.json) (SHA-256 `0a22e51a8e109dbadbd713f27b84826421a0e156bdd9d97856a053a4eb0cee32`).

- [Retained qualification evidence: docs/report/publication-replay/landclim-published-window-correspondence/paper-correspondence.csv](paper-correspondence.csv) (SHA-256 `591b32c97d66ceb0884388e41e714f51fd51ff79a01ffc9dbd4ae697a75b91ee`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md) (source SHA-256 `ffcac6cb938189c61113cf92453c4ee1c79fcd9a69305d4bf15fec387bbca898`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
