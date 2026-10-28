# LegacyAge depth estimates for ABBO and DALMUT

We acquired the original chronology and comparison tables from [Li et al.'s
LegacyAge 1.0 PANGAEA deposit](https://doi.org/10.1594/PANGAEA.933132),
licensed CC BY 4.0. The full S5 and S6 files and their URL, HTTP and hash
receipt remain in the external `bijux-pollenomics-data/legacyage/pangaea-933132`
source store. The exact sample-level [depth join](sample-depth-join.csv),
[unmatched row](unmatched-samples.csv) and [machine summary](report.json) are
derived from those files and the governed Neotoma relational samples and age
claims. Cite the PANGAEA dataset as: Li, Chenzhi; Postl, Alexander; Böhmer,
Thomas; Dolman, Andrew M; Herzschuh, Ulrike (2021): *Harmonized chronologies
of a global late Quaternary pollen dataset (LegacyAge 1.0)*. PANGAEA.
[doi:10.1594/PANGAEA.933132](https://doi.org/10.1594/PANGAEA.933132).

| Core | Neotoma dataset | Pollen samples | Exact S5 sample-depth joins | Unmatched |
| --- | ---: | ---: | ---: | --- |
| ABBO | 19913 | 107 | 107 | None |
| DALMUT | 20034 | 72 | 71 | Sample `175354` at 4.5 cm |

S5 contains centimetre-grid depths 648–896 for ABBO and 0–288 for DALMUT.
The join uses native sample depths only when the numeric depth exactly equals
an S5 depth. DALMUT's 4.5 cm sample lies between grid values and has no
assigned LegacyAge estimate here. All 178 exactly joined Neotoma point ages
lie within their respective S5 95% age ranges; these remain **different age
models**. The LegacyAge mean minus the Neotoma point age ranges from −362 to
+25 years for ABBO (median −16), and from −294 to +108 years for DALMUT
(median −4). Negative differences place the LegacyAge mean younger in BP
units. Interval inclusion does not make the two age models interchangeable or
provide a joint age posterior. S5 provides calibrated years BP minima,
maxima, medians, means and reported uncertainty widths. S6 compares ABBO
with `EPD 1` and DALMUT with
`author preferred`; it records an AWI Bacon chronology for both, with the
original chronology within the LegacyAge 95% interval. That comparison does
not identify the chronology used by LandClim or transfer LegacyAge ages to
the historical author workbook.

We separately applied the authors' [interior depth-allocation rule](depth-allocation/README.md)
to the 4.5 cm DALMUT sample. Original S4 pollen depths match all 72 Neotoma
depths for this core; published S5 rows at 4 and 5 cm give a derived midpoint
minimum −94, maximum 541.5, median 257 and mean 215 calibrated years BP.
This interpolates rounded published summaries. It is not an exact S5 row,
joint posterior or LandClim-selected age. The exact-row join above remains
71 of 72 by definition.

This is a source-backed alternative chronology for an age-aware development
analysis. It does not establish historical basin geometry, count denominator,
taxon/PPE eligibility or analytical rights for the other source materials.
**No ABBO or DALMUT LRA sample is admitted by this join.**

Reproduce into an absent disposable output directory from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 \
  docs/report/source-relations/neotoma/legacyage-chronology/replay.py \
  --repository . \
  --source-dir ../bijux-pollenomics-data/legacyage/pangaea-933132 \
  --output artifacts/jobs/legacyage-neotoma-depth-join-replay
```

The producer checks the exact S5/S6 and Neotoma input hashes, row identities,
age units, model grids, one-to-one sample ages, exact-match denominator and
the unmatched 4.5 cm row. Compare all three replayed files byte for byte
with the governed files in this directory.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

**Supported claim.** Published LegacyAge summaries join 178 exact ABBO/DALMUT sample depths and retain one unmatched half-centimetre sample.

**Unsupported claim.** Range inclusion does not equate age models, provide a joint posterior, or authenticate a historical LandClim chronology.

**Actual verification performed.** Read the two-core summary, 178-row exact join and unmatched-sample export; no source table download or age model rerun.

**Remaining input or review.** Historical selected chronology remains separate from this CC BY 4.0 alternative; basin, count, taxon/PPE and other material rights need qualification.

**Cause category.** Alternative age-model correspondence is not historical selection authority.

**Consequence.** The source-backed alternative can support a separately declared development sensitivity only.

**Precise next acceptance route.** Freeze a new age-aware protocol using the chosen published model and explicit support rules; obtain missing source/scientific decisions before LRA admission.

**Negative or refused result.** DALMUT sample 175354 at 4.5 cm is not an exact S5 row; 0 ABBO/DALMUT LRA samples admitted.

**Matched denominator.** ABBO 107/107 and DALMUT 71/72 exact depth joins; 178 point ages inside corresponding S5 ranges; 1 unmatched sample.

- [Retained qualification evidence: docs/report/source-relations/neotoma/legacyage-chronology/report.json](report.json) (SHA-256 `544020c69762d5b86a0c6f9cd4e06b10894c8e4139058f988e28d2970edd0a74`).

- [Retained qualification evidence: docs/report/source-relations/neotoma/legacyage-chronology/sample-depth-join.csv](sample-depth-join.csv) (SHA-256 `00fb70fc6201b07873d2ec13ea59ec6018c656ae5f680f881c055d1a0a4b4ac6`).

- [Retained qualification evidence: docs/report/source-relations/neotoma/legacyage-chronology/unmatched-samples.csv](unmatched-samples.csv) (SHA-256 `a4de894f8e001d1ae66db2338fe555145f3bef00e502acdfc83c9c1faabb29fb`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
