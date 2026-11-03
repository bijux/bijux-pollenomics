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
23 time windows, an authors chronology, `siteradius = 160 m` as defined in
the workbook's `readme` sheet, and an `NR` access marker. Neotoma binds all
72 source samples to one `DALMUT` collection unit
(`neotoma:collection-unit:14989`) and one dataset
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
| LandClim II `siteradius` | 160 m, per the workbook definition | A circle with that radius has area 8.0425 ha; this does not identify a historical shoreline. |

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

We separately tested the existing Norway-excluded **observed-pollen**
predictions against [LegacyAge age intervals](../../../docs/report/regions/nordic/dalmutladdo-age-interval-sensitivity/README.md).
Only two of 72 Dalmutladdo samples have a full reported 95% interval inside
their original 500-year bin. The four frozen methods retain eight predictions
across those two bins; the other 20 originally scored bins have no eligible
sample. This is a prior-exposed pollen-only support check. It neither resolves
the historical LandClim chronology nor admits a basin or PPE for LRA.

Our already governed [31-target source-mass ledger](../../../docs/report/regions/nordic/author-taxonomy-mass/sites.csv)
accounts for all 72 selected Neotoma pollen samples at this site: **46,477
of 47,085** native pollen counts map to 19 author targets, **600** map to
author-excluded labels and **8** remain unmapped. The arithmetic closes
(46,477 + 600 + 8 = 47,085). These are observed-pollen count assignments;
they do not authenticate the LRA terrestrial denominator, resolve taxon
concepts for excluded counts or authorize a PPE/fall-speed choice.

Separately, we [allocated the LegacyAge 1.0 age summaries](../../../docs/report/source-relations/neotoma/legacyage-chronology/depth-allocation/README.md)
at the one DALMUT pollen depth absent from its exact S5 row join. The original
S4 depth metadata match all 72 Neotoma samples, and the authors' interior
allocation rule applied to published 4 and 5 cm S5 summaries yields a derived
4.5 cm minimum −94, maximum 541.5, median 257 and mean 215 calibrated years
BP. This does not identify the LandClim-selected chronology, supply a joint
posterior, or change the zero-LRA-admission decision above. Its derived
minimum-to-maximum range crosses 500-year bin boundaries and adds no sample
to the strict interval-contained pollen sensitivity.

## What would change this decision

We need a qualified sample/window packet for `DALMUT` that identifies the
selected author chronology and uncertainty, source pollen rows, historical
basin outlines or defensible age-specific radii, exact terrestrial count
denominator, reviewed taxon/PPE/fall-speed mapping and permitted analytical
use. The 7.2/8.00 ha difference and two printed age intervals need a source
explanation or a declared sensitivity treatment before numerical use. The
open Nordic LRA need retains the resolver. Once
those fields refer to the same 72 samples and windows, run the existing LRA
consumer and withheld pollen prediction; observed-pollen scores do not settle
this source gate.

Reproduce this bounded metadata/control result from the repository root with
the retained primary PDF in the qualified private source store:

```sh
source_store="/path/to/qualified/bijux-pollenomics-data"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/dalmutladdo-lra-input/replay.py \
  --repository . \
  --paper "$source_store/reference-sources/dalmutladdo/bjune-2004.pdf" \
  --output artifacts/jobs/dalmutladdo-source/replayed
```

The producer requires an absent output directory. Compare its `controls.csv`
and `report.json` byte for byte with the governed files beside this page.


## Literal Betula/Ulmus support on the common Nordic windows

The [prospective two-core source audit](../pollen-reconstruction/nordic-literal-window-support/protocol.json)
now checks the exact Betula (native ID 29) and Ulmus (310) panel against all
72 original DALMUT owners. It selects the unique calibrated **11601** point
chronology, keeping collection reference 11600, both native default flags,
all alternative ages, absent/null bounds and complete chronology declarations.
These point ages are not a recovered LandClim historical input or joint age law.

All 72 owners have complete literal pollen-NISP denominators, totaling
**47,085 grains**. Betula is reported at all 72; Ulmus is reported at 29 and
absent at 43. The absent cells are not reported zeros. The whole-core panel
is unavailable, and every requested half-open 2700–5700 BP window also
contains at least one missing Ulmus cell:

| Calibrated BP, half-open | All native members | Members missing Ulmus | Full literal pollen NISP | Two-taxon aggregate |
| --- | ---: | ---: | ---: | --- |
| 2700–3200 | 5 | 4 | 3,392 | Unavailable |
| 3200–3700 | 4 | 2 | 2,766 | Unavailable |
| 3700–4200 | 3 | 2 | 2,230 | Unavailable |
| 4200–4700 | 1 | 1 | 782 | Unavailable |
| 4700–5200 | 2 | 1 | 1,325 | Unavailable |
| 5200–5700 | 4 | 2 | 2,824 | Unavailable |

The nineteen window members retain a defined full-pollen total of 13,319.
Panel counts, panel total and outside-panel mass remain null for all six
windows; we do not aggregate only complete samples or interpret absence as
zero abundance. The companion LAIH source supplies six complete windows,
but DALMUT's missing cells prevent this declared common-axis four-country
LRA comparison. Source confirmation of the missing-value interpretation or
a genuinely compatible Norwegian source would be needed to revisit it.

The actual producer and independent source observer both pass at
`d826e04d42eab50f885ec080d315d39b324894b1`, checking all 222 LAIH/DALMUT owners,
twelve windows and the exact original byte identities. All five source pins,
4,576 tracked Python files, protocol, HEAD and index remain stable. Producer
wall time is 2.07 s at 216,088,576 B peak RSS; observer is 1.91 s at
216,186,880 B. Both meet 90 s, 1 GiB and 8 MiB bounds. All 83 controls and
twelve-file static checks pass; test setup/type failures remain retained,
with no changed source predicate or actual-run retry.

Complete local products are in
`artifacts/root/nordic-literal-window-support/study/`; independent facts are
`artifacts/verification/nordic-literal-window-support/verification.json`
(SHA-256 `ae730e5d508b53265c17ecaf921280e9781f1930950128c09079c26ab8c88fc9`).
The maintained producer is
`bijux_pollenomics_dev.essd_reproduction.nordic_coupled.literal_window_support.study`;
the independent observer is
`tests.source_completion.pollen_reconstruction.test_nordic_literal_window_support_result`
with the dev package on `PYTHONPATH`. No source acquisition, inverse fit,
kernel, model prediction, scoring or source-use decision ran. Historical
geometry, the area discrepancy, selected LandClim inputs and LRA admission
remain unresolved.

<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** One DALMUT 72-sample source lineage and 11 published radiocarbon lab/depth/age/error controls match. Explicit calibrated chronology 11601 and all 72 native owners now have complete literal pollen denominators; all six requested Betula29/Ulmus310 windows retain explicit missing-Ulmus refusal.

**Unsupported claim.** Time-matched Norwegian LRA reconstruction for the 72 samples.

**Actual verification performed.** Retained 11-row controls and source-bound machine report are cited; index did not rerun source PDF or replay. Actual two-core source producer and independent observer at d826e04d42eab50f885ec080d315d39b324894b1 pass on their first attempts: all 222 native owners, twelve windows, five source/provenance pins and 4,576 Python files with protocol, HEAD and index stable. Producer: 2.07 s, 216,088,576 B RSS, 388,030 B final products. Observer: 1.91 s, 216,186,880 B RSS, 3,181 B verification. Both meet 90 s, 1 GiB and 8 MiB bounds. All 83 controls and twelve-file static checks pass. Initial test-import, expected-exception and typing findings remain retained; only test setup or annotations changed, with no source predicate or actual-run retry. No acquisition, engine, model or score.

**Remaining input or review.** The 72-sample core and 11 lab/depth/age/error controls are matched; historical basin differs across 7.2/8.00 ha claims, two printed intervals exclude their centres, and selected denominator/PPE/rights are unbound. Resolver: DALMUT core/author custodian and qualified chronology/basin reviewer Reopen when: Same-core selected sample/window packet disposes basin and printed-interval differences and binds count, parameter and use rights.

**Cause category.** data|assumption|access/rights|qualified review

**Consequence.** Observed-pollen count assignment does not authenticate LRA denominator or historical 7.2/8.00 ha basin.

**Precise next acceptance route.** Resolve the same-core historical basin and two printed interval discrepancies in a versioned DALMUT sample/window packet, bind denominator, PPE and rights, then rerun the LRA prerequisite screen before admission.

**Negative or refused result.** Zero DALMUT LRA samples admitted; two printed calibrated intervals exclude their centres. Every requested window refuses its two-taxon aggregate as incomplete, despite complete full-pollen NISP. Missing Ulmus is not reported zero; this core does not unlock the declared common-axis four-country LRA comparison.

**Matched denominator.** 72 pollen samples, 23 LandClim windows; 46,477/47,085 native counts map to 19 author targets in observed-pollen ledger. New literal audit: 72 owners and 47,085 full-pollen NISP, 29 complete panels and 43 missing Ulmus cells. Nineteen members occupy six fixed windows with 13,319 full NISP; respective missing-Ulmus counts are 4,2,2,1,1,2. No panel or excluded mass is invented.

Retained evidence: [reports/science/dalmutladdo-lra-input/controls.csv](controls.csv), [reports/science/dalmutladdo-lra-input/report.json](report.json), [reports/science/pollen-reconstruction/nordic-literal-window-support/protocol.json](../pollen-reconstruction/nordic-literal-window-support/protocol.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
