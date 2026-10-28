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

On the separate [16-label Denmark-held-out pollen study]
(../../docs/report/countries/denmark/solsoe-source-lineage/legacyage-interval-sensitivity/README.md),
15 of 91 comparable Solsø samples have full LegacyAge 95% intervals inside
their original 500-year bins. They occupy eight of 24 parent bins and retain
32 previously frozen predictions across four methods. Nearest-site mean
absolute fraction error is 0.032310 on those eight restricted bins, versus
0.032104 using each bin's complete parent pollen counts. No retained sample
changes its nominal bin, so this is a sample-support sensitivity,
not a new chronology fit or evidence for LRA accuracy.

## Core ownership within the observed-pollen target

The separate observed-pollen target pools the 65 selected `SOLSOE81` samples
and 26 selected `SOLSOE83` samples into **24 nominal 500-cal-BP bins**. A
source-core decomposition reproduces every parent bin's sample and count
denominators: **129,768 reported pollen grains**, of which **38,295** belong
to the study's 16 literal labels. Both cores contribute positive counts on
that axis in **11 bins**; the remaining **13 bins** contain one core. No
shared bin has a zero denominator on that axis. These are conditional
recorded-count compositions, including `Nuphar`, rather than an eligible
terrestrial LRA denominator; a zero for an unreported label does not establish
measured ecological absence.

For the 11 shared bins, we compared each core's unsmoothed composition using
Hellinger distance, `sqrt(sum((sqrt(p)-sqrt(q))^2)/2)`. The observed core
compositions differ by **0.046596–0.218394**. The existing pooled composition
weights each core by its retained 16-label grain count; the 1981 core's
weight ranges from **0.185400 to 0.901268**. Thus a shared bin does not imply
equal core contribution. In the **9500–<10000 cal-BP** bin, four 1981 samples
contribute 1,910 retained grains and one 1983 sample contributes 358. Their
core distance is 0.218394. Averaging the two normalized core compositions
with equal weights, solely as a sensitivity comparator, differs from the
existing grain pool by Hellinger distance **0.076995**, with a maximum
absolute taxon-fraction difference of **5.26 percentage points**. This is the
largest such pooling difference across the 11 shared bins.

This decomposition preserves the frozen predictions and scores. It measures
composition and pooling sensitivity, without choosing a preferred weighting
or estimating accuracy. The two cores belong to one lake, and nominal bin
membership supplies no joint chronology posterior. The result therefore adds
neither an independent vegetation outcome nor the missing historical
79-row selection, basin geometry or analytical rights.

## What would change this decision

We need a source-owner packet naming the actual LandClim II 79 pollen rows,
their physical core and depths, selected age model with time support, and
historical basin outlines or justified age-specific radii. We also need the
eligible terrestrial count denominator, reviewed taxon/PPE/fall-speed
mapping and permitted analytical use for the `R` marked record. Those fields
must refer to the same samples and windows. The
open Nordic LRA need records the resolver and reopening
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
