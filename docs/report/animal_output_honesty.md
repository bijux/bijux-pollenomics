# Animal output honesty

- Tracked sample rows: `1468`
- Mapped sample rows: `322`
- Blocked sample rows: `1146`
- Unresolved sample rows: `378`
- Country-published sample rows: `12`

| Project species | Source-native taxon mismatches | Tracked samples | Mapped samples | Blocked samples | Unresolved samples | Country-published samples |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Bos taurus | Bos primigenius: 3 | 132 | 31 | 101 | 33 | 5 |
| Camelus dromedarius | — | 31 | 0 | 31 | 0 | 0 |
| Canis lupus familiaris | — | 4 | 0 | 4 | 1 | 0 |
| Capra hircus | — | 82 | 82 | 0 | 0 | 0 |
| Equus caballus | — | 550 | 148 | 402 | 2 | 0 |
| Felis catus | — | 106 | 54 | 52 | 0 | 0 |
| Ovis aries | Capra hircus: 1 | 200 | 5 | 195 | 1 | 5 |
| Rangifer tarandus | — | 20 | 0 | 20 | 0 | 0 |
| Sus scrofa domesticus | — | 343 | 2 | 341 | 341 | 2 |


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Actual normalized animal entity/map populations and distinct chronology/event acceptance boundaries.

**Supported claim.** This honesty account keeps mapped, blocked, unresolved and country-published sample units and source-native taxon mismatches explicit.

**Unsupported claim.** Project-species labels cannot erase Bos primigenius or Capra hircus source taxonomy mismatches; published membership is not domestication or farming evidence.

**Actual verification performed.** Read all nine project-species rows and totals; checked 1468=322+1146 and separate 378 unresolved/12 country-published values. No taxonomic or output producer was rerun.

**Remaining input or review.** Qualified taxonomic interpretation and sample-level date/location/source review remain needed, especially when project and source-native taxa differ.

**Cause category.** Project versus source-native taxonomy and asymmetric publication support.

**Consequence.** Mapped and country-published are nested/overlapping memberships, not additive sample populations; unresolved is a diagnostic subset.

**Precise next acceptance route.** Trace each mismatched source-native sample through project and taxonomy records, retain explicit wild/progenitor scope, and rerun source-owned output contracts before changing biological labels.

**Negative or refused result.** Three cattle-project samples retain Bos primigenius andone sheep-project sample retains Capra hircus native labels; 1146 samples remain blocked.

**Matched denominator.** 9 project-species rows total 1468 tracked, 322 mapped, 1146 blocked, 378 unresolved and 12 country-published sample rows. Historical 331 mapped is not current 322; sample memberships are not 165 atlas features.

Qualified authored reader SHA-256: `93eeb18a90da669e5fc3133392dccec8398a06aeee2c8626423252b79294002e`.

- [Retained qualification evidence: docs/report/animal_output_honesty.json](animal_output_honesty.json) (SHA-256 `e31a154caf4951ffdf2b8ae5d53e65a4967d78e3c3d405af1b6219812c394aee`).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md) (source SHA-256 `3a0a899e96cfe7d95bdef41012516f39ce2b68606212efecafe1d909b6ccd045`).

- [Canonical scientific account: reports/science/animal-sample-chronology.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-sample-chronology.md) (source SHA-256 `0f4b689193ff2e872be0155dc77e48be083f917812248c6b29cb6b364c390545`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
