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

**Supported claim.** The output audit accounts for current mapped locality features, sample membership, country publications and traceability without conflating their units.

**Unsupported claim.** Bundle presence, full traceability and country output hits are not reference-grade readiness, scientific country approval or worldwide completeness.

**Actual verification performed.** Read the retained output audit and entity-capability account; reconciled 165 candidate/traceable features, 322 mapped and 1146 blocked sample IDs. No output publisher or browser was rerun.

**Remaining input or review.** Blocked/unresolved samples and mixed coordinate/taxon scopes require source-owner review; current browser/map behavior needs separate native execution.

**Cause category.** Product publication inventory with unresolved biological/source admission.

**Consequence.** Fivecountry/species output hits andfourcountry bundles are publication inventory, not five additional sites or a global admission.

**Precise next acceptance route.** Reproduce the exact source-owned products, review identity deltas and unresolved samples, then qualify source/geography/chronology decisions separately from output presence.

**Negative or refused result.** 1146 blocked and 378 unresolved samples remain; zero country outputs for mapped horses do not erase the 73 global horse locality features.

**Matched denominator.** 1468 tracked=322 mapped+1146 blocked; 165 traceable locality features; 12 country sample rows across 4 country bundles and 5 species/country output hits. Historical 170/331 is superseded by 165/322.

- [Retained qualification evidence: docs/report/animal_output_audit.json](animal_output_audit.json) (SHA-256 `32b6ac488b84fecd80020ba61894a50b8cad63b7f34546b262636043440e01f7`).

- [Retained qualification evidence: reports/science/animal-entity-capability/report.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/report.json) (SHA-256 `fe56d60f131e53eeca7e39b512188e23a701f69539be09c42770f7ed70379780`).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md).

- [Canonical scientific account: reports/science/animal-sample-chronology.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-sample-chronology.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
