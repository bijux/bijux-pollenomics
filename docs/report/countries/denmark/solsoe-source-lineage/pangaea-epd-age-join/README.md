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

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/solsoe-lra-input.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/solsoe-lra-input.md) (source SHA-256 `e6b29b0cfd3e763b8bc38ca390f894b0cc5c583259040a3e3c9fef2bf363fe71`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
