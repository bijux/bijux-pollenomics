# LegacyAge depth estimates for the two Solsø cores

We joined the primary S5 and S6 tables from [Li and colleagues' LegacyAge 1.0
PANGAEA deposit](https://doi.org/10.1594/PANGAEA.933132) (2021, CC BY 4.0)
to the named Neotoma sample depths at Solsø. The full source tables and their
download receipts remain in the external
`bijux-pollenomics-data/legacyage/pangaea-933132` source store. The
[machine report](report.json) records both source SHA-256 values, the exact
Neotoma sample and age-claim hashes, source units and core identifiers.

| Neotoma dataset | Core | Samples | S5 model depths | Exact sample-depth joins | Comparable calibrated ages | Refused calibrated ages |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 4445 | SOLSOE81 | 66 | 492 | 66 | 65 | 1 |
| 4446 | SOLSOE83 | 26 | 185 | 26 | 26 | 0 |

All **92** source samples have an exact S5 depth in centimetres; no rounding or
interpolation was used. The [sample ledger](sample-depth-join.csv) retains each
Neotoma calibrated point age and the corresponding S5 minimum, maximum,
median, mean and reported uncertainty fields. The 1981 sample `352996` at
98 cm has a calibrated Neotoma point age of 7 BP with a negative younger
bound. Its Neotoma claim remains **refused** (`negative_bp`) in the
[refusal ledger](refused-samples.csv), despite having an exact S5 depth and a
LegacyAge interval. This is the same source-age issue recorded in the
[published EPD age correspondence](../pangaea-epd-age-join/README.md).

For SOLSOE81, 57 of 66 Neotoma point ages lie within their matched S5 95%
ranges and nine lie outside. The 57 include the refused negative-bound
Neotoma claim, leaving 56 of 65 comparable claims inside. The LegacyAge mean
minus Neotoma point age spans
−635 to +378 years (median +16). For SOLSOE83, all 26 point ages lie within
their matched S5 ranges; the mean difference spans −471 to +158 years
(median −3.5). S6 separately describes the 1981 original chronology as
partially or completely outside the LegacyAge 95% confidence intervals and
the 1983 original chronology as within them. These are **different age
models**; row-wise interval membership is a descriptive source comparison,
not an inference about a joint age posterior.

This join does not identify which samples made up LandClim II's published
79-sample Solsø sequence, prove its historical age-model selection, provide
sample-age basin geometry, or admit LRA input. It can support a separately
declared observed-pollen chronology sensitivity with its own fixed prediction
and matched-support accounting.

The [producer](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/countries/denmark/solsoe-source-lineage/legacyage-chronology/replay.py) checks source hashes and core/sample ownership, then
writes the sample ledger, refusal ledger and report. Replay from the repository
root into an absent disposable output directory:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/countries/denmark/solsoe-source-lineage/legacyage-chronology/replay.py \
  --repository . \
  --source-dir ../bijux-pollenomics-data/legacyage/pangaea-933132 \
  --output artifacts/jobs/solsoe-legacyage-depth-join-check
```

The two primary sources are the S5 chronology table (66,989,363 bytes;
SHA-256 `bbe0e8d5854acf091a11737ddedc10d5656f8a25c8eeb9637b85f9e69a37cb41`)
and S6 chronology comparison (438,320 bytes; SHA-256
`2a058f08472199b0545e4562e6860371dfaba7ce74140b1e0b4dbdce0ce55300`).
Cite Li, Chenzhi; Postl, Alexander; Böhmer, Thomas; Dolman, Andrew M;
Herzschuh, Ulrike (2021): *Harmonized chronologies of a global late
Quaternary pollen dataset (LegacyAge 1.0)*, PANGAEA,
[doi:10.1594/PANGAEA.933132](https://doi.org/10.1594/PANGAEA.933132).


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Solsø two-core native counts/ages, source lineage and unresolved historical79 versus current92 selection.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/solsoe-lra-input.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/solsoe-lra-input.md) (source SHA-256 `e6b29b0cfd3e763b8bc38ca390f894b0cc5c583259040a3e3c9fef2bf363fe71`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
