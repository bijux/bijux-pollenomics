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

**Supported claim.** The retained exact-depth join links all 92 Solsø sample depths to alternative LegacyAge S5 estimates and retains separate S6 chronology comparisons.

**Unsupported claim.** Row-wise S5 interval membership is not a joint age posterior, the historical author chronology, selection of LandClim II79 samples or LRA basin support.

**Actual verification performed.** Read the source-bound report and sample/refusal ledgers; checked 66+26 depth matches,65+26 comparable samples and the single negative-bound refusal. No private S5/S6 rejoin or age model was run.

**Remaining input or review.** Authenticate the historical author chronology/sample selection and sample-age basin support; evaluate alternative chronology under a separately declared response and support rule.

**Cause category.** Alternative chronology correspondence with unresolved historical selection.

**Consequence.** Different point ages can be compared descriptively; agreement does not authorize replacing Neotoma ages or treating alternative model estimates as independent observed truth.

**Precise next acceptance route.** Use the frozen S5/S6 hashes and exact cm-depth sample IDs to reproduce the join, retain negative_bp, then predeclare any restricted-support sensitivity before scoring.

**Negative or refused result.** SOLSOE81 has 9 of 66 point ages outside S5 intervals; the negative-bound sample 352996 remains refused even though its depth and alternative interval match.

**Matched denominator.** Two cores:66/492 S5 depths and 26/185;92 exact joins,0 unmatched;91 comparable+1 refused. Point intervals:57/66 inside in 1981,26/26 in 1983. LRA-admitted 0.

Qualified authored reader SHA-256: `afe3741f14051de330dac1279ef0288aad78badda484e992dbf5c2424301d7b1`.

- [Retained qualification evidence: docs/report/countries/denmark/solsoe-source-lineage/legacyage-chronology/report.json](report.json) (SHA-256 `dc06e30d7a290bb81ad6c8f0da1ec3b8a804f883af388692855698e9ee555be2`).

- [Retained qualification evidence: docs/report/countries/denmark/solsoe-source-lineage/legacyage-chronology/sample-depth-join.csv](sample-depth-join.csv) (SHA-256 `0a5a6c4fea4b547021e236ffdb4e5ec16178876b161f6d0556e6dd9ebcd80925`).

- [Retained qualification evidence: docs/report/countries/denmark/solsoe-source-lineage/legacyage-chronology/refused-samples.csv](refused-samples.csv) (SHA-256 `052d97c8a2f01743cdbf425a41c7c5c37c5ac1e8f8b4a5ba5ea9db7e874d07e8`).

- [Canonical scientific account: reports/science/solsoe-lra-input.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/solsoe-lra-input.md) (source SHA-256 `e6b29b0cfd3e763b8bc38ca390f894b0cc5c583259040a3e3c9fef2bf363fe71`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
