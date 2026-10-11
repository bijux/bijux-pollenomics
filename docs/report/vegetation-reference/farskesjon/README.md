# Färskesjön pollen and forest-plot support

The retained [source-bound report](report.json) examines the one EMPD2–Swedish
NFI spatial lead with a pollen collection-month note: `Nielsen_b4`, a lake
surface-sediment sample labeled “Farskesjon 0-1 cm.” Its EMPD2 record says the
surface sample was collected in **September 2013**; `agebp = -63` is a source
age field, not a dated collection day. The linked
[Åkesson et al. (2015) study](https://portal.research.lu.se/en/publications/from-landscape-description-to-quantification-a-new-generation-of-/)
analyzes a new 2013 Färskesjön pollen core with REVEALS and compares its
landscape estimates with historical maps. It does not turn a nearby forest
inventory plot into a measured whole-lake vegetation reference.

The exact nearest NFI plot-year row has an Excel 1900-system inventory serial
that decodes to **17 May 2013**, 107–136 days before the September pollen
collection month. The workbook describes its plot as a circle of radius **7 m**
and area **153.94 m²**. Reprojecting its private SWEREF99 TM source point to
WGS84 and applying the WGS84 inverse geodesic gives **427.1219 m** between the
two recorded source points. The source-point separation exceeds the declared
plot radius by **420.1219 m**. The [SLU NFI data guide](https://www.slu.se/globalassets/slu.se/om-slu/organisation/institutioner/skoglig-resurshushallning/riksskogstaxeringen/dokument/dokument/info-data-for-calibration.pdf)
also limits this temporary plot subset: it cannot support geographic-area
totals or means.

The selected NFI row does contain **measured plot tree volume**, totaling
302.8481 m³/ha across its five coarse workbook classes. Most is in the
source's `VolOtherDec` class (266.1164 m³/ha). Those are real measurements of
one small forest plot, not 31-taxon landscape-cover fractions at the lake or
independent vegetation truth for its pollen source area. This particular
proximity lead is **refused** as a paired validation reference. The other
15 reviewed leads retain their own unresolved prerequisites; their status is
not decided by this plot.

The producer pins the exact private EMPD2 SQLite, NFI workbook and spatial
lead JSON by SHA-256, selects the plot-year through the private lead, verifies
its source headers/units and date epoch, and independently recomputes distance.
It publishes neither the private plot key nor coordinates. Reproduce into an
absent destination from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/vegetation-reference/farskesjon/plot_support.py \
  --source-root /path/to/private/reference-sources/empd2-nfi \
  --output artifacts/jobs/farskesjon-plot-support.json
```
