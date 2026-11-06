# Nordic source capability and country dimensions

The [retained source/country replay](report.json) joins the governed
11-family source-stage matrix to the 198-cell country coverage ledger. It
requires every family to have one row for each of six country partitions and
three distinct dimensions: source-reported, governed assignment, and
publication. The resulting 66 family/partition entries retain the original
availability, lifecycle, reason codes, source snapshot and all nullable counts
separately for each dimension. The four Nordic countries and the `UNASSIGNED`
and `OUTSIDE` partitions are all present.

The parent ledger's 20 input artifacts were rechecked against their byte counts
and SHA-256 digests. The source-stage matrix has 11 rows and a 187-row
capability/materialization audit; the country ledger has 198 cells. This
consumer does not reinterpret a `null` count as zero, sum incompatible
families, or promote capture to scientific admission.

The [combined source reconciliation](../../../source-relations/source-reconciliation/README.md)
also checks the three historical Rootsi and OpenLand intake receipts and their
12 four-country claims. Those claims remain separate from this 11-family cube;
their original archives do not create new admitted country observations.

The [Neotoma dataset ledger](neotoma-entities/README.md) adds source-bound
entity decisions for one family: 85 datasets occur in the selected direct
observed-pollen study and 124 do not. Its separate sample prerequisites do not
admit any dataset to LRA or measured-vegetation validation. Entity decisions
for the other source families still require their own source evidence.

The [used-dataset publication ledger](neotoma-attribution/README.md) joins
those 85 Neotoma study datasets to exact provider citation responses. Seventy-nine
have one provider-flagged primary publication; six need primary-link review.
Thirteen carry distinct source DOI names, with 18 datasets in the union of
citation-review cases. Neotoma's policy-level CC BY 4.0 statement and these
metadata do not resolve sample-specific scientific admission or vegetation truth.

The existing [SEAD site ledger](../../../source-relations/sead-country-retrieval/README.md)
already records all 2,195 discovered site IDs and UUIDs. Governed boundaries
assign 2,069 to SE/DK/NO/FI and retain 103 for review plus 23 unassigned;
only assigned sites occur in the retrieved and normalized site consumers.
This is archaeological site context and country accountability. It does not
admit a SEAD pollen series, an LRA cohort, or vegetation truth. The two linked
entity ledgers therefore cover different scientific roles and denominators.

LandClim's governed sequence inventory at
`data/landclim/normalized/nordic_pollen_site_sequences.csv`
supplies 490 context rows: Sweden 198, Denmark 127, Norway 93 and Finland 72.
These rows already feed the atlas and describe source site coverage, not
authenticated historical counts. The separate [1,128-row LandClim II study
crosswalk](../../../publication-replay/landclim-study-inputs/README.md) leaves
every historical primary input identity unresolved; its Nordic country labels
are publication metadata. Neither inventory supplies measured vegetation truth
or a qualified LRA cohort for the current Neotoma sites.

The [human and animal DNA source-scope review](../../../source-relations/dna-scope/README.md)
keeps two more entity populations distinct. AADR v66 has 51,005 annotation
rows across its 1240K and HO captures, representing 27,755 Genetic IDs;
these are human-source accountability units. The animal point surface has
165 features backed by 322 distinct sample IDs, of which eight Nordic
locality features represent 12 sample IDs. Its 1,468-row foundation still
has eleven unresolved paper-link rows. Neither population supplies pollen
counts or an independent vegetation reference, and the eight animal locality
features are not a Nordic pollen cohort.

The [Nordic AADR entity account](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/aadr-nordic-entities/README.md)
joins all 1,325 exact four-country source Genetic IDs to their country sample
products: 1,231 appear and 94 lack source coordinates. The
[animal entity account](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md)
checks the existing 322 mapped and 1,146 map-excluded sample decisions against
all 1,468 normalized IDs without copying the original decision rows. These
are source-to-product membership results, not scientific or source-country
admission for either family.

| Family | Governed raw stage | Governed published stage | Four-country publication availability | Qualification |
| --- | --- | --- | --- | --- |
| AADR | present | present | collected in SE/DK/NO/FI | authority and source review required |
| animal aDNA | present | present | collected in SE/DK/FI; zero observations in NO | authority and biological sample review required |
| boundaries | present | present | collected in SE/DK/NO/FI | boundary inclusion review required |
| EMPD2 | missing | missing | blocked in SE/DK/NO/FI | source-reported partial coverage is not an admitted reference |
| HYDE | missing | missing | blocked in SE/DK/NO/FI | private custody is separate from governed source admission |
| LandClim | present | present | collected in SE/DK/NO/FI | context publication is not vegetation truth |
| Neotoma | present | present | collected in SE/DK/NO/FI | point context is not LRA admission |
| NFI | missing | missing | blocked in SE/DK/NO/FI | source and country reference review required |
| RAÄ | present | refused | blocked in SE; source unavailable elsewhere | authority and review unresolved |
| SEAD | present | present | collected in SE/DK/NO/FI | source-reported country cells are zero, governed site assignments are nonzero |
| SVAR | present | present | blocked in SE; source unavailable elsewhere | source authority refused |

“Collected” in this table is the exact `available_collected` publication
availability code, not a claim that every source family has an approved
analytical use. The full report supplies the separate lifecycle status and
count denominator for each cell. In particular, SEAD's source-reported zero
country cells coexist with governed and published site counts because those
dimensions answer different questions. The source-stage matrix's missing HYDE
row describes governed repository materialization; it does not deny the
separately retained private archive.

RAÄ also has a separately identified `raa/lamningar-v1` native source-context
profile. The report preserves that optional `source_context_profile` alongside
the historical WFS stage. It permits the retained official capture's native
identities, verbatim fields, relationships and separately typed remains versus
positional-uncertainty geometry context, under its recorded source-use terms.
The [national source account](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/archaeology-native-reconciliation/README.md)
owns its 764,383-record population and payload qualification. Historical WFS
density retains its existing inventory, summary and review requirements;
matching that historical population is not a prerequisite for the separately
identified native capture. Scientific interpretation, chronology, events and
publication admission remain false in the native profile, and the country
cube retains its existing count and availability meanings.

The native reader and existing stage/country/source-capability generators were
executed on the retained capture at source `0ae2ea669`. The new profile is the
only semantic stage addition: every legacy stage field, all 187 capability audit
rows, and every count/status/source field in the 198 country cells agree. Required
parent/build identities were refreshed through the existing generators.

## Current country-ledger authority

The 28 October 2026 [governed ledger](../../../../../data/country_dimension_coverage.json)
retains all 198 count, availability and lifecycle cells while identifying each
partition's actual assignment authority. The current Finnish boundary profile
includes both `FIN` and `ALD`; the historical SEAD admission retains its original
2,069-site cohort and boundary digest. Source-country fields and publications
are not labeled as fresh current-boundary replays without evidence.

The updated writer and independent full-cube check are documented in
[the country account](../../../../../reports/science/country-evidence-status.md#current-assignment-authority-accounting).
The existing source-capability consumer was then run at `47da870a2` on the
committed current parents: 0.96 s, RSS 49,332,224 bytes. Its independent 1.03 s
readback, RSS 42,172,416 bytes, verifies all 66 entries/198 dimension projections,
all 20 parent pins and the unchanged 187 capability rows, source stages, counts
and lifecycle states. Both meet their 60 s / 512 MiB / 8 MiB envelopes.
The new raw result remains under
`artifacts/root/source-capability-boundary-authority/` and its independent
observation under `artifacts/verification/source-capability-boundary-authority/`.

The retained report download above keeps its own earlier parent identities.
It has not been overwritten or relabeled as this later execution. The command
below evaluates the current governed parents; exact replay of an earlier
snapshot requires its recorded input bytes. Source receipt, assignment metadata
and scientific admission remain separate.

## Reproduce

From the repository root, use a fresh output directory:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.source_capability \
  --repository "$PWD" \
  --output "$PWD/artifacts/jobs/source-capability/reproduction"
```

The producer refuses a missing or duplicate source/country cell, changed
parent artifact, negative count, incomplete source audit or changed input
bytes. It emits no new country assignment, ecological classification,
cross-source comparison, or release decision.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Named Nordic source/development wrapper; its own source denominator remains separate from canonical study/account limits.

**Supported claim.** The retained account joins eleven source families to six country partitions and three distinct availability dimensions without conflating reported source, governed assignment and publication.

**Unsupported claim.** Captured or published source entries do not establish scientific admission, authentic historical LandClim inputs, LRA cohorts, ecological events or measured vegetation truth.

**Actual verification performed.** The source-bound three-scope producer at a18530b54 completed in 326.099 s. Independent decoded preservation and all three actual JavaScript index-factory checks passed in 65.517 s aggregate, preserving unrelated science and retained chronology context. Freshly served World Chromium passed 22 source-backed and labelled synthetic temporal cases; this does not qualify general browser behavior, external providers or query latency. Regional animal/index populations and 13 retained chronology nodes are unchanged. The source-country capability capture was not rerun. The earlier thirteen-input entity reconciliation at 10bf26d61 confirms 1,481 = 335 mapped + 1,146 excluded in 167 features, with unchanged twelve-ID Nordic subset; country producers and older captures were not rerun. Current entity reconciliation at a1801f5be43845a9d34b0cd09be4607958ba09ac completes in0.127s/RSS43696128B,13inputs+producer/HEAD/indexstable:1482source IDs=335mapped+1147excluded/167features. OnlyBER11_L is added asoneexcluded source; alloldmappedIDs/Nordic12IDs8features/falseadmissions unchanged. No originalcountry, map, source, chronology or model producer is rerun; previous actuals retain their sourceepochs.

**Remaining input or review.** Per-family entity, chronology and rights decisions remain required. Current animal evidence has 163 features/324 mapped samples after exact child-owned admission; four ambiguous goat identities remain refused. The retained source-country account keeps its original capture scope and is not requalified by current DNA accounting.

**Cause category.** Source-country capability accounting with separately refreshed current DNA context.

**Consequence.** Null and zero remain different, incompatible families cannot be summed as one scientific cohort, and stale contextual population prose cannot enlarge current point support.

**Precise next acceptance route.** Qualify source-specific scientific admission independently. Re-execute the source-country owner only when its own governed country/source inputs change; preserve its captured 198-cell population and the distinct current DNA source account.

**Negative or refused result.** All1,128historical primary LandClim inputs remain unauthenticated; no measured vegetation target or LRA cohort is created by source availability.

**Matched denominator.** Eleven families by six partitions by three dimensions = 198 cells/66 family-partition entries; 187 capability-audit rows remain the retained capture. The current linked animal accounting has 167 features/335 mapped records, separate from eight Nordic localities/twelve mapped records.

- [Retained qualification evidence: docs/report/regions/nordic/source-capability/report.json](report.json) (SHA-256 `42eb47abd321c9cf6856ca8e4cf75bbfae1a5fd9c6517a8075692cbba6b50019`).

- [Retained qualification evidence: docs/report/source-relations/dna-scope/report.json](../../../source-relations/dna-scope/report.json) (SHA-256 `dd88281f34bd1c685b4abda3ba46565c704d9769849d17f83eab97f805ae653d`).

- [Retained qualification evidence: reports/science/animal-entity-capability/report.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/report.json) (SHA-256 `2c7807f58aa96ce33426817d9907fb89ea1b4c5f96854175fdf0ee75a070bc60`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

- [Canonical scientific account: reports/science/nordic-pollen-study.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/nordic-pollen-study.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
