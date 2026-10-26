# What the original LegacyAge run inputs establish

We recovered the original input archive and R script from
[Li et al.'s LegacyAge code deposit](https://zenodo.org/records/5815192),
DOI `10.5281/zenodo.5815192`, published 3 January 2022 under CC BY 4.0.
The [LegacyAge paper, section 4](https://essd.copernicus.org/articles/14/1331/2022/#section4)
identifies this deposit separately from the PANGAEA summary tables.
This supplies previously unretained control and model-setting metadata for
four named core series. It also exposes a precision difference between the
archived and already retained versions of the original-chronology table.
No age model, pollen prediction or LRA fit was run.

## Inputs and populations

The original ZIP (3,583,171 bytes) and R file (22,634 bytes) were acquired once
on 26 October 2026 into the shared source store's
`legacyage/zenodo-5815192/`. The source manifest retains response headers,
HTTP status, acquisition times, byte sizes, SHA-256 and matching provider MD5
checksums. Raw bytes remain unchanged. The official record metadata supplies
the license; its initial request headers and exact timestamp were not retained.
The machine result [pins the five consumed inputs](legacyage-run-inputs.json).
The new original files and source manifest remain outside product Git.

The ZIP has exactly three CSV members: S1 chronological controls (19,990 rows),
S3 parameter settings (2,823 rows) and S4 original chronologies (158,418 rows).
We checked the member population and sizes and streamed the selected rows
without extracting the archive. These pinned CSVs use semicolon separators
and Windows text encoding; the retained PANGAEA S4 uses tabs and UTF-8.

| Native series / dataset | S1 controls | S3 settings | Matched S4 pollen depths | Numerically different S4 age cells | Different S4 error cells |
| --- | ---: | ---: | ---: | ---: | ---: |
| ABBO / 19913 | 6 radiocarbon | 1 | 107 | 97 | 0 |
| DALMUT / 20034 | 11 radiocarbon | 1 | 72 | 127 across two age series | 0 |
| SOLSOE81 / 4445 | 33 radiocarbon + 1 prior-information date | 1 | 66 | 98 across two age series | 62 |
| SOLSOE83 / 4446 | 7 radiocarbon | 1 | 26 | 46 across two age series | 24 |
| LAIH / 52082 | 0 | 0 | 0 | 0 | 0 |
| BUS / 53995 | 0 | 0 | 0 | 0 | 0 |
| BOKE / 54001 | 0 | 0 | 0 | 0 | 0 |

The last three dataset IDs are absent from these tables. These zeros describe
membership in this release, rather than missing pollen or absence of a
chronology elsewhere. SOLSOE81 and SOLSOE83 remain two cores of one lake.
The 271 matched depths and the 454 changed numerical cells are different
denominators; changed cells are not independent observations.

The primary R script's S1 and S3 PANGAEA URLs were subsequently captured once
into the same shared source store, alongside the already retained PANGAEA S4.
The new S1 and S3 captures contain 7,009,490 and 900,588 bytes; both returned
HTTP 200 on 26 October 2026 and record a 7 December 2021 `Last-Modified` date.
Their acquisition metadata and source hashes were appended without changing
the earlier S4/S5/S6 capture claims. Each has the same row and field population
as its corresponding ZIP member; that does not establish matching values.

## Settings are source assumptions, not a realized posterior

All four S3 records specify `Marine=FALSE` and `Memory=0.3`. ABBO records
`Resolution.cm=5`, `Waterline=648`, `Add.surface=TRUE` and
`Starting.age=-52`. DALMUT records 5 cm sections, an added surface and
starting age −10, with its waterline left `NA`. SOLSOE81 records a 95 cm
waterline, 20 sections, accumulation-rate token 70, an added surface and
starting age −30; it also retains the 578 cm added-date fields and deleted
depth 141 cm. SOLSOE83 records a 386 cm waterline, 10 cm sections and
`Add.surface=FALSE`, with its starting age left `NA`.

The JSON preserves every nonmissing parameter token, including explicit
`FALSE`; missing and empty source fields are not converted to measured zero.
The R source separately substitutes zero for missing waterline/reservoir
values, builds added-surface ages as `max(-70, Starting.age, na.rm=TRUE)`
with error 30, and passes `mem.strength=20` and `acc.shape=1.5` to Bacon.
Those are documented executable rules, rather than new field measurements.
The table's added/deleted-depth declarations also do not prove that every
field is executed by this script; its Bacon-input preparation consumes S1
and the explicitly implemented transformations.

The S3 comparison confirms identical nonmissing tokens for all four core
setting rows. In each row, the archived `Need.calibration.2`,
`Need.calibration.3` and `Need.calibration.6` empty strings become literal
`NA` in PANGAEA. The twelve differences remain explicit. This comparison
does not infer that empty and `NA` have identical meaning in every consumer.

The archived script defaults to datasets 47502 and 4320. Its active reads
fetch S1/S3/S4 from PANGAEA URLs, rather than reading the ZIP members. Its
R package versions and random seed are unpinned. Thus neither the archived
settings nor a new execution would identify the realized historical S5
chronology, recover a joint posterior, or establish LandClim's selected ages.
The published record lists graph archives, code, metadata and a demonstration
video; this intake obtained no posterior draws and downloaded no graph archive.

## The S4 versions must remain distinct

We joined each series by native dataset ID and exact numeric pollen depth.
Both S4 versions have the same 271 selected depths and field axes. All changed
age/error cells differ by at most **0.005 in the native S4 numeric units**.
The R script multiplies the original-age/error fields by 1,000 when constructing
comparison plots, so that bound corresponds to five years under its declared
transformation; radiocarbon and calibrated series retain their own age types.

For example, the archived ABBO surface age is `-0.052` and the retained
PANGAEA token is `-0.05`. SOLSOE83's first two age tokens are `2.731` and
`2.783`, versus `2.73` and `2.78`. The source error token `2.799` versus `2.8`
is retained without interpreting it as a newly calibrated confidence interval.
Source coordinates also differ in recorded precision. The exact field counts,
maximum gaps and first differing tokens appear in the JSON.

These differences are compatible with a coarser published representation.
We establish the literal difference, without inferring which bytes the
historical code consumed. No existing age assignment, interval calculation,
source score or LRA decision was replaced by these archived values.

The precision difference can change bin membership. Applying the original
R's multiplication by 1,000 and the existing half-open 500-year convention
`[500*k, 500*(k+1))` to each matching calibrated source-age series gives
exactly four different source-token assignments:

| Native core and depth | Archived calibrated token | Retained token | Archived / retained bin index |
| --- | ---: | ---: | ---: |
| ABBO, 866 cm | 7.999 | 8 | 15 / 16 |
| DALMUT, 160 cm | 5.997 | 6 | 11 / 12 |
| SOLSOE81, 478 cm | 6.496 | 6.5 | 12 / 13 |
| SOLSOE83, 502 cm | 4.997 | 5 | 9 / 10 |

This compares the source tokens; it selects no chronology and assigns no
sample to an admitted study. Radiocarbon-only series are outside this
calibrated-token sensitivity. Original signed ages retain negative bin
indices where applicable; none is clipped to zero. There is no pollen
pooling, model fit or score change in this check.

## Control precision also reaches the numerical model inputs

The two S1 versions match all **58 controls** by source dataset, laboratory
label and numeric depth in centimetres. There are zero unmatched controls
and zero duplicate identities. Of those, **57** have the same literal
`Carbon-14` method in both versions. The SOLSOE81 prior-information row
remains outside the radiocarbon arithmetic; it is not a measured date.

The primary R script constructs its pre-calibration numbers as
`age_kyr * 1000` and `(older_error_kyr + younger_error_kyr) * 500`.
We compared these exact formulas, preserving both error tokens and their
average even when they are asymmetric. No normal distribution, confidence
level or joint age law is inferred from that arithmetic. Curve selection,
missing-error defaults, calibration and Bacon fitting were not executed.

| Series | Compared radiocarbon controls | Changed age arguments | Changed mean-error arguments | Distinct changed controls |
| --- | ---: | ---: | ---: | ---: |
| ABBO | 6 | 1 | 2 | 3 |
| DALMUT | 11 | 8 | 7 | 9 |
| SOLSOE81 | 33 | 0 | 13 | 13 |
| SOLSOE83 | 7 | 0 | 3 | 3 |

Nine age arguments and 25 mean-error arguments change across 28 distinct
controls. Each absolute difference is at most **five years**. For example,
the ABBO source radiocarbon-age token `2.235` becomes `2.23` kyr BP, and a
source error token `0.035` becomes `0.04` kyr. DALMUT's `0.605` becomes
`0.6`, with some `0.065` error tokens becoming `0.06`. The complete matched
numeric inputs, signed differences, method exclusions and unmatched/refused
populations are retained in the JSON. No matched radiocarbon input
is refused; missing, invalid or negative errors would be retained as a
refusal rather than supplied as zero or silently defaulted.

This is a source-version sensitivity of specified input arithmetic. It does
not estimate a resulting chronology shift or establish which version
produced S5. A future alternative-age reconstruction must choose and cite
its exact control/settings release, executable/dependency versions and
protocol before any refit; a re-created run would be a new chronology with
its own uncertainty, rather than the lost historical posterior.

## Verification and reuse

The maintained [input reader](../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/pollen_age_support/legacyage_run_inputs.py)
reproduces this result from the shared originals:

```sh
source_store="/path/to/qualified/bijux-pollenomics-data"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m \
  bijux_pollenomics_dev.source_completion.pollen_age_support.legacyage_run_inputs \
  --source "$source_store/legacyage/zenodo-5815192" \
  --retained-s4 "$source_store/legacyage/pangaea-933132/table-s4-original-chronology.csv" \
  --output artifacts/physical-core/legacyage-run-inputs-replayed.json
```

The output must be absent. The reader uses exact decimal arithmetic, preserves
negative ages and refuses repeated depths, unmatched depth axes, incompatible
fields and changed missingness. It never interpolates, calibrates or fits ages.
Twelve focused tests, configured Ruff checks/format and strict mypy on the
reader and tests passed before commit. An initial observer assertion expected
the spelling `0.00` for an exact zero where Decimal returned `0`; that assertion
was corrected without changing production behavior. The first mypy run also
identified a reused bytes/text stream variable, which was renamed.

An independent pandas parser and native dataset/depth merge checked all 9,485
non-key literal cells across the 271 rows, every changed age/error cell, all
four parameter records and source-control denominators without importing the
maintained reader. Independent rational arithmetic also reproduced all four
source-token bin crossings. Its bounded result is retained under
`artifacts/physical-core/independent-source-check.json`. These are precommit
verification results for reviewed working source, rather than a claimed
exact-HEAD scientific study.

The same command subsequently ran with the consumed reader committed at
`9c39ac1d84d986e230d01995816ec38e27e40d24`, changing only the destination to
`artifacts/physical-core/legacyage-committed-source.json`. It returned exit
zero in 2.1333455 seconds and reproduced the governed JSON byte for byte.
The consumed reader and the original three pinned source inputs were unchanged. Separate
AADR working changes were present, so this identifies the committed consumed
source rather than claiming a clean whole-tree study. The independent
source/token and rational-bin checks above apply to the identical result.

The subsequent S1/S3 extension passed **20 focused tests**, with an
independent pandas native-key join and exact rational arithmetic reproducing
all 57 pre-calibration numeric comparisons, the 58-control population and
all twelve S3 empty/`NA` differences. These new checks exercise reviewed
working source; the earlier committed replay qualifies the original
three-input result only.

The extended five-input reader then ran unchanged from committed consumed
source `69c2745684bdf454aa1458050307851ab666f9f4`, with the same replay
arguments and destination
`artifacts/physical-core/legacyage-controls-committed-source.json`. It returned
exit zero in 2.2574483 seconds and reproduced the extended governed JSON byte
for byte. The five original input hashes and consumed source remained stable;
the independent control/token checks apply to that identical output.

This is partial source preparation toward a declared chronology profile.
The existing [ABBO](../abborrtjarnen-source-method.md),
[DALMUT](../dalmutladdo-lra-input/README.md) and
[Solsø](../solsoe-lra-input.md) decisions remain in force. Historical input
identity, selected chronology/uncertainty, dated basin support, count/taxon/PPE
admission, original pollen-source rights and independent scientific review
remain separate. The original source-core outcome remains open, with zero
additional LRA samples admitted.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Exact source-version reconciliation of archived and PANGAEA S1/S3/S4 metadata, declared run transformations, four calibrated-token bin crossings and matched control/settings/depth populations without calibration or model fitting.

**Unsupported claim.** Historical S5 posterior recovery, selection of the original LandClim ages, a new calibrated uncertainty distribution, resulting chronology shifts, pollen-score changes or additional admitted LRA samples.

**Actual verification performed.** The unchanged five-input reader at 69c274568 reproduced the governed JSON byte for byte. Independent pandas/native-key and Fraction arithmetic checked 271 matched depths, 9,485 non-key cells, 58 controls including 57 radiocarbon comparisons, four settings records, twelve empty/NA differences and four exact source-token bin crossings. Twenty focused extension tests and configured lint/types passed. No interpolation, calibration or Bacon fit was executed.

**Remaining input or review.** Archive and PANGAEA metadata versions expose different precision and missingness representations. The original settings and exact pre-calibration arithmetic do not identify which bytes or unpinned runtime produced historical S5, recover joint draws or select the LandClim chronology. Resolver: Chronology analyst selecting explicit metadata/model inputs for new work; original source custodian for a claimed historical realization or selected-age identity. Reopen when: For historical claims, bind the exact executed control/settings release, runtime and selected sample-age realization; for a new profile, declare its chosen inputs and model rather than calling a recreation the lost posterior.

**Cause category.** data|assumption|comparability

**Consequence.** Reuse the exact retained metadata/version arithmetic as source preparation while retaining version, source-age type, signed tokens and unresolved historical realization separately.

**Precise next acceptance route.** Choose and cite an explicit control/settings release and predeclared model for any new chronology analysis, as a new analysis. Reopen historical-posterior or selected-age claims only with the source-owned executed inputs/realization; the completed source reconciliation itself needs no new fitting or blanket approval.

**Negative or refused result.** LAIH, BUS and BOKE are absent from this metadata release, not missing pollen populations. Source-age/error precision differences and explicit empty-versus-NA cells remain; no matched radiocarbon control was refused and no signed source age was clipped. No historical input or original core decision was replaced.

**Matched denominator.** Seven requested dataset IDs; four series have 271 matched S4 depths, 58 S1 controls with 57 radiocarbon rows and four S3 settings. Source-version differences affect 454 S4 numeric cells, 28 distinct pre-calibration controls and twelve settings cells; changed cells are not independent observations.

Retained evidence: [reports/science/chronology/legacyage-run-inputs.json](legacyage-run-inputs.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
