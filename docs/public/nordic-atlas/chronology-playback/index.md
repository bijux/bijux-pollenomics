---
title: Nordic Chronology Playback
audience: reader
type: analysis
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-09-06
---

# Nordic Chronology Playback

These six governed animations replay dated evidence from the oldest window
toward the present across Denmark, Finland, Norway, and Sweden. They use the
same source selectors and temporal rules as the interactive Nordic atlas.

The five Neotoma animations show discrete dated source observations. Changing
spatial visibility through time can look flow-like, but it is not evidence of
movement, migration, causation, or propagation. The open-land animation is
non-interpolated modeled context from
[PANGAEA 937075](https://doi.org/10.1594/PANGAEA.937075), published with the
[Githumbi et al. (2022) reconstruction](https://doi.org/10.5194/essd-14-1581-2022);
it is not an observed pollen trajectory. Null ages remain unavailable and are
never converted to zero.

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
| exact taxon: *Secale* | 469 nodes / 469 observations | 45 contiguous windows; 100 years except the terminal window; source taxon 967 only |
| open land (OL) | 75 modeled cells per frame | 25 source-defined windows; no interpolation |

Counts retain their declared denominator. Nodes and observations are not added
together, and the modeled-cell denominator is not compared as though it were a
pollen-observation count.

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
  <figcaption>Source-native UPHE observations only, with the same interval and four-country rules as the atlas.</figcaption>
</figure>

## AQVP — Aquatic Vascular Plants

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/neotoma-source-code-aqvp.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/neotoma-source-code-aqvp.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/neotoma-source-code-aqvp.mp4">Open the AQVP chronology video.</a>
  </video>
  <figcaption>Source-native AQVP observations only. Empty windows remain empty instead of being filled or interpolated.</figcaption>
</figure>

## Exact Taxon — *Secale*

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-967.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-967.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/neotoma-source-taxon-967.mp4">Open the exact *Secale* chronology video.</a>
  </video>
  <figcaption>Only Neotoma source taxon 967 (*Secale*): 469 nodes and 469 observations. Broader cereal categories are not silently merged into this exact-taxon view.</figcaption>
</figure>

## PANGAEA Open-Land Context

<figure class="bijux-media-card">
  <video controls preload="metadata" muted playsinline loop poster="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-ol.poster.png">
    <source src="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-ol.mp4" type="video/mp4">
    <a href="../../../gallery/nordic-atlas/chronology/media/pangaea-937075-metric-ol.mp4">Open the open-land modeled-context video.</a>
  </video>
  <figcaption>Open-land metric OL from PANGAEA 937075: 75 modeled cells in each of 25 source-defined windows from 11,700 BP toward the present.</figcaption>
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
