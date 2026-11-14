# Bökesjön pilot: source evidence and methods

[Return to the pilot assessment](README.md).

## Counts, zeros and denominators

| Source | Full source samples | Selected samples | Reported positive pollen cells | Omitted known-taxon cells | Reported pollen NISP |
| --- | ---: | ---: | ---: | ---: | ---: |
| BOKE | 52 | 3 | 67 | 293 | 2,553 |
| KRAG | 96 | 4 | 151 | 281 | 3,973 |

There are **792 selected taxon/sample slots**. All 218 reported cells are positive
integers; no selected native cell explicitly reports zero. The omitted slots
remain distinct from measured zeros. [Taxon support](taxon-support.csv) and
[every selected slot](native-count-slots.csv) retain each count and disposition.
An empty count is unavailable, not numeric zero.

The Neotoma methods paper describes sparse storage: organismal zeros are not
stored. An occurrence elsewhere in the same dataset can support conditional
nondetection only if the analyst looked for that taxon in every sample. The audit
marks such **candidates without applying zero imputation**. It requires at least
one positive identification in that dataset. This is neither literal reported
zero nor proof that a plant was absent. [Williams et al. (2018), p. 164](https://doi.org/10.1017/qua.2017.105).

The separately supplied BOKE workbook records explicit numeric zero for four
cereal types in each selected row: 12 zero cells. Its stored pollen-sum aggregate
is **2,556**, whereas the matched public native rows total **2,553**. These source
denominators are preserved separately. Private row-level pollen-sum values remain
in the local evidence. Group summaries, marker/laboratory fields, spores, stomata and algae
must not all be summed as independent terrestrial pollen taxa. The private
workbook and raw lookup rows are not republished here.

The workbook header names `Sample age (LANDCLIM)` without a typed age unit.
Its row selection here uses those source numeric labels as separate correspondence
evidence; it does not establish age-unit equivalence or a shared uncertainty law.

A public Neotoma-only analysis does not require importing those private workbook
zeros or adopting its denominator. Conversely, the workbook's zero cells cannot
be relabeled as explicit Neotoma measurements.

### The remaining cereal and taxonomy questions

BOKE's full source dataset contains Avena-type, Hordeum-type, Triticum-type and
Secale cereale, but omits them in all three selected native samples. The workbook
provides the separate explicit-zero evidence described above.

KRAG has 27 reported counts under `Poaceae (Cerealia-type)` and 3 under
`Poaceae (Cerealia) undiff.`. Both labels lack an exact route in the retained
source-owned author lookup. A further 3 counts belong to an unmapped sedge type.
KRAG has **no separately reported Secale taxon anywhere in its source dataset**;
its rye split therefore cannot be inferred from BOKE's zeros or the same-dataset
nondetection rule. A scientifically justified pooled cereal group would need
its own classification and compatible parameter decision. The later
[official taxon-definition follow-up](taxon-definitions.md) supplies a
Cyperaceae family-parent candidate for the three sedge counts, while retaining
the source audit's unchanged exact-unmapped disposition and unresolved aquatic
eligibility.

The candidate author-lookup mass accounting closes exactly:

| Source | Candidate assigned NISP | Author-excluded NISP | Unmapped NISP | Total |
| --- | ---: | ---: | ---: | ---: |
| BOKE | 2,497 | 56 | 0 | 2,553 |
| KRAG | 3,823 | 117 | 33 | 3,973 |

These are version-bound candidate routes, not applied taxonomic transformations
or a qualified terrestrial denominator. The existing two-taxon Betula/Ulmus
comparison contains two tree taxa and cannot quantify forest versus open land.

## Parameters and chronology

[Parameter coverage](parameter-coverage.json) retains exact native-label matches,
all 31 source targets and both European versions (55 taxa each; 110 rows in total).
[The target table](parameter-targets.csv) gives the original LandClim PPE/SD and
fall-speed spellings. Genus/species, pollen-type and family aliases require a
declared crosswalk rather than silent string repair.

For each European version separately, literal nominal RPP/fall-speed matches
cover 2,379/2,553 reported BOKE NISP and 3,509/3,973 KRAG NISP. Requiring a reported SE
as well reduces those figures to 2,367 and 2,765. These are **label-coverage counts**,
not reconstruction coverage or an applicability verdict. Missing SE does not
invalidate a stated nominal reference value, and it never becomes zero variance.
Compiled-mean SE and LandClim SD remain different quantities. The European
Ulmus RPP remains missing. [Wieczorek and Herzschuh (2020)](https://essd.copernicus.org/articles/12/3515/2020/)
and [deposited reference](https://doi.pangaea.de/10.1594/PANGAEA.922661).

BOKE's selected chronology 38422 is the source LANDCLIM calibrated-BP smoothing
spline. The selected point ages are 2,723.3, 2,960.6 and 3,078.1 BP. KRAG explicitly
selects calibrated chronology 13366; its conflicting native default declarations
remain separate. Window membership uses the half-open interval [2700, 3200).

BOKE's 29 controls comprise 17 radiocarbon and 12 lead-210 entries. They match the
retained source objects, but their native age labels are heterogeneous. Raw
radiocarbon ages are not calibrated sample-age intervals. Signed lead-210 values,
repeated depths, missing laboratory numbers and null sample-age bounds remain
unchanged. No calibration, interpolation or joint age-uncertainty law was created.
The discussion note that 0–1 cm can represent roughly 10 years is not applied as a
universal sedimentation rate or BOKE-specific uncertainty model.

## Physical basin evidence and scientific review

The official SMHI chart 3-1832 identifies Bökesjön lake 616314-135069 and shows its
irregular outline and depth contours. Its survey-date and measurement-water-level
fields are blank and it marks no pollen-core station. The catalogue's 1983 entry,
the 1985 report's winter 1984 caption, modern 1.5/1.6 ha areas and the LandClim 80 m
radius remain separate claims. None establishes the shoreline at 2700–3200 BP.
[Existing basin account](../../../../docs/report/source-relations/neotoma/boke-basin/README.md)
· [official chart source](https://vattenwebb.smhi.se/svarwebb/rest/downloadmap/616314-135069).

[Three declared static-basin profiles now have an executed sensitivity comparison](basin-sensitivity/README.md). The outer-ring span is 3.03 percentage points; clipping masks an 8.47-point signed inner-ring span. These results concern only Betula and Ulmus.

A separately declared static-basin reconstruction can be scientifically useful
under justified assumptions and sensitivity checks. It must not be called an
observed ancient geometry. The user confirms that no additional written BOKE
core/chronology/basin/taxon/PPE approval has been supplied. Literature and
numerical agreement do not create that missing qualified decision.

## Independent validation and the 10 percentage-point rule

The user confirms **10 percentage points**, not relative 10 percent, as cover-error
guidance. For a compatible independently measured point, this means
`abs(predicted cover percent - observed cover percent) <= 10`.
There is no measured pair on which to evaluate it here. It is not applied to
pollen-composition losses or used to convert conditional sensitivity into accuracy.
Overall model selection, cohort eligibility and scientific acceptance must be
specified before confirmatory outcomes.

The bounded reference search reviewed historical maps, Småland map studies,
Hellman validation material, known NFI leads, modern national land-cover mapping,
Bökesjön habitat descriptions and archaeological context. None supplied a
matched ancient non-pollen cover vector. The historical-map archive begins in
1628 CE; the reviewed surveys and classified imagery are modern. This is an
account of the reviewed routes, not proof that no suitable evidence exists
anywhere. [Existing vegetation-reference account](../../vegetation-reference.md).

A compatible reference must match site, date, cover categories, units and spatial
footprint. A modern or Danish benchmark could test another explicitly declared
claim; it cannot be substituted for direct ancient BOKE validation.

## Verification and reproduction

The source audit executed at committed source
`916c9489de8fd4fcac24fcf973add288f7ea2c86`: 13.37 seconds, 176 MB peak RSS,
917,327 product bytes. The 120-second wall timeout was enforced; 512 MiB RSS and 8 MiB
output limits were checked after execution. The independent observer made 20,646
scalar comparisons in 14.23 seconds / 107 MB and found zero count discrepancies.
It checked all 35 consumed pins, 792 native slots, 29 controls, both DOI notices,
parameter rows and private workbook cells without importing the producer's
transformation helpers. Binary workbook decoding shares the pinned xlrd 2.0.2
reader; classification and numerical accounting are independent.

**67 focused source tests** pass, alongside strict typing and configured style
checks. No LRA engine was called by this source audit. A launcher syntax refusal
occurred before any scientific child process and is retained separately; the
first actual scientific producer and observer both completed successfully.
[result identity](result.json) retains exact source/runtime/resource evidence.

Run from the repository, with the development package installed:

```bash
python -B -m bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot \
  --repository . --output artifacts/bokesjon-source-reproduction
```

Reproduce the public data tables from those saved products:

```bash
python reports/science/pollen-reconstruction/bokesjon-pilot/project.py \
  --study artifacts/bokesjon-source-reproduction \
  --output artifacts/bokesjon-public-tables
```

The five projected tables/JSON bodies reproduce byte for byte from the executed
products. Raw private lookup routes and workbook header witnesses are excluded.

Optional `--workbook` and `--author-lookup` arguments admit only their exact pinned
private-source bytes. They require the supported optional xlrd 2.0.2 decoder for
the workbook and preserve all private rectangles locally. Omitting them leaves
that evidence unavailable rather than fabricating it.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** The complete source-native BOKE/KRAG taxon window, public core/chronology/rights identities and literal parameter availability are source-bound and independently checked.

**Unsupported claim.** A scientifically admitted full forest/open/cereal reconstruction, observed ancient basin, calibrated age/parameter uncertainty, untouched confirmation or measured vegetation accuracy.

**Actual verification performed.** 67 focused tests; producer 13.37 s / 176 MB and independent observer 14.23 s / 107 MB; all 35 pins, 792 native slots, 29 controls, 2 DOIs, 31 LandClim targets, 110 European reference rows and private workbook cells checked; 20,646 scalar comparisons, maximum count error 0.

**Remaining input or review.** Qualified taxon/denominator/parameter and static-basin/regional applicability decisions remain absent; reviewed sources supply no matched ancient non-pollen cover vector. Resolver: BOKE/KRAG source custodians, qualified palynology/chronology/basin reviewers and an independent vegetation-reference owner. Reopen when: A scoped justified source/profile decision or compatible independent measured cover packet is supplied.

**Cause category.** assumption|comparability|data|qualified review

**Consequence.** Keep all omissions, source denominators, unresolved cereal/rye mapping and missing uncertainty/refusal states distinct; do not score vegetation accuracy.

**Precise next acceptance route.** Select and justify the complete taxon/parameter profile and physical assumptions, carry the admitted inputs through the maintained LRA workflow, then evaluate a separately frozen compatible independent reference.

**Negative or refused result.** No full 31-taxon or rye-split admission; KRAG 33 reported NISP lack exact author-lookup routes; no admitted measured vegetation pair; missing source counts are not zero-filled.

**Matched denominator.** 148 source samples: 52 BOKE + 96 KRAG; 7 selected samples: 3 + 4; 792 taxon/sample slots: 218 reported positive + 574 omitted candidates; reported NISP 2,553 + 3,973. Workbook 2,556 and 12 explicit crop-zero cells remain separate.

Retained evidence: [reports/science/pollen-reconstruction/bokesjon-pilot/result.json](result.json), [reports/science/pollen-reconstruction/bokesjon-pilot/native-count-slots.csv](native-count-slots.csv), [reports/science/pollen-reconstruction/bokesjon-pilot/parameter-coverage.json](parameter-coverage.json), [reports/science/pollen-reconstruction/bokesjon-pilot/independent-check.json](independent-check.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
