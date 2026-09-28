# LandClim II PFT and LCT output crosswalk

The [column ledger](columns.csv), [LCT group ledger](lct_groups.csv), [25-window results](windows.csv), and [input-hash report](report.json) bind this review to the exact PANGAEA 937075 parameter CSV, mean/SE archive, and repository source receipt. The producer reads all 50 archived CSV members: 25 mean and 25 standard-error files, each with 420 grid rows and the same 50-column header. Mean and SE grid IDs match within each time window.

The parameter table names 12 PFT codes across 31 taxon rows. The archived outputs place 13 PFT codes between 31 taxon columns and three LCT columns. Twelve PFT codes match the parameter table by exact code. `ISTS` is the sole output code with no parameter-table definition or taxon assignment. The [paper](https://essd.copernicus.org/articles/14/1581/2022/) says 12 PFTs and the [PANGAEA description](https://doi.org/10.1594/PANGAEA.937075) says 11; those publisher prose pages are linked but their bytes are not retained in this review. **The 11/12/13 classification question and the meaning of `ISTS` remain unresolved.** An exact code match does not by itself authenticate a taxon-name transformation or a historical grouping version.

## Admitted output arithmetic

For all **10,500 mean grid/window rows**, the archived LCT values agree within the declared absolute tolerance of `1e-9` with these sums of the archived PFT columns:

| LCT | Published mean columns whose sum matches |
| --- | --- |
| ET | TBE1 + TBE2 + IBE + MTBE + TSE + MTSE |
| ST | IBS + **ISTS** + TBS + TSD |
| OL | LSE + GL + AL |

The maximum absolute residual is below `2e-13` for each LCT. The parameter table's ST block lists IBS, TBS and TSD; the output's ST mean includes the additional `ISTS` column numerically. This is an observed property of this archived output version, not an admission of `ISTS` taxonomy or of the paper's PFT count.

Standard errors must be handled separately. A naive sum of constituent PFT standard-error columns differs from the LCT standard error in 7,588 ET rows, 7,892 ST rows, and 5,921 OL rows. The source files do not provide a complete LCT covariance or aggregation lineage here, so this review does not infer an SE formula or allow SEs to be pooled by the mean formula.

## Reproduce

From the repository root with the development package available, choose an absent output directory:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  -m bijux_pollenomics_dev.essd_reproduction.pft_crosswalk \
  --repository . \
  --output artifacts/jobs/landclim-pft-crosswalk/replay
```

The producer refuses changed input hashes, a missing or duplicated window, mismatched mean/SE grid identities, changed table/output code sets, or a mean arithmetic disagreement beyond the declared tolerance. No private author input or historical R execution is used.
