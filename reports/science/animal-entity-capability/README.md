# Which animal samples reach the map?

We compared the ten normalized species sample tables with the retained
[point candidates](../../../data/adna/final/atlas/animal_atlas_point_candidates.json)
and [map exclusion decisions](../../../docs/report/animal_atlas_exclusion_report.json).
The two existing per-sample sources form an exact, disjoint partition of the
1,464 normalized sample IDs. We keep those original decision rows as the
entity ledger instead of copying them into a second list. The
[reconciliation result](report.json) binds all 13 inputs by size and SHA-256.

| Map decision | Sample IDs | Meaning |
| --- | ---: | --- |
| In 163 point features | 324 | Source-backed map candidate membership; no scientific admission |
| Excluded from point map | 1,140 | 378 unresolved locality, 409 without coordinate provenance, 327 failing the point contract, 26 with unresolved chronology |
| **Normalized foundation** | **1,464** | Every ID has exactly one map decision |

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

The maintained [reconciliation](report.json), after installation of the qualified
source/map products at `a18530b54738b71dfef4d69becaf56ae7ecc4827`, returned exit
zero in **0.156 s** process wall time. Its thirteen raw input pins bind the
current **1,464 = 324 + 1,140** partition, 163 point features and unchanged
twelve-ID Nordic subset. Hyena's Lair and Yana contribute six existing
PRJEB44430 horse owners after complete source-owned child-support admission;
no old mapped owner was removed. Their original dates, coordinates and source
identities remain unchanged. Contextual or undated children do not acquire a
numeric date from locality coverage. The four PRJEB90141 comparator keys still
retain five accession alternatives in their source tables and supply no
normalized/map identities; this reconciliation does not resolve their specimens.

The [independent complete source comparison](../../../artifacts/verification/adna-locality-atlas-consumer/verification.json)
qualifies the current partition and all 37 native outputs. World has 225
child-support intervals across 126 temporally admitted locality points and
37 contextual points; sixty disjoint-support gaps remain empty. The
[three-scope preservation](../../../artifacts/verification/adna-locality-map-preservation/verification.json)
and actual packaged index checks pass, followed by
[22 served Chromium cases](../../../artifacts/verification/adna-locality-served-temporal/observation.json).
Eighteen browser cases use retained source evidence; four are labelled synthetic
controls. The source-backed SEAD [0, 10,000] BP display envelope does not establish
an exact zero-year source date: [0, 0] BP is tested separately as a synthetic
point. These actuals qualify the current consumer's source and temporal behavior,
without source-country, biological, field or query-latency admission.

The [owning chronology account](../animal-sample-chronology.md#current-source-and-map-population)
records the qualified source and three-scope map execution. Its separate
1,475-row chronology corpus has 319 admitted temporal nodes and 1,156 refusals;
Europe-plus and Nordic each have thirteen temporal nodes. Those nodes are not
this point-locality denominator: Nordic's temporal-node labels are DK seven /
FI two / SE four, while the twelve mapped IDs above are DK five / FI two /
SE five.

The earlier reconciliation at `04f1c48579ad39775ac116cee6df1f7a858e74de`
qualified 1,464 = 318 + 1,146 in 161 features. Its receipt remains historical;
the six newly mapped source owners account for the current difference.

## Historical source and country-record lifecycle verification

The [lifecycle account](../adna-source-lifecycle/report.json) records a **historical 1,468-ID epoch**, before the four goat identities were refused. Its retained execution covers the four actual country animal bundle producers and CSV writers; it was not rerun for the current reconciliation. The full country bundles match the retained summaries as JSON values, including localities, sample provenance, citations, warnings and chronology precision. All 48 sample CSV fields match byte for byte: Denmark five, Finland two, Norway zero and Sweden five. The Norwegian product zero remains a source/publication support limitation.

At that historical epoch, all ten normalized sample JSONs retained the animal-DNA domain and false pollen/pollen-propagation eligibility for 1,468 sample IDs. Their source families were ENA 1,411, BioProject 22, SRA 20 and GenBank 15; modalities were 1,442 archive-read records and 26 mitogenome-only records. Every one of 60 nonempty literal sample-lineage/chronology source pointers resolves to frozen retained bytes or a named ZIP member. Three compressed article/archive transports lack historical metadata digests; current frozen byte correspondence does not authenticate those original source histories.

The [capture](../adna-source-lifecycle/capture.json) records six native-zero stages, eight country CSV comparisons, four complete animal bundles and 26 maintained boundary controls. That historical source-ID partition was 322 mapped + 1,146 excluded = 1,468, in 165 point features. The capture JSON is unchanged and is not evidence for a current 1,468-ID population. This verifies the metadata lifecycle and domain separation. It supplies no accepted empirical classification, new map/browser capture, genotype result, source-rights decision or independent human biological review.



The retained atlas source-view packet authenticates all captured software bodies at its original execution epoch. Six portal-reader modules are historical Git witnesses while their current maintained software is qualified separately. Reading or transporting that fixed packet does not admit fresh source reproduction, rerun its generators or browser, or change the scientific admission of displayed records.

<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Every normalized animal source ID has one map membership/exclusion; actual non-pollen source flags and full four-country chronology/provenance publication contracts retain source-domain separation.

**Unsupported claim.** Scientific animal/ecological admission or source-country authority.

**Actual verification performed.** The current 13-input entity replay at code a18530b54 over the independently qualified installed products passes in0.156s/RSS42991616B:1464=324 mapped+1140 excluded IDs in163 features;12 Nordic IDs/eight features remain. All13 inputs/HEAD/index stay stable. The earlier13-input replay04f1c4857 and historical1468-ID lifecycle capture retain their original scope; neither was rerun or relabeled. At a18530b54738b71dfef4d69becaf56ae7ecc4827 the actual saved-animal producer and independent observer first pass preserve all1464 owners:324 mapped in163 features and1140 reasoned exclusions; all4729 tracked package files/1681 animal inputs/101 opened resources/194 discoveries remain stable. Two newly visible horse localities retain six original owners (Hyena's Lair contextual, Yana only its supported child date); no dates are invented. World126 timed-admitted/37 contextual features retain225 child intervals and60 disjoint gaps. The necessary three-scope map producer first passes327.244s/RSS4992991232B/126381319 generatedB within600s/8GiB/192MiB;7181 inputs/2325 actual reads and source epoch are stable. Independent decoded scientific preservation and all three current packaged JavaScript factories first pass in65.517s aggregate within180s, with all unrelated records and319 retained source nodes exact. Nordic275094 search entries/35103623 posting memberships match a fresh full-document equality bridge to authenticated prior proof, followed by actual new-wire JavaScript restoration. Current served World Chromium closure first passes22 cases in2.718s/full-process-treeRSS1236041728B:18 source-backed cases/four explicit synthetic controls,25 served files,zero runtime errors and restored UI state. Site5070 retains its0–10000BP display envelope; the0BP point is explicitly synthetic. No query-latency, fullUI, new source census, field or biological admission claim.

**Remaining input or review.** The 1,464-ID point-map partition is closed, but 1,140 exclusions include unresolved locality, coordinate provenance and chronology; eleven paper links and biological/country authority remain open. Resolver: Animal source custodian and qualified provenance/biological reviewer Reopen when: Source-backed locality, coordinates, chronology, paper links and admission are decided per sample.

**Cause category.** data|qualified review

**Consequence.** Map candidates and product zeros cannot be read as biological distribution or pollen context.

**Precise next acceptance route.** Source-backed locality, coordinates, chronology, paper links and admission are decided per sample. Then update reports/science/source-cohorts.md.

**Negative or refused result.** 1,140 excluded:378 locality,409 coordinate provenance,327 point contract and26 chronology;11 paper links unresolved. Mapped membership and product zeros do not establish biological distribution or ecological admission.

**Matched denominator.** 1,464 IDs =324 mapped sample IDs in163 point features +1,140 excluded; separate Nordic subset12 mapped IDs in eight features. World163 features=126 temporally admitted+37 contextual, with225 child intervals/60 disjoint gaps; these are not additional independent source observations.

Retained evidence: [reports/science/animal-entity-capability/report.json](report.json), [docs/report/animal_atlas_exclusion_report.json](../../../docs/report/animal_atlas_exclusion_report.json), [reports/science/adna-source-lifecycle/report.json](../adna-source-lifecycle/report.json), [reports/science/adna-source-lifecycle/capture.json](../adna-source-lifecycle/capture.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
