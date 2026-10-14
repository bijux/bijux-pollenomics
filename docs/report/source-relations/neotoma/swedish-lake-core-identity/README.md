# Bussjösjön and Bökesjön core leads

The [source-bound comparison](report.json) checks Neotoma/EPD datasets 53995
and 54001 against LandClim II metadata rows 978 and 977. For Bussjösjön and
Bökesjön respectively, both sources list 69 and 52 samples, while their site
points differ by 0.383 m and 0.445 m. The Neotoma and published elevations
differ by 211 m and 33 m. These are review leads, not established common cores
or basin geometries. The published 69 m and 80 m radii are not transferred.

The native sequences contain 68,668 and 42,548 pure-pollen NISP units, plus
15,561 and 10,280 other NISP units. All 69 and 52 samples have one native
calibrated-BP age claim. Their native age endpoints differ from the published
series-end labels by at most 0.5 years numerically, but the source chronology
labels and age support do not establish a common selected chronology. The
[generated interpretation](REPORT.md) keeps the sample and category context;
the [manifest](manifest.json) binds all source inputs and results.

The producer uses the governed prerequisite projection and a
[two-sample independent count-mass receipt](count-mass-crosscheck.json)
extracted from the earlier source audit. Its scientific JSON fields reproduce
the earlier working result exactly; only the input identities changed. Run
from the repository root into a new artifact directory:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.swedish_lake_core_correspondence \
  --raw-part data/neotoma/raw/neotoma_pollen_dataset_downloads/part-008.json \
  --raw-manifest data/neotoma/raw/neotoma_pollen_dataset_downloads/manifest.json \
  --workbook data/landclim/raw/landclim_ii_site_metadata.xlsx \
  --workbook-receipt data/landclim/raw/landclim_sources.json \
  --count-mass docs/report/source-relations/neotoma/swedish-lake-core-identity/count-mass-crosscheck.json \
  --projection docs/report/source-relations/neotoma/lra-prerequisites/projection.json \
  --output artifacts/swedish-lake-core-identity/replay
```

The separate [Bussjösjön basin review](../bussjosjon-basin/README.md) retains
the 2.5264 km conflict with a later inventory point. Neither nearby LandClim
metadata point resolves that discrepancy. No LRA sample, source right or
original pollen denominator is admitted by this comparison.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

**Supported claim.** The two-lake comparison preserves full native count/age coverage and close LandClim metadata leads for BUS/BOKE.

**Unsupported claim.** Submetre points and nearly equal endpoint numbers do not establish common cores, historical radii, selected chronology or pollen denominator.

**Actual verification performed.** Read both source-bound lake records, manifest and two-sample mass receipt; no count/core consumer replay.

**Remaining input or review.** Elevation/coordinate conflicts, original count support, source chronology/geometry and analytical-use decisions remain.

**Cause category.** Metadata and endpoint agreement are incomplete physical-core authority.

**Consequence.** 69 m/80 m radii are not transferred and candidate-filter counts do not replace native sample totals.

**Precise next acceptance route.** Bind exact cores, selected sample ages and justified basin/count/taxon/parameter profiles with source permission before admission.

**Negative or refused result.** BUS 49/260 m and BOKE 57/24 m elevation claims differ; all radius transfers refused and 0 LRA samples.

**Matched denominator.** BUS 69 and BOKE 52 native samples versus 66/50 prerequisite candidates; pure-pollen NISP 68,668/42,548 and other NISP 15,561/10,280.

Qualified authored reader SHA-256: `e5bba0eafdcd6226ef7b2079f9d27101a3f7e3883645ca39a660808e5c2e714a`.

- [Retained qualification evidence: docs/report/source-relations/neotoma/swedish-lake-core-identity/report.json](report.json) (SHA-256 `d2b80a81ed26c7d3f327488290927de6220a3ca39c8d7d15514c258c75dc7594`).

- [Retained qualification evidence: docs/report/source-relations/neotoma/swedish-lake-core-identity/manifest.json](manifest.json) (SHA-256 `bf8f76d4513859615b84ec7d408a774c26591bd89a8d0d5a34b43d18d70b907a`).

- [Retained qualification evidence: docs/report/source-relations/neotoma/swedish-lake-core-identity/count-mass-crosscheck.json](count-mass-crosscheck.json) (SHA-256 `afff295e29fb5210ff94dbf599ba0b1530191b6e06abc3f96e35bb06f05812d9`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
