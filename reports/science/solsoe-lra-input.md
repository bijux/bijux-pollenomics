# Why Solsø is still a source lead, not an admitted LRA core

## Our decision

We identified the Danish Solsø lake, its two Neotoma pollen cores and several
primary author records. We can use its **91 selected Neotoma samples** in the
country-held-out observed-pollen study. We admit **zero Solsø samples to LRA**.
The site and pollen source correspondences are real, but they do not identify
the 79 samples, chronology and historical basin geometry used in LandClim II.
We keep those missing joins as source questions rather than assigning a
modern basin size to every pollen window.

## What we established

The [source-lineage result](../../docs/report/countries/denmark/solsoe-source-lineage/report.json)
binds LandClim I's reported **2.5 ha** lake area, LandClim II's `Solsoe`
record in grid 824, and Neotoma EPD site 3432. The LandClim II metadata name
**79 pollen samples**, an authors chronology, an `R` access marker and a
`siteradius` value of **89 m**, as defined in the workbook's `readme` sheet.
A circle with that radius has area 2.488 ha, numerically close to the reported
2.5 ha. The Neotoma site centroid is about 69 m from the LandClim II point.
These comparisons support a common site lead; none dates a shoreline or binds
the radius to a selected sample.

Neotoma has **66** source samples in `SOLSOE81` and **26** in `SOLSOE83`.
Our observed-pollen cohort selects 65 and 26. The excluded 1981 sample has a
calibrated 7 BP age with a −41 BP younger bound; we refused that age claim
instead of treating it as a valid comparable age. Applying LandClim II's
published 10–11659 BP span to all 92 Neotoma calibrated ages retains **90**,
still 11 more than the published 79. That arithmetic does not reproduce the
authors chronology or sample selection.

We then checked primary records rather than guessing the missing 11 rows:

| Primary correspondence | What we confirmed | Limit for LandClim II input |
| --- | --- | --- |
| [1981 controls and area](../../docs/report/countries/denmark/solsoe-source-lineage/pangaea-core-controls/README.md) | The PANGAEA event reports 2.5 ha; 30 of 34 radiocarbon controls match Neotoma on their recorded fields. | The selected 65 Neotoma samples use a calibrated MADCAP chronology, not a demonstrated LandClim II authors chronology. |
| [1981 pollen counts](../../docs/report/countries/denmark/solsoe-source-lineage/pangaea-pollen-profile/README.md) | All 66 depths and 2,881 positive count cells match the Neotoma 1981 core; 18 renamed labels are unique numerical candidates. | The match authenticates that core's count lineage, not the 79 author sample rows or a reviewed 31-target denominator. |
| [Published final ages](../../docs/report/countries/denmark/solsoe-source-lineage/pangaea-epd-age-join/README.md) | All 92 depths occur in the EPD final-age table, with calibrated ages and bounds matching Neotoma within 0.5 BP after unit conversion. | This authenticates the EPD calibrated claims, not the later authors chronology. |
| [Odgaard core study](../../docs/report/countries/denmark/solsoe-source-lineage/original-core-selection/README.md) | Seven 1983 radiocarbon controls match; the paper locates two cores and gives a 9000 BC basin reconstruction. Its published core intervals select 76 Neotoma age proxies, or 74 within the LandClim II age span. | Neither 76 nor 74 equals 79, and a 9000 BC basin does not specify every sample-age basin. |

The 1981 source notes a hiatus near depths 472–480 that the 1983 core covers.
Core identity and chronology therefore affect the historical windows, even
where the same lake name appears in every source. The modeled LandClim I/II
vegetation products are also not independent measured vegetation outcomes.

We joined the [primary LegacyAge S5/S6 age tables]
(../../docs/report/countries/denmark/solsoe-source-lineage/legacyage-chronology/README.md)
to both Neotoma cores at exact depths: **66/66 SOLSOE81** and **26/26
SOLSOE83** samples matched. One 1981 Neotoma sample still has a refused
negative-bound age claim; the alternative age row does not repair it.
Neotoma point ages fall inside their LegacyAge 95% ranges for 57/66 samples
from 1981 and 26/26 from 1983; only 56/65 comparable 1981 age claims are
inside because the refused claim is among the 57. S6 separately describes
the original 1981 chronology as partly or wholly outside its intervals and
the 1983 chronology as within. This supports a new age-aware pollen
sensitivity. The historical LandClim 79-row selection and chosen chronology
remain unresolved.

## What would change this decision

We need a source-owner packet naming the actual LandClim II 79 pollen rows,
their physical core and depths, selected age model with time support, and
historical basin outlines or justified age-specific radii. We also need the
eligible terrestrial count denominator, reviewed taxon/PPE/fall-speed
mapping and permitted analytical use for the `R` marked record. Those fields
must refer to the same samples and windows. The
[open Nordic LRA need](../needed/README.md) records the resolver and reopening
rule. Once the packet is qualified, rerun admission, the real LRA consumer and
held-out pollen prediction before scoring the target pollen.

Reproduce the current site-lineage screen from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.solsoe_source_lineage \
  --repository . --output artifacts/jobs/solsoe-source-lineage
```

The [governed source page](../../docs/report/countries/denmark/solsoe-source-lineage/README.md)
routes each primary control, count and age check. Its machine report pins
the released LandClim and Neotoma input hashes.
