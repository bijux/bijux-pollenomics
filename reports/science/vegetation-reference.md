# What our vegetation references can establish

The [historical-map paper account](smaland-historical-maps-paper.md),
[southern Swedish validation account](southern-sweden-validation-paper.md)
and [Namibian source-paper account](namibia-pollen-vegetation-paper.md)
explain the published methods and examples before this repository's
source-admission decisions. Their published results and our bounded source
checks have separate populations. The [main-paper inventory](paper-accounts.md)
keeps the underlying original studies and partial source access explicit.

## Our decision

We require an independent vegetation measurement matched to a pollen sample
in physical site, time, taxon response and spatial support before scoring a
repository prediction as vegetation accuracy. We screened the available
Swedish forest plots, historical maps and published REVEALS comparison under
that rule. None supplies an admitted pair for the predictions we produced.
The [EMPD2–NFI decision](../../docs/report/validation/empd2-nfi-pairing/report.json)
retains **zero admitted measured pairs** among 16 nearby candidates. We have
therefore not calculated a repository vegetation accuracy score.

The maintained outcome-blind source replay and independent observer on source
commit `97be88f37a117a518c8c4639ccca98927e13cb24` both returned native zero;
the [retained source witness](vegetation-reference/empd2-nfi-pairing-source.json)
binds their exact public CSV and report. All 16 leads remain refused and zero
measured pairs are admitted. The replay joins all 16 native pollen records,
26 source fields and 19 public fields, and selects only six NFI metadata
columns across 43,892 rows and 6,018 tract/plot keys. It calls no outcome
decoder or LRA implementation. XML/sharedStrings bytes were read; this is
not a claim that raw outcome bytes were unread. Sixteen selected distances
were independently checked, without repeating the full spatial screen.
Original source/resource copies and omitted bytecode identities remain
distinct; this is not fresh-compilation, ecological or human acceptance.

We separately acquired the original CC BY 4.0 [Namibian modern soil-pollen and
vegetation tables](../../docs/report/vegetation-reference/namibia-pollen-vegetation/README.md)
from PANGAEA. Their source-bound join contains ten pollen sites and 150
site-radius vegetation rows, yielding 750 five-taxon pairs. These are actual
published observations, but their soil samples, savanna taxa, calculated
vegetation areas and unspecified sample/image dates do not match any Nordic
lake prediction. Repeated radius rows are not independent pollen samples.
We retain the joined rows as an out-of-domain development source without a
model score or a selected pollen-source radius. We then compared the conditional
five-taxon pollen and vegetation compositions at each of the publisher's 15
radius labels. The [site-level descriptive distances](../../docs/report/vegetation-reference/namibia-pollen-vegetation/radius-sensitivity.csv)
retain ten sites per label; their mean Hellinger distances are **0.3664** at
100 m, **0.3427** at 400 m and **0.3777** at 1,500 m. The
[source-bound calculation](../../docs/report/vegetation-reference/namibia-pollen-vegetation/radius-sensitivity.json)
does not determine whether the publisher's areas describe rings or cumulative
disks and does not choose a pollen-source radius. It compares two observed
subcompositions; it is not a model prediction score.

## Fixed forest-plot development comparison

The [16-row forest-plot table](vegetation-reference/forest-plot-pollen.csv)
opens the five native NFI basal-area fields for the already selected leads.
Its [descriptive protocol](../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/vegetation/forest_plot_pollen.py)
was committed at `c4772abcffa57deeaeb5349ce2628b20d3ac60e2` before these
basal-area outcomes were decoded. The earlier outcome-blind witness above
remains a record of its own execution; it does not describe this later run.
All 16 leads are exposed development material, including Färskesjön, whose
tree volume was previously examined. No lead, distance, taxon, radius or
outcome-based exclusion was selected after viewing these results.

There are **14 distinct physical plots and 14 plot-years**, not 16 independent
vegetation measurements. Two plot-years each occur in two lead rows. The table
reuses the existing opaque plot-year identities and publishes no additional
private plot keys, coordinates or dates. Source-bound workbook metadata
declares **m²/ha** and a **7 m circular plot, 153.94 m²**; these small-plot
quantities are neither landscape cover nor the lake's pollen source area.

The run decoded all **70 unique basal-area cells** successfully and retained
all 16 rows, including refusals:

| Result under the frozen three-genus rule | Leads | Meaning |
| --- | --- | --- |
| Missing at least one exact canonical pollen genus row | 12 | Absence remains missing; neither aliases nor zero-fill repair the panel. |
| Zero selected basal-area denominator | 3 | All five basal fields are present, but the selected tree subcomposition is undefined. |
| Complete descriptive comparison | 1 | Both selected subcompositions are defined; this does not admit a vegetation-reference pair. |

The provisional development crosswalk is Pinus = BaPine + BaContorta,
Picea = BaSpruce and Betula = BaBirch; BaOtherDec remains a separate reported
field. This is not a qualified botanical equivalence. Pollen uses only native
canonical variables 75, 126 and 12, respectively, with the original count and
digitisation flags checked. Thirteen absent genus cells affect the 12 incomplete
panels; none is replaced by a measured zero. No noncanonical alias rows linked
to these three IDs occurred in the selected count rows. The table retains the
literal sum of all reported native
values and its selected/excluded partition for accounting. Other variables
can have sum or nonpollen roles, so this is not a guaranteed grain count,
complete pollen denominator or biological-coverage estimate.

Only the existing Färskesjön lead, `Nielsen_b4`, has a complete comparison.
Its selected basal area is **5.5707963941942589 m²/ha** out of
**36.6073331238383109 m²/ha** across the five fields: 15.22% selected and
84.78% BaOtherDec. Its selected pollen counts are 279 Pinus, 13 Picea and
362 Betula, totaling 654. The half-L1 distance between the two conditional
three-genus compositions is **0.42660550458715596**. This is descriptive
discordance between different quantities, not prediction error, vegetation
accuracy, regional forest composition or an LRA result. One retained value
does not supply an independent validation population, a confidence interval
or a success threshold. All 16 vegetation-pair admissions remain false;
time, spatial footprint, taxonomy, rights and qualified benchmark decisions
remain unresolved.

The actual command returned native zero in **4.79 s** and produced the
**6,859-byte CSV** with unchanged source Git/worktree and original raw-source
identities. Forty-two synthetic cell, count, identity, denominator, refusal
and public-output controls passed, together with configured lint, formatting
and strict types. Independent code review covered the scientific and private
output boundaries. A separate original-XML/SQLite and Decimal80 check confirmed
all 16 rows, 70 unique basal cells/80 mapped values, 476 reported native count
rows, exact integer/decimal sums and all refusal decisions. Ninety nonempty
fraction/difference/distance displays satisfy the fixed **2e-16** comparison
bound; the maximum absolute difference is **4.66e-17**. Reconstructing the
existing opaque identities reused only the shared pyproj 3.7.2 coordinate
transformation primitive; this is not independent geodesy. The original
workbook, SQLite source and source-bound measurement schema retain their
existing integrity pins; no source files or
datasets are copied into this result.

## What we checked

| Evidence | What we established | Why it does not validate our predictions |
| --- | --- | --- |
| [Färskesjön EMPD2–NFI lead](../../docs/report/vegetation-reference/farskesjon/README.md) | A May 2013 forest plot has measured tree volume, a 7 m radius and a source point 427.122 m from the lake surface pollen point. The pollen collection note says September 2013. | A small, separated plot does not measure the lake's landscape pollen source area. Its five volume classes are not 31-taxon vegetation-cover fractions; the plot precedes the possible September sample days by 107–136 days. We refused this pair. |
| [Cui et al. historical maps](../../docs/report/vegetation-reference/smaland-historical-maps/README.md) | Three bogs have published map-coverage percentages within 3 km and one dated pollen sample per bog shared by the two modern windows. | The article and appendix do not give the full numerical class areas or distance-weighted fractions needed for an exact vegetation target. Complete modern map coverage is not a second independent pollen sample. We retain source support, not a scored pair. |
| [Published southern Swedish Figure 6](../../docs/report/vegetation-reference/southern-sweden-figure/README.md) | On nine region/taxon labels printed in all three panels, the published REVEALS estimates have mean absolute error 5.11 percentage points from the figure's observed vegetation, versus 17.33 for published raw pollen. | This is a rounded, label-selected reading of another study's two regional figures. It does not score our model, recover its 26-taxon result or provide nine independent landscapes. |

The [Färskesjön machine decision](vegetation-reference/farskesjon/report.json)
retains the measured plot volume, date, distance and private-source hashes;
plot identifiers and coordinates remain private. The
[historical-map coverage rows](vegetation-reference/smaland-historical-maps/coverage.json)
keep the distinct TW3 and TW4 map periods and the three shared pollen counts.
The [published-figure calculation](vegetation-reference/southern-sweden-figure/report.json)
and [printed-label transcription](vegetation-reference/southern-sweden-figure/printed-labels.csv)
keep the nine-label denominator visible. Their source-bound producers and
reproduction commands are grouped here with those governed results.

We separately projected the recovered [Pyrenees botanical surveys](../../docs/report/vegetation-reference/pyrenees-botanical-projection/README.md) onto a declared 17-axis botanical panel. Each strict scenario refuses all 125 complete vectors when source blanks remain unknown; eight separately declared taxonomy, parent-row and blank alternatives that treat blanks and unlisted axes as zero yield 125 conditional vectors each. The recovered 125-plot source is distinct from the paper’s 116-plot selection, and its missing Cichorioideae axis prevents full 18-axis reproduction. This source transformation establishes no matched pollen cohort or vegetation accuracy score.

## Why modeled cover is not a vegetation reference

We checked whether the southern Sweden LandClim modeled-cover grid could
independently validate our observed-pollen lakes. The [source-lineage
receipt](../../docs/report/countries/sweden/pollen-model-lineage/report.json)
matches Neotoma sites Abborrtjärnen, Bussjösjön and Bökesjön to LandClim II
site records ABB, BUS and BOKE. Each pair has the same site sample count
(107, 69 and 52) and coordinates within 0.5 m after source rounding.
LandClim lists these as reconstruction inputs. This is strong site-level
lineage evidence, though exact sample reuse and influence on each grid result
are not authenticated.

Bussjösjön and Bökesjön both belong to grid **779**, used by five of the six
[southern Sweden synthesis targets](../../docs/report/countries/sweden/sweden_land_use_synthesis_v66.csv).
Finjasjön uses grid 829, which alone does not establish independence from
other pollen inputs. LandClim cover is a modeled result rather than a measured
vegetation outcome. We therefore do not score the grid against these pollen
sites as independent vegetation validation. The source observations remain
useful for descriptive comparison, with their distinct chronology and basin
limits visible.

## Reproduction

From the repository root, run the three vegetation-source producers with
their pinned private packets and the modeled-lineage consumer into absent
destinations under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/vegetation-reference/farskesjon/plot_support.py \
  --source-root /path/to/private/reference-sources/empd2-nfi \
  --output artifacts/jobs/vegetation-reference/farskesjon.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/vegetation-reference/smaland-historical-maps/coverage.py \
  --source-root /path/to/private/reference-sources/smaland-historical-maps \
  --output artifacts/jobs/vegetation-reference/smaland.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/vegetation-reference/southern-sweden-figure/compare.py \
  --source-pdf /path/to/private/reference-sources/southern-sweden-vegetation-validation/gaillard-2010.pdf \
  --output artifacts/jobs/vegetation-reference/southern-figure
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_model_lineage \
  --repository . --output artifacts/jobs/vegetation-reference/model-lineage
```

The first three producers reproduce four numeric files byte for byte. The
model-lineage producer writes its separate governed JSON receipt. These
source-bound producers and result files retain the exact identities. The
plot replay reads original source bytes but publishes no private plot
identifiers or coordinates.

The separate forest-plot comparison uses the same shared source store and an
absent output path. This reproduces the frozen development question rather
than the earlier outcome-blind source replay:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m \
  bijux_pollenomics_dev.source_completion.vegetation.forest_plot_pollen \
  --repository . --private-source-store "$SOURCE_STORE" \
  --output artifacts/science/forest-plot-pollen/comparison.csv
```

`SOURCE_STORE` is the existing shared store containing
`reference-sources/empd2-nfi/`. The actual run used source commit
`c4772abcffa57deeaeb5349ce2628b20d3ac60e2`; its CSV is retained above.
New confirmatory work needs a distinct, independently grouped cohort, with
reviewed outcomes and a frozen benchmark before test-label access. These
already exposed 16 leads cannot become that cohort by changing the genus
rule or calling their basal-area fields newly unopened.

## What follows

We can use these sources to explain spatial coverage, reject an unsuitable
plot, and compare values printed in the historical paper. We cannot use any
of them as an independent ecological outcome for our Nordic observed-pollen
models or English LRA forward-pollen study. The country and lake pollen scores
in this repository compare predicted pollen with observed pollen; they do not
become vegetation scores because a nearby map, plot or published validation
figure exists.

To change that decision, we need a source-owner-reviewed set of original
vegetation fractions and pollen counts, with linked physical cores, dates,
taxon mapping, landscape support and rights. The full Hellman ten-lake
source data or another independently matched cohort could meet that need.
We will freeze the benchmark and predictions before viewing its outcomes.
The open research need records the requested source
packet and resolver.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Source-bound plot/map/printed-figure screens, modeled-input dependence and modern Namibia descriptive comparisons preserve separate populations. Actual Pyrenees 17-axis botanical projection retains all 16 declared scenarios and their source/refusal/conditional assumptions without a matched pollen cohort or vegetation score. A separately frozen, source-bound NFI development comparison retains all 16 leads: 12 missing exact canonical pollen panels, three zero selected basal-area denominators and one different-estimand descriptive comparison.

**Unsupported claim.** Nordic repository measured-vegetation accuracy, independent validation by LandClim/HYDE modeled cover, full Pyrenees 18-axis or 116-plot paper reproduction, or vegetation accuracy inferred from botanical projection or Namibia descriptive distances. The NFI basal-area versus pollen comparison does not establish vegetation prediction accuracy or an untouched benchmark.

**Actual verification performed.** Original plot/map/nine-label/Namibia sources and modeled LandClim dependency checks are synthesized from retained producer outputs. Pyrenees actual native/maintained/canonical captures retain 54 guards and 64424 independent Decimal comparisons at 2e-13 tolerance; new code/name, parent and blank alternatives preserve positive source mass and ambiguity. That earlier index refresh performed no source reacquisition, numerical model or qualified human review. Separately retained maintained outcome-blind source replay and independent observer both returned native zero on source commit `97be88f37a117a518c8c4639ccca98927e13cb24`; both public products are byte identical. All 16 native records, 26 source fields, 19 public fields, 43,892 metadata rows and 6,018 tract/plot keys and six selected metadata columns are bound; outcome decoder and LRA implementation counters remain zero. Sixteen selected distances were independently rechecked, not the full screen. Original timeout remains whole exit 1/native exit 124; no cache/source equivalence or new metadata job is claimed. The later outcome-opening consumer at c4772abcffa57deeaeb5349ce2628b20d3ac60e2 returned native zero in 4.79 s with unchanged source Git/worktree and raw identities, writing the 6859-byte CSV. It binds the original 16 leads, 14 distinct physical plots and plot-years, 70 unique basal-area cells, literal canonical pollen IDs 75/126/12 and all reported-value accounting sums. Forty-two synthetic controls, configured lint/format/strict types and independent scientific/private-output code review pass. No model, LRA, source acquisition or qualified human admission is supplied. Independent original XML/SQLite plus Decimal80 verification confirms all 16 rows, 14 physical plots/plot-years, 70 unique BA cells/80 mapped values, 476 native reported count rows, exact sums, 13 absent genus cells across 12 incomplete panels and all 15 refusals. Ninety fraction/difference/TV displays pass the predeclared 2e-16 bound (maximum absolute difference 4.66e-17); only the shared pyproj 3.7.2 CRS primitive is reused for existing opaque identities, not independent geodesy.

**Remaining input or review.** Nordic EMPD2-NFI, historical-map and printed-figure leads yield zero admitted site/time/taxon/footprint/units/rights matched prediction-reference pairs. Namibia modern observed subcompositions have distinct savanna soil-pollen support. Pyrenees botanical vectors are conditional on taxonomy, parent-row and zero-for-blank scenarios; recovered 125 plots differ from the unrecovered paper 116 selection and lack Cichorioideae/full 18-axis reproduction. The frozen forest-plot development table gives one descriptive comparison and 15 refusals; these exposed, unmatched quantities do not constitute a predictive validation cohort. Resolver: Measurement and pollen source custodians plus independent landscape/palynology/taxonomy and rights reviewers Reopen when: A source-owner-reviewed original vegetation/pollen packet supplies genuinely matched physical sites, dates, taxa, landscape support, units, uncertainty and terms; freeze benchmark and predictions before previously unopened outcomes.

**Cause category.** data|assumption|comparability|access/rights|qualified review

**Consequence.** Keep all source and model roles separate, null vegetation metrics unchanged and original 125/author 116/full 18-axis panel populations distinct. Publish aggregate qualified accounts while private detailed botanical/taxonomy and plot records retain their source-specific rights limits. Preserve the strict pre-outcome genus rule and missing-versus-zero distinction; all 16 leads are development-exposed, including prior Farskesjon volume access. Reported native-value sums are accounting totals, not assured grains or a complete pollen denominator.

**Precise next acceptance route.** Acquire original measured fractions and pollen counts with linked physical cores, dates, taxon crosswalk, compatible landscape footprint/units/uncertainty and intended-use rights; obtain independent pairing/benchmark decisions, freeze predictions before new outcomes, then score eligible channels and update model-use. Pyrenees historical reproduction separately needs the author 116 plot selection, complete 18-axis mapping and source-qualified taxonomy/blank/rights decisions. The exposed 16-lead NFI cohort cannot supply unopened confirmation; use a distinct, independently grouped and qualified future cohort.

**Negative or refused result.** Zero of 16 nearby EMPD2-NFI candidates admitted; Färskesjön footprint/volume/date mismatch and missing historical-map numeric fractions remain. Pyrenees 8 strict unknown-blank scenarios refuse 1000 complete vectors; eight declared-zero alternatives yield 1000 conditional vectors. Missing Cichorioideae, Potentilla genus proxy and 25 original zero-code analyst associations remain explicit; Nordic vegetation score stays unavailable. The new 16-row NFI development table retains 12 missing canonical pollen panels and three zero selected basal-area denominators; only Nielsen_b4 has defined selected subcompositions (descriptive half-L1 0.42660550458715596), and all 16 vegetation-pair admissions remain false.

**Matched denominator.** 16 nearby Nordic leads;three Småland bogs with shared modern pollen anchors;nine printed labels across two published regional figures;ten Namibian soil sites/150 radius rows/750 five-taxon pairs. Separate Pyrenees 125 recovered plots/208 taxa/1757 positive observations:16 scenarios,2000 plot contexts,34000 raw axis cells;1000 strict refusals and 1000 conditional 17-axis vectors. None is a pooled independent accuracy population. Separate NFI development calculation: 16 fixed leads, 14 physical plots/14 plot-years, two plot-years reused twice, five BA fields/70 unique cells, 15 refusals and one descriptive comparison; no independent validation population.

Retained evidence: [reports/science/vegetation-reference/farskesjon/report.json](vegetation-reference/farskesjon/report.json), [reports/science/vegetation-reference/smaland-historical-maps/coverage.json](vegetation-reference/smaland-historical-maps/coverage.json), [reports/science/vegetation-reference/southern-sweden-figure/report.json](vegetation-reference/southern-sweden-figure/report.json), [docs/report/validation/empd2-nfi-pairing/report.json](../../docs/report/validation/empd2-nfi-pairing/report.json), [docs/report/vegetation-reference/namibia-pollen-vegetation/report.json](../../docs/report/vegetation-reference/namibia-pollen-vegetation/report.json), [docs/report/vegetation-reference/namibia-pollen-vegetation/radius-sensitivity.json](../../docs/report/vegetation-reference/namibia-pollen-vegetation/radius-sensitivity.json), [docs/report/vegetation-reference/pyrenees-botanical-projection/report.json](../../docs/report/vegetation-reference/pyrenees-botanical-projection/report.json), [docs/report/vegetation-reference/pyrenees-botanical-projection/source-account.json](../../docs/report/vegetation-reference/pyrenees-botanical-projection/source-account.json), [reports/science/vegetation-reference/empd2-nfi-pairing-source.json](vegetation-reference/empd2-nfi-pairing-source.json), [reports/science/vegetation-reference/forest-plot-pollen.csv](vegetation-reference/forest-plot-pollen.csv).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
