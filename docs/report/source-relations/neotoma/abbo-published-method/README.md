# Abborrtjärnen published method and later source records

[Giesecke (2005)](https://doi.org/10.1007/s00334-005-0070-2)
reports the Abborrtjärnen pollen percentages on a terrestrial-pollen-and-spore
sum excluding aquatic taxa and *Sphagnum* spores. Radiocarbon results were
calibrated with IntCal98 and BCal; the paper used PSIMPOLL 4.10 to fit a
four-term polynomial through the calibrated dates. The paper warns that
alternative interpolation choices materially affect sample ages between dates.
The publisher identifies the article as volume 14, pages 133–147. An
[author-uploaded full text](https://www.researchgate.net/publication/226533995_Holocene_forest_development_in_the_central_Scandes_Mountains_Sweden)
provides the methodological details.

These are the **2005 publication's** choices. The later Neotoma/EPD record
selects chronology `EPD 1`, a linear interpolation through six calibrated
controls and a core top; its 107 sample ages have no retained uncertainty
bounds. The [control comparison](../abbo-age-controls/README.md) matches the
six radiocarbon lab/depth/age/error controls to PANGAEA. The Rootsi `ABB.xls`
age labels differ from Neotoma's across the sequence and do not declare their
unit or model. No source establishes that either later export selected the
published polynomial.

The paper's percentage definition is **not** a measured denominator for
Neotoma sample `173174` or a LandClim REVEALS taxon subtotal. Its 23 pollen
NISP observations total 1,206, including four `Indeterminable` grains; six
nonpollen observations total 57. The source does not supply a reviewed
per-sample denominator or a LandClim-eligible taxon mask. `E(T500)` in a
different palynological richness analysis is a rarefaction target, not this
sample's raw count. No fixed count of 500 or Bacon chronology is admitted.

The 2005 paper says that at least **1,000 pollen grains and spores** were
counted in nearly all samples. This is a counting target, not an exact count
for sample `173174`. A bounded calculation from the retained Neotoma raw
dataset `19913` (sample depth `650` in the source's unstated unit, matching
PANGAEA `6.50 m`) applies the paper's stated exclusions:

| Source count group | NISP | Treatment in calculated candidate |
| --- | ---: | --- |
| All pollen observations | 1,206 | Start |
| Aquatic pollen: *Nuphar* 1, *Nymphaea alba* 4 | 5 | Exclude |
| Nonsphagnum spores: *Equisetum* 1, *Lycopodium annotinum* 1, monolete Polypodiophyta 16 | 18 | Add |
| *Sphagnum* spores 20, *Pediastrum* colonies 13, *Pinus* stomata 6 | 39 | Outside this pollen-and-spore sum |

The resulting **candidate is 1,219** (`1,206 − 5 + 18`) if four
`Indeterminable` pollen grains were included, or **1,215** if they were
excluded. The paper does not resolve that four-grain treatment for this
export. These are source-label calculations, not an author-confirmed
percentage denominator, a fixed 500-grain count, or a REVEALS taxon subtotal.
The input is `data/neotoma/raw/neotoma_pollen_dataset_downloads/part-004.json`,
SHA-256 `d96046c88b497ba07082120e446fecacad0d9b5533d8960bdbc03811976ea435`;
the [core comparison manifest](../abbo-core-identity/manifest.json) pins
the same bytes.

Separately, the retained [author taxonomy lookup](../author-taxonomy-mass/README.md)
(SHA-256 `3a745f9b7606e5d0b59feaba2683b930c8d3990e4810f8217b69160a29a1b507`)
assigns **1,190 of 1,206 pollen NISP** in this Neotoma sample to **13**
LandClim author targets. It labels the remaining **16** grains excluded and
leaves none unmapped. This is a sample-level source-lookup partition of pollen
only. It neither includes the nonsphagnum spores in the 2005 percentage
candidate nor establishes the time-window pooling, historical input revision,
or reviewed REVEALS denominator for the LandClim ABB sequence.

The [core identity lead](../abbo-core-identity/README.md) supplies Neotoma
dataset `19913`, site `13338`, collection unit `ABBO`, sample `173174`, and
LandClim II site metadata row 968 for sequence `ABB`. The [native count
comparison](../abbo-native-correspondence/README.md) matches 107 depths and
2,183 explicit same-label count pairs across the two exports. These are
strong series correspondence, while physical-core identity, historical basin
geometry, selected LandClim chronology, complete taxon/PPE mapping, and
analytical-use rights remain unresolved. The LandClim row's 98 m **site**
radius and the PANGAEA 3 ha area do not establish an age-specific basin
radius. No ABBO LRA reconstruction is admitted.
