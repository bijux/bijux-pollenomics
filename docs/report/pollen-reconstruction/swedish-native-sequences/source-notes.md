# Swedish source-owned pollen sequences

[Browse the three lake trajectories](index.html). The page reads the published
`observations.json` table directly. The same rows produce the table download and
the counts and sampled-age extent in `map-summary.geojson`; site coordinates come
from the source site records. The site map is a coordinate overview, without a
basemap or inferred spatial support.

The source-backed cohort is Abborrtjärnen (`19913`), Bussjösjön (`53995`) and
Bökesjön (`54001`). It contains 228 samples, 5,464 reported native NISP pollen
rows and 46 source chronology controls. Source sample IDs, depth, selected
calibrated age, model identity, controls, taxon IDs and names, counts, contributor
names, DOI, and raw JSON row locators remain available in the linked tables.
The source snapshots are EPD datasets accessed through Neotoma; use is subject
to [the EPD data policy](https://epdweblog.org/epd_data_home/epd_policy/) and
attribution to Neotoma, EPD and the original investigators. The exact source-file
hashes and output hashes are in [the manifest](manifest.json).

The raw Neotoma record does not label the depth unit in these rows, so the
published depth unit remains unknown. A [separate source-bound ABBO comparison](../../source-relations/neotoma/abbo-profile/README.md)
finds that all 107 Abborrtjärnen depths match the PANGAEA meter depths after
division by 100 and five taxon count series agree at all 107 positions. This
supports a centimeter interpretation for that one native series, while leaving
the Neotoma source field and the other two lakes' units unchanged. The
PANGAEA event's 3 ha area is not a time-specific historical basin boundary.
The calculated percentage uses only
reported pollen NISP rows in each sample.
The source supplies no separate denominator. Unreported taxa are not filled with
zero, and counts retain their native labels. Sample age bounds are absent; the
source chronology control table preserves available control limits and the
named age model. The view plots each reported sample point without interpolation,
and it does not assert continuous temporal support, vegetation composition, or
LRA reconstruction. The atlas point layer has not yet been wired to this sequence
surface; its source export and this trajectory remain separate consumers.

The [source overlap report](source-overlap.json) detects eight same-name,
near-coordinate LandClim metadata leads across all three lakes (maximum point
gap below 0.45 m). This flags possible shared source lineage before any
agreement is described as independent corroboration. Name and point agreement
do not prove that original cores or samples are identical; that source review
remains open. LandClim model cells are not counted as observations here.

Regenerate into an empty directory under `artifacts/` and compare the five data
files and manifest with this directory:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m bijux_pollenomics_dev.source_completion.swedish_pollen_sequences \
  --data-root data/neotoma/raw/neotoma_pollen_dataset_downloads \
  --destination artifacts/swedish-native-sequences/replay
```

The focused replay test also checks the published table against the existing
Swedish direct-pollen cohort's sample and native NISP counts. These source
sequences expose the native observations used by that separate binned predictor;
the trajectory itself reports no predictive skill.

Reproduce the overlap check with the same source-site table and retained
LandClim site metadata:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m bijux_pollenomics_dev.source_completion.swedish_pollen_overlap \
  --sites docs/report/pollen-reconstruction/swedish-native-sequences/sites.json \
  --landclim data/landclim/normalized/nordic_pollen_site_sequences.csv \
  --output artifacts/swedish-native-sequences/overlap-replay
```


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-bound conditional reconstruction or exposed pollen development wrapper; own source assumptions and exact scored/refused populations must be preserved alongside account links.

**Supported claim.** The source-owned trajectory/table/map-summary readers expose exact reported native pollen rows, selected point ages, named chronology controls and source coordinates without interpolation. Source overlap flags potential shared lineage, not independent corroboration.

**Unsupported claim.** Full raw-core grain-sum authority, zero counts for unreported taxa, depth units for all lakes, continuous age support, historical core/sample identity, vegetation composition, LRA reconstruction or predictive skill from the trajectory.

**Actual verification performed.** The source notes and retained observations/site/map/overlap manifests were inspected. The separate ABBO source comparison supports a scoped centimeter interpretation from 107 matched depths and five count series, while native labels remain unchanged. This qualification performs no source acquisition, trajectory replay, atlas/browser interaction or numerical model execution.

**Remaining input or review.** Native depth units are unlabeled, sample-age bounds and a separate pollen denominator are absent, and historical identity is unresolved for the 8 near-coordinate same-name leads. A present-day 3 ha PANGAEA event area is not an age-specific basin boundary. Other lakes do not inherit ABBO’s depth-unit interpretation.

**Cause category.** data | assumption | comparability | qualified review

**Consequence.** Percentages divide only reported native pollen NISP. Keep source labels/missingness and chronology metadata visible, and do not count LandClim modeled cells as observations or treat name/coordinate matches as independent source evidence.

**Precise next acceptance route.** Obtain source-specific denominator/depth/age semantics and authentic core/sample linkage before stronger source or LRA claims; admit age-specific basin/parameters and measured vegetation separately. Verify atlas integration as its own consumer rather than infer it from this coordinate overview.

**Negative or refused result.** Unreported taxa are not filled with zero.8 metadata leads across the 3 lakes have point gaps below 0.45 m but do not prove identical original cores/samples. No continuous trajectory, predictive accuracy or LRA result is established.

**Matched denominator.** 3 native datasets 19913/53995/54001;228 source samples;5,464 reported native NISP pollen rows;46 source chronology controls. ABBO’s separate unit/count comparison covers 107 depths and 5 taxa; those are not additional independent samples.

- [Retained qualification evidence: docs/report/pollen-reconstruction/swedish-native-sequences/manifest.json](manifest.json) (SHA-256 `9f9a29740c56ec64dc089e50d57514071146fc3945a90d3e3b270dedfb5e722b`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/swedish-native-sequences/source-overlap.json](source-overlap.json) (SHA-256 `6c3e60cb4144fbde19eaf7ee3ce044343d6d181d7f102ac38a49c4f887b09cc5`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/swedish-native-sequences/sites.json](sites.json) (SHA-256 `9956683a701d5ed576836e1f37d894dce81d8e6cb1050a10dfc3980190140b37`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

- [Canonical scientific account: reports/science/pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/pollen-prediction.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
