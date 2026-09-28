# Bussjösjön basin and coordinate review

The [Neotoma/EPD source site](../../../../../data/neotoma/raw/neotoma_pollen_sites.json)
`28869` places Bussjösjön at **55.46667° N, 13.81667° E**. Its pollen dataset
`53995` belongs to collection unit `39238` (`BUS core`, handle `BUS`). The
source says that the core was taken at the lake centre in 2.5 m of water, but
does not supply a core GPS position or a site area. The 69-sample
[direct-pollen cohort](../../../pollen-reconstruction/swedish-direct-pollen/cohort.csv)
uses this site coordinate for centre-distance comparisons; those comparisons
do not require a lake boundary.

The author-generated [Jenny et al. (2016) supplementary inventory, Table S2
(PDF page 8)](https://pure.mpg.de/rest/items/item_2354057/component/file_2357941/content)
lists Bussjösjön at **55.44559° N, 13.80172° E**, with lake area **0.03 km²
= 3 ha**, catchment area 0.5 km² and maximum depth 3.0 m. Its row cites
[Olsson et al. (1997)](https://link.springer.com/article/10.1023/A:1007967832177),
a sediment chemistry study, as its source. The inspected supplementary PDF
has SHA-256
`a27df91931ff8a4c75da3daf6699a0e12d2b3c9c084db55a77ab1e69d69dced0`.
The great-circle distance between the inventory coordinate and the Neotoma
site point is **2.5264 km** (haversine, Earth radius 6371.0088 km). The
inventory is a published source for its own lake entry, but neither its
coordinate nor its 3 ha area identifies the Neotoma `BUS` pollen core.

A [Lund University literature synthesis (2019), PDF page 16](https://lup.lub.lu.se/luur/download?fileOId=8985529&func=downloadFile&recordOId=8985524)
places Bussjösjön at the coarse 55°28′ N, 13°49′ E, close to the Neotoma
site point. It reports approximately **2 ha in the early Holocene** and
**0.3 ha at the time described**, attributing shrinkage to drainage begun in
the nineteenth century. It also says cores were collected in 1984–85. These
are secondary summaries of earlier field studies, not surveyed boundaries for
the Neotoma samples. [Olsson et al. (1997)](https://link.springer.com/article/10.1023/A:1007967832177)
independently describe rerouting of the drainage system and a large reduction
in effective catchment area; catchment area is not lake surface area.

The [LandClim metadata](https://doi.org/10.1594/PANGAEA.937075) give `BUS`
`siteradius` 69 m, equivalent to **1.4957 ha** if treated as a circular lake
radius. The existing [Swedish source questions](../../../pollen-reconstruction/swedish-source-questions.csv)
also retain a 2 ha source value. These numbers have different source roles
and possible time meanings. The 2016 inventory coordinate could reflect a
transcription error or a distinct location; the available records do not
decide which. None binds a time-specific lake boundary or radius to the
Neotoma pollen samples. **Historical basin geometry and every Bussjösjön LRA
sample remain unadmitted.** Resolve the inventory coordinate against the
original lake survey and link the `BUS` core to dated basin outlines before
selecting an LRA radius. The direct observed-pollen result remains valid for
its declared coordinate-based estimand.
