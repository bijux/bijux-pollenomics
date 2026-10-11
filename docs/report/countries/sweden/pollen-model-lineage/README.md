# Swedish observed-pollen and modeled-cover lineage

The [Swedish Neotoma direct-pollen cohort](../../../pollen-reconstruction/swedish-direct-pollen/cohort.csv)
contains three observed-pollen sites. The published [LandClim II site
metadata](https://doi.org/10.1594/PANGAEA.937075), retained in the
[Nordic sequence registry](../../../../../data/landclim/normalized/nordic_pollen_site_sequences.geojson),
list ABB, BUS and BOKE at the same coordinates (within 0.5 m after source
rounding) and with the same respective sample counts: 107, 69 and 52. The
LandClim metadata label these as reconstruction input sites, while the Neotoma
records identify observed pollen counts. Matching site metadata is strong
evidence of a shared site lineage; sample-by-sample identity and influence on
each reconstructed grid value have not been authenticated.

BUS and BOKE are both assigned to LandClim grid **779**. Five of the six
targets in the [southern Sweden synthesis](../sweden_land_use_synthesis_v66.csv)
consume that same grid: Bjäresjösjön, Gullåkra, Havgårdssjön, Vesums mossar
and Östra Ringsjön. Finjasjön consumes grid 829 and has no matching site in
this three-site cohort; that does not establish independence from other pollen
inputs. The [machine-readable receipt](report.json) identifies each source
file by SHA-256 and gives every target's grid and distance to the matching
observed-pollen sites.

**A comparison of these Neotoma observations with grid 779 modeled vegetation
cannot serve as independent pollen-to-vegetation validation.** LandClim cover
is a model result, not measured vegetation, and its input registry already
names both southern observed-pollen sites in the same grid. The Neotoma
chronologies also lack sample-age uncertainty bounds. A lake trajectory can
still describe the two products side by side, but agreement or contradiction
of their numbers would be descriptive and source-dependent. Independent SEAD
site/chronology context in the Sweden synthesis does not currently supply a
qualified local vegetation or land-use measurement. No LRA basin geometry or
measured vegetation pair is admitted by this lineage check.

Reproduce the receipt from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_model_lineage \
  --repository . --output artifacts/jobs/swedish-model-lineage-replay
```

Compare the regenerated `report.json` with the governed file here. A changed
cohort, sequence registry or synthesis requires a new lineage decision.
