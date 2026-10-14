# Animal atlas readiness

- Status counts: `{'publishable': 4, 'thin': 2, 'blocked': 4}`

| Species | Status | Candidate points | Mapped samples | Blocked samples | Unresolved samples | Mappable coordinate provenance | Refused coordinate provenance | Coordinate-provenance denominator | Mappable share | Publication share of mappable coordinates | Reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Equus caballus | publishable | 73 | 148 | 402 | 2 | 208 | 0 | 208 | 1.0000 | 0.3510 | 73 candidate point rows now survive the current atlas contract. |
| Sus scrofa domesticus | thin | 2 | 2 | 341 | 341 | 2 | 0 | 2 | 1.0000 | 1.0000 | 2 candidate point rows remain too thin for broad atlas claims. |
| Ovis aries | thin | 2 | 5 | 195 | 1 | 2 | 0 | 2 | 1.0000 | 1.0000 | 2 candidate point rows remain too thin for broad atlas claims. |
| Bos taurus | publishable | 22 | 31 | 101 | 33 | 24 | 1 | 25 | 0.9600 | 0.9167 | 22 candidate point rows now survive the current atlas contract. |
| Capra hircus | publishable | 27 | 82 | 0 | 0 | 27 | 0 | 27 | 1.0000 | 1.0000 | 27 candidate point rows now survive the current atlas contract. |
| Canis lupus familiaris | blocked | 0 | 0 | 4 | 1 | 0 | 1 | 1 | 0.0000 | N/A | 4 blocked sample rows and 1 refused coordinate-provenance rows still prevent atlas publication. |
| Felis catus | publishable | 39 | 54 | 52 | 0 | 40 | 0 | 40 | 1.0000 | 0.9750 | 39 candidate point rows now survive the current atlas contract. |
| Camelus dromedarius | blocked | 0 | 0 | 31 | 0 | 1 | 0 | 1 | 1.0000 | 0.0000 | 31 blocked sample rows and 0 refused coordinate-provenance rows still prevent atlas publication. |
| Rangifer tarandus | blocked | 0 | 0 | 20 | 0 | 0 | 1 | 1 | 0.0000 | N/A | 20 blocked sample rows and 1 refused coordinate-provenance rows still prevent atlas publication. |
| Equus asinus | blocked | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0.0000 | N/A | 0 blocked sample rows and 1 refused coordinate-provenance rows still prevent atlas publication. |


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Actual normalized animal entity/map populations and distinct chronology/event acceptance boundaries.

**Supported claim.** The readiness table distinguishes four publishable, two thin and four blocked tracked-species publication surfaces with their mapped and blocked support.

**Unsupported claim.** Publishable is a software/metadata posture, not reference-grade biological evidence, complete species coverage or an ecological field recommendation.

**Actual verification performed.** Read all ten species rows and retained status counts; distinguished candidate features, mapped samples and coordinate-provenance denominators. No readiness producer or source review was rerun.

**Remaining input or review.** Blocked samples, unresolved site/chronology and coordinate refusals need native evidence; thin pig/sheep footprints require broader source-qualified support before broad claims.

**Cause category.** Species-asymmetric source and publication readiness.

**Consequence.** 73 horse locality features representing 148 samples do not imply 208 distinct eligible sampling sites; coordinate-provenance records and atlas features use different denominators.

**Precise next acceptance route.** Resolve species-owned missing identity/date/coordinate evidence and replay the publication contract; retain separate feature, sample and coordinate-provenance counts rather than ranking by a mixed share.

**Negative or refused result.** Four species remain blocked; two thin surfaces have only two locality features each. No readiness label grants scientific admission.

**Matched denominator.** 10 tracked-species rows=4 publishable+2 thin+4 blocked; candidate locality total 165 and mapped samples 322. Horse 73/148, goat 27/82, cat 39/54, cattle 22/31, sheep 2/5, pig 2/2.

Qualified authored reader SHA-256: `a9a4f1728852d5074dfd2c144e8edb831915b215e05668a4602a85c600b8b678`.

- [Retained qualification evidence: docs/report/animal_atlas_readiness.json](animal_atlas_readiness.json) (SHA-256 `f88f5cb2da735b255f13795e335ab13dd99de323f4a153237dfa1242d10412d8`).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md) (source SHA-256 `fdca2e23ab7891334135a9b72600149ec44ac2b4c8f5e7452da1ccec7289281d`).

- [Canonical scientific account: reports/science/animal-sample-chronology.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-sample-chronology.md) (source SHA-256 `0f4b689193ff2e872be0155dc77e48be083f917812248c6b29cb6b364c390545`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
