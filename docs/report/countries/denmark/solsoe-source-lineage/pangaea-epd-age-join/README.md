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
