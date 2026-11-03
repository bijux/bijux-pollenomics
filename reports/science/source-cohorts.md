# How we selected source cohorts and comparisons

We selected Neotoma/EPD counts and the authors' exact taxonomy lookup for the
[Denmark/Finland/Norway](denmark-finland-norway-author-pollen.md) and
[Swedish](sweden-author-pollen.md) 31-target observed-pollen studies. We
excluded each target country from training before prediction. This tests
pollen composition transfer on one Danish, 28 Finnish, 52 Norwegian and
three Swedish physical sites. We retained native count mass, assignments,
excluded names, refused site-bins and frozen prediction identities. We keep
the 31-target closed denominator separate from the earlier 16-label result.
Neither study admits its samples to LRA.

We use the [governed source-capability report](../../docs/report/regions/nordic/source-capability/README.md)
to distinguish source-reported, governed-assignment and publication
availability across 11 families and six country partitions. We do not select
an analytical cohort from those family-level cells. Our selected
**observed-pollen** cohorts have these source denominators and scored bins:

| Country | Physical sites | Selected samples | Assigned/native pollen NISP | Scored/attempted 500 BP bins | Governed result |
| --- | ---: | ---: | ---: | ---: | --- |
| Denmark | 1 | 91 | 122,998/129,768 | 24/24 | [DK/FI/NO result](../../docs/report/regions/nordic/author-target-pollen/report.json) |
| Finland | 28 | 1,797 | 1,229,019/1,260,281 | 435/435 | [DK/FI/NO result](../../docs/report/regions/nordic/author-target-pollen/report.json) |
| Norway | 52 | 3,544 | 2,018,295/2,286,020 | 1,084/1,178 | [DK/FI/NO result](../../docs/report/regions/nordic/author-target-pollen/report.json) |
| Sweden | 3 | 228 | 221,800/240,966 | 51/54 | [Swedish result](../../docs/report/regions/nordic/swedish-author-target-pollen/report.json) |

The governed results own the site, sample and count-mass values. Their
[DK/FI/NO coverage](../../docs/report/regions/nordic/author-target-pollen/coverage.csv)
and [Swedish coverage](../../docs/report/regions/nordic/swedish-author-target-pollen/coverage.csv)
retain every attempted and scored bin. The [DK/FI/NO input manifest](../../docs/report/regions/nordic/author-target-pollen/input-manifest.json),
[Swedish input manifest](../../docs/report/regions/nordic/swedish-author-target-pollen/input-manifest.json),
[DK/FI/NO scores](../../docs/report/regions/nordic/author-target-pollen/scores.csv)
and [Swedish scores](../../docs/report/regions/nordic/swedish-author-target-pollen/scores.csv)
retain prediction identities and results. We refused 94 Norwegian bins and
three Swedish bins without eligible training support instead of recording
zero-valued predictions. Denmark's single site cannot estimate within-country
between-site variation. We treat all four country results as development
evidence because the Nordic outcomes were previously exposed.

### Native sequence boundaries in the exposed cohort

We checked endpoint support in the same **5,660 selected samples at 84 sites**,
preserving each dataset and physical collection unit. These define 85 source
sequences: the Danish site contains two distinct cores. Another 180 captured
samples belong to those same owners, giving 5,840 samples for the separate
captured-owner comparison. This context does not enlarge the selected cohort
or establish that a complete historical sequence was captured. The
[compact result](source-cohorts/neotoma-sequence-support/report.json),
[eight country/scope rows](source-cohorts/neotoma-sequence-support/countries.csv)
and [five refusal owners](source-cohorts/neotoma-sequence-support/refusals.csv)
retain their separate denominators.

| Country | Selected / captured samples | Dataset–collection-unit sequences | Native taxon rows per scope | Positive at bottom, selected / captured | Depth/count-refused rows, selected / captured |
| --- | ---: | ---: | ---: | ---: | ---: |
| Sweden | 228 / 228 | 3 | 295 | 37 / 37 | 0 / 0 |
| Denmark | 91 / 92 | 2 | 235 | 54 / 54 | 0 / 0 |
| Finland | 1,797 / 1,946 | 28 | 1,583 | 450 / 447 | 6 / 9 |
| Norway | 3,544 / 3,574 | 52 | 4,299 | 1,108 / 1,108 | 67 / 67 |

Each taxon row retains one native variable ID, taxon ID and reported name at
one dataset/collection-unit owner. It is **not** a unique regional taxon,
31-target author composite, biological arrival or independent observation.
Across 6,412 rows per scope, 2,135 selected versus 2,098 captured rows have a
reported positive count at the shallowest sample; corresponding deepest-sample
counts are 1,649 and 1,646. A positive endpoint flags possible observation-window
truncation. Other resolved endpoints have no listed measurement, rather than
a reported zero: selected top/bottom counts are 4,204/4,690 and captured counts
4,238/4,690. No endpoint in this result has a reported-zero-only measurement.
Missing measurements do not establish biological absence; missing and reported
zero remain distinct throughout the detailed output.

The native scan retains 185,996 observations: 124,794 valid integer pollen
NISP rows, 193 invalid NISP rows and 61,009 other-element/unit rows. It reuses
the country study's integer-only count rule; invalid values are not rounded
or converted to zero. Depth/count refusals affect 73 selected and 76 captured
taxon rows. Dataset 62017 has missing depths; 52255 and 58530 retain invalid
counts. Age-order refusal affects 309 selected and 312 captured rows, including
the depth/count refusals, an age reversal in dataset 4445 and mixed selected
chronology IDs in 45331. Individually resolved source ages are not a coherent
sequence chronology merely because every sample has an age. All 136 signed
negative captured source point ages survive, including six selected Swedish
ages. BP types and year units, the 1950 reference, exact claim IDs and physical
ownership remain explicit. The per-sample payload does not declare a depth
unit; we report native depth order and gaps without labelling them centimetres.

Read-only inspection of the original JSON tokens in the retained
[Skogstjern dataset 52255](../../data/neotoma/raw/neotoma_pollen_dataset_downloads/part-007.json)
and [Palomaa dataset 58530](../../data/neotoma/raw/neotoma_pollen_dataset_downloads/part-009.json)
clarifies these 193 count refusals: six Skogstjern Picea entries are `0.5`,
and 187 Palomaa entries across nine native taxa range from `0.5` to `1075.5`.
All are positive half-integers, with source unit `NISP` and detection status
`reported_value`; none is a mathematically integral count rejected merely
because its JSON token parsed as a float. The retained 29 September 2026
publication responses remain at
`neotoma/publication-links/2026-09-29/responses/dataset-52255-publications.json`
and `dataset-58530-publications.json` in the existing source store. They supply
publication relationships, not a rule interpreting fractional counts. The
[primary Skogstjern PANGAEA table](https://doi.pangaea.de/10.1594/PANGAEA.885277?format=html)
independently lists all six literal Picea `0.5` values at depths 2.87, 2.91,
3.07, 3.13, 3.50 and 4.14 m. Its separate rare-type notation does not establish
what those fractions mean. Neither the examined counting-method text nor
Palomaa's annual-sample/amalgamation note supplies their measurement or
encoding origin. We assume no weighting, averaging or rounding rule. This
source-token clarification adds no model, study, ecological interpretation or
scientific admission; the declared integer-count predicate, cohort and
refusals remain unchanged.

The corrected consumer ran at `5cb4cc36465da75fd9473d14552c276fb3c6b41c`,
exiting zero in **7.584 seconds**, with measured peak RSS **839,057,408 bytes**.
Its detailed CSVs total 7,084,870 bytes, within the declared 120-second,
1.5-billion-byte measured-memory and 16-million-byte output bounds. Memory and
storage were checked after execution; these were not enforced allocation or
filesystem limits. Eighteen focused controls, configured Ruff, formatting and
strict mypy pass. The independent observer at
`ce9ac38163e80127cd6a8c0a73c3d509e6713bda` reconstructed all 5,840 sample
rows, 12,824 taxon/scope rows and 185,996 native observations, including the
136 signed ages, without calling the producer's aggregation. It exited zero
in **11.221 seconds**, with peak RSS **746,553,344 bytes** and zero model fits.

The original successful invocation at `39fa622396eff889bf2e76ec7f46a476fe7f0c47`
is retained under `artifacts/nordic-sequence-support/source-run`. It incorrectly
also labelled repeated missing depths as duplicate depths. The narrow
correction compares only finite depths: all 12,824 taxon rows were compared,
and **only 132 reason fields** changed, covering 66 axes in both scopes at
dataset 62017/collection unit 45043. Every sample CSV byte, other table field,
refusal status, count and endpoint result remained unchanged. Corrected detailed
outputs and independent checks remain under
`artifacts/nordic-sequence-support/finite-depth-boundaries`; this account keeps
the compact summaries rather than another full CSV copy.

The executed commands, wrapped by the existing bounded executor and
`/usr/bin/time -l`, were equivalent to these repository-relative invocations;
the compact result preserves their literal original argument lists. Replays
require new absent output paths.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m \
  bijux_pollenomics_dev.source_completion.nordic.sequence_support \
  --repository "$PWD" \
  --output "$PWD/artifacts/nordic-sequence-support/finite-depth-boundaries"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B \
  packages/bijux-pollenomics-dev/tests/source_completion/nordic/test_sequence_support_result.py \
  --repository "$PWD" \
  --result "$PWD/artifacts/nordic-sequence-support/finite-depth-boundaries" \
  --output "$PWD/artifacts/nordic-sequence-support/finite-depth-boundaries/independent-check.json"
```

This is a source-count diagnostic on already exposed development samples,
under the retained Neotoma/EPD attribution and default CC BY 4.0 policy. No
private author taxonomy lookup is consumed or redistributed. It supplies no
biological absence, arrival date, empirical event, calibrated chronology,
historical basin or new LRA admission. The paired scopes share observations;
their endpoint counts cannot be treated as independent samples or a country
ranking. This bounded result advances the sequence-truncation diagnostic,
without completing the broader coverage/fairness or four-country scientific
acceptance requirements.

## LRA source gate

We require one identified physical core with selected chronology,
time-matched basin geometry, an eligible count and taxon denominator, fall
speeds and permitted PPE use before LRA admission. Our
[ABB source correspondence](../../docs/report/source-relations/neotoma/abbo-native-correspondence/README.md)
matches many depth and count cells, but the
[published-method review](abborrtjarnen-source-method.md)
still cannot bind the LandClim-selected age model and historical basin series.
For Solsø, our [source decision](solsoe-lra-input.md) still lacks the actual
79 LandClim II input rows, selected authors chronology and historical basin
series despite a reported area and matched age controls. For Norwegian
Dalmutladdo, our [source control comparison](dalmutladdo-lra-input/README.md)
matches 72 samples and all 11 radiocarbon source controls, while conflicting
reported areas and missing time-matched basin and analytical-use fields still
prevent LRA admission. Finnish Laihalampi has an exact 150-sample, single-core
lead and consistent modern area claims, but its [source decision](laihalampi-lra-input/README.md)
still needs the selected age vector and dated basin. We recorded these exact gaps in
research needs; we have not substituted study-wide
assumptions for a named core's missing evidence.

The existing [site-level author-taxonomy mass ledger](../../docs/report/regions/nordic/author-taxonomy-mass/sites.csv)
accounts for 84,078 assigned, 916 excluded and 309 unmapped native counts at
Laihalampi, and 46,477 assigned, 600 excluded and eight unmapped at
Dalmutladdo. Both sums close on their respective 150 and 72 selected
Neotoma samples. This reuses the prior observed-pollen study; neither
31-target subcomposition is an admitted LRA denominator.

## Context and validation sources

We reconciled [AADR v66 Nordic human Genetic IDs](aadr-nordic-entities/README.md)
against the four retained country sample products. Of 1,325 exact
source-reported country IDs, 1,231 appear in those products and 94 do not:
one Danish, 92 Finnish and one Norwegian ID lack source coordinates. The
per-ID ledger explains product membership; the AADR accountability receipt
still refuses country-assignment, map and scientific admission. These human
metadata rows do not contribute pollen or vegetation observations.

We also checked [animal sample map membership](animal-entity-capability/README.md)
without duplicating the existing per-ID decisions. Ten normalized species
tables contain **1,464 sample IDs**; **324** appear in **163 point features**
and the other **1,140** retain named map exclusions. Two source-backed horse
localities, Hyena's Lair and Yana, add six existing PRJEB44430 owners without
new specimen identities, coordinates or dates. The complete saved-source
consumer and independent comparison qualify all 37 native outputs; the installed
thirteen-input entity replay verifies this exact disjoint partition.
Twelve mapped IDs occur in eight Nordic-labeled features: Denmark five,
Finland two and Sweden five. The separate
[current animal chronology account](animal-sample-chronology.md#current-source-and-map-population)
retains all 1,475 source rows, with 319 admitted temporal nodes and 1,156
refusals; Europe-plus and Nordic each have thirteen temporal nodes. Those exact
chronology layers and their historical source-identity sidecars are retained,
without rerunning the chronology census. The separate current locality surface
has 225 child-support intervals across 126 temporally admitted points, 37
contextual points and sixty preserved gaps. All three assembled map surfaces and
their packaged indexes pass independent preservation/readback. Twenty-two served
Chromium cases include eighteen source-backed cases and four synthetic controls:
a source-backed SEAD [0, 10,000] BP display envelope is distinct from the synthetic
exact [0, 0] BP point. Locality hulls supply no occurrence inside a support gap
and do not date an undated member. These are different denominators and scopes;
the [owning account](animal-sample-chronology.md#current-source-and-map-population)
retains their exact receipts and limits. The four PRJEB90141 source keys and five accession
alternatives remain identity-ambiguous without altered dates, coordinates or
source taxa. Map placement and source labels remain context, not a qualified
source-country, pollen or ecological cohort. The linked lifecycle capture's
1,468 IDs / 322 mapped IDs / 165 features describe its historical epoch and
were not rerun as the current population.

We also joined every reviewed SEAD chronology claim to its governed country and
site decision in the [country claim account](../../docs/report/source-relations/sead/chronology-country-accounting/README.md).
The 25,109 claims belong to 853 distinct sites among 2,069 assigned sites:
Sweden 22,643 claims at 741 sites, Denmark 1,939 at 56, Norway 468 at 27,
and Finland 59 at 29. Another 126 site decisions remain outside that assigned
population. These are chronology source rows, not pollen samples or admitted
ecological events. We retained all 25,109 propagation refusals, including the
13,170 claims eligible only for chronology display.

Our [SEAD handoff account](../../docs/report/source-relations/sead/README.md#handoff-accounting)
checks the 61 source tables, 86 joins and four-country review denominators
through the governed map candidate. It retains zero eligible ecological events
and a refused release status; its local accounting result does not supply the
missing scientific authority.

We checked [country retrieval and evidence denominators](../../docs/report/source-relations/sead/country-coverage/README.md)
against the same full SEAD capture. All 2,069 assigned sites were retrieved
and normalized; the 126 review or unassigned sites are scope exclusions, not
retrieval losses. The 61 table receipts and 19,005 query receipts are complete
with zero recorded failures or retries. Source-native observations total
163,107 in Sweden, 5,264 in Denmark, 8,950 in Norway and 442 in Finland.
All 177,763 have refused ecological-event dispositions and zero events are
eligible. These source units cannot be substituted for our pollen-site or
measured-vegetation denominators.

We also traced the captured [SEAD source units by country](../../docs/report/source-relations/sead/source-unit-accounting/README.md):
1,245 of the 2,069 assigned sites link to 4,432 sample groups, 32,308
physical samples, 129,918 analysis entities, 43,392 distinct linked datasets
and 68,705 analysis values. All captured analysis values in this source table
trace to Swedish sites; the zero Danish, Norwegian and Finnish table rows do
not mean those countries lack other environmental observations. The 126
excluded site decisions have unknown downstream source-unit counts, not zeros.
No country has an eligible ecological event in the retained capture.

### Keyed SEAD component preparation

Our [categorical component table](source-cohorts/sead-categorical-values.csv)
retains all 4,800 native component keys and parent observations at 393 sites.
Each row keeps the exact source `site_uuid`, entity/sample/group/dataset keys,
class/type/item identities and nullable component fields beside the parent display.
All 4,800 component values and variant fields are source-null; resolving an item
key does not turn its label into an observed value. The 2,821 parent/item display
differences remain visible. No duplicate component key, orphan, missing entity or
site parent, or one-to-many parent fan-out occurs in this capture. Missing source
files or invalid relations refuse the consumer instead of becoming null rows.

The maintained categorical consumer ran at `e38230752` with exit zero in 4.12 s,
scanning 177,763 staged observations and reconciling all 68,705 parent analysis
values. An independent standard-library check joined nine original source tables
through entity, physical sample, sample group and site, confirming every exported
native key, exact UUID, class/type/item, raw value and parent display. Fifty-five
focused tests, lint, formatting and strict types pass. The
[original 15-group report](../../docs/report/source-relations/sead/analysis-categorical-values/report.json)
is unchanged. Twenty-five rows have chronology context only, 4,775 lack entity
chronology and all 4,800 remain refused as ecological events. This is typed source
preparation, with no new ecological interpretation, rights or scientific approval.

The separate [integer component table](source-cohorts/sead-integer-values.csv)
exposes 24,701 keyed source rows at 394 sites, joining 4,769 physical samples
and 15,429 datasets without aggregating away individual components. It keeps
native integer values, parent text, exact Decimal parses and comparison states
beside the source class/type, units, qualifiers and chronology/event dispositions.
There are 22,933 numeric equalities, 1,763 parent parse failures and five exact
precision differences. A display such as `<5` is not rewritten as the exact
measurement 5. Component qualifiers remain distinct from parent text: 1,712 are
reported (`~`: 1,149; `<`: 414; `>`: 148; `max`: one), while 22,989 are null.
All 24,701 variant fields are null. The 4,430 linked unit rows say `Years`;
20,271 expose no unit. Neither this unit label nor a growth-year source class
selects a sample chronology or establishes its reference epoch.

The integer consumer ran at `ffbbd20c7`, exit zero in 4.61 s, producing one
13,337,653-byte CSV. It retained 3,989 eligible chronology-claim links, 64
context-only links and 20,648 absent links, with zero ecological events. An
independent nine-original-table join verifies every component/parent/entity/
sample/group/site key, exact UUID, class/type/unit, nullable source value and
qualifier, all 1,763 parse failures and all five precision differences. Sixty-six
controlled tests and the separate original governed-source test pass, with
configured lint/format/types. The original compact report is unchanged; duplicate,
orphan, missing-parent and fan-out ledgers are empty for this source population.
This table supplies inspectable preparation rows, not scientific event or source
rights approval. The [integer lineage account](../../docs/report/source-relations/sead/analysis-integer-values/README.md)
retains the original summary and the optional reproduction command.

The [Boolean component table](source-cohorts/sead-boolean-values.csv) preserves
11,603 exact component/parent pairs across 397 sites, 4,774 physical samples and
6,088 datasets. All component flags are native Booleans: 1,708 true and 9,895
false. The separate native parent `boolean_value` matches every component;
parent display strings remain independently preserved, with no label-to-Boolean
translation. Thirty-eight component qualifiers contain literal `nära`; the other
11,565 are null. No source unit or same-entity chronology claim is exposed for
these rows, and all remain refused as ecological events.

Native storage and declared metadata are distinct. The 738 Sapwood-indicator
components retain value class 23, type 1 (`Count`) and base type `integer`
beside their actual Boolean values. Another 10,865 have Boolean type metadata.
The preparation table marks that distinction without coercing false to zero,
rewriting the source declaration or assigning ecological meaning. A true
component with parent display `Not dated` does not become an accepted date.
Component families overlap in sites and samples; their row counts must not be
added as independent specimens or ecological observations.

The maintained Boolean consumer ran at `64fd304cf`, exit zero in 4.26 s,
producing one 6,847,316-byte CSV. An independent nine-original-table join checks
every native key, exact site UUID, class/type/unit relation, component, qualifier,
parent display and parent flag, including the 738 mixed declarations. All 57
focused tests and configured lint/format/types pass. The original 17-group
report remains unchanged, and duplicate/orphan/missing-parent/fan-out ledgers
are empty. The [Boolean lineage account](../../docs/report/source-relations/sead/analysis-boolean-values/README.md)
gives the optional command. These are source preparation and software checks;
scientific meaning, rights and event admission still need qualified decisions.

### Source publication custody

We reconciled the [raw-to-public site identities](../../docs/report/source-relations/sead/public-custody/README.md)
across the 61 captured tables, 86 parent-child joins, assigned country
decisions, normalized exports and four-country map: all 2,069 source site
IDs/UUIDs agree. The separate [interval-set review](../../docs/report/source-relations/sead/interval-sets/README.md)
traces all 25,109 chronology claims to 13,170 display-eligible AD-year
claims and 7,244 record-interval features at 370 sites; 299 of those sites
have separated interval components. The atlas chronology discovery layer is
Swedish; the four-country site inventory is context, not a four-country
event layer. A site-wide span cannot fill gaps between its source intervals.

We exercised a [built four-country SEAD map candidate](../../docs/report/source-relations/sead/map-candidate/README.md)
in a browser and checked its source-bound layers. The 2,069 site points are
context; 1,219 have no numeric site envelope. Swedish discovery retains
7,244 numeric interval features and 1,555 unresolved records. A source-backed
interval gap stays empty under the live time filter, while 0 BP remains a
valid numeric value. The 25,109 claim review admits zero ecological events,
the built map has zero accepted propagation edges, and source release is still
refused. These results verify the current map posture, not an ecological
propagation network.

We decided that the present four-country scientific comparison tests
**observed-pollen prediction**, not national archaeology density or candidate
rankings. No archaeology count enters its training inputs, outcomes, scores or
country denominators. We therefore do not acquire Danish, Finnish and
Norwegian heritage registries for this comparison. This is a scope decision,
not evidence that archaeology is absent or comparable across countries.
Sweden-only RAÄ cannot stand in for the other national registries; its current
source authority is refused even for Swedish analytical density. SEAD is
environmental-archaeology context with its own site and record units, not a
replacement national inventory. The
[country capability table](../../docs/public/pollenomics-data/sources/country-source-limitations.md)
records this asymmetry. If we later compare archaeological density or use
heritage context to rank candidates across all four countries, that analysis
must first identify appropriate national sources and review each source's
licence, observation unit, classification, coverage, update method and time
support. Missing capture must remain unknown rather than a zero.

We reconciled the [LandClim modeled cells in the Nordic map](../../docs/report/source-relations/landclim/map-export-lineage/README.md)
with the governed temporal grid and published map shards. All 2,515 temporal
features match the static map transport; 1,875 belong to the PANGAEA 937075
LandClim II reconstruction. Across 100 country/window slices, 73,696 metric
pairs carry numeric estimates and standard errors, while 14,429 pairs are
explicitly null. The map's selector retains the source window and country,
and its download contract retains the method and modeled evidence role. We
also [downloaded and reconciled a 32-cell Denmark/Sweden frame](../../docs/report/source-relations/landclim/browser-export/README.md)
at 0–100 BP, including all 47 estimate and standard-error keys. All 1,875
normalized LandClim II polygons are one-degree squares about the archived
grid centers. PANGAEA's WGS84 geocode policy and GeoJSON's CRS84 specification
support our coordinate interpretation; the source CSV and derived GeoJSON do
not carry a separate file-level CRS declaration. Rootsi and Neotoma metadata
overlaps do not identify the historical cell contributors, and SEAD supplies
context rather than an independent vegetation result.

We checked modeled HYDE quantities and native grid reconciliation at seven
CE labels in the [country cropland report](hyde-cropland-source-account.md).
We use that result as modeled context, not as observed vegetation or measured
pollen-model benefit. Our [independent vegetation screen](../../docs/report/validation/empd2-nfi-pairing/README.md)
admits zero source-measurement pairs. We will score vegetation accuracy only
after matching measured targets and their sampling design.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Four-country 31-target observed-pollen source population and related context/refusal decisions are documented. Animal context separately retains 1,464 normalized IDs, 324 mapped IDs in 163 locality features and 1,146 explicit exclusions; twelve Nordic mapped IDs do not mean thirteen temporal nodes. Separate SEAD categorical staging preserves 4,800 native component/parent identities, exact site UUIDs and distinct nullable fields, item identities and parent displays. Integer preparation separately exposes 24,701 exact component/parent rows, native qualifiers and units, parsed displays and refusal states. Boolean preparation preserves 11,603 exact keyed rows, actual Boolean values, parent flags, native qualifiers and declared type discrepancies without interpretation or coercion.

**Unsupported claim.** Nordic LRA cohort, independent measured vegetation or joint multi-source causal explanation.

**Actual verification performed.** Retained country score, capability, registry and reference reports are synthesized; index did not rerun. The categorical consumer ran at e38230752, exit 0/4.12 s, scanning 177,763 observations and 68,705 parent values. Independent original-table joins confirm all 4,800 component identities, exact site UUIDs and native fields; 55 focused cases and configured lint/types pass. Original grouped report unchanged. Integer staging ran at ffbbd20c7, exit zero in 4.61 s, producing 13,337,653 CSV bytes. Independent nine-original-table joins confirm all 24,701 native identities and exact UUIDs, units, qualifiers, 1,763 parent parse failures and five precision differences. Sixty-six controlled checks and one original governed-source case pass with lint/types. Original summary unchanged. Boolean staging ran at 64fd304cf, exit zero in 4.26 s, producing 6,847,316 CSV bytes. Independent nine-original-table joins confirm every native key/UUID, qualifier, component and parent flag, plus all 738 Count/integer declarations. Fifty-seven focused tests and lint/types pass; original grouped report unchanged. Current animal source/entity followthrough separately verifies1464=318 mapped+1146 excluded in161 features; the actual13-input entity replay passed in0.12 s/RSS40386560 B, and seven current source/map/evidence checks passed. The three-scope map producer and independent Nordic index observer passed with source fields and unchanged nonanimal context preserved; no SEAD or pollen study was rerun for this correction. Current source-owned animal followthrough at a18530b54 independently verifies1464=324 mapped+1140 excluded IDs/163 features and complete three-scope map preservation, current JavaScript indexes and22 served temporal controls. Pollen/event populations and all319 retained source chronology nodes remain unchanged; no empirical admission follows.

**Remaining input or review.** Observed-pollen cohort membership and modeled context do not supply admitted Nordic LRA inputs, independent measured vegetation, complete cross-domain identities or all source rights. Resolver: Country core/reference/registry source owners and qualified source reviewers Reopen when: Specific physical site/window or observation gains matched chronology, geometry, denominator, rights and review; rerun only affected consumer.

**Cause category.** data|comparability|access/rights|qualified review

**Consequence.** Keep country pollen and contextual archives separate from historical core admission.

**Precise next acceptance route.** Specific physical site/window or observation gains matched chronology, geometry, denominator, rights and review; rerun only affected consumer. Then update reports/science/nordic-pollen-study.md.

**Negative or refused result.** NO 94/1,178 bins and SE 3/54 bins refused; zero qualified Nordic LRA inputs and zero measured-cover pairs. SEAD item lookup does not supply an observed category; all 4,800 source components remain event-refused, with no unit exposure. Integer qualifiers and nearby chronology claims are not exact measurements or selected ages; 1,763 parse failures and five precision differences remain explicit, with all events refused. Boolean storage does not repair Count/integer declarations or interpret parent labels; all 11,603 remain event-refused.

**Matched denominator.** DK 1 site/91 samples/24 bins; FI 28/1,797/435; NO 52/3,544/1,084; SE 3/228/51 scored on 31 targets. Separate animal context: 1,464 normalized IDs = 324 mapped + 1,140 excluded; 163 locality features; 12 Nordic mapped IDs. Separate SEAD categorical rows: 4,800 components/parents at 393 sites; 4,800 null values and variants; 1,979 equal/2,821 different parent/item displays; 25 chronology-context-only/4,775 unavailable; zero events. Integer table: 24,701 components/parents, 394 sites, 4,769 samples, 15,429 datasets; 1,712 reported/22,989 null qualifiers, 4,430 Years-linked/20,271 unexposed units; zero events. Boolean table: 11,603 components/parents at 397 sites/4,774 samples/6,088 datasets; 1,708 true/9,895 false; 38 literal nära qualifiers; 738 Count/integer declarations; no unit or same-entity chronology, zero events.

Retained evidence: [docs/report/regions/nordic/source-capability/README.md](../../docs/report/regions/nordic/source-capability/README.md), [reports/science/vegetation-reference.md](vegetation-reference.md), [reports/science/animal-entity-capability/report.json](animal-entity-capability/report.json), [reports/science/source-cohorts/sead-categorical-values.csv](source-cohorts/sead-categorical-values.csv), [reports/science/source-cohorts/sead-integer-values.csv](source-cohorts/sead-integer-values.csv), [reports/science/source-cohorts/sead-boolean-values.csv](source-cohorts/sead-boolean-values.csv).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
