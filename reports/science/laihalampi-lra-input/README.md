# Why Laihalampi is a Finnish core lead, with no admitted LRA input

## Our decision

We matched a named Finnish lake, its `LAIH` sediment core and **150 source
samples** across LandClim II and Neotoma/EPD. LandClim I's reported **25.50 ha**
and the area of a 285 m circle (**25.5176 ha**) nearly agree. LandClim II's
`readme` sheet defines `siteradius` as the site radius in metres. This is a
strong physical site and sample-series lead. We admit **zero Laihalampi
samples to LRA** because
the exact author-selected ages, historical basin geometry and analytical
count/taxon/PPE/rights packet are not yet qualified for the same windows.

## What we established

LandClim II records `LAIH`, a lake, 150 pollen samples in 24 time windows,
`Authors chronology`, `siteradius = 285 m`, and an `R` access
marker. The LandClim II and Neotoma points differ by about **0.37 m** under
WGS84 geodesic distance. Neotoma site 28072 binds one `LAIH` collection unit
(37925) and EPD dataset 52082 to 150 distinct depths at 1–150 cm. The
calibrated non-parametric weighted-regression chronology supplies **150
comparable point ages**; the separate radiocarbon chronology supplies 150
context-only ages. A point age does not itself preserve its uncertainty.

Our [source-bound machine result](report.json) pins the two LandClim workbook
hashes, selected-cohort hash and the Neotoma relational parts. It records five
named radiocarbon controls plus an assumed core-top control in the Neotoma
calibrated chronology. The [original Heikkilä and Seppä paper](https://doi.org/10.1016/S0277-3791(02)00189-0)
reports a 25.5 ha lake, two parallel 150 cm cores with one used for analyses,
and 150 pollen samples. The author's [available full-text copy](https://www.researchgate.net/publication/248479486_A_11000_yr_palaeotemperature_reconstruction_from_the_southern_boreal_zone_in_Finland)
states that the fitted model used five calibrated radiocarbon dates plus an
assumed contemporary top and 11,000 cal BP base. Its Table 2 lists a sixth,
deeper date, Hela-4421. The authors explicitly excluded that date from the
age-depth fit because its calibrated age was too old relative to their
deglaciation-based basal-age estimate. Hela-4421 is also absent from the
Neotoma calibrated control set, which agrees with the paper's
control-selection decision. We have **not** authenticated the exact LandClim
II sample ages against the paper or recovered its age-depth uncertainty
series. Direct access to the author-hosted PDF returned HTTP 403; the linked
author-hosted full text supports this interpretation but does not provide
PDF byte parity. The paper's
500-terrestrial-grain counting statement describes a laboratory protocol, not
the exact denominator of each admitted LRA sample.

The agreement of two *modern* area records is not a historical shoreline
series. The early lake's independent-basin history in the paper does not
numerically specify a radius for each LandClim time window. The `R` marker
also requires an explicit analytical-use and redistribution review; we do not
infer permission from data availability or authorship.

Our already governed [31-target source-mass ledger](../../../docs/report/regions/nordic/author-taxonomy-mass/sites.csv)
accounts for all 150 selected Neotoma pollen samples at this site: **84,078
of 85,303** native pollen counts map to 24 author targets, **916** map to
author-excluded labels and **309** remain unmapped. The arithmetic closes
(84,078 + 916 + 309 = 85,303). This is an observed-pollen subcomposition,
not a verified LRA terrestrial denominator or source-approved PPE/fall-speed
mapping.

The [June 2021 LandClim II release](https://doi.pangaea.de/10.1594/PANGAEA.937075)
does publish the 31-taxon PPE and fall-speed table it says was used for its
gridded REVEALS reconstruction, under CC BY 4.0. Our retained
[`Taxa_to_PFT` table](../../../data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv)
has SHA-256 `32eac151566b41c186745dd077fabcddde06f64f9a3a2056699e88dbabd76d4d`.
That resolves availability of the released parameter table. The retained
author example binds a parameter and covariance profile to its own 17 sites,
but does not include `LAIH`. Neither source proves the exact taxon/PPE mapping
or covariance applied to Laihalampi's historical input, or grants analytical
use of its `R`-marked pollen source.

## What would change this decision

We need the LandClim-selected `LAIH` age vector/model and uncertainty, the
source pollen rows and eligible terrestrial denominator for each selected
window, a time-matched basin-radius or polygon series, a core-bound application
of the published PPE/fall-speed table and covariance profile, and
source-specific analytical rights. The paper explains
Hela-4421's exclusion; a qualified source packet must still identify the
exact age vector and uncertainty applied by LandClim II, including how the
assumed 11,000 BP base entered its selected model. The
[Nordic LRA need](../../needed/README.md)
keeps those fields open. Once bound, run actual reconstruction and withheld
forward-pollen prediction before comparing methods.

Reproduce the repository-source metadata result from the root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/laihalampi-lra-input/replay.py \
  --repository . --output artifacts/jobs/laihalampi-source/replayed
```

The output directory must be absent. Compare its `report.json` byte for byte
with the governed result beside this page. The original paper is cited for
independent context; this machine replay does not claim paper-PDF byte parity.
