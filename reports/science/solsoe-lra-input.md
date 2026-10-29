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
| [Odgaard core study](../../docs/report/countries/denmark/solsoe-source-lineage/original-core-selection/README.md) | Seven 1983 radiocarbon controls match; the paper locates two cores and gives a 9000 BC basin reconstruction. The retained historical half-unbounded central-age calculation selects 76 Neotoma point proxies, or 74 within the LandClim II age span; it omitted two stated outer boundaries and is not the complete paper-interval selection. | Neither 76 nor 74 equals 79, and a 9000 BC basin does not specify every sample-age basin. |


The complete source-calendar central-point proxy uses inclusive 1981 intervals
[-31,3490] and [7210,11650] BP and the 1983 interval[3700,7180] BP under the
existing declared `BC + 1950` arithmetic convention. That convention is not a
resolved no-year-zero calendar conversion. The paper's 9700 BC older endpoint
is extrapolated. The maintained registered replay and independent source
observer on source commit `c397f95cc2cbe8f451df17b4f7fa6a856ad71a75` both
returned native zero. The separately [retained current result](../../docs/report/countries/denmark/solsoe-source-lineage/closed-central-point-selection/report.json)
selects **75 raw central-point proxies** (55+20), or **74** (54+20) within the
LandClim II age span. The original half-unbounded 76/74 report remains unchanged
and its original execution custody is unresolved. The current replay retains
all 92 native raw records and refusals, 14 chronology-view control rows and
seven underlying radiocarbon controls. It authenticates the retained PDF's
identity and checks the existing source control declarations, without fresh
PDF table extraction or recovery of original provider history.

This is a descriptive central-value proxy, not uncertainty containment,
support overlap or analytical eligibility. Native sample 353061 has a 12417 BP
center outside the older proxy limit, while its 11495–13410 BP support overlaps
that limit. Sample 353060 has an 11507 BP center inside, with its older 12037 BP
bound outside. Sample 352996 has a 7 BP center inside the raw proxy but retains
its `refused`/`negative_bp` source status, raw younger bound −41 and normalized
BP endpoints null. No proxy flag repairs that refusal, recovers the 79 author
rows, establishes chronology equivalence or admits any Solsø sample to LRA.

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


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Solsø source site/two-core lead and 92-depth exact LegacyAge alternative join are documented.

**Unsupported claim.** Historical LandClim 79-row LRA input or age-specific shoreline.

**Actual verification performed.** Retained PANGAEA count/control, final-age and LegacyAge lineage checks are cited; index did not rerun. Separately retained maintained closed central-point replay and independent source observer both returned native zero on source c397f95cc2cbe8f451df17b4f7fa6a856ad71a75. Exact 92 raw/refusal records, 14 chronology-view rows and seven declared radiocarbon controls are retained; closed 75 and bounded 74 are descriptive proxy counts. PDF identity was authenticated without fresh table extraction or original-provider recovery.

**Remaining input or review.** LandClim names 79 Solsø rows but Neotoma has 92; age-span filtering retains 90. Selected rows/chronology, age-specific shoreline, eligible denominator, parameter mapping and R-marked rights remain open. Resolver: Solsø/LandClim source custodians and qualified Danish chronology/basin reviewer Reopen when: Actual 79-row same-core source packet with selected ages, geometry, counts, PPE and terms passes admission.

**Cause category.** data|assumption|access/rights|qualified review

**Consequence.** Do not substitute complete alternate chronology or 2.5 ha/89 m modern area for selected historical basin.

**Precise next acceptance route.** Authenticate the historical SOLSOE81/SOLSOE83 selection and exact 79-row same-core age, basin, count, PPE and rights packet; rerun the LRA prerequisite screen before revising this account or admitting historical inputs.

**Negative or refused result.** Zero Solsø LRA samples admitted; age-span filter yields 90, not 79 historical rows. Current closed 75 and bounded 74 proxies still differ from79. Native352996 remains refused/negative_bp despite descriptive central-point membership; original historical-v1 production is not recovered.

**Matched denominator.** 66 SOLSOE81 +26 SOLSOE83 =92 Neotoma samples; 91 selected observed-pollen samples; LandClim names 79. Current descriptive closed 75=55+20 and bounded 74=54+20 from 92 raw central-age records;14 control-view rows represent seven underlying declared radiocarbon controls, not 14 independent controls.

Retained evidence: [docs/report/countries/denmark/solsoe-source-lineage/report.json](../../docs/report/countries/denmark/solsoe-source-lineage/report.json), [docs/report/countries/denmark/solsoe-source-lineage/legacyage-chronology/README.md](../../docs/report/countries/denmark/solsoe-source-lineage/legacyage-chronology/README.md), [docs/report/countries/denmark/solsoe-source-lineage/closed-central-point-selection/report.json](../../docs/report/countries/denmark/solsoe-source-lineage/closed-central-point-selection/report.json), [reports/science/source-lineage/solsoe-closed-point-source.json](source-lineage/solsoe-closed-point-source.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-claim-semantic-sha256: 484b50aae85588807d48766df14c3592f2735ac11ee15c479e09cdcdd331ddfb -->
<!-- scientific-authored-source-sha256: 4645533db3784a7a63711e98b6fd01e6ef6a91a6b6cc0040ec4d305597592c36 -->
<!-- scientific-verification-and-limits:end -->
