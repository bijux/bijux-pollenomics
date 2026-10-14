# DALMUT LegacyAge age summary at 4.5 cm

We allocated the [published LegacyAge 1.0](https://doi.org/10.1594/PANGAEA.933132)
S5 age summaries to Neotoma sample `175354` at 4.5 cm. The source tables are
licensed CC BY 4.0. The [authors' R procedure at the inspected commit](https://github.com/LongtermEcology/LegacyAge-1.0/blob/9ae54335e61a7a93426530141ef057dc85412e42/R-script_bacon_age-depth_modelling_LegacyAge1_0.R#L248-L275)
reads the S4 pollen-record depths and applies its interior Case II rule to the
adjacent one-centimetre age-grid summaries.

S4 contains 72 DALMUT records for dataset `20034`, site `13388`, and their
depths match all 72 Neotoma samples from that dataset, including 4.5 cm. S5
contains the 0–288 cm one-centimetre grid for the same dataset. This establishes
the source depth and datum correspondence needed for this allocation.

| Depth | Minimum | Maximum | Median | Mean |
| --- | ---: | ---: | ---: | ---: |
| Published S5 at 4 cm | −96 | 482 | 229 | 188 |
| Published S5 at 5 cm | −92 | 601 | 285 | 242 |
| Derived midpoint at 4.5 cm | **−94** | **541.5** | **257** | **215** |

All ages are calibrated years BP. The derived minimum-to-maximum width is
635.5 years. These numbers interpolate the **published rounded summaries**;
they may differ slightly from interpolation of the authors' unrounded Bacon
output. The result is a derived summary allocation, not an exact S5 row or a
joint age posterior. It does not select a historical LandClim chronology or
admit this sample to an LRA reconstruction. The exact-source-row join in the
[parent study](../README.md) remains unchanged.

S4 and S5 original bytes and their DOI, license, URL and hashes are retained in
the external `bijux-pollenomics-data/legacyage/pangaea-933132` source store.
The [machine result](report.json) records the row values and source identities.
Reproduce from the repository root into an absent disposable output directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 \
  docs/report/source-relations/neotoma/legacyage-chronology/depth-allocation/replay.py \
  --repository . \
  --source-dir ../bijux-pollenomics-data/legacyage/pangaea-933132 \
  --output artifacts/jobs/legacyage-depth-allocation-replay
```

Compare the resulting `report.json` byte for byte with the governed result.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

**Supported claim.** The authors’ interior depth-allocation rule yields a declared midpoint of rounded 4 cm/5 cm age summaries for one 4.5 cm DALMUT sample.

**Unsupported claim.** Interpolated rounded summaries are not an exact S5 source row, unrounded Bacon output, joint age posterior or selected historical LandClim age.

**Actual verification performed.** Read the exact bracketing and derived summary values and source-procedure commit in report.json; no posterior generation or calibration.

**Remaining input or review.** A use-specific chronology choice and all independent LRA prerequisites remain unresolved.

**Cause category.** Derived age-summary interpolation has limited numerical and probabilistic scope.

**Consequence.** The exact-row join remains 71 of 72 despite this separate allocation.

**Precise next acceptance route.** Declare the alternative chronology and rounded-summary allocation explicitly in any future sensitivity protocol, then qualify remaining inputs.

**Negative or refused result.** No exact-source-row or LRA admission is created; original unmatched status remains.

**Matched denominator.** 1 sample at 4.5 cm, 2 bracketing S5 rows; derived cal BP minimum −94, maximum 541.5, median 257, mean 215; 72 S4 depths correspond.

Qualified authored reader SHA-256: `efb04490b5cd3777b916fc6d25e33b35877fb8ed764f206c6cb907242d7bb535`.

- [Retained qualification evidence: docs/report/source-relations/neotoma/legacyage-chronology/depth-allocation/report.json](report.json) (SHA-256 `469e755a507fd0325b7d78d3c3ac4a5d79402036072cbd4a3d6e2e3a82226e43`).

- [Retained qualification evidence: docs/report/source-relations/neotoma/legacyage-chronology/report.json](../report.json) (SHA-256 `544020c69762d5b86a0c6f9cd4e06b10894c8e4139058f988e28d2970edd0a74`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
