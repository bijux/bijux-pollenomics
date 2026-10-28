# Which animal samples reach the map?

We compared the ten normalized species sample tables with the retained
[point candidates](../../../data/adna/final/atlas/animal_atlas_point_candidates.json)
and [map exclusion decisions](../../../docs/report/animal_atlas_exclusion_report.json).
The two existing per-sample sources form an exact, disjoint partition of the
1,481 normalized sample IDs. We keep those original decision rows as the
entity ledger instead of copying them into a second list. The
[reconciliation result](report.json) binds all 13 inputs by size and SHA-256.

| Map decision | Sample IDs | Meaning |
| --- | ---: | --- |
| In 167 point features | 335 | Source-backed map candidate membership; no scientific admission |
| Excluded from point map | 1,146 | 378 unresolved locality, 409 without coordinate provenance, 332 failing the point contract, 27 with unresolved chronology |
| **Normalized foundation** | **1,481** | Every ID has exactly one map decision |

Eight candidate features carry a Nordic inclusion label and refer to 12
distinct sample IDs: Denmark five, Finland two and Sweden five. No Norwegian
animal feature occurs in this retained point surface; that is a product zero,
not evidence that Norway lacks ancient animal remains. Country labels and
map support classes do not establish source-country authority or qualified
biological review. Unresolved paper links and source capability decisions
remain separate; this result admits no ecological, pollen or vegetation analysis.

The [producer](replay.py) checks the normalized IDs against both original
decision sources, refuses overlap, missing IDs, duplicate mappings and broken
sample lineage, then reports the joined counts. Reproduce into a new directory
from the repository root and compare `report.json` byte for byte:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/animal-entity-capability/replay.py \
  --repository . --output artifacts/jobs/animal-entity-capability-replay
```


## Current reconciliation and source epochs

At committed source `988d1ff127bad598ff359cd14fc7bc1409ce5325`, the unchanged
[producer](replay.py) completes in **0.129 seconds**, peak native RSS
**45,236,224 B**. Only the cattle CSV input size and SHA-256 differ from the
previous report, reflecting eleven publication-metadata bindings. Every other
report value is exact: **1,481 = 335 mapped + 1,146 excluded**, 167 locality
features, the twelve-ID/eight-feature Nordic subset and false country/scientific
admission. All 6,544 files consumed across the paired source reports plus HEAD
and index remain unchanged. This refresh adds no mapped owner, selected date,
coordinate, scientific decision or new map/browser execution.

The earlier `10bf26d6` run remains qualified at 0.100 seconds, RSS 43,532,288 B,
under its original cattle CSV identity. That source/map epoch introduced
seventeen recovered owners: eleven mapped and six excluded (five point-contract
and the undated PGULL-2131 chronology refusal). Those observations and all older
source identities remain unchanged; they are not rerun or retagged here.

The owning [chronology account](../animal-sample-chronology.md#current-locality-atlas-maps-and-temporal-runtime)
records the current source, three-scope map and temporal qualification. World
retains 236 child-support intervals across 130 temporally admitted and 37
contextual locality features; 67 gaps remain empty. Its distinct source-chronology
corpus has 1,492 owners, 335 displayable nodes and 1,157 refusals. The equal
counts of 335 mapped normalized records and 335 chronology nodes do not identify
the same membership. Each regional scope retains thirteen source-chronology
nodes, separate from the twelve mapped IDs above. No locality hull supplies a
missing specimen date or makes overlapping source records independent animals.

The current saved-atlas producer and independent readback, decoded three-map
preservation and native index checks pass. Nordic's prior factory qualification
is reused only after exact code/bootstrap/controller/wire/semantic equality; its
original source epoch is preserved. Actual served Chromium passes 27 source-backed
and synthetic cases, including all four Qinghai contextual nodes and a recovered
horse owner. The four goat comparator keys/five candidate accessions remain
ambiguous; they supply no newly resolved normalized identity. No source-country,
biological, field, ecological or query-latency admission follows from these
software/data checks.

Earlier source epochs remain historical. At `a18530b5`, the same reconciliation
qualified 1,464 = 324 mapped + 1,140 excluded IDs in 163 features, with 225
child-support intervals and sixty gaps; its 22 served cases are retained under
their own producing inputs. At `04f1c4857`, it qualified 1,464 = 318 + 1,146 in
161 features. Neither older execution is relabelled or rerun for the current
source population. The original current-population actuals remain under
`artifacts/root/animal-source-consumers/entity-capability-{candidate,result.json}`.
The publication-metadata refresh is retained under
`artifacts/root/source-population-review/current-animal-reports/`.

## Historical source and country-record lifecycle verification

The [lifecycle account](../adna-source-lifecycle/report.json) records a **historical 1,468-ID epoch**, before the four goat identities were refused. Its retained execution covers the four actual country animal bundle producers and CSV writers; it was not rerun for the current reconciliation. The full country bundles match the retained summaries as JSON values, including localities, sample provenance, citations, warnings and chronology precision. All 48 sample CSV fields match byte for byte: Denmark five, Finland two, Norway zero and Sweden five. The Norwegian product zero remains a source/publication support limitation.

At that historical epoch, all ten normalized sample JSONs retained the animal-DNA domain and false pollen/pollen-propagation eligibility for 1,468 sample IDs. Their source families were ENA 1,411, BioProject 22, SRA 20 and GenBank 15; modalities were 1,442 archive-read records and 26 mitogenome-only records. Every one of 60 nonempty literal sample-lineage/chronology source pointers resolves to frozen retained bytes or a named ZIP member. Three compressed article/archive transports lack historical metadata digests; current frozen byte correspondence does not authenticate those original source histories.

The [capture](../adna-source-lifecycle/capture.json) records six native-zero stages, eight country CSV comparisons, four complete animal bundles and 26 maintained boundary controls. That historical source-ID partition was 322 mapped + 1,146 excluded = 1,468, in 165 point features. The capture JSON is unchanged and is not evidence for a current 1,468-ID population. This verifies the metadata lifecycle and domain separation. It supplies no accepted empirical classification, new map/browser capture, genotype result, source-rights decision or independent human biological review.



The retained atlas source-view packet authenticates all captured software bodies at its original execution epoch. Six portal-reader modules are historical Git witnesses while their current maintained software is qualified separately. Reading or transporting that fixed packet does not admit fresh source reproduction, rerun its generators or browser, or change the scientific admission of displayed records.

<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Every current normalized animal source ID has one explicit map membership or exclusion. The 1,481 records partition as 335 mapped and 1,146 excluded in 167 locality features; country, chronology and biological admission remain separate.

**Unsupported claim.** Scientific animal/ecological admission or source-country authority.

**Actual verification performed.** At committed source988d1ff127bad598ff359cd14fc7bc1409ce5325, the unchanged thirteen-input entity producer passes0.129seconds, RSS45,236,224B. Compared with the earlier10bf report, only cattleCSV input size/SHA changes; all populations, memberships and decisions are exact. Parallel current source reports preserve6544source files+HEAD/index. Earlier10bf/a185/04f and1468-ID lifecycle actuals remain their original source epochs; no model, country, census, map or browser replay.

**Remaining input or review.** The current ID partition is complete, but 1,146 point-map exclusions and unresolved specimen, chronology and source-country interpretations prevent stronger biological/ecological admission. Resolver: Animal source custodian and qualified provenance/biological reviewer Reopen when: Source-backed locality, coordinates, chronology, paper links and admission are decided per sample.

**Cause category.** data|qualified review

**Consequence.** Map candidates and product zeros cannot be read as biological distribution or pollen context.

**Precise next acceptance route.** Source-backed locality, coordinates, chronology, paper links and admission are decided per sample. Then update reports/science/source-cohorts.md.

**Negative or refused result.** 1,146 exclusions comprise 378 locality, 409 coordinate-provenance, 332 point-contract and 27 chronology refusals. Norway has zero mapped labels in this product, not zero archaeological remains. Ambiguous specimen/paper links and qualified biological interpretation remain open.

**Matched denominator.** 1,481 normalized source IDs = 335 mapped in 167 features + 1,146 excluded. Nordic retains twelve mapped IDs in eight features (DK5/FI2/SE5). World130 admitted/37 contextual localities retain236 occurrence intervals/67 gaps. Distinct source chronology1492owners/335nodes/1157refusals is not this mapped-ID population.

Retained evidence: [reports/science/animal-entity-capability/report.json](report.json), [docs/report/animal_atlas_exclusion_report.json](../../../docs/report/animal_atlas_exclusion_report.json), [reports/science/adna-source-lifecycle/report.json](../adna-source-lifecycle/report.json), [reports/science/adna-source-lifecycle/capture.json](../adna-source-lifecycle/capture.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
