# Published EPD ages for the two Solsø cores

[Giesecke and colleagues' final EPD sample-age table](https://doi.pangaea.de/10.1594/PANGAEA.804596) (2013, CC BY 3.0) gives depths in metres and calibrated ages and bounds in ka BP. The [source-bound replay](report.json) joins its rows to Neotoma sample-owned calibrated claims by the literal `SOLSOE81` or `SOLSOE83` core handle and depth converted from metres to centimetres.

All **92 published Solsø rows** match distinct Neotoma sample depths: 66 in the 1981 core and 26 in the 1983 core. For every row, the age, younger bound and older bound agree to at most **0.5 BP** after the published ka values are converted to years; this is consistent with Neotoma's integer-year rounding. The published younger bound of one 1981 row is **−0.04091 ka** and joins to `neotoma:sample:352996`, the same negative-bound sample refused by the Danish prerequisite screen. This confirms the source lineage and refusal rather than resolving it.

The five core handles at the other four Danish sites in the captured Neotoma set are absent from this **2013 final age table**. That absence does not prove that no other dated publication or later chronology exists. The table is from the same EPD chronology lineage reflected in Neotoma; agreement does not create an independent chronology, identify LandClim II's 79 Solsø input samples, supply a dated basin outline, or admit any sample to LRA.

The downloaded tab-delimited source is held in the external data store as `epd/pangaea/epd-age-cut-pangaea-804596.tsv` (3,613,957 bytes; SHA-256 `d332d5c7921b914e84da689c918607befdb162f5c68bbcce9cd3534d1f5e58e0`). Its publisher DOI, license and native units are retained in the [report](report.json). Reproduce the join from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/countries/denmark/solsoe-source-lineage/pangaea-epd-age-join/replay.py \
  --repository . \
  --published /path/to/private/source/store/epd/pangaea/epd-age-cut-pangaea-804596.tsv \
  --output artifacts/jobs/solsoe-epd-age-join/report.json
cmp artifacts/jobs/solsoe-epd-age-join/report.json \
  docs/report/countries/denmark/solsoe-source-lineage/pangaea-epd-age-join/report.json
```

The configured report-owner route authenticates this exact table with
`configs/ci/qualified-report-sources/solsoe-published-epd-ages.json` and rechecks
its four relational inputs and retained join source before publishing one
`source-products/report.json` beneath an absent artifact destination. Its
source-root argument names the separate retained data store. The descriptor
records acquisition custody as unestablished and scientific admission as false;
it does not reconstruct a capture history or authorize new chronology claims.
The source-bound route preserves the existing report schema, arithmetic,
negative-bound refusal and zero admitted samples. Genuine reference/replay
execution and byte comparison remain separate verification requirements.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Solsø two-core native counts/ages, source lineage and unresolved historical79 versus current92 selection.

**Supported claim.** The retained published 2013 EPD age table matches 92 distinct Solsø core/depth rows to Neotoma calibrated ages and both bounds within 0.5 BP conversion/rounding.

**Unsupported claim.** Shared EPD chronology lineage is not independent age validation and absence of other core handles from one 2013 table does not prove they have no chronology elsewhere.

**Actual verification performed.** Read the joined report and exact qualified table descriptor; checked 66+26 matches,all three residual maxima 0.5 BP and the preserved negative-younger-bound identity. No source download or age join was rerun.

**Remaining input or review.** Historical LandClim 79 sample selection, author chronology, basin geometry and qualified source reuse remain unresolved.

**Cause category.** Published source-age correspondence, separate from independent chronology and LRA admission.

**Consequence.** The join corroborates source lineage and its refusal; it does not repair or truncate the negative age bound.

**Precise next acceptance route.** Authenticate the exact 3,613,957-byte PANGAEA804596 table and four relational inputs, execute the source-bound route, and obtain independent historical input/basin evidence before LRA.

**Negative or refused result.** Sample 352996 retains−0.04091 ka younger bound/negative_bp refusal; five handles at four other Danish sites are absent from this table; LRA-admitted 0.

**Matched denominator.** 92 published Solsø rows=66 SOLSOE81 + 26 SOLSOE83,92 distinct depth matches; age/younger/older residual≤0.5 BP; one negative-bound sample; zero LRA samples.

Qualified authored reader SHA-256: `5eeeef9a4f021a75d8c5b4825961d0b7b76a86ee4be3d6f8c46eb3a8b2f1bf88`.

- [Retained qualification evidence: docs/report/countries/denmark/solsoe-source-lineage/pangaea-epd-age-join/report.json](report.json) (SHA-256 `5039c9ff04263799f5b1e95c2027cdba710203c561220d9bfbea884bf6d52f49`).

- [Canonical scientific account: reports/science/solsoe-lra-input.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/solsoe-lra-input.md) (source SHA-256 `3f8a2b8a26f84b4029a7f1e3761a4eac3e9a7a07514a375d5aa5cbc1781a7caf`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
