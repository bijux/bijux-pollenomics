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
