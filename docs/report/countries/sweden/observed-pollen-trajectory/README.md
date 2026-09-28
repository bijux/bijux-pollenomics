# Bussjösjön and Bökesjön observed-pollen trajectory

**Question:** Do the two observed-pollen series move together across their
common calibrated-BP bins, and does independent dated context justify a local
land-use conclusion?

The [machine-readable report](report.json) joins the two prepared
[Neotoma/EPD site series](../../../pollen-reconstruction/swedish-direct-pollen/REPORT.md)
over 13 common 500-cal-BP bins (-500–6000 BP). It compares exact native
`Alnus` and `Plantago lanceolata` counts as fractions of (a) all native NISP
and (b) the declared 16-taxon subcomposition. Each bin retains both sample
counts and denominators. Site-to-site directional labels require the same
sign in both denominators at both lakes and at least 0.5 or 1.0 percentage
point change. The [transition table](transitions.csv) records all 48
taxon/threshold/transitions. These fixed thresholds are descriptive
sensitivity checks, not sampling confidence intervals or ecological effect
sizes.

At the 0.5-point threshold, `Alnus` has five descriptive same-direction
transitions and one opposite-direction transition; the remaining 18
taxon/transitions cannot pass the denominator/effect threshold. At the
1.0-point threshold, three `Alnus` transitions agree and one contradicts;
20 cannot pass. For example, from 1000–1500 to 500–1000 cal BP, the full-NISP
`Alnus` fraction falls **10.00→3.69%** at BUS and **12.53→9.55%** at BOKE;
both directions persist within the 16-taxon denominator. From 5000–5500 to
4500–5000 cal BP, it rises **34.13→47.28%** at BUS and falls **23.47→20.53%**
at BOKE, also in both denominators. A second, coarser 1000-year aggregation
of the 0–6000 BP observations is retained in the report to expose sensitivity
to window width. Different pollen catchments and absent sample-age uncertainty
bounds prevent these directional descriptions from establishing one regional
vegetation history.

The independent [SEAD discovery chronology](../../../../../data/sead/derived/sweden_archaeology_site_discovery.geojson)
adds only counts of dated map features and distinct nearby sites whose source
intervals overlap a pollen bin. The report computes 10 and 20 km circles at
the Neotoma coordinates. For BUS it also computes both circles at the
[published lake inventory point](../../../source-relations/neotoma/bussjosjon-basin/README.md),
2.5264 km away. In the 500–1000 BP bin, the BUS 10 km count changes from
**129 to 115 dated features** with that point choice. A dated SEAD site is
not a qualified land-use observation, and feature counts are not pollen,
vegetation cover, or site activity rates. The spatial circles do not imply a
resolved historical lake basin.

The separate [source-lineage check](../pollen-model-lineage/README.md) places
BUS and BOKE among the LandClim inputs for grid 779. That modeled-cover grid
therefore cannot independently validate these observed-pollen series. Every
bin has `incomparable_no_qualified_ecological_proxy` for SEAD versus pollen
and `cannot_conclude_no_independent_vegetation_measurement` for land use.
Agreement and contradiction labels in this report refer **only to the two
observed pollen site directions**. They are not LRA reconstructions, measured
vegetation tests, or causal land-use claims.

Reproduce from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_lake_trajectory \
  --repository . --output artifacts/jobs/swedish-lake-trajectory-replay
```

Compare the generated JSON/CSV with the governed files here. The report pins
the two pollen profiles, SEAD discovery surface and LandClim lineage receipt
by SHA-256. New source ages, environmental observations or basin coordinates
require a new qualified comparison.
