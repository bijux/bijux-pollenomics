---
title: Nordic Chronology Playback
audience: reader
type: analysis
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-09-07
---

# Nordic Chronology Playback

These twenty-five governed animations replay dated evidence from the oldest window
toward the present. Denmark, Finland, Norway, and Sweden remain available as
the same four filter scopes used by the interactive Nordic atlas; a country
with no evidence for a selected taxon remains empty and is not presented as
covered.

The seventeen Neotoma animations show discrete dated source observations. Changing
spatial visibility through time can look flow-like, but it is not evidence of
movement, migration, causation, or propagation. The eight PANGAEA animations
show non-interpolated modeled taxon, land-cover, and plant-functional-type
context from [PANGAEA 937075](https://doi.org/10.1594/PANGAEA.937075), published
with the
[Githumbi et al. (2022) reconstruction](https://doi.org/10.5194/essd-14-1581-2022);
a modeled surface is not an observed pollen trajectory. Null ages remain
unavailable and are never converted to zero.

Each rendered frame keeps the map stage clear of search, navigation, and
interactive control panels. A separate evidence key identifies the selected
series, BP window, visible and total counts, scientific posture, and color
meaning. The animations use the atlas's tile-free background so borders,
labels, and provider failures cannot obscure or compete with the evidence.

<div class="bijux-quicklinks">
  <a class="md-button md-button--primary" href="../../../report/regions/nordic/nordic_map.html">Explore the interactive atlas</a>
  <a class="md-button" href="../../../report/regions/nordic/nordic_playback_storyboards.json">Inspect the storyboard contract</a>
  <a class="md-button" href="../../../gallery/nordic-atlas/chronology/publication-manifest.json">Inspect media provenance</a>
</div>

## What Each Animation Represents

| Animation | Governed population | Temporal presentation |
| --- | ---: | --- |
| all Neotoma pollen samples | 9,988 nodes / 215,903 observations | 230 contiguous windows; 100 years except the terminal window |
| TRSH — trees and shrubs | 9,978 nodes / 114,225 observations | 230 contiguous windows; 100 years except the terminal window |
| UPHE — upland herbs | 9,928 nodes / 91,739 observations | 230 contiguous windows; 100 years except the terminal window |
| AQVP — aquatic vascular plants | 4,991 nodes / 9,666 observations | 192 contiguous windows; 100 years except the terminal window |
| Avena source-label preset | 110 nodes / 110 observations | 140 contiguous windows; 13,907–6.3 BP |
| Hordeum source-label preset | 572 nodes / 572 observations | 124 contiguous windows; 12,318–2.780076 BP |
| Triticum source-label preset | 375 nodes / 375 observations | 107 contiguous windows; 10,646–2.780076 BP |
| Secale source-label preset | 707 nodes / 707 observations | 45 contiguous windows; 4,461–0 BP |
| Cerealia source-label preset | 676 nodes / 676 observations | 119 contiguous windows; 11,891–0 BP |
| exact taxon: *Avena* | 7 nodes / 7 observations | 18 contiguous windows; 1,725–6.3 BP; source taxon 3915 only |
| exact taxon: *Hordeum* | 87 nodes / 87 observations | 67 contiguous windows; 6,645–11 BP; source taxon 3923 only |
| exact taxon: *Triticum* | 153 nodes / 153 observations | 72 contiguous windows; 7,197.5–11 BP; source taxon 969 only |
| exact taxon: *Secale* | 469 nodes / 469 observations | 45 contiguous windows; 100 years except the terminal window; source taxon 967 only |
| exact taxon: Poaceae (Cerealia) | 28 nodes / 28 observations | 24 contiguous windows; 2,337–0 BP; source taxon 416 only |
| exact taxon: *Avena/Triticum* | 34 nodes / 34 observations | 92 contiguous windows; 9,138–24 BP; source taxon 415 only |
| exact taxon: *Hordeum/Secale* | 2 nodes / 2 observations | 14 contiguous windows; 1,751–376 BP; source taxon 3924 only |
| exact taxon: *Secale cereale* | 191 nodes / 191 observations | 31 contiguous windows; 3,067–0 BP; source taxon 3926 only |
| modeled cereal type (Cerealia.t) | 75 modeled cells per frame | 25 source-defined windows; no interpolation |
| modeled *Secale cereale* | 75 modeled cells per frame | 25 source-defined windows; no interpolation |
| open land (OL) | 75 modeled cells per frame | 25 source-defined windows; no interpolation |
| evergreen trees (ET) | 75 modeled cells per frame | 25 source-defined windows; no interpolation |
| summer-green trees (ST) | 75 modeled cells per frame | 25 source-defined windows; no interpolation |
| low shrub, broadleaved evergreen (LSE) | 75 modeled cells per frame | 25 source-defined windows; no interpolation |
| grassland — all herbs (GL) | 75 modeled cells per frame | 25 source-defined windows; no interpolation |
| agricultural land — cereals (AL) | 75 modeled cells per frame | 25 source-defined windows; no interpolation |

Counts retain their declared denominator. Nodes and observations are not added
together, and the modeled-cell denominator is not compared as though it were a
pollen-observation count. Each Neotoma taxon label remains bound to its distinct
source taxon ID; similar cereal labels are not merged or silently resolved to a
species.

### Country Availability for Source-Label Presets

| Source-label preset | Denmark | Finland | Norway | Sweden |
| --- | ---: | ---: | ---: | ---: |
| Avena | 6 | 6 | 40 | 58 |
| Hordeum | 23 | 20 | 88 | 441 |
| Triticum | 6 | 9 | 60 | 300 |
| Secale | 15 | 79 | 49 | 564 |
| Cerealia | 0 | 117 | 45 | 514 |

These are literal source-label memberships rather than accepted taxonomic
classifications. A source taxon may belong to more than one preset, so preset
rows must not be added together as a unique-observation total.

### Country Availability for Exact Taxa

| Exact source taxon | Denmark | Finland | Norway | Sweden |
| --- | ---: | ---: | ---: | ---: |
| *Avena*, 3915 | 0 | 0 | 1 | 6 |
| *Hordeum*, 3923 | 0 | 19 | 7 | 61 |
| *Triticum*, 969 | 0 | 3 | 2 | 148 |
| *Secale*, 967 | 15 | 76 | 13 | 365 |
| Poaceae (Cerealia), 416 | 0 | 2 | 0 | 26 |
| *Avena/Triticum*, 415 | 6 | 0 | 28 | 0 |
| *Hordeum/Secale*, 3924 | 0 | 0 | 0 | 2 |
| *Secale cereale*, 3926 | 0 | 3 | 36 | 152 |

Values are source-observation counts, and each row reconciles to its governed
population above. Zero means no admitted observation for that exact source
taxon in that country; it does not mean absence in the past environment.

## All Neotoma Pollen Samples

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/neotoma-source-sample-presence.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/neotoma-source-sample-presence.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/neotoma-source-sample-presence.mp4">Open the all-sample chronology video.</a>
  </video>
  <figcaption>All admitted Neotoma sample-presence nodes, replayed from the oldest dated window toward the present.</figcaption>
</figure>

## TRSH — Trees and Shrubs

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/neotoma-source-code-trsh.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/neotoma-source-code-trsh.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/neotoma-source-code-trsh.mp4">Open the TRSH chronology video.</a>
  </video>
  <figcaption>Source-native TRSH observations only. The sequence shows dated observation visibility, not inferred dispersal.</figcaption>
</figure>

## UPHE — Upland Herbs

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/neotoma-source-code-uphe.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/neotoma-source-code-uphe.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/neotoma-source-code-uphe.mp4">Open the UPHE chronology video.</a>
  </video>
  <figcaption>Source-native UPHE observations only, with the same interval rules and four-country filter controls as the atlas.</figcaption>
</figure>

## AQVP — Aquatic Vascular Plants

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/neotoma-source-code-aqvp.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/neotoma-source-code-aqvp.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/neotoma-source-code-aqvp.mp4">Open the AQVP chronology video.</a>
  </video>
  <figcaption>Source-native AQVP observations only. Empty windows remain empty instead of being filled or interpolated.</figcaption>
</figure>

## Avena Source-Label Preset

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/neotoma-source-preset-avena.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/neotoma-source-preset-avena.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/neotoma-source-preset-avena.mp4">Open the Avena source-label chronology video.</a>
  </video>
  <figcaption>All observations whose literal source labels belong to the governed Avena preset: 110 nodes and 110 observations. This is not an accepted taxonomic classification.</figcaption>
</figure>

## Hordeum Source-Label Preset

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/neotoma-source-preset-hordeum.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/neotoma-source-preset-hordeum.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/neotoma-source-preset-hordeum.mp4">Open the Hordeum source-label chronology video.</a>
  </video>
  <figcaption>All observations whose literal source labels belong to the governed Hordeum preset: 572 nodes and 572 observations. Ambiguous labels remain visibly ambiguous.</figcaption>
</figure>

## Triticum Source-Label Preset

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/neotoma-source-preset-triticum.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/neotoma-source-preset-triticum.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/neotoma-source-preset-triticum.mp4">Open the Triticum source-label chronology video.</a>
  </video>
  <figcaption>All observations whose literal source labels belong to the governed Triticum preset: 375 nodes and 375 observations. The sequence does not infer movement.</figcaption>
</figure>

## Secale Source-Label Preset

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/neotoma-source-preset-secale.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/neotoma-source-preset-secale.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/neotoma-source-preset-secale.mp4">Open the Secale source-label chronology video.</a>
  </video>
  <figcaption>All observations whose literal source labels belong to the governed Secale preset: 707 nodes and 707 observations. Exact and ambiguous labels stay independently inspectable.</figcaption>
</figure>

## Cerealia Source-Label Preset

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/neotoma-source-preset-cerealia.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/neotoma-source-preset-cerealia.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/neotoma-source-preset-cerealia.mp4">Open the Cerealia source-label chronology video.</a>
  </video>
  <figcaption>All observations whose literal source labels belong to the governed Cerealia preset: 676 nodes and 676 observations. This source-label view remains separate from modeled cereal context.</figcaption>
</figure>

## Exact Taxon — *Avena*

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-3915.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-3915.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-3915.mp4">Open the exact <em>Avena</em> chronology video.</a>
  </video>
  <figcaption>Only Neotoma source taxon 3915 (<em>Avena</em>): 7 nodes and 7 observations.</figcaption>
</figure>

## Exact Taxon — *Hordeum*

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-3923.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-3923.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-3923.mp4">Open the exact <em>Hordeum</em> chronology video.</a>
  </video>
  <figcaption>Only Neotoma source taxon 3923 (<em>Hordeum</em>): 87 nodes and 87 observations.</figcaption>
</figure>

## Exact Taxon — *Triticum*

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-969.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-969.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-969.mp4">Open the exact <em>Triticum</em> chronology video.</a>
  </video>
  <figcaption>Only Neotoma source taxon 969 (<em>Triticum</em>): 153 nodes and 153 observations.</figcaption>
</figure>

## Exact Taxon — *Secale*

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-967.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-967.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-967.mp4">Open the exact <em>Secale</em> chronology video.</a>
  </video>
  <figcaption>Only Neotoma source taxon 967 (<em>Secale</em>): 469 nodes and 469 observations. Broader cereal categories are not silently merged into this exact-taxon view.</figcaption>
</figure>

## Exact Taxon — Poaceae (Cerealia)

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-416.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-416.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-416.mp4">Open the exact Poaceae (Cerealia) chronology video.</a>
  </video>
  <figcaption>Only Neotoma source taxon 416, Poaceae (Cerealia): 28 nodes and 28 observations.</figcaption>
</figure>

## Exact Taxon — *Avena/Triticum*

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-415.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-415.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-415.mp4">Open the exact <em>Avena/Triticum</em> chronology video.</a>
  </video>
  <figcaption>Only Neotoma source taxon 415 (<em>Avena/Triticum</em>): 34 nodes and 34 observations. It is not resolved to either genus.</figcaption>
</figure>

## Exact Taxon — *Hordeum/Secale*

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-3924.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-3924.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-3924.mp4">Open the exact <em>Hordeum/Secale</em> chronology video.</a>
  </video>
  <figcaption>Only Neotoma source taxon 3924 (<em>Hordeum/Secale</em>): 2 nodes and 2 observations. It is not merged into either genus.</figcaption>
</figure>

## Exact Taxon — *Secale cereale*

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-3926.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-3926.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-3926.mp4">Open the exact <em>Secale cereale</em> chronology video.</a>
  </video>
  <figcaption>Only Neotoma source taxon 3926 (<em>Secale cereale</em>): 191 nodes and 191 observations. This observed source category remains separate from the modeled PANGAEA metric below.</figcaption>
</figure>

## PANGAEA Modeled Cereal Type — Cerealia.t

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-cerealia-t.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-cerealia-t.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-cerealia-t.mp4">Open the modeled cereal-type chronology video.</a>
  </video>
  <figcaption>Cerealia.t modeled context from PANGAEA 937075: 75 modeled cells in each of 25 source-defined windows. This surface is distinct from exact source-taxon observations and is not an abundance or propagation claim.</figcaption>
</figure>

## PANGAEA Modeled *Secale cereale*

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-secale.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-secale.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-secale.mp4">Open the modeled <em>Secale cereale</em> chronology video.</a>
  </video>
  <figcaption><em>Secale cereale</em> modeled context from PANGAEA 937075: 75 modeled cells in each of 25 source-defined windows. It is kept separate from Neotoma source taxon 967 and is not treated as an observed trajectory.</figcaption>
</figure>

## PANGAEA Open-Land Context

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-ol.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-ol.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-ol.mp4">Open the open-land modeled-context video.</a>
  </video>
  <figcaption>Open-land metric OL from PANGAEA 937075: 75 modeled cells in each of 25 source-defined windows from 11,700 BP toward the present.</figcaption>
</figure>

## PANGAEA Evergreen-Tree Context

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-et.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-et.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-et.mp4">Open the evergreen-tree modeled-context video.</a>
  </video>
  <figcaption>Evergreen-tree land-cover metric ET from PANGAEA 937075: 75 modeled cells in each of 25 source-defined windows. It is context, not a source-observation or propagation layer.</figcaption>
</figure>

## PANGAEA Summer-Green-Tree Context

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-st.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-st.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-st.mp4">Open the summer-green-tree modeled-context video.</a>
  </video>
  <figcaption>Summer-green-tree land-cover metric ST from PANGAEA 937075: 75 modeled cells in each of 25 source-defined windows. It is not silently combined with ET or source pollen observations.</figcaption>
</figure>

## PANGAEA Low-Shrub Context

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-lse.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-lse.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-lse.mp4">Open the low-shrub modeled-context video.</a>
  </video>
  <figcaption>Low shrub, broadleaved evergreen source PFT code LSE from PANGAEA 937075: 75 modeled cells in each of 25 source-defined windows.</figcaption>
</figure>

## PANGAEA Grassland Context

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-gl.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-gl.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-gl.mp4">Open the grassland modeled-context video.</a>
  </video>
  <figcaption>Grassland — all herbs source PFT code GL from PANGAEA 937075: 75 modeled cells in each of 25 source-defined windows.</figcaption>
</figure>

## PANGAEA Agricultural-Land Context

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-al.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-al.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-al.mp4">Open the agricultural-land modeled-context video.</a>
  </video>
  <figcaption>Agricultural land — cereals source PFT code AL from PANGAEA 937075: 75 modeled cells in each of 25 source-defined windows. It remains distinct from exact cereal-taxon evidence.</figcaption>
</figure>

## Scientific Boundary

Candidate succession remains refused with reason
`accepted_scientific_classifications_not_available`. Accordingly, these media
contain no arrows, inferred edges, interpolated heat flow, or causal migration
claim. A future propagation product must first admit versioned scientific
classifications, retain uncertainty, apply the same rules across borders, and
publish sensitivity and refusal evidence alongside any candidate edges.

The [interactive Nordic atlas](../../../report/regions/nordic/nordic_map.html)
supports exact ecological-code and taxon selection, Older and Newer navigation,
playback, and direct inspection of the active denominator and visible count.
