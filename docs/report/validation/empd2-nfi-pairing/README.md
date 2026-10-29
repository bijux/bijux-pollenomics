# EMPD2–NFI observed vegetation pairing decision

The [pair ledger](pairs.csv) records **16 geographic proximity leads and zero admitted observed vegetation pairs**. The [machine-readable report](report.json) binds each refusal to the original EMPD2 SQLite and Swedish NFI workbook SHA-256 identities. This is an outcome-free source review: NFI tree measurement cells were not read, no vegetation reconstruction was evaluated, and no benchmark threshold was frozen.

## Source and denominator

The original Swedish subset has 132 EMPD2 metadata samples. The NFI workbook has 43,892 plot-year rows across 6,018 distinct tract/plot keys. WGS84 inverse-geodesic screening after transforming NFI points from SWEREF99 TM gives 53 plot-year/sample combinations within 1 km, across 16 pollen samples. The ledger selects one nearest NFI plot-year per sample, including 14 distinct selected plot-years. Distance is only a lead-generation screen. It does not establish shared time, vegetation footprint, measurement units, or independent validation support.

The original source dossier, spatial screen, EMPD2 SQLite and NFI workbook are
preserved in the external private source store. The [result](report.json)
records the exact input hashes checked by its producer. The dossier and screen
contain exact NFI row locations and are not tracked in Git. The tracked [SLU
calibration guide](inputs/slu-calibration-guide.pdf) retains its pinned local
bytes. Its original retained2026-09-21/a063 provider retrieval/copy chain
remains unqualified. A separate official SLU page-to-PDF acquisition on source
commit `d027effd6c0ac91512cd586c3a51db987ea46d54` and its independent observer
both returned native zero. Their [retained current-source account](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/vegetation-reference/slu-current-guide-source.json)
binds the HTTP200/TLS-verified page, literal download href and exact same
136,339-byte guide. This guide source owner is independent of the workbook
metadata owner; the older metadata capsule's guide-admitted-false claim remains
literal. The current acquisition does not recover the missing historical copy.

The public source capsule omits raw HTML and runtime binaries and removes
cookie headers from its declared HTTP metadata projections while preserving
the original raw-response hashes. The earlier documentary licence/use review
receipt is not currently authenticated; this admission performs no fresh PDF
text extraction or licence/use revalidation. It grants no additional workbook
or observation rights and does not turn plot measurements into regional totals.
The producer checks the private inputs' exact hashes and reads only the NFI
workbook's first six identity/coordinate fields to bind every selected plot-year
to an original row and recompute each geodesic distance. The source-native NFI
date is checked during replay but omitted from the public CSV; pollen `agebp`
is not treated as a collection year. The tracked CSV replaces each NFI
row location and key with an opaque SHA-256 identity; it contains no NFI tract,
plot, year, date, or coordinates.

[PANGAEA's EMPD2 source record](https://doi.org/10.1594/PANGAEA.909130) identifies the pollen source and CC BY 4.0 terms. The [SLU National Forest Inventory calibration guide](https://www.slu.se/globalassets/slu.se/om-slu/organisation/institutioner/skoglig-resurshushallning/riksskogstaxeringen/dokument/dokument/info-data-for-calibration.pdf) states CC0 1.0 terms and describes temporary forest plot observations intended for calibration or validation of remote-sensing products. Plot observations cannot by themselves establish regional vegetation area totals or means.

The [source measurement schema](nfi-measurement-schema.json) reads the original
workbook's field dictionary and only inventory date, plot area and land-use
metadata from its 43,892 plot-year rows. The dictionary describes an undivided
circular plot with radius 7 m and area 153.94 m²; every plot-year row has that
area. Five tree-group basal-area columns are labeled in m²/ha: pine, contorta,
spruce, birch and other deciduous trees. The workbook also contains five
land-use codes; their meanings are not assigned by this schema. Inventory
dates remain source-native Excel serial values. No basal-area or other tree
measurement outcome cell was decoded, and no target taxon composition or
minimum benchmark threshold was chosen. Five other workbook headers lack exact
field-dictionary names and remain listed in the schema report. To reproduce
this bounded schema read:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.empd2_nfi_reference.measurement_schema \
  --private-source-store /path/to/private/source-store \
  --output artifacts/jobs/empd2-nfi-pairing/nfi-measurement-schema.json
```

The original bounded metadata producer was genuinely replayed on source commit
`60bf419979bdc682ef227fb01e42a4f5ed6e2722`. Both the producer and its
independent dictionary/header/area/time observer returned native zero; the public
schema is byte-identical to the retained JSON. The replay selected columns D, G
and H for 43,892 plot-year rows, or 131,676 metadata cells. It streamed the
complete worksheet XML and decoded zero tree measurement outcome cells.

The [retained source and execution capsule](https://github.com/bijux/bijux-pollenomics/blob/main/data/validation/nfi-measurement-metadata-capture/capture.json)
contains the original receipts, logs, public output and 2,139 declared first-party
source files, including 1,161 observed import origins. Its separate metadata-only
assembly on commit `d027effd6c0ac91512cd586c3a51db987ea46d54` reran no workbook
projection or scientific model. Private workbook and runtime payloads are omitted;
their original registered identities remain explicit. These receipts establish the
bounded metadata replay, with zero admitted measured pairs or new guide acquisition.

## Retained outcome-blind source replay

The maintained replay and independent source observer on commit
`97be88f37a117a518c8c4639ccca98927e13cb24` both returned native zero.
Their [retained source witness](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/vegetation-reference/empd2-nfi-pairing-source.json)
binds the exact unchanged public CSV/report and all 16 native source joins.
Six metadata columns cover 43,892 rows and 6,018 tract/plot keys; all 26 source
and 19 public fields were checked. Outcome decoder and LRA implementation
calls stayed zero. XML/sharedStrings bytes were read; raw outcome bytes are
not claimed unread. Only the 16 selected pair distances were rechecked,
without a fresh full spatial screen. All 16 candidates remain refused.

The source capsule retains 2,159 public first-party source/resource files,
92 declared controls and 66,501 ordered input identities. The 4,356 original
bytecode identities are omitted payloads and establish no source/cache or
fresh-compilation equivalence. Private source-bound pair locations, original
private inputs and native runtime payloads are not published. The earlier
timeout stays a failed execution; these later native-zero receipts do not
relabel it. Authored source retention is not a new metadata execution.

## Current decision

All 16 leads lack an authenticated pollen collection date, opened NFI tree
measurement values, a pollen taxon denominator and tree-taxon crosswalk, and a
reviewed rule mapping a 153.94 m² plot observation to the pollen basin or
reconstruction support. Five leads also have unresolved cross-source physical
sample identity; one collection note requires authentication. The benchmark
still lacks a qualified independent-source/leakage review and non-null
predeclared minimum sample and error thresholds. Each missing field is explicit
in the CSV. The 16 rows are **refusals for the current benchmark**, not 16
negative measured observations.

The bounded decision can be replayed with the original raw holdings and tracked review inputs:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  PYTHONPATH=packages/bijux-pollenomics-dev/src:packages/bijux-pollenomics/src \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.empd2_nfi_pairing \
  --repository . \
  --private-source-store /path/to/private/source-store \
  --output artifacts/jobs/empd2-nfi-pairing/publication
```

The output destination must be absent. Source-bound replay requires the
original SQLite, workbook, dossier and spatial screen in the private source
store. The producer checks their identities; default focused tests exercise
the tracked guide, public output and refusal contract without them. Its private
source-row ledger can be regenerated for review and discarded with the run
output. The decision can change
only after the missing source facts and scientific review are supplied, then
with a new source-bound record; proximity alone cannot promote a lead.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Named measured/mapped/published reference scope and unmatched temporal/taxon/observation/independence limits.

**Supported claim.** The source-bound outcome-free review retains sixteen geographic leads and refuses every lead as a currently admissible observed vegetation pair.

**Unsupported claim.** Proximity, plot area and dictionary units do not provide paired vegetation measurements, a regional target, authenticated pollen collection dates or a frozen performance benchmark.

**Actual verification performed.** Read the retained pair decision and bounded workbook-schema account, including zero decoded tree measurement outcomes; bound their public identities. No private workbook, tree values, spatial screen or reconstruction was opened or rerun for this qualification. Separately retained original official-page/literal-link/PDF acquisition and its independent observer returned native zero and authenticate the unchanged guide bytes. Authored source custody omits HTML/runtime payloads/cookie values. No new source request, workbook projection or documentary licence review is performed; the prior8be8 review receipt is not currently authenticated. The original SLU guide ownership criterion remains verbatim and unresolved: exact current guide bytes and a genuine current download do not establish the original provider retrieval/copy receipt or the publication/use statement bound to those bytes. Native results remain partial source evidence; no numerical result, permission, human decision or LRA admission changes. The separately retained maintained outcome-blind source replay and independent observer returned native zero and both public products byte-match;16 native joins, 26 source fields, 19 public fields, six metadata columns, 43,892 rows and 6,018 tract/plot keys are checked. No outcome decoder/LRA calls, private payload publication or fresh-compilation equivalence is claimed.

**Remaining input or review.** Missing pollen dates, measured tree outcomes, taxon denominator/crosswalk, footprint relation and qualified source/leakage review remain; five leads need extra physical identity review and one collection note needs authentication.

**Cause category.** Independent-measurement admission refusal despite geographic proximity.

**Consequence.** The sixteen rows are missing benchmark support, not sixteen negative measured observations; benchmark policy and evaluation remain false.

**Precise next acceptance route.** Recover the named missing source facts and reviewed plot-to-basin relation, then predeclare non-null sample/error minima before opening qualified independent evaluation outcomes and recording a new decision.

**Negative or refused result.** Zero measured pairs are admitted, no reconstruction is evaluated and no tree-outcome cell is decoded by this schema review. Five headers lack exact dictionary counterparts and remain unresolved.

**Matched denominator.** 132 Swedish EMPD2 samples; 43892 NFI plot-years/6018 tract-plot keys; 53 combinations within 1 km across 16 pollen leads and 14 selected plot-years. Plot 153.94 m² with five m²/ha basal-area dictionary groups is not regional cover.

- [Retained qualification evidence: docs/report/validation/empd2-nfi-pairing/report.json](report.json) (SHA-256 `cc90bccae9c54808dfea71cb4c07bb1bd12273e10eefbe889981369e34f66642`).

- [Retained qualification evidence: docs/report/validation/empd2-nfi-pairing/nfi-measurement-schema.json](nfi-measurement-schema.json) (SHA-256 `5b4d5bb087501af7b223ffa8c5494a8ad4073a0503906b47aa36a2748a8e1505`).

- [Retained qualification evidence: reports/science/vegetation-reference/slu-current-guide-source.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/vegetation-reference/slu-current-guide-source.json) (SHA-256 `b28238feadb2cee4ed5da5ec7a2eb9241f67b583d3156d32c60a7e8947bdc07c`).

- [Retained qualification evidence: reports/science/source-cohorts/original-owner-acceptance.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/original-owner-acceptance.json) (SHA-256 `e03c2de940f5a127ebd9886ae038b278b7c6e6b8ef8d35cb4755d633a532ab05`).

- [Retained qualification evidence: reports/science/vegetation-reference/empd2-nfi-pairing-source.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/vegetation-reference/empd2-nfi-pairing-source.json) (SHA-256 `c1e4d8623b7d695b2c705cf5c3d69f474d107c3458d1aaa8b3e1ddeda82b6050`).

- [Canonical scientific account: reports/science/vegetation-reference.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/vegetation-reference.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
