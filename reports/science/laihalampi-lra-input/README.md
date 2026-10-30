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

We checked the exact source chronology flags and all 300 sample-age claims
against the retained raw Neotoma download. Both chronology payloads assert
`isdefault = true`, but the collection unit's `defaultchronology` points to
**37159**, the `C14 BP` linear-interpolation model. The calibrated
`cal yr BP` model is **37160**. The normalized sample claims therefore mark
all 150 radiocarbon ages as the effective default and none of the 150
calibrated ages as that default. Source default flags do not select a common
calendar-age model: the radiocarbon series remains context-only, while the
calibrated series supplies the comparable point ages. Neither flag identifies
the LandClim-selected historical vector.

The 150 native sample depths occupy every integer position from 1 to 150.
Sorting by source depth, each chronology has **149 adjacent pairs**, with
**zero age reversals or ties**. The calibrated points span **0–11,000 BP**;
the radiocarbon points span **112.7273–8,984.615 BP**. Every point fits its
own source-declared chronology range. Those two spans use different age
bases and are not a numerical age-error comparison. These are ordering and
source-support checks, not a recovered age-depth fit or proof of complete
physical-core sampling.

All **300 raw sample-age claims lack younger and older uncertainty bounds**.
The 150 comparable calibrated claims have normalized endpoints equal to their
point ages; those degenerate display intervals do not supply a confidence
interval or joint chronology posterior. We retain the source flags, exact
point values and missing bounds without substituting radiocarbon errors or
core-top control intervals for sample uncertainty. The retained download
`data/neotoma/raw/neotoma_pollen_dataset_downloads/part-007.json` and the
relational sources remain separately bound by their exact bytes; these checks
do not change any study scores or the zero-LRA-admission decision.

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

We checked the complete primary [LegacyAge S5/S6 deposit]
(https://doi.org/10.1594/PANGAEA.933132) by its `Dataset_ID` field. Neither
table contains a row for this core's Neotoma dataset `52082`. The checked S5
and S6 SHA-256 values are respectively
`bbe0e8d5854acf091a11737ddedc10d5656f8a25c8eeb9637b85f9e69a37cb41`
and `2a058f08472199b0545e4562e6860371dfaba7ce74140b1e0b4dbdce0ce55300`.
This release supplies no LAIH sample-depth age vector; the selected-age
question remains open.

## Literal Betula/Ulmus support on the common Nordic windows

A new [prospective source audit](../pollen-reconstruction/nordic-literal-window-support/protocol.json)
asks whether the same six 2700–5700 BP windows used by the Nordic coupled
consumer have complete literal Betula (native ID 29) and Ulmus (310) counts.
Whole-core incompleteness alone could not settle that question. We accounted
for all 150 native owners, their original order, all age claims and full
chronology declarations. Selection uses calibrated model **37160**, keeping
the collection reference 37159 and both native default flags distinct.
Missing or null uncertainty bounds remain missing or null, without creating
an uncertainty law or identifying LandClim's historical selected vector.

All 150 samples have complete literal pollen-NISP denominators. The full
source total remains **85,303**, while the whole-core two-taxon panel remains
unavailable because eight Ulmus cells are absent. Those eight absences are
outside the requested windows. Every one of their **40 native sample owners**
has both requested taxa, so all six fixed windows are supported:

| Calibrated BP, half-open | Samples | Betula | Ulmus | Full literal pollen NISP | Outside the two-taxon panel |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2700–3200 | 9 | 1,582 | 33 | 5,072 | 3,457 |
| 3200–3700 | 7 | 1,702 | 58 | 4,304 | 2,544 |
| 3700–4200 | 6 | 1,381 | 50 | 3,322 | 1,891 |
| 4200–4700 | 6 | 1,421 | 62 | 3,489 | 2,006 |
| 4700–5200 | 6 | 1,669 | 41 | 3,546 | 1,836 |
| 5200–5700 | 6 | 1,713 | 53 | 3,341 | 1,575 |

The forty samples contain 23,074 literal pollen grains, of which 9,765 belong
to this two-taxon panel. This is a defined subcomposition rather than an
accepted terrestrial-pollen denominator. No missing cell was converted to zero,
no incomplete sample was silently removed, and no published parameter or
geometry was substituted. The companion Dalmutladdo audit refuses all six
two-taxon aggregates because every window contains missing Ulmus observations;
these results therefore do not yet unlock the proposed four-country LRA fit.

One producer and one independent source observer both passed at commit
`d826e04d42eab50f885ec080d315d39b324894b1`. The observer verifies every field
for all 222 LAIH/DALMUT native owners and twelve window dispositions against
the exact original parts. Five source/provenance pins, all 4,576 tracked
Python files, protocol, HEAD and index remain stable through both jobs.
Producer wall time is 2.07 s with 216,088,576 B peak RSS; observer is 1.91 s
with 216,186,880 B peak RSS. Both meet the prospective 90 s, 1 GiB and 8 MiB
bounds. All 83 integrated controls and twelve-file lint, formatting and strict
typing checks pass. Initial test-import and expected-exception mistakes remain
retained; neither changed a source predicate or required an actual-run retry.

The producer is
`bijux_pollenomics_dev.essd_reproduction.nordic_coupled.literal_window_support.study`;
the independent observer is
`tests.source_completion.pollen_reconstruction.test_nordic_literal_window_support_result`
with the dev package directory on `PYTHONPATH`. Complete local products remain
at `artifacts/root/nordic-literal-window-support/study/`; independent facts are
at `artifacts/verification/nordic-literal-window-support/verification.json`
(SHA-256 `ae730e5d508b53265c17ecaf921280e9781f1930950128c09079c26ab8c88fc9`).
This is retained-source accounting without acquisition, engine calls, model
fits, scores, new source-use permission or physical LRA admission. The zero
admission decision above remains unchanged.

## What would change this decision

We need the LandClim-selected `LAIH` age vector/model and uncertainty, the
source pollen rows and eligible terrestrial denominator for each selected
window, a time-matched basin-radius or polygon series, a core-bound application
of the published PPE/fall-speed table and covariance profile, and
source-specific analytical rights. The paper explains
Hela-4421's exclusion; a qualified source packet must still identify the
exact age vector and uncertainty applied by LandClim II, including how the
assumed 11,000 BP base entered its selected model. The
Nordic LRA need
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


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** LAIH physical site, 150-depth Neotoma/LandClim lead and original author Hela-4421 control exclusion are documented. Explicit calibrated chronology 37160 now supports complete literal Betula29/Ulmus310 counts in all six 2700–5700 BP windows across forty native owners; full-core incompleteness remains separate.

**Unsupported claim.** Selected historical Finnish LRA input or rights-qualified reconstruction.

**Actual verification performed.** Retained core machine result, original paper/control review and published parameter table are described; index did not rerun. Actual two-core source producer and independent observer at d826e04d42eab50f885ec080d315d39b324894b1 pass on their first attempts: all 222 native owners, twelve windows, five source/provenance pins and 4,576 Python files with protocol, HEAD and index stable. Producer: 2.07 s, 216,088,576 B RSS, 388,030 B final products. Observer: 1.91 s, 216,186,880 B RSS, 3,181 B verification. Both meet 90 s, 1 GiB and 8 MiB bounds. All 83 controls and twelve-file static checks pass. Initial test-import, expected-exception and typing findings remain retained; only test setup or annotations changed, with no source predicate or actual-run retry. No acquisition, engine, model or score.

**Remaining input or review.** 150 LAIH depths and parameter-table availability are known; selected LandClim age vector/uncertainty, dated basin, eligible denominator, core-specific PPE/covariance and R-marked source rights remain open. Hela-4421 exclusion is settled. Resolver: LAIH core/LandClim custodians and qualified chronology/basin/taxon reviewer Reopen when: Same-core 150-row selected age/window, geometry, count, parameter and permitted-use packet is authenticated.

**Cause category.** data|assumption|access/rights|qualified review

**Consequence.** Do not substitute modern 25.50 ha/285 m circle, alternative age rows or generic published PPE for core-specific historical support.

**Precise next acceptance route.** Authenticate the selected LAIH 150-row chronology, dated basin, denominator, PPE/covariance and rights; rerun docs/report/source-relations/neotoma/lra-prerequisites/README.md before revising this account or admitting LRA rows.

**Negative or refused result.** Zero LAIH LRA samples admitted; LegacyAge S5/S6 contain no dataset 52082 row. Whole-core two-taxon aggregate remains unavailable. The six requested windows are supported, but this supplies no historical geometry, selected LandClim vector, uncertainty law, eligible terrestrial denominator, parameter-use approval or new rights.

**Matched denominator.** 150 distinct source depths and 24 LandClim windows; observed-pollen ledger maps 84,078/85,303 native counts to 24 author targets. New literal audit: all 150 owners and 85,303 full-pollen NISP; 142 complete panels and eight absent Ulmus cells outside the six fixed windows. Forty window owners contribute 23,074 full NISP and 9,765 panel grains; no missing-to-zero conversion.

Retained evidence: [reports/science/laihalampi-lra-input/report.json](report.json), [data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv](../../../data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv), [reports/science/pollen-reconstruction/nordic-literal-window-support/protocol.json](../pollen-reconstruction/nordic-literal-window-support/protocol.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
