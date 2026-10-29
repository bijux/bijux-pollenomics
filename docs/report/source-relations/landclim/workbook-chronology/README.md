# Rootsi workbook age-column audit

The [replay](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/source-relations/landclim/workbook-chronology/replay.py) verifies the four private workbook hashes against the
[79-sequence overlap ledger](../../rootsi-landclim-overlap/overlap.csv), then
reads only the source-native age-column structure. Its [report](report.json)
retains exact sheet-row locations and values for chronology reversals. The
workbooks remain in the private source store.

| Sequence | Sample rows | Explicit source age column | Finding |
| --- | ---: | --- | --- |
| FLINK | 109 | `Sample age (cal AD/BC)` | The value jumps from −3850.6025 at sheet row 55 to +3910.8433 at row 56, then returns to negative ages. |
| HOLK | 40 | `Sample age (cal AD/BC)` | The bottom two ages rise from −1491.0767 to −1490.1805; the 40 exact numeric ages contain no duplicates. |
| RANV | 141 | None | Column two is `SALIX`; no workbook sample-age field is present. |
| STAV | 77 | None | Column two is `Picea`; no workbook sample-age field is present. |

The FLINK jump is a candidate sign error, but the local bytes do not authorize
a corrected value. HOLK has a small source-order reversal; the claim of
duplicated ages in the inherited review is not supported by exact equality of
these 40 workbook cells. RANV and STAV have site coverage metadata elsewhere,
which are not sample dates. No source age uncertainty, model identity, historical
publication-input identity, or per-sequence analytical rights is established.
All four remain refused for dated-event and LRA use on this evidence.

A separate [Neotoma source witness](../neotoma-chronology-witness/README.md)
depth-matches all FLINK and STAV workbook rows. It identifies the FLINK
row-56 sign disagreement and supplies a candidate STAV calibrated-BP point-age
vector from the shared EPD lineage. It does not correct the workbook or
authenticate either sequence as the historical LandClim input.

An arithmetic check rounds the extrema of `1950 − source age` to integer BP and
compares them with the sequence metadata bounds. HOLK's full 40-cell extrema
produce **−50 to 3441 BP**, matching its metadata; its last sheet row instead
produces 3440 BP, consistent with the bottom reversal. FLINK's full 109-cell
extrema produce **−1961 to 12011 BP**, while its metadata say **−50 to 12011
BP**. Omitting the single cell immediately after the interior reversal yields
the metadata bounds. This is a diagnostic of the discrepancy, not evidence
that the omitted cell should be changed or that the 1950 arithmetic is an
approved calibrated-age conversion. The report retains the diagnostic omission
separately from the unchanged source values.

**Source-holder decision needed:** Does the LandClim II FLINK input use this
exact 109-row workbook, and what is the authoritative `cal AD/BC` value at
sheet row 56? For HOLK, which age-depth model and ordering govern the last two
samples, and how are their uncertainty bounds represented? For both sequences,
which conversion convention produced the published BP extrema? The request is
for source records and model identifiers, not permission to replace the cells
with a visually plausible value. RANV needs a sample-age source linked to its
141 workbook rows; STAV needs historical author-input and model-version
confirmation for the Neotoma candidate age vector.

Reproduce from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/source-relations/landclim/workbook-chronology/replay.py \
  --source-root ../bijux-pollenomics-data/landclim/rootsi-workbooks \
  --output artifacts/jobs/rootsi-workbook-chronology/report.json
cmp artifacts/jobs/rootsi-workbook-chronology/report.json \
  docs/report/source-relations/landclim/workbook-chronology/report.json
```


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Author/source lineage, transformations and distinct modeled products; chronology and historical run admission remain separate.

**Supported claim.** The four-workbook age audit preserves actual age-column presence, reversals and numeric metadata diagnostics.

**Unsupported claim.** Sequence coverage and 1950-minus-age arithmetic do not authorize sample-age conversion, row omission, calibration or historical input identity.

**Actual verification performed.** Read all four retained workbook findings and metadata comparisons; no original workbook, cached grid or model was rerun. Two unchanged canonical Rootsi source producers and their independent raw-workbook/Neotoma observers returned four native zeros on c292dafa60f9d992f162c92dd327207d9aefd76b; both full typed reports and complete publication bytes match. The source-bound isolated base/pure-xlrd cache is distinct from observed147/SOURCE3331. All3548 original identities remain explicit in an authored58member source capsule; private workbooks/archive/intake and runtime/xlrd payloads remain omitted. FLINK sign discrepancy,HOLK reversals,RANV/STAV absent ages, negativeBP and no source age bounds remain literal. Declared1950-minus-age/0.0500001 are arithmetic diagnostics, not calendar/no-year-zero conversion or age correction. No dated basin, historical-input, independent chronology/ecology, rights/human or LRA admission, and no new retention-native outcome.

**Remaining input or review.** FLINK/HOLK source-model/order explanations and RANV/STAV sample ages with model/unit/uncertainty authority remain needed.

**Cause category.** Missing age columns and source-native age-order contradictions.

**Consequence.** No dated event or LRA sample is admitted by this audit.

**Precise next acceptance route.** Resolve the source-specific age-model and sample-row questions, retaining native cells and both reversal witnesses unchanged.

**Negative or refused result.** FLINK and HOLK each retain one reversal; HOLK has 0 exact duplicate ages; RANV and STAV have no sample-age column.

**Matched denominator.** 4 workbooks:FLINK 109, HOLK 40, RANV 141, STAV 77 sample rows; age comparisons apply only to the 149 FLINK/HOLK age labels.

- [Retained qualification evidence: docs/report/source-relations/landclim/workbook-chronology/report.json](report.json) (SHA-256 `b2c732c11669837c9aa75b8b0a5bfb7568dbf86071014ccfb4b30d3dcfc2eb13`).

- [Retained qualification evidence: reports/science/source-lineage/rootsi-workbook-chronology.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-lineage/rootsi-workbook-chronology.json) (SHA-256 `f903bb2c7671d04b67410b7ba73ed2aebe1d5ca9f86a54354aaa10746d65e47b`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
