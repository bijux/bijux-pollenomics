# Rootsi and LandClim II candidate overlap

The [row ledger](overlap.csv) binds 79 unique Rootsi metadata candidates to 79 of the 223 normalized LandClim II site features. It uses the five byte-identical derived candidate files retained in `data/landclim/review/rootsi-candidate-inputs/`, the published LandClim II site metadata workbook and receipt, and the normalized site consumer. [report.json](report.json) records their exact input hashes, denominators, the matching profile, and the dependency boundary. Regenerate with `python -m bijux_pollenomics_dev.source_completion.rootsi_landclim_overlap --repository . --output <absent-repository-directory>` using the repository's development package environment. The replay requires the tracked review copy and its fixed manifest and file hashes. The private typed workbooks are not part of this copy.

The 79 typed workbooks are retained under `landclim/rootsi-workbooks/` in the
external source data store, outside the product repository. Its
`manifest.json` has SHA-256
`dde88290dbdeca7a1047db74d5fb55a85c03a68daaef53795c5da9c1aebbd510`;
it binds 79 workbook members totaling **4,466,176 bytes** to the captured
archive hash
`f64d4dd411bc92362c9db2701c919063c2432e53fa523052e602da5f1a86183c`.
Every member name and SHA-256 matches this report's 79-row ledger. This
source-store custody supersedes dependence on disposable local run artifacts
for these workbook bytes. It does not authenticate the workbooks as the
historical inputs or clear their analytical reuse rights.

The original `rootsi.7z` archive is separately retained at
`landclim/rootsi-workbooks/original/rootsi.7z` in the same private store. The
[intake custody review](../source-intake-custody/README.md) verifies its
509,919 original bytes against the historical receipt; this does not promote
the receipt's sample claims to admitted counts.

The join is a **metadata candidate overlap**. Each row carries its Rootsi typed-workbook member and hash claim, source and publication locators, sequence labels, sample counts, access marker, chronology label, and the consumer's site feature ID. It does not authenticate the historical workbook as the LandClim input or identify historical pollen cells. Across the 79 candidates, 78 Rootsi sample-count claims agree with the LandClim publication metadata. EKE differs: Rootsi claims 25 and LandClim reports 42. This review does not settle the historical input denominator or equivalence.

The LandClim site time bounds are **sequence coverage**, not sample ages or change events. Thirty-five site features have numeric coverage intervals. Thirty-six have negative BP source bounds and eight have partial source bounds; their normalized numeric intervals are refused. The ledger keeps the source Top/Bottom BP labels alongside the refusal reason. The chronology basis text is a source label, not an authenticated sample chronology.

A [source-byte-bound age-column audit](../landclim/workbook-chronology/README.md)
checks FLINK, HOLK, RANV and STAV directly. It preserves one source-age reversal
in each of FLINK and HOLK and confirms that RANV and STAV have no workbook
sample-age column. The [Neotoma chronology witness](../landclim/neotoma-chronology-witness/README.md)
then depth-matches FLINK and STAV to shared EPD records, resolving the location
of FLINK's sign discrepancy and identifying an STAV candidate age vector.
Neither comparison establishes a qualified historical LandClim age model.

The LandClim II DOI, sequence ID, country, access marker, sample count, site window count, and source workbook provenance must match before a row is emitted. `LCGRID_ID` is retained as site metadata. It does not prove that a specific Rootsi workbook or site contributed to a particular modeled grid cell, time window, value, or standard error. That contributor lineage remains unresolved.

These candidate dependencies block treating LandClim REVEALS outputs as independent vegetation ground truth for the matched Rootsi inputs. Per-sequence rights, historical input identity, source-age basis, taxonomy, count denominator, and exact grid/window contribution remain unresolved. This review does not certify complete V2-DATA-007 grid/window/value/SE lineage or admit raw Rootsi observations for scientific use.

## Gilltjärnen source question

The [published LandClim II metadata](https://doi.pangaea.de/10.1594/PANGAEA.937075), workbook `LANDCLIMII metadata file` row 994, describes `GIL` as a lake at 60.083333° N, **15.083333° E**, with `siteradius` **169 m**, 101 pollen samples, 24 time windows, eight radiocarbon dates for its model, and an `Authors chronology` label. The workbook's explanation sheet explicitly defines `siteradius` in metres. The overlap ledger's `24` is `site_window_count`, not a radius. Neotoma site 28866 instead places its `GILL` core at 60.08333° N, **15.83333° E**, and has 101 source samples. The 0.75° longitude disagreement is approximately 42 km at this latitude, far beyond the 169 m reported radius. Equal sample counts and similar sequence names cannot resolve that conflict. [Antonsson et al. (2006)](https://doi.org/10.1002/jqs.1004) identifies a radiocarbon-dated Gilltjärnen pollen record, but its accessible abstract does not bind these two database coordinates, the two core handles, or a time-specific basin outline.

**Question for the source holder:** Which coordinate is correct for the physical `GIL`/`GILL` sediment core, does the LandClim `GIL` input contain the same 101 counted samples as Neotoma dataset 53991, and what evidence binds the reported 169 m modern site radius and author chronology to each retained sample age? Until the identity, historical basin geometry, count denominator and analytical-use rights are resolved, this candidate supports metadata context and the separate Neotoma observed-pollen transfer only; it does not admit Gilltjärnen to LRA or make LandClim output independent vegetation truth.

## Private structural row review

The private source store also retains `landclim/rootsi-workbooks/structural-review/`.
Its `custody.json` has SHA-256
`f718e3d954e655968af804b94d5ab52bde9bddf922cda4ba9e506c7f4e97adb3`.
The review preserves 79 workbook profiles, 7,459 header positions, 5,170
mechanical data-row candidates, a 79-row sample-denominator review, and the
original report. The five outputs are byte-identical across the two retired
local replay directories. Both original manifests are retained because they
record different producer file identities despite identical outputs. The
[retirement receipt](../../maintenance/artifact-retention/rootsi-workbook-review-retirement.json)
records exact hashes and directory scope. These private candidates preserve
the refused source review; they do not establish chronology, taxonomy, count
meaning, historical input identity, reuse rights, or scientific admission.
