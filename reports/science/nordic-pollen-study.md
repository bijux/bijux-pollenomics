---
title: Nordic Pollen Study and Source Decisions
audience: scientific_review
type: report
status: scoped
owner: bijux-pollenomics-scientific
last_reviewed: 2026-10-28
---

# What we established about Nordic pollen and source admission

We keep governed numeric products and producers under
`docs/report/pollen-reconstruction/`; unprefixed paths below refer to that
directory. We use this report to connect source admission to prediction,
method correspondence and the remaining scientific questions. The
[evidence index](../evidence-index.md) leads to each exact result row.

## What we admitted from source records

We retained sample-level counts, selected ages, chronology controls and taxon
trajectories for three Neotoma/EPD lakes in our
[Swedish native pollen sequences](../../docs/report/pollen-reconstruction/swedish-native-sequences/source-notes.md).
In an [independent PANGAEA EPD comparison](../../docs/report/source-relations/neotoma/abbo-profile/README.md),
we matched all 107 Abborrtjärnen depths after an exact 100-to-1 conversion
and 535 selected taxon-count cells. We did not infer historical basin geometry
from its 3 ha event area; its core date also differs from the Neotoma
collection-unit date. Our [Bökesjön basin review](../../docs/report/source-relations/neotoma/boke-basin/README.md)
found a 1984 mapped lake and two modern area measurements, neither bound to
the fossil core and sample ages.

We refused a Gilltjärnen basin transfer because
[LandClim II row 994](../../docs/report/source-relations/rootsi-landclim-overlap/README.md)
gives a 169 m radius and 101 samples at 15.083333° E, while the 101-sample
Neotoma `GILL` core is at 15.83333° E. Their approximately 42 km discrepancy
and equal sample counts do not establish core identity or age-specific basin
geometry.

For Danish Solsø, we kept the
[EPD/PANGAEA `SOLSOE81` core record](https://doi.pangaea.de/10.1594/PANGAEA.740759)
separate from later site-area reports. It gives a 2.5 ha event area, 0.98 m
water depth and a strongly drained lake. Neotoma dataset 4445 binds the same
core handle to collection unit 4303 and reports a 25,563 m² site area, but
its centroid (8.61341° E, 56.12846° N) is 1.352 km from the PANGAEA event
point (8.63333° E, 56.13333° N) by WGS84 inverse geodesic. An
[author's later comparison](https://doi.org/10.1046/j.1365-2745.2000.00490.x)
lists `SOL` at 4 ha and 2 m maximum depth (Table 1), citing Odgaard (1994),
without binding either EPD core or an age-specific shoreline. We cannot use
that area or the 2.5 ha event area for fossil-sequence LRA rings while the
record and time support differ. Neotoma dataset 4446 is a separate
`SOLSOE83` core. We reproduce no source data from the PANGAEA record, which
carries CC BY-NC 3.0 terms, and admit neither core to LRA on this evidence.
Our [Solsø LRA source decision](solsoe-lra-input.md) separately compares
LandClim I/II, PANGAEA and Neotoma sample selection; its 69 m
LandClim-II-to-Neotoma point distance does not erase the distinct 1.352 km
PANGAEA-event-to-Neotoma point discrepancy described here.

## Replayed source visits preserve normalized observations

We checked one authentic Bökesjön (`BOKE`) download, dataset **54001**, site
**28872**, collection unit **39241**, through the maintained relational builder.
The [existing native correspondence](../../docs/report/source-relations/neotoma/boke-native-correspondence/report.json)
authenticates its original Neotoma part. We selected that complete download
once, then supplied the same native record twice in memory. We neither copied
nor redownloaded source data, and used all **52** samples rather than the
50-sample modeling subset.

All nine normalized tables remain exactly equal: one site, collection unit,
dataset and chronology; 29 chronology controls; 52 samples and 52 age claims;
1,885 observations and 142 derived variables. Native identities, observation
values and units, complete age claims and chronology/control payloads survive.
The [eight-row occurrence table](source-lineage/neotoma-occurrence-accounting.csv)
keeps source visits separate: replay doubles registered visits, while one
additional copy of each native entity enters the identical-repeat exclusion
count. There are no unregistered visits or conflicting entity variants in
this comparison. Variables remain a derived lookup, outside those eight
native occurrence partitions. The repeated snapshot passes the public
materialization, validator and exact read-back of every published part,
including diagnostics.

The country bins retain **50 comparable and two refused age claims**, with
1,885 normalized observations. Without a boundary decision, the site stays
**UNASSIGNED**, with zero propagation eligibility; a raw country label is not
substituted for qualified attribution. Replaying one download supplies no new
independent samples, chronology approval, source rights, ecological mapping
or LRA admission. This is a source-structure and accounting result for one
dataset, not a new full-archive or scientific validation claim.

The native check passed at source `5aa3c58cec6ded98454d09875ad6c81ccd87a675`
in **1.396 s**, with **160,743,424 bytes** maximum sampled RSS. The original
attempt at `c7d7cfc56` failed because the test used `sample_id` for age claims;
the corrected test uses their actual `subject_id` parent. That failed attempt
remains preserved; the correction did not change the normalizer or raw input.
The [maintained test](../../packages/bijux-pollenomics/tests/unit/collection/sources/neotoma/relational/test_occurrence_accounting.py)
is opt-in and reproducible from the repository root:

```sh
BIJUX_POLLENOMICS_NEOTOMA_BOKE_OCCURRENCE_CHECK=1 \
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python3 -B -m pytest \
  --rootdir=. -c configs/pytest.ini \
  packages/bijux-pollenomics/tests/unit/collection/sources/neotoma/relational/test_occurrence_accounting.py::test_native_boke_repeated_download_preserves_all_source_entities \
  -q -s -o cache_dir="$PWD/artifacts/neotoma-occurrences/pytest-cache" \
  --basetemp="$PWD/artifacts/neotoma-occurrences/native"
```

## Classification and propagation refuse unreviewed mappings

At committed source `a0dce0304`, we ran the maintained
[scientific-evidence consumer](../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/scientific_evidence.py)
on the unchanged Neotoma relational snapshot:

```sh
python -B -m bijux_pollenomics_dev.ci.scientific_evidence --repository-root "$PWD"
```

| Population | Unmapped | Not applicable | Accepted | Total |
| --- | ---: | ---: | ---: | ---: |
| Source concepts | 1,298 | 53 | 0 | 1,351 |
| Observation memberships | 351,162 | 19,774 | 0 | 370,936 |

An independent reconstruction of the historical accounting isolates one change:
the current parser retains `cf` in “Vaccinium cf V. uliginosum,” a concept with
two observations. Restoring that former marker omission and the historical
producer metadata reproduces the exact original audit identity. All source,
country, observation and mapping-status partitions remain unchanged.

The actual downstream consumer produced zero eligible propagation events and
zero directed candidates. All 16 sensitivity-scenario records match the
historical records exactly; the current output adds its actual producer,
contract and classification identities. The classification and propagation
release states remain refused, with public release disabled. These are
mechanical source-accounting and refusal checks. They supply no accepted
ecological mapping, human approval, inferred propagation or ecological accuracy.
The [release policy](../../configs/release_evidence_policy.json) owns the bounded
regenerable output paths.

## Seven-core author Betula/Pinus source support

The new source audit establishes complete **author-mapped Betula/Pinus counts
for all 542 native owners** in seven core sequences at **six physical sites**
across Sweden, Denmark, Finland and Norway. Forty-one of 42 predeclared windows
are supported. Solsø 81 has no source member in [4700,5200) BP; that window stays
empty, with null panel and full-mass aggregates. No owner was dropped to obtain
complete support. The two Solsø cores share site 3432 and cannot count as two
independent places.

This is a different estimand from the qualified literal Betula/Ulmus study:
Dalmutladdo's missing Ulmus still refuses that older panel. Here the exact
published-author lookup maps native Betula (29) to Betula, and native Pinus (385) or
Pinus sylvestris (1287) to Pinus, with each core's native identity retained. This is
a declared author harmonization, with no claim of native botanical equivalence,
reviewed local parameter applicability or whole-vegetation composition.

| Core | Country | All owners | Window members | Supported windows | Panel N | Full pollen NISP | Outside panel N |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Abborrtjärnen | Sweden | 107 | 37 | 6/6 | 41,506 | 46,402 | 4,896 |
| Bökesjön | Sweden | 52 | 20 | 6/6 | 4,340 | 18,207 | 13,867 |
| Bussjösjön | Sweden | 69 | 21 | 6/6 | 1,711 | 22,991 | 21,280 |
| Solsø 81 | Denmark | 66 | 20 | 5/6 | 5,835 | 33,200 | 27,365 |
| Solsø 83 | Denmark | 26 | 18 | 6/6 | 4,400 | 19,626 | 15,226 |
| Laihalampi | Finland | 150 | 40 | 6/6 | 15,017 | 23,074 | 8,057 |
| Dalmutladdo | Norway | 72 | 19 | 6/6 | 11,455 | 13,319 | 1,864 |

The 175 window members contribute **84,264 panel counts, 176,819 full source
pollen NISP and 92,555 outside-panel counts**. These are counts under the strict
source NISP law, not independent-grain or vegetation-area estimates. All 542
owners retain finite selected chronology points; 367 are outside these windows,
including six negative source points. All original age wrappers, alternative
models, default flags, signed/absent/null bounds, native depths, count rows and
attribution remain in the detailed local ledgers. ABBO/BOKE/BUS legitimately
select their native collection reference. Other cores select the explicit
calibrated alternative; none is selected merely by a generic default flag.
Solsø 81's point 7 BP / younger bound −41 remains outside these windows without substitution.

The [prospective protocol](pollen-reconstruction/nordic-author-window-support/protocol.json)
fixes all seven native core identities, six half-open 500-year windows from
2700 to 5700 calibrated BP, AD 1950, and the exact retained source/lookup/parameter
bytes. All 31 ordered author parameter axes bind before selecting Betula/Pinus:
RPP 5.10571/6.05833, fall speed 0.024/0.031 m/s and covariance diagonal
0.092006056/0.056016002, cross0. This supplies a coherent declared parameter
profile; it supplies no Pinus transport factor, dated geometry or fitted model.

### Correction, actual execution and independent readback

The first actual pair at `cce1a547bf11afcb25245b8b3c6b576e236f6909` passed its
software comparisons but exposed a shared domain mistake during root source
review. The ID/name-only selectors counted Pinus stomata as duplicate pollen
in two Bökesjön owners. Their original rows separately declare stomate/stomate
and pollen/pollen; all datum accounting already retained those distinctions.
The first 40-supported/one-empty/one-incomplete result is retained as diagnostic
evidence and is not the accepted pollen-support finding.

Correction `352d7bce7275fa2b9451e058a213494201b237c0` excludes only explicit,
consistent nonempty non-pollen element roles from the pollen-axis selector.
Stomate-only is missing pollen, never measured zero. Unknown, blank or
contradictory metadata and genuine pollen duplicates still refuse. All original
non-pollen rows remain preserved, outside the panel and full pollen mass.
The protocol, original counts, strict full-mass law, literal-panel results and
90 s / 1 GiB / 16 MiB budgets remain unchanged. The corrected pair used fresh outputs;
neither first result was overwritten.

At frozen committed `352d7bce7`, the corrected producer exited zero in
**3.190 process seconds**, peak RSS **330,219,520 B**, with **7,144,029 B**
of final products. Independent source/Decimal traversal exited zero in
**1.616 seconds**, peak RSS **334,659,584 B**, verifying every ordered owner,
all 42 dispositions, complete count/full/excluded mass, native metadata and all 31
parameter axes. The 8,074-byte verification SHA-256 is
`c2614d70a60607647dc1993ed7791676f1806132329b1848b11c03a93f4d70c6`;
producer result SHA-256 is
`15c65ede7fdd1d39e7d0383ff07beb4f928855846c0f0697fb837c76460a40c4`.
Both jobs preserve all 4,851 parent-frozen files, 4,600 tracked Python files,
14 scientific input pins, protocol and HEAD/index. Source code was committed
before the runs. Preceding integration passed 190 controls including 83 old
literal regressions; the corrected producer/oracle integration passed 153
controls with configured scoped Ruff/format and strict types. Earlier fixture
construction failures remain recorded; no numerical threshold was relaxed.

Detailed products remain local under
`artifacts/root/nordic-author-window-support/pollen-element-study/`; the
independent check is under
`artifacts/verification/nordic-author-window-pollen-elements/`. First-pair
products remain under the original `study/` and verification directory. To
reproduce, use an absent output path and the canonical shared original root:

```sh
PYTHONPATH=packages/bijux-pollenomics-dev:packages/bijux-pollenomics-dev/src \
PYTHONDONTWRITEBYTECODE=1 PYTHONOPTIMIZE=0 \
.venv/bin/python -B -m \
  bijux_pollenomics_dev.essd_reproduction.nordic_coupled.author_window_support.study \
  --repository "$PWD" --original-data-root /path/to/shared/original-data \
  --protocol "$PWD/reports/science/pollen-reconstruction/nordic-author-window-support/protocol.json" \
  --output "$PWD/artifacts/nordic-author-window-support"
```

Use the independent CLI module
`tests.source_completion.pollen_reconstruction.test_nordic_author_window_support_result`
with the same repository/original-root/protocol, `--products` pointing to that
producer directory and a separate absent `--output`. Set OMP/OPENBLAS/MKL/
VECLIB/NUMEXPR numeric thread counts to one for both actuals. No source was
acquired or rewritten, and no kernel, reconstruction, prediction or score ran.
That source audit supplies the inputs to the separate matched physical comparison
below. Source-use, historical geometry, parameter transfer, independent vegetation
and untouched confirmation retain their distinct evidence requirements.

## Matched six-place physical pollen transfer

Adding Danish, Finnish and Norwegian training places reduces point-pollen error
on the same 18 Swedish target windows for both declared methods. Physical
forwarding has slightly higher aggregate error than the direct-pollen baseline.
These are conditional development results on previously exposed observations;
they do not establish historically supported LRA or independent vegetation skill.
The [prospective protocol](pollen-reconstruction/nordic-physical-transfer/protocol.json)
was committed before implementation and actual execution. The
[native derived summary](pollen-reconstruction/nordic-physical-transfer/summary.json)
retains every group, target, matched comparison and sensitivity denominator.

### Fixed inputs, excluded targets and prediction support

The primary profile uses Abborrtjärnen, Bökesjön, Bussjösjön, Solsø 83,
Laihalampi and Dalmutladdo: six physical places, four countries, six half-open
500-year windows from 2700 to 5700 calibrated BP, AD 1950, and the source audit's
author Betula/Pinus panel. Its 36 source windows contain 155 native owners.
Static metadata radii are respectively 98, 80, 69, 89, 285 and 160 m; wind is
3 m/s, dispersal parameter D is 0.12, gamma is 0.25 and regional extent is
100,000 m. These are declared geometry and parameter hypotheses, with no claim
that modern metadata supplies dated shorelines or locally validated parameters.

For each allowed training source, the maintained fixed-site inverse computes
`closure(counts / (K * PPE))`, using the exact selected 2×2 author covariance.
The physical predictor averages these source cover compositions and forwards
them through the target response, `closure(K_target * PPE * mean_cover)`.
The declared observation layer is one homogeneous integrated annulus, with
ring weight one and zero additional regional contribution. The direct predictor
averages the same sources' closed pollen panels using the same weights.
This inverse-to-forward calculation supplies no fitted local LOVE component.
The exact covariance enters the inverse API, but this study scores point
predictions and propagates no count, age, geometry or parameter uncertainty.

Every Swedish leave-place-out fold excludes the target's whole physical family;
the paired training scopes are Sweden only and the four-country pool. Separate
country holdouts exclude the entire target country. Solsø 81 and 83 are
alternative collections at one physical site and are never pooled. No target
counts enter its own forecast. All predictions and response bytes were saved,
authenticated and reopened before scoring target observations.

The three profiles are equal-place weighting with Solsø 83 (primary),
equal-country then equal-place-within-country weighting with Solsø 83, and
equal-place weighting substituting Solsø 81. Country/place weights are fixed
after structural exclusion. A missing, invalid, zero-total or empty required
source window refuses both methods, without dropping or reweighting a source.
A missing target observation can still receive a count-free forecast; its score
remains unavailable. A physical response failure refuses its physical channel.

Each profile attempts 36 Swedish scope contexts and 36 country-holdout
contexts, each with two methods. The complete population is **216 contexts /
432 method outcomes: 414 scored, 16 prediction-refused and two unavailable
target observations**. All 16 refusals arise from the empty Solsø 81
[4700,5200) BP training window: six Swedish pooled outcomes and ten
country-holdout outcomes. Its two Danish target outcomes have saved predictions
but no observation to score. Profiles reuse observations and cannot be counted
as independent replications.

### Sweden-only versus Nordic training on identical Swedish targets

The primary comparison holds all three Swedish targets, 18 target windows and
78 native target owners fixed. Scores are fractions; the macro first averages
windows within each target and then weights targets equally. Native-owner
weighting is reported separately and does not make repeated owners independent.
For this two-component response, MAE equals total variation, so those metrics
are not independent corroboration.

| Training scope | Method | Site-macro MAE / TV | Site-macro Hellinger | Native-owner-weighted MAE |
| --- | --- | ---: | ---: | ---: |
| Sweden only | Physical forward | 0.242912 | 0.192677 | 0.258270 |
| Sweden only | Direct pollen | 0.242412 | 0.192251 | 0.257537 |
| Nordic pool | Physical forward | 0.198419 | 0.157884 | 0.205986 |
| Nordic pool | Direct pollen | 0.197962 | 0.157570 | 0.205701 |

Pooling lowers MAE at each Swedish target, though Bussjösjön's physical gain is
only 0.000542. Within the pooled comparison, physical/direct MAE is
0.237134/0.237692 at Abborrtjärnen, 0.295869/0.293800 at Bökesjön and
0.062255/0.062392 at Bussjösjön. Thus physical forwarding is slightly better at
two targets and poorer at Bökesjön, which determines the aggregate difference.
This fixed-cohort contrast supplies no causal estimate of adding countries.

### Separate country-held-out results and sensitivity

The primary country holdouts exclude every training place in the target country.
Each Swedish target contributes six scored windows; the other countries each
have only one target place and six windows. These small, temporally dependent
samples do not establish country-wide independent transfer skill.

| Target country | Places / windows / native owners | Physical MAE | Direct MAE | Physical Hellinger | Direct Hellinger |
| --- | ---: | ---: | ---: | ---: | ---: |
| Sweden | 3 / 18 / 78 | 0.169943 | 0.169635 | 0.136902 | 0.136691 |
| Denmark | 1 / 6 / 18 | 0.252516 | 0.251254 | 0.210804 | 0.209898 |
| Finland | 1 / 6 / 40 | 0.047262 | 0.044780 | 0.034643 | 0.032821 |
| Norway | 1 / 6 / 19 | 0.314500 | 0.311908 | 0.228004 | 0.226015 |

The primary macro slightly favors direct pollen in all four countries, but the
Swedish native-owner-weighted ranking reverses: physical MAE 0.172178 versus
direct 0.172351. The aggregation rule matters. Under equal-country training,
Finnish macro MAE instead favors physical (0.055585 versus 0.056111), while
owner-weighted MAE favors direct (0.062341 versus 0.062143). We retain both
rankings rather than claiming a uniformly superior method.

Equal-country weighting reduces the pooled Swedish macro MAE on the same
18 windows / 78 owners to 0.187747 physical and 0.187339 direct. Bussjösjön
becomes slightly poorer, so this density sensitivity is not a universal gain.
The Solsø core substitution must instead use the **15 common Swedish windows /
65 owners**: physical pooled MAE changes from 0.200219 (83) to 0.202752 (81),
and direct MAE from 0.199597 to 0.202089. Solsø 81 improves Abborrtjärnen and
worsens Bökesjön and Bussjösjön. The empty window is retained, and different
Danish 81/83 target observations are not treated as paired targets.

### Actual execution, independent checks and limits

The producer and independent Decimal80 observer ran at committed source
`827515a9aa6c9cb7487f2f44d9b153644b1f7efb`. The producer completed in
2.987 process seconds, peak RSS 226,590,720 B, with 1,587,622 B of final
products. The observer completed in 1.174 seconds, peak RSS 148,226,048 B,
verifying all 216 contexts / 432 outcomes, the full 31-axis parameter and
covariance source, nine retained response factors, source exclusions, weights,
inverse/forward calculations, scores and matched populations. Its unchanged
absolute tolerance is 1e-12, including pre-closure quantities. All 4,929
parent-frozen source/input files and HEAD/index remained stable during each run.
The prospective producer/observer limits were 180 s / 768 MiB / 16 MiB each.

Nine saved response factors were consumed as pinned fixed coefficients; their
two numerical kernel modules match their recorded origins, but the complete
old engine is not relabeled as a current-runtime execution. Only three new
Pinus factors, at radii 80/69/89 m, were integrated. An independent R integration
completed once in 0.494 seconds, peak RSS 88,784,896 B, under 60 s / 512 MiB /
1 MiB limits. Maximum Python–R factor difference is 1.6670e-13, below the fixed
1e-8 comparison tolerance. Numerical error estimates and agreement are
nonrigorous and supply no physical accuracy or rigorous integral certificate.

The first R readback failed on a metadata-header ordering mismatch. Review also
found two decimal spellings of the same binary64 integration tolerance. Reader
correction `d447bc5c9f0545756ba1acf22475c1a74d39bec8` accepts the exact named
header set regardless of column order and requires exact binary64 equality of
those controls. Duplicate/missing/extra fields, row order and numerical factor
tolerance remain strict. The original builder is authenticated from its Git
blob; the new observer identifies its separate source commit. The corrected
readback passed in 0.242 seconds, peak RSS 32,899,072 B, with all ten original
actual products unchanged. The original failure remains preserved. No Python
kernel, R integration, prediction or score was rerun for this correction.

Integrated synthetic checks passed 167 controls before actual execution;
69 focused metadata/custody controls and scoped lint, format and strict types
passed for the reader correction. The producer result SHA-256 is
`6ec3f1d9eac45232bacee23a01c675f4b3098363870102fdca1c0b4487444fa4`;
Decimal verification is
`c694c8627d632e63a15e6187d6bd1c7ad6f53ed5993525b6c6de65a548c056f3`;
R readback verification is
`19f249a6d5e9eb92007787dea2205c9f1d939aad93058b8d029921c00833fd88`.

Detailed predictions, responses, scores and result remain local under
`artifacts/root/nordic-physical-transfer/study/`; independent checks remain
under `artifacts/verification/nordic-physical-transfer/` and
`artifacts/verification/nordic-physical-transfer-r/`. The tracked derived
summary is byte-identical to the native summary and contains no individual raw
count table. Reproduction requires the exact protocol-bound shared inputs and
original dependency/source epoch; later delivery commits are not new actuals.
From that source epoch, with numeric thread counts set to one:

```sh
PYTHONPATH=packages/bijux-pollenomics-dev:packages/bijux-pollenomics-dev/src \
PYTHONDONTWRITEBYTECODE=1 PYTHONOPTIMIZE=0 \
.venv/bin/python -B -m \
  bijux_pollenomics_dev.essd_reproduction.physical_forward.country_transfer \
  --repository "$PWD" \
  --protocol "$PWD/reports/science/pollen-reconstruction/nordic-physical-transfer/protocol.json" \
  --output "$PWD/artifacts/nordic-physical-transfer"
```

The independent module
`tests.source_completion.pollen_reconstruction.test_nordic_physical_transfer_result`
uses `--repository`, `--protocol`, `--products` and a separate absent `--output`.
The R prepare/check commands are owned by
`tests.source_completion.pollen_reconstruction.nordic_physical_transfer.kernel_reference`.
The original matched Swedish-training experiment now has an actual conditional
physical result, country holdouts and density/core sensitivity. The stronger
LRA requirement still needs an admitted real regional/local cohort; this study
does not supply it. Dated geometry, source-use and parameter applicability,
calibrated uncertainty, measured vegetation and untouched confirmation remain
separate scientific requirements. No further numerical variant was selected to
reverse a poorer result.

## Scope and conclusion

We produced exploratory observed-pollen predictions on the previously exposed
17-site author cohort, a three-lake Swedish 16-label holdout, Denmark/Finland/
Norway 16-label country holdouts, four 31-author-target country holdouts, and
additional Swedish bog and lake transfers on that author axis. We also ran a
real [English constrained LOVE study](english-lra-pollen-prediction.md): 14 of
15 outer folds yielded held-out forward-pollen predictions, while BECKHAM
refused. Its earlier analytical and optimizer feasibility attempts remain
separate numerical refusals. We retained bounded correspondence to author-R
and the published archive, and modeled HYDE country context. We now also
retain a [conditional physical-forward pollen comparison](pollen-reconstruction/matched-pollen-forward/README.md)
at Swedish targets, using fixed saved metadata geometry and restricted panels.
That completed numerical prediction does not admit a historically supported
Nordic basin/core reconstruction. Independent vegetation accuracy, a
source-complete paper reproduction and a measured benefit from HYDE remain
unestablished. We performed no untouched confirmatory pollen evaluation.

For the 17-site English author development search, we used 31 taxa and
whole-site holdouts in three grid-stratified folds. We have not reviewed site
aliases across databases. We had already exposed all target outcomes and
used them in designing the search; the selected candidate is exploratory,
not an unbiased final skill estimate.

We selected a WGS84 radial-basis-function candidate on centered log-ratio
compositions with a 0.25 distance-quantile scale and ridge 0.1. We applied
half-count smoothing only to CLR training inputs and scored original observed
counts. Its common-support site-macro MAE is lowest in this finite search,
but it covers 174/184 attempted site bins (94.6%) versus 178/184 (96.7%)
for inverse-distance squared. On 174 shared bins, MAE is 0.017774 versus
0.018948 for inverse-distance squared and 0.019621 for training mean. We
retain the roughly 6.2% difference as development evidence alongside lower
coverage and prior outcome exposure.

## Results by scientific question

| Question | Result | Status and scope |
| --- | --- | --- |
| Are the paper-profile calculations consistent with the independent author-R replay? | The installed Python profile matched 14,074 supported mean and SE values; maximum residuals were 1.83881e-13 and 7.15331e-14 in fractional units. The [method correspondence](method-correspondence.md) owns the numerical interpretation. | Verified for these bounded equations and inputs; not a general correctness or historical source-identity claim. |
| Do results correspond to the selected publications? | For exact TW2 support (100–350 BP), the 2016 author-R and June 2021 PANGAEA means differ by maximum 9.19787 percentage points in grid 512 and 10.5527 in grid 562. Standard-error maximum gaps are 3.21615 and 4.25814 points. Both Python-to-R residuals are at most 1.238e-11 points. The 31-taxon mean-vector total-variation gaps are 0.092406 and 0.110704. All 31 mean ± one reported SE envelopes overlap in each grid; this is descriptive and does not test significance. Only 1/25 published-window interval labels matches exactly; the other 24 were excluded from direct comparison. The publication metadata inventory has 1,128 rows but zero authenticated historical primary-input closures. | Numerically reconciled on TW2. Historical raw-input cohorts, the paper's 12 versus PANGAEA's 11 versus archived 13 PFT positions, and the ISTS definition remain unresolved. |
| Are archived PFT/LCT standard errors feasible sums of their component uncertainty? | For each of five observed mean-addend groups (ET, ST, OL, ISTS, TBS), all 10,500 archived grid/window SE rows satisfy the necessary covariance bounds. Respectively 7,588, 7,892, 5,921, 7,013 and 5,859 rows have a nondegenerate bound with the SE strictly inside it. | This bounds a possible joint covariance only. The archive-producing transformation and covariance/delta-method replay remain unresolved. |
| Can other sites predict held-out pollen? | On the 17-site author cohort, the selected CLR-RBF scores 174 common site bins at site-macro MAE 0.017774 and Hellinger 0.256559. On those same bins inverse-distance scores MAE 0.018948 and Hellinger 0.269752, and training mean scores 0.019621 and 0.283346. Separately, Swedish Neotoma whole-site holdouts score 39 target site-bin rows per method across 13 500-cal-BP bins: nearest-site is best among the four fixed candidates (site-macro MAE 0.055371; Hellinger 0.395725), narrowly ahead of training mean (0.057177; 0.406399). | Both are exploratory and prior-exposed. The Neotoma outcomes concern declared 16-taxon subcompositions; three Swedish lakes do not support broad transfer claims. |
| Does an untuned site mean predict withheld author pollen? | The [source-bound equal-site baseline](../../docs/report/pollen-reconstruction/author-example-site-mean-holdout/README.md) scores 177 of 184 observed site-bin targets across 17 author site IDs; seven bins have no other training site. Site-macro MAE is 0.018949 fraction and total variation is 0.293703. | Prior-exposed development evidence on author-prepared counts. Its 177 scored bins differ from the later search’s 174 common bins, so these metrics do not establish model improvement. No LRA, Swedish or vegetation claim. |
| Does country-held-out direct-pollen prediction work in the Nordic extension? | Denmark: 24 scored bins at one site; nearest-site site-macro MAE 0.029809 and Hellinger 0.353519. Finland: 435 scored bins at 28 sites; nearest-site MAE 0.033223 and Hellinger 0.289538. Norway: 1,084 scored bins at 52 sites; inverse-distance-squared MAE 0.027012 and Hellinger 0.260268. The Finnish CLR-RBF is substantially worse (MAE 0.082477), and 94 Norwegian target bins remain refused. | Exploratory, prior-exposed observed-pollen subcomposition results only. Denmark has one site and cannot establish between-site Danish skill. No LRA, vegetation, or all-country skill claim. |
| Does the broader author taxonomy support Nordic observed-pollen transfer? | On 31 author lookup targets, 1,543 country-held-out site-bins score three fixed baselines (4,629 method rows), with 94 Norwegian refusals. Nearest-site site-macro MAE is 0.023242 in Denmark and 0.017335 in Finland; inverse-distance-squared MAE is 0.019459 in Norway. Assigned native NISP is 94.78% DK, 97.52% FI and 88.29% NO. | Exploratory prior-exposed observed-pollen result. Its response and denominator differ from the 16-label study, so the scores are not a direct improvement estimate. No LRA or vegetation claim. |
| Can the three Swedish lakes be held out against the other Nordic countries on that same author axis? | All 228 Swedish source samples are excluded from 81 DK/FI/NO training sites. Three fixed methods score 51 of 54 attempted Swedish site-bins (153 method rows); three early bins are refused. Inverse-distance-squared has the lowest equal-site MAE, 0.028740, and Hellinger, 0.413111. Assigned native NISP is 221,800/240,966 (92.05%) across all bins. | Exploratory prior-exposed observed-pollen result at only three target sites. The earlier Swedish author-parameter screen covers 39 common bins, not all 54. No Swedish LRA or independent vegetation claim. |
| Can an additional Swedish core be held out against those Nordic training sites? | A metadata-selected Storasjö bog core contributes 77 physical samples and 22 scored bins on the same 31-target axis. All three fixed methods score the same 22 bins (66 rows); nearest-site MAE is 0.015389 and Hellinger is 0.243786. Author-assigned NISP is 35,505/35,767; a parallel EPD dataset duplicates all 77 depths, ages and pollen count vectors and is excluded. | Additional prior-exposed development transfer at one bog core. The predictions were committed before target scoring. It does not establish country-wide skill, LRA or independent vegetation accuracy. |
| Can the same fixed methods transfer to three more Swedish lake cores? | A metadata-selected, source-default age cohort contributes 268 samples and 63 site-bins at Gilltjärnen, Lake Avegöl and Flinkasjön. All three methods score every bin (189 rows), assigning 231,115/238,797 native NISP to 31 targets. Inverse-distance-squared equal-site MAE is 0.017334 and Hellinger 0.286757; nearest-site MAE is 0.017932. | Prior-exposed development transfer across three physical lake sites, with predictions committed before scoring. The best method differs by lake; no LRA, independent vegetation, country-wide or confirmatory claim. |
| Can fold-specific LRA information predict withheld-site pollen or vegetation? | Our first author-prepared attempt refused all 15 folds after negative LOVE cover in 54/54 inspected ring rows. We then constrained local cover on the 30-target English author profile: 192/195 training fits completed and 14/15 outer folds published 42 forward-pollen predictions. Inverse-distance-squared vegetation gave site-macro pollen MAE 0.021088. The [separate English account](english-lra-pollen-prediction.md) retains the optimizer refusal, matched direct-pollen comparison and basin-radius forward sensitivity. | This is an English, prior-exposed LRA-derived pollen score. We have no independent vegetation truth. We admitted zero Swedish or four-country Nordic fossil cores to LRA because same-core chronology, historical basin, count denominator, PPE use and rights remain unresolved. |
| Can conditional physical forwarding change pollen error on matched Swedish support? | Eight retained cores at seven places support 154 requested contexts and 308 family outcomes: 200 scored and 108 refused. On 26 jointly scored windows at BOKE and BUS, pooled physical-forward MAE/TV is 0.108040 versus direct-panel 0.120778. BUS is poorer under pooled physical forwarding (0.154732 versus 0.154539 direct); only SOLSOE83 adds source support on 12 matched contexts. The [complete account](pollen-reconstruction/matched-pollen-forward/README.md) retains all outcomes and the 1,424-value independent Decimal check. | Fixed metadata-geometry point calculation on previously exposed two-taxon panels; no foreign-country target, independent vegetation, calibrated uncertainty, historical-source admission or untouched accuracy claim. |
| Are predictions accurate against independent measured vegetation? | The EMPD2–NFI review selected 16 spatial leads within 1 km and admitted 0 independent vegetation pairs. The dated Färskesjön lead is one 7 m forest plot 427 m from the lake point. A historical-map screen retains three bogs' map coverage and pollen anchors, but no exact numerical map-class values. A separate published Swedish validation figure prints nine matched pollen/REVEALS/observed-vegetation labels; its selected subset has REVEALS MAE 5.11 versus pollen MAE 17.33 percentage points. | This repository's predictors were not evaluated against measured vegetation. The published figure is a different study and its selected printed labels do not provide the original ten-lake input cohort or full 26-taxon accuracy. |
| Do HYDE or extra countries add useful information? | Native ISO-grid sums agree with 84 four-country cropland totals at seven CE labels and three scenarios. The separate count-only private-window adapter still refuses country assignments. No paired pollen ablation was run. | Source-grid correspondence established for selected cropland labels; matched pollen use remains blocked by rights, formal CRS, calendar, covariate support and scenario interpretation. |

For Swedish LRA screening, we found that exact-name LandClim II PPE/FSP
coverage intersects only six direct-cohort labels, retaining 18.1–38.7% of
each site's native NISP. The authors' taxonomy lookup assigns 98.5080%,
72.4801% and 97.3183% at Abborrtjärnen, Bussjösjön and Bökesjön, with the
remainder excluded or unmapped; all 31 author targets bind to the author
code's RPP, fall-speed and covariance files. A 1986 field study maps an
approximately 0.3 ha Bussjösjön and an older gyttja edge, while a later
3 ha inventory point lies 2.5264 km from the Neotoma site point. We cannot
bind a calibrated historical basin outline to those pollen samples. Our
[source cohort account](source-cohorts.md) and open needs
retain the same-core decisions needed before Swedish LRA.

The separate [30-taxon optimized LOVE feasibility pilot](../../docs/report/pollen-reconstruction/author-lra-optimized-feasibility/README.md)
retained the excluded `Filipendula` count mass and source request identities. Its
two bounded one-pair requests both refused optimizer convergence; it produced no
LRA prediction or score.

The selected CLR-RBF therefore improves the development score against the declared simple baselines on common support, but does not establish Swedish transfer, LRA-derived prediction skill, vegetation accuracy, publication reproduction or HYDE value. A separate [buffered author spatial study](../../docs/report/pollen-reconstruction/author-buffered-pollen/README.md) on two adjacent grids retained four methods' frozen predictions and scores. Its fixed fitted-RBF diagnostic performed worse than the training mean (MAE 0.040564 versus 0.025298 on 140 common bins); it remains a distinct, previously exposed diagnostic and is not the selected three-fold model.

The [archived PFT taxon arithmetic](publication-correspondence/pft-crosswalk/README.md)
now identifies the three published taxon-mean columns that sum to `ISTS` and
the six that sum to `TBS` in all 10,500 grid/window rows. Custody-bound author files support seven of nine parameter-to-output taxon names exactly and `Castanea sativa` through a source-name LUT; `Quercus deciduous t.` has no exact author source-name row. This evidence does not define
`ISTS` biologically, authenticate the source-to-output name changes, settle the
paper/archive PFT count discrepancy, or supply an SE aggregation rule. The
[paper's Sect. 3.2](https://essd.copernicus.org/articles/14/1581/2022/)
assigns deciduous Quercus type to TBS, while the archive's corresponding taxon
mean is an ISTS addend. The disagreement remains explicit in the
[publication correspondence account](../../docs/report/pollen-reconstruction/paper-correspondence.md), whose detailed
narrative is now owned by `reports/science/publication-correspondence.md`.

The Nordic direct-pollen study uses the exact 16-label response selected for the Swedish direct-pollen cohort and excludes the target country from each training set. The corrected Neotoma screen finds 91 Denmark, 1,797 Finland and 3,544 Norway candidate samples across 1, 28 and 52 physical sites. The held-out score table contains 6,172 method rows over 24 Danish, 435 Finnish and 1,084 Norwegian scored bins. Norway retains 94 refused target bins. These are prior-exposed observed-pollen results, not independent landscape or vegetation truth. Direct-pollen eligibility does not admit these data to LRA: basin geometry, exact PPE/FSP support, count-denominator choices and other source decisions remain unresolved. Independent vegetation screening admitted zero EMPD2 records in Denmark, Norway or Finland; the reviewed NFI sources lack an admitted country cohort. The source review and exact output digests are in the [Nordic direct-pollen report](../../docs/report/regions/nordic/direct-pollen/RESULTS.md), its [manifest](../../docs/report/regions/nordic/direct-pollen/manifest.json), and the public source reviews for [LandClim](../../docs/public/pollenomics-data/sources/landclim.md), [Neotoma/EPD](../../docs/public/pollenomics-data/sources/neotoma.md), [vegetation references](../../docs/public/pollenomics-data/sources/empd2-nfi-review.md), and [HYDE](../../docs/public/pollenomics-data/sources/hyde.md).

The separate [31-target author-taxonomy study](denmark-finland-norway-author-pollen.md)
uses the same Danish, Finnish and Norwegian candidate samples with the source
lookup's explicit excluded and unmapped count mass. It saves country-excluded
predictions before scoring all 1,543 supported site-bins. Nearest-site is the
lowest-MAE fixed baseline in Denmark and Finland; inverse distance squared is
lowest in Norway. The response aggregates more native NISP than the 16-label
study, but its fractional-error scores are not comparable across those two
different taxon axes. All target countries were previously exposed, so the
result is development evidence only.

The [Swedish country holdout on that same 31-target axis](sweden-author-pollen.md)
excludes all three Swedish lakes from the Danish, Finnish and Norwegian
training input. It scores 51 of 54 Swedish site-bins, with three refused
early bins. The broader all-bin source denominator is reconciled exactly to
the earlier 39-common-bin Swedish author-parameter screen. The four-country
responses are source-bound but remain small, prior-exposed development
studies; no measured vegetation or LRA result follows from them.

The [additional Storasjö core holdout](../../docs/report/regions/nordic/swedish-neotoma-holdout/README.md)
uses the previously fixed three baselines and 81 DK/FI/NO training sites. Its
protocol selected one of two parallel EPD datasets before target counts were
read; a subsequent source review found their 77 pollen count vectors identical
at matching depths. The 22-bin result extends the observed-pollen development
evidence to one bog core, with a distinct pollen source setting from the three
earlier Swedish lakes. It adds no LRA or measured-vegetation validation.

A [training-only Nordic development search](nordic-observed-pollen-selection.md)
selected IDW for Denmark and tuned CLR-RBF for Finland and Norway. The
[frozen country transfer result](nordic-observed-pollen-transfer.md)
scores the same 1,543 site-bins as the fixed study. Selected versus IDW
site-macro MAE is 0.033022 versus 0.033022 in Denmark, 0.034871 versus
0.034375 in Finland, and 0.033942 versus 0.027012 in Norway. Tuning improves
over the older fixed RBF in Finland and Norway, but does not beat IDW on either
country's matched support. Country outcomes had been inspected before this
protocol; the comparison is development evidence, not independent validation.

## Denominators and exclusions

- **Development pollen search:** 12 candidates, 17 author site groups, 3 grid-stratified whole-site folds, 184 attempted observed site bins, 174 common scored bins. The selected candidate scores 174/184 bins; the 10 unscored attempts remain in the denominator and in the coverage output.
- **Publication correspondence:** 14,074 author-example mean/SE values with zero missing or extra keys; 31 taxa compared on the sole exact published support, TW2 100–350 BP, for each of grids 512 and 562. No retrospective interval shifting was applied.
- **Archived uncertainty feasibility:** Five PFT/LCT aggregate groups times 10,500 grid/window SE rows; zero necessary-bound violations. Nondegenerate strictly interior counts are 7,588 ET, 7,892 ST, 5,921 OL, 7,013 ISTS and 5,859 TBS. The original covariance and archived release transformation were not recovered.
- **Swedish pollen-only study:** 3 Neotoma/EPD lakes, 228 source samples, 13 common 500-cal-BP bins and 39 held-out target site-bin rows per fixed method. The exact-name 16-taxon subcomposition retains 45.4–57.2% of native NISP; 3,615 exclusion rows retain every other observed label/count. **LRA:** zero folds run because basin geometry/time support and parameterized denominator are not sufficiently established.
- **Nordic direct-pollen country holdout:** Denmark 91 candidates at one site, Finland 1,797 at 28 sites and Norway 3,544 at 52 sites. The respective scored-bin denominators are 24, 435 and 1,084; Norway retains 94 refused bins. Four fixed methods yield 6,172 scored country-bin-method rows. These are not LRA or vegetation denominators.
- **Published target-cohort source measures:** The separate [native-unit account](../../docs/report/regions/nordic/direct-pollen/source-measures/README.md) partitions 174,970 distinct DK/FI/NO source observations into 22 country/unit/decision strata. Of 165,699 NISP/count-labeled rows, 116,727 pass the existing direct-pollen predicate and 48,972 retain a refusal; 2,057 concentration, 160 influx, and 7,054 other-unit rows remain separate and refused. Percentage/proportion, presence/absence, and missing-unit categories have zero rows **within this selected target cohort only**. These are observation/source-unit denominators, not the 24/435/1,084 scored-bin or 16-label pollen-mass denominators. Original predictions and scores are unchanged.
- **Nordic author-taxonomy pollen:** The same 91/1,797/3,544 target samples aggregate into 31 author targets, retaining 122,998/1,229,019/2,018,295 assigned native NISP in DK/FI/NO while keeping excluded and unmapped mass explicit. Three fixed methods score 4,629 rows on 1,543 shared site-bins; 94 Norwegian bins are refused.
- **Swedish author-taxonomy country holdout:** 228 Swedish source samples at three sites aggregate to 221,800 assigned of 240,966 native NISP across 54 candidate site-bins. Three fixed methods score 153 rows on 51 supported bins; three are refused. The prior 39-common-bin parameter screen's 169,013/187,002 NISP matches the same-bin subset exactly.
- **Neotoma source membership:** Our [per-sample account](neotoma-study-membership/README.md) joins all 12,388 normalized source samples to the four 31-target study metadata sets and the original pollen screen. Exactly 5,660 samples at 84 sites are selected; 233 same-site nonselections are refused by source prerequisites, 6,218 are outside selected sites, and 277 have unresolved source country. Six Swedish metadata selections have negative source ages and age-prerequisite refusals; their three nominal `-1` bins are refused before prediction. Membership does not imply an LRA or vegetation result.
- **Additional Swedish core holdout:** Storasjö contributes 77 physical samples after excluding a parallel duplicate EPD dataset, 22 supported 500 BP site bins, 66 fixed-method scores, and 35,505 author-assigned of 35,767 native pollen NISP. This single bog core is development evidence only.
- **Nordic selected transfer:** 12 training-only candidates over three whole-site inner folds for each excluded country yielded 40,932 trial scores and 2,439 RBF fits. The frozen selected predictors and IDW score the same 24, 435 and 1,084 outer bins; selected RBF loses to IDW in Finland and Norway. All outer cohorts were previously exposed.
- **Conditional physical-forward comparison:** Eight source cores/seven places, four Swedish targets/77 source windows, two scopes/154 contexts, two families/308 outcomes; 200 scored and 108 refused. Only BOKE and BUS have both families/scopes on 26 common windows, 13 each. The two-taxon fractions and literal windows differ from the older 31-target/500-year cohorts. SOLSOE83 adds 12 matched source contexts; no DK/FI/NO target evaluation or complete physical-source admission follows.
- **Vegetation reference:** 16 spatial leads reviewed; zero admitted pairs. These are not 16 independent validation observations.
- **HYDE:** three private scenario windows retain 72,576 source-index positions each, including 29,217 missing values. Separately, release country tables supply 84 modeled cropland values for four Nordic countries, seven CE labels and three scenarios. All 84 native grid/ISO-country sums conserve the matched country tables within 0.000001 km². No pollen ablation was run.
- **Rootsi historical-input linkage:** 79 unique metadata candidates among 1,128 publication records, 1,049 with no candidate, zero authenticated historical inputs and zero reproduction-ready rows. The 79 retained candidate workbooks replayed to 7,459 header positions and 5,170 mechanical data rows; 78 sample-count claims agree and EKE claims 25 while the replay finds 42. This is structural evidence only.

## Reproduction and evidence

| Result | Producer, configuration and inputs | Retained output |
| --- | --- | --- |
| Development pollen search | Twelve fixed candidates were compared over three deterministic whole-site folds. Its input-manifest SHA-256 is `48d853468f979a04636642c6c757e9d05edf708d799b29cbae4d2286a9ac0acb`; the retained design declares folds, taxa, selection rule and prior exposure. | `author-development-design.json`, `author-development-interpretation.md`, `leaderboard.csv`, `coverage.csv`, `scores.csv`, and `author-development-predictions.csv.gz` in this directory |
| Author-prepared LRA development | The source-bound 1250–1750 cal BP cohort has 15 positive-count sites and 31 taxa. Whole-site folds complete training but all refuse negative reconstructed local cover. This is a prior-exposed English numerical diagnostic under declared geometry assumptions. | [Author LRA development report](english-analytical-love/README.md), `report.json`, `folds.csv` and `cover-diagnostics.csv` |
| Constrained author LRA development | A 30-target closed subcomposition excludes 159 of 20,732 author NISP. A bounded simplex LOVE backend reconstructs 192/195 training items and publishes 42 withheld-site method predictions over 14/15 folds; BECKHAM remains refused. All 42 published pollen predictions are scored after separate target opening, with site-mean MAE 0.026273 (training mean), 0.021132 (nearest) and 0.021088 (inverse-distance-squared). Fixed direct-pollen baselines score lower on the same 14 sites; vegetation accuracy is not evaluated. | [Constrained LOVE report](english-lra-pollen-prediction.md), `report.json`, `folds.csv`, `predictions.csv`, `scores.csv` and [matched direct-pollen comparison](../../docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/comparison.json) |
| Author raw/prepared counts | A private-source recount of the 17 author examples finds 501,713 raw counts and 299,660 prepared counts. The 202,053-count difference partitions into 200,247 author-excluded, 418 unmapped and 1,388 outside-window counts; each site matches its prepared total. Exact `Plantago` lookup labels prevent a six-count misclassification at LOBBSBOG. This does not identify publication inputs. | [Author preparation audit](../../docs/report/source-relations/landclim/author-preparation-audit/README.md) and its [source-bound report](../../docs/report/source-relations/landclim/author-preparation-audit/report.json) |
| Buffered spatial-block pollen comparison | The same 17 author sites in two adjacent withheld grids with a 20 km basin-edge buffer. Three fixed baselines score 148/184 observed site bins; a fixed half-count CLR-RBF scores 140/184. On the 140-bin common support its site-macro MAE is 0.040564 versus 0.025298 for the training mean. Strict-positive CLR training support is absent in both blocks. | [Source-bound study](../../docs/report/pollen-reconstruction/author-buffered-pollen/README.md), [four-method result](../../docs/report/pollen-reconstruction/author-buffered-pollen/comparisons/fitted-common-support/REPORT.md), four method prediction and score directories, and the [custody manifest](../../docs/report/pollen-reconstruction/author-buffered-pollen/manifest.json). This is prior-exposed English direct-pollen development evidence. |
| Author and archive correspondence | Independent R/Python author-example replay and exact-window PANGAEA comparison; the former passes declared tolerances, while the latter is descriptive across revisions. The three-way ledger traces the installed Python result through independent author R to the archive; mean-vector diagnostics and reported uncertainty envelopes describe the TW2 difference. A 25-window axis check establishes that only TW2 has exact shared bounds. | [Full author-example ledger](../../docs/report/publication-replay/landclim-author-example-correspondence/README.md), [full published-window ledger](../../docs/report/publication-replay/landclim-published-window-correspondence/README.md), [three-way provenance](../../docs/report/publication-replay/landclim-published-window-provenance/README.md), [uncertainty envelopes](../../docs/report/publication-replay/landclim-published-window-uncertainty/README.md), [window alignment](../../docs/report/publication-replay/landclim-window-alignment/README.md), detailed narrative in `reports/science/publication-correspondence.md`, and `paper-correspondence.csv` here |
| Publication study input identity | The pinned public site-metadata workbook yields 1,128 row-level locators and 4,512 explicit missing-input/rights refusals. Nordic source labels total 84 SE, 66 DK, 42 NO and 31 FI; these are not admitted historical study inputs or governed country cohorts. A source-bound Amsoldingersee check finds one current core with the reported 23 sample IDs, but zero of three cores with an exact `E#69` bridge or authenticated author chronology. | [Full-study input inventory](../../docs/report/publication-replay/landclim-study-inputs/README.md), [one-row source refusal](../../docs/report/publication-replay/landclim-amsoldingersee-source-review/README.md), [primary-source crosswalk](../../docs/report/publication-replay/landclim-study-inputs/primary-source-crosswalk.csv), [refusal ledger](../../docs/report/publication-replay/landclim-study-inputs/refusals.csv) and source-bound [manifest](../../docs/report/publication-replay/landclim-study-inputs/manifest.json) |
| Archived PFT/LCT uncertainty | Pinned PANGAEA source archive standard errors pass necessary lower and upper bounds for five observed aggregate/addend groups on all 10,500 grid/window rows each. | [Uncertainty-bound report](publication-correspondence/pft-crosswalk/uncertainty-bounds/report.json) and [window ledger](publication-correspondence/pft-crosswalk/uncertainty-bounds/windows.csv) |
| Rootsi structure and chronology | The retained structural replay covered 79 candidate workbooks, 7,459 header positions and 5,170 mechanical rows; 78 of 79 sample-count claims agree. A separate source-bound Neotoma check pairs all 109 FLINK and 77 STAV depths, identifies the single FLINK sign discrepancy, and supplies an STAV candidate point-age vector. Cell-level workbook content is not redistributed; historical input identity and use rights remain unresolved. | [LandClim source review](../../docs/public/pollenomics-data/sources/landclim.md), [FLINK/STAV chronology witness](../../docs/report/source-relations/landclim/neotoma-chronology-witness/README.md) and `swedish-source-questions.csv` |
| Nordic country readiness and direct-pollen transfer | Exact-label targets were separated from training by country. Frozen predictions were scored after prediction outputs were saved. The result contains 6,172 country-bin-method rows, with unsupported target bins retained in coverage. | `docs/report/regions/nordic/direct-pollen/RESULTS.md`, `manifest.json`, `coverage.csv`, `scores.csv` and `predictions.csv`; source and LRA limits are stated in the linked public source reviews. |
| Nordic author-target observed pollen | The exact author lookup maps selected native counts into 31 targets. Three fixed, country-excluded predictors score 4,629 method rows after prediction hashes are frozen; site and taxon diagnostics retain the aggregation. | [31-target study](denmark-finland-norway-author-pollen.md), [frozen predictions](../../docs/report/regions/nordic/author-target-pollen/predictions), `scores.csv`, `site-scores.csv` and `taxon-diagnostics.csv` |
| Swedish author-target observed pollen | All Swedish target sites are excluded from 81 DK/FI/NO training sites. Frozen 31-target predictions score 51 bins by three fixed methods, with three explicit refusals and exact native-count closure to the 39-common-bin screen. | [Swedish 31-target holdout](sweden-author-pollen.md), [predictions](../../docs/report/regions/nordic/swedish-author-target-pollen/predictions) and [scores](../../docs/report/regions/nordic/swedish-author-target-pollen/scores.csv) |
| Additional Swedish lake transfer | Three metadata-selected EPD lake cores contribute 268 calibrated-age samples; frozen 31-target predictions score all 63 site-bins with matched source count mass. | [Our three-lake account](sweden-lake-transfer.md), [prediction freeze](../../docs/report/regions/nordic/swedish-lake-transfer/prediction-freeze.json), [scores](../../docs/report/regions/nordic/swedish-lake-transfer/scores.csv) and [verification](../../docs/report/regions/nordic/swedish-lake-transfer/verify.py) |
| Nordic selected model transfer | A three-fold training-site search chose predictors without target-country counts. Its selected predictions were frozen and scored on identical fixed-study support, retaining 94 Norwegian refusals. | [Development search](nordic-observed-pollen-selection.md), [selected transfer](nordic-observed-pollen-transfer.md), freeze and paired scores |
| Swedish pollen-only and LRA boundary | Neotoma/EPD native pollen was admitted for direct prediction under the EPD CC BY 4.0 policy. LRA remains refused on unresolved, time-matched basin geometry and restricted exact-name parameter coverage. | `swedish-direct-pollen/` in this directory and `swedish-source-questions.csv`; the [LandClim](../../docs/public/pollenomics-data/sources/landclim.md) and [Neotoma](../../docs/public/pollenomics-data/sources/neotoma.md) reviews state the LRA boundary. |
| Vegetation boundary | The EMPD2/NFI source review admits zero matched pairs; the dated Färskesjön plot is too small and distant for the landscape estimand. The historical-map study supplies map coverage and pollen anchors at three bogs, without original numerical vegetation fractions. A separate published figure yields a bounded nine-label comparison of the original Swedish REVEALS study, not validation of this repository's predictions. | [Our vegetation-reference decision](vegetation-reference.md), [Färskesjön plot support](../../docs/report/vegetation-reference/farskesjon/README.md), [historical-map support](../../docs/report/vegetation-reference/smaland-historical-maps/README.md), [published Swedish figure comparison](../../docs/report/vegetation-reference/southern-sweden-figure/README.md), [EMPD2/NFI source review](../../docs/public/pollenomics-data/sources/empd2-nfi-review.md) and [NFI access review](../../docs/public/pollenomics-data/sources/nordic-nfi-reference-access.md) |
| HYDE modeled context | Source-reported Nordic cropland totals and matched native ISO-grid conservation at seven CE labels, with the source declaration review and separate private scenario windows. | [Country result](hyde-cropland-source-account.md) and [HYDE source review](../../docs/public/pollenomics-data/sources/hyde.md) |

We retained development predictions, per-candidate coverage, score
definitions, source hashes and refusal rows in the linked repository outputs.
We did not open a new final outcome set or call this an outcome-independent
confirmatory redesign.

To verify the tracked result, configuration and producer digests locally, run:

```sh
.venv/bin/python docs/report/pollen-reconstruction/verify_report.py
```

We retained the Swedish producer
`bijux_pollenomics_dev.source_completion.swedish_direct_pollen` with its
configuration, source hashes, cohort, prepared profiles, frozen predictions,
scores and exclusions under `swedish-direct-pollen/`. We retained the author
development design, leaderboard, coverage, candidate scores and compressed
predictions in the same governed directory. The Nordic country-held-out
products remain under `docs/report/regions/nordic/direct-pollen/`. We keep
raw snapshots in their source repositories under the public source reviews.

### Author source custody and reproduction

We use private source files alongside the tracked author-development producer.
We retained the exact original input manifest and 193 source/reference files
(2,282,688 bytes excluding the manifest) under `landclim/author-reference`
in the external source-data store. They include prepared counts, site
geometry, time windows, a taxon crosswalk and independent R reference files.
The grouped-development consumer needs 22 of those files plus the manifest.
We keep the files private because redistribution rights remain unresolved.
Their custody and author geometry do not admit the separate Swedish Neotoma
cohort to LRA.

Our [custody record](../../docs/report/pollen-reconstruction/author-source-custody.json)
binds the exact manifest, consumed input hashes, source revision, producer
and source reader independently of disposable run directories. Supply the
private capsule path to authenticate it with the existing source reader,
then reproduce the previously exposed development comparison:

```sh
author_source_root=/path/to/private/source/store/landclim/author-reference
.venv/bin/python docs/report/pollen-reconstruction/verify_report.py \
  --author-source-root "$author_source_root"
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.author_pollen_spatial.development_search \
  --author "$author_source_root/author" \
  --reference "$author_source_root/reference" \
  --output artifacts/author-pollen-development-reproduction
```

We treat the output directory as disposable; the documented results and
private source capsule survive its removal. Readers without the private
source files can inspect retained predictions and scores, but cannot rerun
the source-backed study from this report alone.

## Reopening conditions and remaining work

The Swedish and Nordic Neotoma direct-pollen results are reproducible from the retained producers and source manifests. For Sweden, use `bijux_pollenomics_dev.source_completion.swedish_direct_pollen` with the retained `swedish-direct-pollen/config.json`. For the Nordic country holdout, use `bijux_pollenomics_dev.source_completion.nordic_direct_pollen` and the reproduction command in `docs/report/regions/nordic/direct-pollen/RESULTS.md`. Swedish LRA can reopen when time-matched basin geometry, BUS source-area discrepancies, and an acceptable parameterized count denominator are documented. Rootsi workbook comparisons separately require their unresolved rights, age, taxonomy and denominator decisions. Independent vegetation scoring additionally needs authenticated pollen collection dates, cross-source identity and a defensible mapping from measured field variables to the target estimand. The [HYDE country result](hyde-cropland-source-account.md) verifies native country totals and grid cropland conservation at seven CE labels. A matched pollen comparison still requires release/member rights, formal CRS, historical CE/BP support and a justified land-use covariate design.

Nordic country-held-out direct-pollen prediction is available for Denmark, Finland and Norway on both declared taxon axes. The [Danish chronology coverage replay](../../docs/report/countries/denmark/pollen-chronology-coverage/README.md) accounts for all five captured Danish sites: 279 pollen-count samples, 91 comparable-age candidates at Solsø and 188 prerequisite refusals. The 188 refusals comprise 104 samples described as Eemian or middle Pleistocene, outside this Holocene prediction scope; 83 samples without source-bound Holocene eligibility; and one Solsø sample whose calibrated age interval has a negative BP bound. We retain that source bound and refuse its comparison under the current nonnegative-BP rule. The DK/NO/FI LRA extension can reopen after country-specific Neotoma taxa/PPE, chronology, count-denominator, basin and rights review identifies admitted inputs; independent vegetation work additionally needs accessible measured source records and matched pollen/reference support. The 91 Danish, 1,797 Finnish and 3,544 Norwegian source-screen candidates are not the scored-bin denominators; coverage and refusals are retained separately in the [16-label](../../docs/report/regions/nordic/direct-pollen/coverage.csv) and [31-target](../../docs/report/regions/nordic/author-target-pollen/coverage.csv) studies.

Until those conditions are met, we claim exploratory prediction on the
exposed 17-site author cohort, exploratory Swedish and other Nordic
observed-pollen transfer, source-bound English LRA forward-pollen prediction
and bounded paper numerical correspondence. We do not certify completion
of the full Nordic LRA and vegetation-validation objective.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Broad Nordic evidence account retains bounded author example, observed-pollen and source-admission results. A distinct saved-metadata-geometry physical inverse-to-forward consumer now supplies conditional restricted-panel point-pollen results at Swedish targets. One authentic BOKE download replayed twice preserves all nine normalized tables while separately counting repeated native entity visits. A distinct author Betula/Pinus source audit now accounts for all542 native owners at six physical places in four countries, with41 supported windows and one empty Solsø81 window. A separate prospective six-place author Betula/Pinus physical inverse-to-forward experiment now compares Sweden-only versus Nordic training on identical Swedish targets, with separate country holdouts and density/core sensitivity. This is fixed-geometry point-pollen development evidence.

**Unsupported claim.** Full historical LandClim reproduction, independently validated Nordic LRA/vegetation accuracy, untouched generalization or causal multi-evidence history.

**Actual verification performed.** Retained linked source, prediction, publication and reference receipts are synthesized; index did not rerun them. The distinct conditional physical-forward producer completed at a890b5e433fd2679768b588bae2774aa3d382e17 with native/collector exit zero and all 6,668 pins unchanged. Its independent Decimal50 check matched 1,424 values at absolute tolerance 1e-12, maximum residual 1.9653480873864026090362878350698437E-16. These saved results are synthesized without repeating prediction or scoring. At committed source a0dce0304, the maintained scientific-evidence consumer also reproduced the unchanged Neotoma source audit: 1351 concepts and 370936 memberships, zero accepted mappings, zero eligible propagation events and zero directed candidates. Independent historical comparison isolates only a retained cf marker for one concept with two observations; all scientific partitions and all 16 scenario records remain identical. The release refusal and absence of human approval are preserved. The opt-in native check passed at 5aa3c58cec6ded98454d09875ad6c81ccd87a675 in 1.395913625 s, maximum sampled RSS 160743424 bytes. Exact source-payload/ID/unit/age checks, eight occurrence partitions and public materialization/read-back passed. The initial test at c7d7cfc56 failed on its incorrect age-claim parent selector; correcting the test to subject_id preserved the original failure and changed no normalizer or raw input. Corrected source-only producer/independent observer at352d7bce7 check all542 owners,42 windows and31 ordered author parameter axes, with4851 parent-frozen files/4600 Python/14 scientific pins and HEAD/index stable. Producer3.190s/RSS330219520B; observer1.616s/RSS334659584B;153 corrected integration controls and scoped static checks pass. The first actual pair atcce1a547b retained an ID-only pollen/stomate selector error, diagnosed against two native BOKE owners and corrected without changing data, protocol, budgets or genuine duplicate refusals; first artifacts remain unchanged. The separate six-place actual producer/Decimal80 observer at827515a9aa6c9cb7487f2f44d9b153644b1f7efb passed in2.987s/RSS226590720B and1.174s/RSS148226048B, checking216contexts/432methodoutcomes at unchanged1e-12 tolerance including pre-closure. All4929 parent files and HEAD/index stayed stable;167 integrated controls passed. Only3new Pinus factors were computed; one independent R integration passed in0.494s/RSS88784896B with maximumfactor gap1.6670e-13 below1e-8. First R readback failed on metadata representation; fixd447bc5c9f0545756ba1acf22475c1a74d39bec8 passed69focused controls and readback0.242s/RSS32899072B, authenticating the original builder and leaving all10actual products unchanged. No numerical rerun or tolerance relaxation. Native summary is retained byte-exact; producer, Decimal and R verification identities appear in the authored account.

**Remaining input or review.** The synthesis retains no source-complete historical Nordic LRA reconstruction, independent Nordic vegetation pairs or fully authenticated historical LandClim input cohort. Completed conditional physical-forward point-pollen predictions use saved metadata geometry and previously exposed panels; source rights and qualified review remain open. Resolver: Country core/archive/reference custodians and qualified scientific reviewers Reopen when: Versioned same-core/window inputs and matched vegetation pairs pass source admission and new frozen evaluation.

**Cause category.** data|assumption|comparability|access/rights|qualified review

**Consequence.** Keep modeled maps, aDNA/SEAD context and observed pollen in separate evidence units.

**Precise next acceptance route.** The conditional matched six-place experiment is complete. LCI-032 still requires an admitted real regional/local LRA cohort; the new fixed-site inverse/forward point calculation supplies no local LOVE or historical basin admission. Establish source-qualified same-core/window geometry, parameters and permitted use, matched measured vegetation and a genuinely untouched cohort before their stronger claims. Preserve count/age/parameter uncertainty and full refusal accounting. Then reassess model use without tuning away poorer results.

**Negative or refused result.** Zero historical authenticated primary inputs, zero historically qualified Nordic LRA cores and zero measured-cover pairs; country bins include refusals. The conditional physical-forward comparison retains 108 no-eligible-source family refusals; pooled BUS MAE/TV is poorer than direct (0.154732 versus 0.154539). The BOKE check preserves two refused age claims, UNASSIGNED country and zero propagation eligibility; replayed visits are not new independent observations. Author Betula/Pinus has one genuinely empty SOLSOE81[4700,5200)BP window; its aggregate remains null. The first BOKE duplicate-axis result was a selector error, not a source absence. No new kernel, reconstruction, prediction, score, geometry/rights/field approval was produced by this source audit. Separate new six-place experiment retains16prediction-refused outcomes from empty Solsoe81[4700,5200)BP and2unavailable target scores. On primary18Swedish windows, pooled physical/direct macroMAE0.198419/0.197962; physical is poorer at BOKE but slightly better at ABBO/BUS. Weighting/country sensitivities reverse some rankings; no universal winner, localLOVE, uncertainty calibration or new field approval.

**Matched denominator.** Four country 31-target cohorts: DK 1/24, FI 28/435, NO 52/1,084, SE 3/51 scored site/bins. Separate conditional physical-forward support: eight source cores/seven places, four Swedish targets/77 windows, 154 contexts/308 family outcomes, 200 scored/108 refused; only 26 jointly matched windows at BOKE/BUS, 13 each, enter the two-target comparison. All scored panels have two taxa. SOLSOE83 adds source support on 12 joint pooled contexts; no DK/FI/NO target score in that older profile. Separate native structure check: one BOKE dataset54001/site28872/unit39241, 52 samples and age claims, 29 controls, 1885 observations and 142 derived variables; all nine tables are identical after replay, with eight native registered populations doubled and one-copy repeat exclusions. Separate author Betula/Pinus source support:542 owners/seven sequences/six sites/four countries;175 window members/41 supported+one empty of42 requested windows;84264 panel=176819 fullNISP minus92555 outside-panel counts. Solsø81/83 share one physical site and are never independent places. Separate new physical transfer: six primary places/four countries/36windows/155native owners, three profiles216contexts/432outcomes=414scored+16prediction-refused+2unavailable targets. Primary Swedish four-way contrast18windows/3targets/78owners; density contrast same18/78; Solsoe81/83 substitution ONLY15commonSwedish windows/65owners. Primary countryholdouts SE3/18/78, DK1/6/18, FI1/6/40, NO1/6/19 (places/windows/owners). Alternative cores share oneplace; profiles/windows are dependent.

Retained evidence: [reports/science/source-cohorts.md](source-cohorts.md), [reports/science/publication-correspondence.md](publication-correspondence.md), [reports/science/pollen-reconstruction/matched-pollen-forward/README.md](pollen-reconstruction/matched-pollen-forward/README.md), [reports/science/pollen-reconstruction/matched-pollen-forward/report.json](pollen-reconstruction/matched-pollen-forward/report.json), [reports/science/pollen-reconstruction/matched-pollen-forward/decimal-comparison.json](pollen-reconstruction/matched-pollen-forward/decimal-comparison.json), [reports/science/pollen-reconstruction/matched-pollen-forward/publication.json](pollen-reconstruction/matched-pollen-forward/publication.json), [reports/science/source-lineage/neotoma-occurrence-accounting.csv](source-lineage/neotoma-occurrence-accounting.csv), [docs/report/source-relations/neotoma/boke-native-correspondence/report.json](../../docs/report/source-relations/neotoma/boke-native-correspondence/report.json), [reports/science/pollen-reconstruction/nordic-author-window-support/protocol.json](pollen-reconstruction/nordic-author-window-support/protocol.json), [reports/science/pollen-reconstruction/nordic-physical-transfer/protocol.json](pollen-reconstruction/nordic-physical-transfer/protocol.json), [reports/science/pollen-reconstruction/nordic-physical-transfer/summary.json](pollen-reconstruction/nordic-physical-transfer/summary.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
