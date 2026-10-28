# Animal output audit

- Report root: `docs/report`
- Atlas bundle present: `true`
- Country bundle count: `4`
- Point candidate count: `165`
- Candidate rows with full traceability: `165`
- Tracked sample rows: `1468`
- Mapped sample rows: `322`
- Blocked sample rows: `1146`
- Unresolved sample rows: `378`
- Country-published sample rows: `12`

## Species output counts

| Species | Atlas localities | Country outputs | Locality artifact shipped | Nordic lead count |
| --- | ---: | ---: | --- | ---: |
| Equus caballus | 73 | 0 | true | 0 |
| Sus scrofa domesticus | 2 | 1 | true | 0 |
| Ovis aries | 2 | 2 | true | 0 |
| Bos taurus | 22 | 2 | true | 0 |
| Capra hircus | 27 | 0 | true | 0 |
| Canis lupus familiaris | 0 | 0 | true | 0 |
| Felis catus | 39 | 0 | true | 0 |
| Camelus dromedarius | 0 | 0 | true | 0 |
| Rangifer tarandus | 0 | 0 | true | 1 |
| Equus asinus | 0 | 0 | true | 0 |

The current public report tree ships `165` mapped non-human animal atlas localities and `5` country-resolved animal output hits across the species table above. Those counts still need to be read beside blocked and unresolved sample totals rather than as a standalone readiness claim.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Actual normalized animal entity/map populations and distinct chronology/event acceptance boundaries.

**Supported claim.** The retained output-audit capture describes its historical publication inventory; the separate current entity account reconciles present mapped locality features and specimen membership.

**Unsupported claim.** Bundle presence, full traceability and country output hits are not reference-grade readiness, scientific country approval or worldwide completeness.

**Actual verification performed.** Current saved-source consumer and independent comparison reconcile all 1464 normalized IDs into 324 mapped IDs in 163 locality features and 1140 reason-coded exclusions. Complete child chronology/provenance packets, coordinates and ownership are preserved; only the declared locality display labels change. Two horse localities add six source-supported owners without assigning a default BP epoch. The retained output-audit capture still describes 165 features/322 mapped IDs; it was not rerun or relabeled. The earlier thirteen-input entity reconciliation at 10bf26d61 confirms 1,481 = 335 mapped + 1,146 excluded in 167 features, with unchanged twelve-ID Nordic subset; country producers and older captures were not rerun. Current entity reconciliation at a1801f5be43845a9d34b0cd09be4607958ba09ac completes in0.127s/RSS43696128B,13inputs+producer/HEAD/indexstable:1482source IDs=335mapped+1147excluded/167features. OnlyBER11_L is added asoneexcluded source; alloldmappedIDs/Nordic12IDs8features/falseadmissions unchanged. No originalcountry, map, source, chronology or model producer is rerun; previous actuals retain their sourceepochs.

**Remaining input or review.** Blocked/unresolved samples and mixed coordinate/taxon scopes require source-owner review. Current source-bound map, full-index and narrow served-temporal checks do not establish broader browser, latency or scientific admission.

**Cause category.** Product publication inventory with unresolved biological/source admission.

**Consequence.** Fivecountry/species output hits andfourcountry bundles are publication inventory, not five additional sites or a global admission.

**Precise next acceptance route.** Reproduce the exact source-owned products, review identity deltas and unresolved samples, then qualify source/geography/chronology decisions separately from output presence.

**Negative or refused result.** 1140 exclusions and 378 unresolved-locality sample rows remain. The historical country-publication capture has no horse outputs and does not erase the current 75 global horse locality features.

**Matched denominator.** Current linked entity result: 1,482 tracked source records = 335 mapped + 1,147 excluded, in 167 locality features. The unchanged country lifecycle has twelve sample publications/four country bundles/five species-country cells. Retained output-audit 165/322 and earlier 161/318 and 170/331 epochs remain historical.

- [Retained qualification evidence: docs/report/animal_output_audit.json](animal_output_audit.json) (SHA-256 `32b6ac488b84fecd80020ba61894a50b8cad63b7f34546b262636043440e01f7`).

- [Retained qualification evidence: reports/science/animal-entity-capability/report.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/report.json) (SHA-256 `2c7807f58aa96ce33426817d9907fb89ea1b4c5f96854175fdf0ee75a070bc60`).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md).

- [Canonical scientific account: reports/science/animal-sample-chronology.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-sample-chronology.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
