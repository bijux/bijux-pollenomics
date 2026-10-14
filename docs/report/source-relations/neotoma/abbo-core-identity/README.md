# Abborrtjärnen cross-source core lead

The [source-bound comparison](report.json) joins one Neotoma/EPD dataset and
sample to the published LandClim II site metadata as an identity **lead**.
Both sources name Abborrtjärnen and report 107 samples; their site points
differ by 0.334 m. The Neotoma core handle is `ABBO`, while the published
sequence is `ABB`. Their reported elevations differ by 13 m. These facts do
not establish that the same physical core, basin extent or chronology was used.

The selected Neotoma sample 173174 has 23 pollen NISP observations totaling
1,206, including four `Indeterminable` grains, plus six nonpollen observations
totaling 57. Its one retained candidate age is 19 calibrated BP without source
bounds. LandClim metadata row 968 reports a 98 m site radius, `Authors
chronology`, and 3/9799 TopBP/BottomBP labels; the Neotoma dataset reports
−52/9815 calibrated-BP endpoints. No radius, chronology or count denominator
is transferred. The [generated interpretation](REPORT.md) retains the full
bounded comparison, and the [manifest](manifest.json) binds the producer and
inputs.

The producer now reads the governed Neotoma prerequisite projection, its
pinned raw source manifest and a [selected count-mass cross-check](count-mass-crosscheck.json)
extracted from the earlier independent mass audit. Its scientific fields
reproduce the historical working report exactly; only input hashes changed
when disposable process inputs were replaced. Reproduce from the repository
root into a new artifact directory:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.abborrtjarne_core \
  --raw-part data/neotoma/raw/neotoma_pollen_dataset_downloads/part-004.json \
  --raw-manifest data/neotoma/raw/neotoma_pollen_dataset_downloads/manifest.json \
  --workbook data/landclim/raw/landclim_ii_site_metadata.xlsx \
  --workbook-receipt data/landclim/raw/landclim_sources.json \
  --count-mass docs/report/source-relations/neotoma/abbo-core-identity/count-mass-crosscheck.json \
  --projection docs/report/source-relations/neotoma/lra-prerequisites/projection.json \
  --output artifacts/abbo-core-identity/replay
```

The separate [Rootsi workbook count comparison](../abbo-native-correspondence/README.md)
preserves wider 107-sample taxon and age disagreements. Neither comparison
admits an LRA sample or resolves analytical-use rights.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

**Supported claim.** The ABBO/ABB comparison preserves a same-name 107-sample/0.334 m point identity lead and selected sample count partition.

**Unsupported claim.** Close points and matched sample counts do not establish a shared physical core, basin radius, selected chronology or count denominator.

**Actual verification performed.** Read the source-bound report, manifest and independent selected count-mass receipt; no source consumer rerun.

**Remaining input or review.** ABBO versus ABB core identity, 13 m elevation discrepancy, age model, basin/count/PPE support and rights require qualification.

**Cause category.** Metadata similarity is insufficient identity authority.

**Consequence.** The 98 m LandClim radius is not transferred to Neotoma.

**Precise next acceptance route.** Reconcile original physical core and selected age/geometry records with source-holder evidence before forming an LRA request.

**Negative or refused result.** Radius transfer is refused; candidate age 19 cal BP has no bounds; 0 samples admitted.

**Matched denominator.** 1 paired metadata lead; 107 native/published samples; selected sample 173174 has 23 pollen observations/1,206 counts plus 6 other observations/57 counts.

Qualified authored reader SHA-256: `34e93a0fd9ea762b45e32b482eb74137427300b83e84756a966fc754df03cdda`.

- [Retained qualification evidence: docs/report/source-relations/neotoma/abbo-core-identity/report.json](report.json) (SHA-256 `e7b22e4cc7caf8831422307dd6b89b7da9b6f8afc07daadb84f07268fdcaa2ea`).

- [Retained qualification evidence: docs/report/source-relations/neotoma/abbo-core-identity/manifest.json](manifest.json) (SHA-256 `c817748f52c5cda435d2f5bbfb746f442aa346ca4f4d2ca71b38ae360bf6739c`).

- [Retained qualification evidence: docs/report/source-relations/neotoma/abbo-core-identity/count-mass-crosscheck.json](count-mass-crosscheck.json) (SHA-256 `fea274f27de4ea834eb38ac4ad8c3a07766aec27bc6a1633e1088f8e247f8e2f`).

- [Canonical scientific account: reports/science/abborrtjarnen-source-method.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/abborrtjarnen-source-method.md) (source SHA-256 `264420c81e18a6ee56b0b612e657f881fa26829a9cc060114d69b15d2491120f`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
