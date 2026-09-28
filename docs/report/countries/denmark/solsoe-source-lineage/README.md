# Solsø pollen cores and published basin metadata

The [source-bound report](report.json) compares the one Danish site in the
[country-held-out observed-pollen study](../../../regions/nordic/direct-pollen/RESULTS.md)
with the source records for [LandClim I](https://doi.org/10.1594/PANGAEA.897303)
and [LandClim II](https://doi.org/10.1594/PANGAEA.937075). The primary
published products are modeled vegetation reconstructions. Their site metadata
describe possible pollen input lineage, not independent vegetation observations.

| Source | Solsø record | Reported count and type | Basin information |
| --- | --- | ---: | --- |
| LandClim I `SiteData` | named Solsø, Bent Odgaard | pollen count not given | `Area of site (ha) (*Actual size)` = **2.5 ha** |
| LandClim II metadata, row 95 | `Solsoe`, grid **824**, author chronology | **79 pollen samples** | `siteradius` = **89**, with no unit in that column |
| [EPD/PANGAEA 740759](https://doi.pangaea.de/10.1594/PANGAEA.740759) | central `SOLSOE81` 1981 core, Bent V. Odgaard | **34 radiocarbon controls** | event explicitly reports **2.5 ha**; drained lake, now mostly fen |
| Neotoma EPD site 3432 | 1981 and 1983 cores | **92 pollen samples**; **91** selected | drained-lake description, polygon site geometry and an `area` field with no established unit |

The Neotoma source has **66** samples in core `SOLSOE81` and **26** in
`SOLSOE83`; **65** and **26**, respectively, are in the held-out cohort. The
excluded 1981 sample at source depth 98 has calibrated age 7 BP with a
**−41 BP younger bound**. Its calibrated claim is refused as `negative_bp`;
its separate uncalibrated radiocarbon claim is context only. The 1981 core
notes a hiatus near source depths 472–480 and says the 1983 core covers that
interval. This makes core and chronology selection material to an historical
reconstruction.

A conditional check of the published LandClim II age span (**10–11659 BP**)
against all 92 Neotoma calibrated sample ages retains **90**: 64 from the 1981
core and 26 from the 1983 core. The two outside values are **7** and **12417
BP**. This still exceeds the published **79** samples by 11, so applying that
age span alone does not recover its input selection. LandClim II's author
chronology might assign different ages; this check does not equate the two
chronologies.

The Neotoma site-polygon centroid lies about **69 m** from the LandClim II
site point. A circle of radius 89 m would have area **2.488 ha**, close to
the LandClim I and primary 1981 core event value of 2.5 ha. This is
conditional arithmetic: the LandClim II radius column does not state its
unit, and neither source binds a historical
lake outline to the 1981 or 1983 sample ages. The Neotoma polygon is a source
site geometry, not a dated lake shoreline. The 79 LandClim II pollen samples
also do not identify which 79 of Neotoma's 92 samples, if any, were used.

The [primary 1981 age-control join](pangaea-core-controls/README.md) links the
area claim directly to `SOLSOE81` and exactly matches 30 of its 34 published
radiocarbon rows to retained Neotoma controls on lab, depth, age, errors and
δ13C. Four published lab controls are absent in the retained Neotoma controls;
24 of the matching controls recur across both Neotoma chronologies. The
collection unit selects an EPD default linear radiocarbon model; a separate
MADCAP chronology is a calibrated `clam` model. All 65 selected 1981 pollen
samples use the latter model's comparable ages. This narrows core identity but
does not select the LandClim II author chronology or establish a historical
basin outline.

The [primary 1981 pollen-count join](pangaea-pollen-profile/README.md) now
also matches all 66 core depths and all 2,881 positive counts to the Neotoma
1981 core, with 129 exact parameter names and 18 unique numerical rename
candidates. The complete 147-parameter count total is 128,653. This
authenticates that core's Neotoma count lineage, but still does not identify
the 79 LandClim II author samples or their 31-target counting denominator.

The LandClim II metadata mark access `R` and use an **authors chronology**;
the 91 selected Neotoma samples have calibrated age claims.
The site-level similarity supports a shared Solsø location and a concrete
basin-size lead, but **zero samples are admitted to LRA** from this comparison.
An admissible reanalysis needs the actual input sample/core identity, rights,
the age-specific basin support and the matching chronology and counting rules.

Reproduce from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.solsoe_source_lineage \
  --repository . --output artifacts/jobs/solsoe-source-lineage
```

The producer checks the released LandClim II workbook and its source receipt,
reads the LandClim I `SiteData` row, reconstructs the hash-bound Nordic cohort,
and verifies the Neotoma relational source manifest. The report records input
hashes and site/core identifiers. Source-use and attribution terms are in the
[Neotoma](../../../../public/pollenomics-data/sources/neotoma.md) and
[LandClim II](../../../../public/pollenomics-data/sources/landclim.md) reviews.
