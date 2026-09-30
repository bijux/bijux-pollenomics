# Our paper and archive correspondence decision

We asked whether the installed publication calculation, the released author
example and the archived paper product represent the same numerical result.
We compared the exact common window before interpreting any difference. We
found strong Python/R calculation correspondence on the retained example and
a real difference from the archived product. We keep source revision, PFT
meaning and historical input membership open below.

## Numerical result

We [reexecuted both released author grids](publication-correspondence/author-example-reexecution.md)
with the original R function and current native REVEALS implementation. We
compared the installed Python publication profile with the independent
author-R replay on 14,074 supported mean and standard-error values across the
retained examples. Maximum residuals are about 1.84e-13 for means and
7.16e-14 for standard errors in fractional units, inside our predeclared
tolerances. The installed calculation therefore does not explain the larger
archive differences on the directly matched TW2 window.

We [traced WHH05 from its released raw sample to the 1500 BP author-example
site estimate](publication-correspondence/author-example-site-replay.md): 301
raw grains become 297 prepared grains after four explicit source exclusions.
The 31 means and 31 standard errors agree between the independently executed
author R and native calculation to at most `4.77e-15` and `8.90e-16` in that
window. Across both example grids, 17 sites provide 184 supported site-windows
out of 425 possible. This is a bounded calculation witness; the archive's
historical site inputs and independent vegetation remain unresolved.

On exact 100–350 BP support, we found maximum archived PANGAEA 937075
mean differences from author-R of 9.19787 percentage points in grid 512
and 10.5527 in grid 562. Standard-error gaps are 3.21615 and 4.25814
points. The largest mean discrepancies are Cyperaceae and Calluna vulgaris.
Each vector sums to 100 percent; Python-to-R residuals are near 1e-11
points or smaller. We report product differences, not vegetation accuracy.
We have not established that the archive and 2016 author example used the
same historical source records.

We found one exact interval match among 25 time windows: TW2, 100–350 BP.
Most later author windows begin and end 50 years later than the corresponding
PANGAEA windows; TW1 starts at -65 BP in the author axis and 0 BP in the
published label. We restricted direct numerical archive comparison to TW2
and did not shift the other rows retrospectively to make them appear matched.

We found overlap between all 31 taxon mean ± one-SE envelopes in each grid.
We use that only to describe two reported uncertainty scales. Dependence
between versions and raw-input identity are unknown, so we do not call the
overlap a significance test.

## Historical reproduction boundary

We reproduced all 17 example `LRAready` files byte for byte from pinned
raw site files and formatter lookups in the
[released author raw-to-prepared replay](../../docs/report/source-relations/landclim/author-example-taxon-support/README.md):
871 raw sample rows and 15,028 matching prepared cells. We thereby closed
the formatting lineage of the retained two-grid example, including five
`WHH05` headers trimmed by R `read.csv`. We did not authenticate historical
Nordic archive input revisions or turn formatter-filled zeros into observed
taxon absences.

We retained 79 unique Rootsi publication-metadata candidates among 1,128
publication records, but authenticated zero historical primary-input records
and zero reproduction-ready rows. We replayed the exact retained bytes for
all 79 typed workbook candidates. The replay records 7,459 header positions,
5,170 mechanical data rows and the original sample-count claims; 78 claims
agree with row counts, while EKE claims 25 and has 42 mechanical data rows.
We verified the retained candidate file structures, not their membership in
a native LandClim archive or their role as published study inputs. We have
not cleared workbook output for public release or evaluated scientific
acceptance.

We have not reconciled the paper's 12-PFT statement, PANGAEA's 11-PFT
description and 13 archived PFT positions. We retained the two public prose
pages under exact 2026-09-21 [capture custody](../../docs/report/maintenance/artifact-retention/landclim-provider-description-custody.json).
The [publisher's machine-readable Table 1](publication-correspondence/pft-crosswalk/publisher-table-review.md)
lists nine paper TBS taxa and no `ISTS` code. In a separate
[source-bound taxon arithmetic replay](publication-correspondence/pft-crosswalk/README.md),
we found that archived `ISTS` means equal the sum of three published taxon
means (`Corylus.avellana`, `Fraxinus` and `Quercus.deciduous`) in all 10,500
grid/window rows. Archived `TBS` means equal the other six taxa listed under
TBS in the parameter table. The maximum absolute split residual is about
`1.02e-13` percentage points. Our [private author-name review](publication-correspondence/pft-crosswalk/author-name-review/report.json)
supports seven of nine parameter-to-output names by exact author-crosswalk
source names and an eighth, `Castanea sativa`, through the custody-bound
author LUT's `Castanea` mapping. `Quercus deciduous t.` has no exact
source-name row in either author file. We therefore claim version-specific
mean arithmetic and bounded name evidence. We do not claim a biological
definition of `ISTS`, an authenticated archived-release taxon
transformation, an SE aggregation rule or the historical paper's PFT count.
Historical chronology, per-sequence rights, source revisions, basin/profile
semantics and full-paper raw-input closure remain open.

We checked all 10,500 grid/window rows for each observed ET, ST, OL, ISTS
and TBS mean-addend group in our
[archived uncertainty-bound replay](publication-correspondence/pft-crosswalk/uncertainty-bounds/report.json).
Every aggregate SE lies between the lower and upper standard-deviation
bounds implied by its component SEs. There are 7,588 ET,
7,892 ST, 5,921 OL, 7,013 ISTS and 5,859 TBS rows with a nondegenerate
bound and a value strictly inside it. These necessary inequalities are
compatible with some covariance; we did not identify the archived covariance
or replay the paper's delta-method uncertainty.

We recorded that [the paper's Sect. 3.2](https://essd.copernicus.org/articles/14/1581/2022/)
assigns deciduous Quercus type to TBS while the archive's
`Quercus.deciduous` mean contributes to `ISTS`. We keep this
paper-versus-archive classification difference visible and do not relabel
the output. The paper describes delta-method SE aggregation; we do not
apply the observed mean sum to archived SE columns.

We narrowed this source gap with the
[public author script lineage](publication-correspondence/pft-crosswalk/author-release-lineage.md).
Its 31 taxon header names match the corresponding archived mean header
positions exactly, but the released scripts do not produce the archive's
13 PFT and three LCT columns. We still need an authenticated
archive-producing PFT/LCT transformation to interpret `ISTS`, the Quercus
assignment and aggregated uncertainty.

We need the source owner to identify historical raw sequence revisions and
selected chronologies for one fully specified published row, then confirm
taxon/count and PFT/ISTS transformations. We recorded questions about
matched Swedish cores and basins separately in `swedish-source-questions.csv`.

## Unsent publication source questions

We prepared the following local questions about PANGAEA 937075's June 2021
results and the author examples at `rmfyfe/landclimII` revision
`57ead2e2fcc493d099be4e5a3092fc396e1c3d3a`. We have not sent them.

1. Which source sequence revisions, selected sample ages and chronology
   decisions produced grid 512's published TW2 (100–350 BP) vector? The
   maximum author-R/archive gaps are 9.19787 percentage points for the mean
   and 3.21615 for the standard error, with Cyperaceae the largest mean gap.
   Which input rows and transformation account for them?
2. Which historical revisions and chronology decisions produced grid 562's
   TW2 vector? Its maximum mean and standard-error gaps are 10.5527 and
   4.25814 percentage points, with Calluna vulgaris largest for both.
3. Which boundary convention and chronology definition governs the other
   windows? Only TW2 has an exact interval match among 25 windows. Most later
   author intervals differ by 50 years at both bounds, and TW1 starts at
   −65 BP in the author axis versus 0 BP in the published label.
4. What publication-specific PFT list, `ISTS` definition and transformation
   generated the archive? The paper, deposit description and archived header
   expose 12, 11 and 13 PFT counts or positions respectively. The released
   taxon means show a three-taxon `ISTS` split from the paper's nine-taxon TBS
   group, including deciduous Quercus; its biological classification and
   uncertainty transformation remain unidentified.
5. Which authenticated workbook or archive members and per-sequence analytical
   terms belong to one fully specified published row? The 79 Rootsi metadata
   candidates among 1,128 publication records have verified workbook
   structure but no authenticated historical primary-input membership. The
   answer must bind chronology, taxon/count denominator, basin geometry and
   parameter-profile records for that row.

We matched the Python profile to the independent author-R replay within
the declared numerical tolerances. Our questions target source identity,
chronology and publication transformation, because we did not observe a
Python/R calculation failure on these source cases.

## HYDE modeled context

We retained 84 source-reported cropland quantities for Denmark, Finland,
Norway and Sweden across seven native CE labels and three scenarios in our
[HYDE country result](hyde-cropland-source-account.md). Our
[native grid check](../../docs/report/regions/nordic/hyde-country-cropland/grid-conservation/README.md)
reproduces all 84 country/year/scenario totals at seven selected CE labels
from the release's ISO and cropland ASCII grids. The maximum absolute
difference is about `8.50e-11` km², below our declared `1e-6` km² tolerance.
We claim bounded internal modeled-source correspondence. We have not scored
a HYDE-assisted pollen model or independent vegetation validation. Release
rights, formal CRS and historical time support still need resolution.

## Repository evidence

- Author computation, archive-window differences, interval alignment and uncertainty envelopes: `paper-correspondence.csv`.
- Numerical implementation and comparison code: `packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/`.
- Archived PFT/LCT and ISTS/TBS mean arithmetic: `reports/science/publication-correspondence/pft-crosswalk/`.
- Rootsi source boundary and workbook replay summary: `docs/public/pollenomics-data/sources/landclim.md` and `swedish-source-questions.csv`.
- Independent vegetation review: `docs/public/pollenomics-data/sources/empd2-nfi-review.md` and `nordic-nfi-reference-access.md`.
- HYDE country totals and native grid reconciliation: `docs/report/regions/nordic/hyde-country-cropland/`; source limitations: `docs/public/pollenomics-data/sources/hyde.md`.
