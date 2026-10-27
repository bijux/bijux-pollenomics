# Rootsi and LandClim II candidate overlap

The [row ledger](overlap.csv) binds 79 unique Rootsi metadata candidates to 79 of the 223 normalized LandClim II site features. It uses the five byte-identical derived candidate files retained in `data/landclim/review/rootsi-candidate-inputs/`, the published LandClim II site metadata workbook and receipt, and the normalized site consumer. [report.json](report.json) records their exact input hashes, denominators, the matching profile, and the dependency boundary. Regenerate with `python -m bijux_pollenomics_dev.source_completion.rootsi_landclim_overlap --repository . --output <absent-repository-directory>` using the repository's development package environment. The replay requires the tracked review copy and its fixed manifest and file hashes. The private typed workbooks are not part of this copy.

For the opt-in original-input replay, set `BIJUX_LANDCLIM_SOURCE_ROOT` to the
qualified external LandClim source store. Its `rootsi-input-closure/metadata.xlsx`
has SHA-256 `08c928407aa1c70c38be8a310a1d9d5e6215434a96ee7fbbd3ba849184e9ee47`;
`rootsi-input-closure/typed-cell-review/manifest.json` has SHA-256
`2e5b5a3a10cec59fc8086c0c99db56bb394e9d1f180bbd5571c1098c262c9179`.
The original 79 workbooks live under `rootsi-workbooks/rootsi/`. The opt-in
workbook replay reads the tracked candidate closure from
`data/landclim/review/rootsi-candidate-inputs/`. These inputs were checked
byte-for-byte against their former local copies. Their source roles and
scientific refusals remain in the governed candidate manifest; a successful
replay does not authenticate the historical paper's input revision.

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
[source-reconciliation audit](../source-reconciliation/README.md) verifies its
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

## Ekenäs source context

[Table 1 in Trondman et al. (2016)](https://link.springer.com/article/10.1007/s00334-015-0536-9/tables/1#table-1-title)
explicitly pairs Ekenäs with EKE: hemiboreal zone, 56.95° N, 16.0167° E,
elevation 90 m, bog, modern radius 20 m. TW1–TW4 each show 20 m; TW5 is grey.
The table footer defines grey as unavailable site/window data and numbers as
radii, generally using modern basin size rather than dated basin geometry.
The five windows are x–100, 100–350, 350–700, 2700–3200 and 5700–6200 cal BP;
x denotes the assumed core-surface age from the coring year. The
[study's chronology methods](https://link.springer.com/article/10.1007/s00334-015-0536-9#Sec4)
specifically rebuilt Ekenäs and Skärsgölarna chronologies using clam 2.1,
IntCal09 and smoothing splines; Ekenäs used four radiocarbon dates plus the
core top, with models not shown. All study records are attributed to the
LANDCLIM pollen archive (Trondman 2014), but no Ekenäs-specific archive
accession or core identifier binds these records to Rootsi or Neotoma. The
paper's 90 m elevation agrees with LandClim I metadata but conflicts with
LandClim II's 20 m. Neither that conflict nor historical chronology equivalence
is resolved.

The retained primary article, Table 1 page, original table image and 17-page
supplement are in the external source store at
`landclim/provider-descriptions/trondman-small-sites/2026-10-27/`:
`publisher-article.html` (study-region/site-selection section `Sec3` and
time-window/chronology section `Sec4`), `publisher-table-1.html` (table title
`table-1-title` and table footer), `publisher-table-1.gif` (Ekenäs row), and
`334_2015_536_MOESM1_ESM.pdf`
([publisher supplement](https://media.springernature.com/original/springer-static/esm/art%3A10.1007%2Fs00334-015-0536-9/MediaObjects/334_2015_536_MOESM1_ESM.pdf)).
Supplement page 1, Online Resource 1, lists Ekenäs among sites included in
RUNS 1–5; pages 2–17 contain RDA and REVEALS taxon/LCT figures and captions.
This 17-page metadata review found no Ekenäs-specific sample, core or archive
identifier, age vector or chronology-control table authenticating a workbook
or native-data join.

## Gilltjärnen source question

The [published LandClim II metadata](https://doi.pangaea.de/10.1594/PANGAEA.937075), workbook `LANDCLIMII metadata file` row 994, describes `GIL` as a lake at 60.083333° N, **15.083333° E**, with `siteradius` **169 m**, 101 pollen samples, 24 time windows, eight radiocarbon dates for its model, and an `Authors chronology` label. The workbook's explanation sheet explicitly defines `siteradius` in metres. The overlap ledger's `24` is `site_window_count`, not a radius. Neotoma site 28866 instead places its `GILL` core at 60.08333° N, **15.83333° E**, and has 101 source samples. The 0.75° longitude disagreement is approximately 42 km at this latitude, far beyond the 169 m reported radius. Equal sample counts and similar sequence names cannot resolve that conflict. [Antonsson et al. (2006)](https://doi.org/10.1002/jqs.1004) identifies a radiocarbon-dated Gilltjärnen pollen record, but its accessible abstract does not bind these two database coordinates, the two core handles, or a time-specific basin outline.

**Question for the source holder:** Which coordinate is correct for the physical `GIL`/`GILL` sediment core, does the LandClim `GIL` input contain the same 101 counted samples as Neotoma dataset 53991, and what evidence binds the reported 169 m modern site radius and author chronology to each retained sample age? Until the identity, historical basin geometry, count denominator and analytical-use rights are resolved, this candidate supports metadata context and the separate Neotoma observed-pollen transfer only; it does not admit Gilltjärnen to LRA or make LandClim output independent vegetation truth.

## Workbook structure

The private structural review covers 79 workbooks, 7,459 header positions,
5,170 mechanical data-row candidates and 79 sample-denominator questions.
Those counts describe the source files. They do not establish chronology,
taxonomy, count meaning, historical input identity, reuse rights or LRA
admission for a physical core.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Author/source lineage, transformations and distinct modeled products; chronology and historical run admission remain separate.

**Supported claim.** The 79-row overlap ledger binds Rootsi metadata candidates and member hashes to 79 of 223 normalized LandClim II site features.

**Unsupported claim.** Metadata overlap and complete workbook custody do not authenticate historical selected cells, grid/window contribution, scientific count semantics or rights.

**Actual verification performed.** Read overlap report/CSV and source-store identities, distinguishing retained 5,170 mechanical row candidates from later source-qualified denominator review; no workbook rescan.

**Remaining input or review.** Historical input revision, core/chronology/taxon/count support, per-sequence rights and contributor mapping remain unresolved.

**Cause category.** Metadata candidate identity and historical scientific authority differ.

**Consequence.** LandClim outputs cannot be used as independent truth for overlapping Rootsi inputs.

**Precise next acceptance route.** Resolve original selected input/core/age/count/geometry/rights packets and exact grid/window contribution before admitting a historical reconstruction.

**Negative or refused result.** 78 sample-count claims agree but EKE 25 versus 42 differs; 44 coverage intervals refused; Gilltjärnen longitude differs 0.75 degree.

**Matched denominator.** 79 unique candidate pairs of 81 metadata rows/1,128 publication rows; 35 numeric coverage intervals, 36 negative-bound and 8 partial refusals; 0 admitted sample chronologies.

- [Retained qualification evidence: docs/report/source-relations/rootsi-landclim-overlap/report.json](report.json) (SHA-256 `c948f235313ddf7b99a3a941cf8167caabe18cbb22580671ae696a7d0aaee264`).

- [Retained qualification evidence: docs/report/source-relations/rootsi-landclim-overlap/overlap.csv](overlap.csv) (SHA-256 `34bb9b19d1a3ba3a479ce77174ea85e87c52f1bae51e42a44b57eaf5739165c6`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
