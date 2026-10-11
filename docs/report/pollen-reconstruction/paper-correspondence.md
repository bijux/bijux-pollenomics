# Paper correspondence interpretation

## Numerical result

The installed Python publication profile agrees with the independent author-R replay on 14,074 supported mean and standard-error values across the retained author examples. Maximum residuals are about 1.84e-13 for means and 7.16e-14 for standard errors in fractional units, inside the predeclared comparison tolerances. The implementation itself therefore does not explain the larger archive differences on the directly matched TW2 window.

For exact 100–350 BP support, the archived PANGAEA 937075 means differ from the author-R replay by maximum 9.19787 percentage points in grid 512 and 10.5527 in grid 562. Standard-error gaps are 3.21615 and 4.25814 points. The largest mean discrepancies are Cyperaceae and Calluna vulgaris. Each vector sums to 100 percent, and Python-to-R residuals are near 1e-11 points or smaller. These are product differences, not vegetation accuracy estimates. The archive and 2016 author example have not been shown to use identical historical source records.

The time-window axis has only one exact interval match out of 25: TW2, 100–350 BP. Most later author windows begin and end 50 years later than the corresponding PANGAEA windows; TW1 starts at -65 BP in the author axis and 0 BP in the published label. The direct numerical archive comparison therefore stays on TW2. No retrospective shift was applied to make the other rows appear comparable.

All 31 taxon mean ± one-SE envelopes overlap in each grid. That is a descriptive comparison of two reported uncertainty scales; dependence between versions and raw-input identity are unknown, so the overlap is not a significance test.

## Historical reproduction boundary

The retained Rootsi candidate closure has 79 unique publication-metadata candidates among 1,128 publication records, but zero authenticated historical primary-input records and zero reproduction-ready rows. I replayed the exact retained bytes for all 79 typed workbook candidates. The replay records 7,459 header positions, 5,170 mechanical data rows and the original sample-count claims; 78 claims agree with row counts, while EKE claims 25 and has 42 mechanical data rows. This verifies the structure of the retained candidate files. It does not verify their membership in a native LandClim archive or authenticate them as the published study inputs. No workbook output is cleared for public release, and scientific acceptance was not evaluated.

The paper's 12-PFT statement, PANGAEA's 11-PFT description and 13 archived PFT positions remain unreconciled. The [publisher's machine-readable Table 1](../publication-replay/landclim-pft-crosswalk/publisher-table-review.md) independently lists nine paper TBS taxa and no `ISTS` code. A separate [source-bound taxon arithmetic replay](../publication-replay/landclim-pft-crosswalk/README.md) shows that archived `ISTS` means equal the sum of three published taxon means (`Corylus.avellana`, `Fraxinus` and `Quercus.deciduous`) in all 10,500 grid/window rows. Archived `TBS` means equal the other six taxa listed under TBS in the parameter table. The maximum absolute split residual is about `1.02e-13` percentage points. The [private author-name review](../publication-replay/landclim-pft-crosswalk/author-name-review/report.json) supports seven of nine parameter-to-output names by exact author-crosswalk source names and an eighth, `Castanea sativa`, through the custody-bound author LUT's `Castanea` mapping. `Quercus deciduous t.` has no exact source-name row in either author file. This establishes version-specific mean arithmetic and bounded name evidence, not the biological definition of `ISTS`, an authenticated archived-release taxon transformation, an SE aggregation rule, or the historical paper's PFT count. Historical chronology choices, per-sequence rights, source revisions, basin/profile semantics and full-paper raw-input closure also remain open.

The [archived uncertainty-bound replay](../publication-replay/landclim-pft-crosswalk/uncertainty-bounds/report.json)
checks all 10,500 grid/window rows for each observed ET, ST, OL, ISTS and
TBS mean-addend group. Every aggregate SE lies between the lower and upper
standard-deviation bounds implied by its component SEs. There are 7,588 ET,
7,892 ST, 5,921 OL, 7,013 ISTS and 5,859 TBS rows with a nondegenerate
bound and a value strictly inside it. These necessary inequalities are
compatible with some covariance; they do not identify the archived covariance
or replay the paper's delta-method uncertainty.

The [paper's Sect. 3.2](https://essd.copernicus.org/articles/14/1581/2022/)
assigns deciduous Quercus type to TBS, whereas the archive's
`Quercus.deciduous` mean is an `ISTS` addend. This is a documented
paper-versus-archive classification difference, not a reason to silently
relabel the output. The same paper describes delta-method SE aggregation;
the observed mean sum cannot be applied to archived SE columns.

The [public author script lineage](../publication-replay/landclim-pft-crosswalk/author-release-lineage.md)
narrows this source gap. Its 31 taxon header names match the corresponding
archived mean header positions exactly, but the released scripts do not
produce the archive's 13 PFT and three LCT columns. An authenticated
archive-producing PFT/LCT transformation is still needed to interpret `ISTS`,
the Quercus assignment and aggregated uncertainty.

The next causal resolution needs the source owner to identify the historical raw sequence revisions and selected chronologies for a fully specified published row, then confirm taxon/count and PFT/ISTS transformations. The unresolved source-owner questions are summarized in `swedish-source-questions.csv`. No message was sent.

## HYDE modeled context

The [HYDE country result](../regions/nordic/hyde-country-cropland/README.md)
now retains 84 source-reported cropland quantities for Denmark, Finland,
Norway and Sweden across seven native CE labels and three scenarios. Its
[native grid check](../regions/nordic/hyde-country-cropland/grid-conservation/README.md)
reproduces all 84 country/year/scenario totals at seven selected CE labels
from the release's ISO and cropland ASCII grids with a maximum absolute
difference of about `8.50e-11` km², below the declared `1e-6` km² tolerance.
This establishes a bounded internal modeled-source correspondence. No
HYDE-assisted pollen model or independent vegetation validation has been
scored; release rights, formal
CRS and historical time support still require resolution.

## Repository evidence

- Author computation, archive-window differences, interval alignment and uncertainty envelopes: `paper-correspondence.csv`.
- Numerical implementation and comparison code: `packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/`.
- Archived PFT/LCT and ISTS/TBS mean arithmetic: `docs/report/publication-replay/landclim-pft-crosswalk/`.
- Rootsi source boundary and workbook replay summary: `docs/public/pollenomics-data/sources/landclim.md` and `swedish-source-questions.csv`.
- Independent vegetation review: `docs/public/pollenomics-data/sources/empd2-nfi-review.md` and `nordic-nfi-reference-access.md`.
- HYDE country totals and native grid reconciliation: `docs/report/regions/nordic/hyde-country-cropland/`; source limitations: `docs/public/pollenomics-data/sources/hyde.md`.
