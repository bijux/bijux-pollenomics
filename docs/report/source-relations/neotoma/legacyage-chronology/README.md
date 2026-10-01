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
