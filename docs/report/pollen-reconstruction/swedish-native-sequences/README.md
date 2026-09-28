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
published depth unit remains unknown. The calculated percentage uses only
reported pollen NISP rows in each sample.
The source supplies no separate denominator. Unreported taxa are not filled with
zero, and counts retain their native labels. Sample age bounds are absent; the
source chronology control table preserves available control limits and the
named age model. The view plots each reported sample point without interpolation,
and it does not assert continuous temporal support, vegetation composition, or
LRA reconstruction. The atlas point layer has not yet been wired to this sequence
surface; its source export and this trajectory remain separate consumers.

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
