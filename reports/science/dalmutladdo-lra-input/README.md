# Why Dalmutladdo is a strong Norwegian core lead, with no admitted LRA input

## Our decision

We identified one Norwegian lake and physical sediment core across the
LandClim I and II records, the Neotoma/EPD relational release and the
[original Boreas study](https://doi.org/10.1111/j.1502-3885.2004.tb01142.x).
The LandClim II, published and Neotoma records each identify **72 pollen
samples**. All 11 published radiocarbon lab, depth, age and error controls
match the Neotoma author's chronology. This is substantially stronger source
lineage than a name-only site match. We nevertheless admit **zero Dalmutladdo
samples to LRA**: the recorded basin areas conflict, no age-specific basin
geometry has been established, and the exact eligible count/taxon/PPE use has
not been reviewed for those 72 samples.

## What we established

The LandClim II site coordinates and Neotoma site point differ by about
**0.36 m** under WGS84 distance. LandClim II lists a lake, 72 pollen samples,
23 time windows, an authors chronology, `siteradius = 160` with unstated
unit, and an `NR` access marker. Neotoma binds all 72 source samples to one
`DALMUT` collection unit (`neotoma:collection-unit:14989`) and one dataset
(`neotoma:dataset:20034`). Its author chronology
(`neotoma:chronology:14989:11601`) assigns 72 comparable calibrated sample
ages using a weighted mixed-effects regression; the separate EPD linear
chronology supplies 72 uncalibrated context ages. We did not substitute the
context chronology for the authors' model.

The paper reports 72 analyzed samples, 11 radiocarbon controls on terrestrial
macrofossils and a mixed-effects age-depth model. It describes a counting
protocol of at least 500 pollen grains and spores of terrestrial taxa, while
noting that some samples have fewer grains. This does **not** fix a common
500-grain denominator for all samples or define the eligible LRA taxon and
PPE denominator. The 500-grain statement is distinct from an `E(T500)`
richness standardization.

| Basin claim | Recorded value | Interpretation |
| --- | ---: | --- |
| Boreas Table 1 lake surface | 7.2 ha | A reported site area, without an age-specific shoreline. |
| LandClim I `SiteData`, `Area of site (ha) (*Actual size)` | `8.00*` ha | A second reported area for the named site. |
| LandClim II `siteradius` | 160, unit unstated | If metres and circular, area would be 8.0425 ha; this is a conditional calculation. |

The [11-row control ledger](controls.csv) matches every published lab ID,
depth midpoint, uncalibrated age and radiocarbon error to the Neotoma author
control. Calibrated centres match in **10/11** rows and printed calibrated
bounds match in **9/11**. The printed Hela-509 interval is 2469–2481 BP
despite a printed centre of 2736 BP; Neotoma has 2470–2763 BP. The printed
Hela-513 interval is 1695–1708 BP despite a printed centre of 3769 BP;
Neotoma has 3645–3838 BP and a centre of 3759 BP. We checked the table
image as well as extracted text. These printed intervals exclude their own
centres, so we do not silently replace them with Neotoma values or infer a
single numerical age-control parity claim.

The [machine result](report.json) binds the exact paper PDF hash, both
LandClim workbook hashes, selected cohort hash and the Neotoma relational
parts. It also records the measured site-point separation, area arithmetic
and match denominators. The paper PDF remains in the private source store;
we publish only its citation, source hash and the derived comparison ledger.

Our already governed [31-target source-mass ledger](../../../docs/report/regions/nordic/author-taxonomy-mass/sites.csv)
accounts for all 72 selected Neotoma pollen samples at this site: **46,477
of 47,085** native pollen counts map to 19 author targets, **600** map to
author-excluded labels and **8** remain unmapped. The arithmetic closes
(46,477 + 600 + 8 = 47,085). These are observed-pollen count assignments;
they do not authenticate the LRA terrestrial denominator, resolve taxon
concepts for excluded counts or authorize a PPE/fall-speed choice.

## What would change this decision

We need a qualified sample/window packet for `DALMUT` that identifies the
selected author chronology and uncertainty, source pollen rows, historical
basin outlines or defensible age-specific radii, exact terrestrial count
denominator, reviewed taxon/PPE/fall-speed mapping and permitted analytical
use. The 7.2/8.00 ha difference and two printed age intervals need a source
explanation or a declared sensitivity treatment before numerical use. The
[open Nordic LRA need](../../needed/README.md) retains the resolver. Once
those fields refer to the same 72 samples and windows, run the existing LRA
consumer and withheld pollen prediction; observed-pollen scores do not settle
this source gate.

Reproduce this bounded metadata/control result from the repository root with
the retained primary PDF at the stated private source path:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/dalmutladdo-lra-input/replay.py \
  --repository . \
  --paper /Users/bijan/bijux/bijux-pollenomics-data/reference-sources/dalmutladdo/bjune-2004.pdf \
  --output artifacts/jobs/dalmutladdo-source/replayed
```

The producer requires an absent output directory. Compare its `controls.csv`
and `report.json` byte for byte with the governed files beside this page.
