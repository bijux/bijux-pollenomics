# Animal foundation validation

- Overall ok: `false`
- Sample rows: `1468`
- Site evidence rows: `553`
- Coordinate rows: `308`
- Atlas rows: `165`

| Check | Passed | Finding count |
| --- | --- | ---: |
| unique_sample_stable_ids | `true` | 0 |
| sample_project_linkage_present | `true` | 0 |
| sample_paper_linkage_present | `false` | 11 |
| supplement_required_projects_archived | `true` | 0 |
| site_evidence_keeps_source_traceability | `true` | 0 |
| mappable_coordinates_keep_complete_basis | `true` | 0 |
| atlas_rows_keep_traceability | `true` | 0 |


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Actual normalized animal entity/map populations and distinct chronology/event acceptance boundaries.

**Supported claim.** The seven-check foundation account retains unique/linkable sample and atlas identities while failing sample-to-paper linkage for 11 rows.

**Unsupported claim.** Six passing structural checks do not override the failed paper linkage or certify reference-grade scientific evidence.

**Actual verification performed.** Read all seven retained checks and population counts; identified the 11 finding paper-linkage failure. No foundation validator or source acquisition was rerun.

**Remaining input or review.** The 11 sample-paper findings require exact primary-paper linkage and qualified source reconciliation before the foundation becomes clean.

**Cause category.** Unresolved source publication linkage in an otherwise traceable metadata foundation.

**Consequence.** overall_ok remains false; structural uniqueness and atlas traceability cannot substitute a missing paper source.

**Precise next acceptance route.** Resolve each named failed sample-paper relation from authentic sources, rerun the maintained validator on exact inputs, and separately review scientific chronology/geography/rights.

**Negative or refused result.** sample_paper_linkage_present false with 11 findings; no passing check converts those failures into admitted evidence.

**Matched denominator.** 1468 sample rows, 553 site-evidence rows, 308 coordinate rows and 165 atlas locality features; 7 checks include 1 failed check with 11 sample-paper findings. These are different entity populations.

Qualified authored reader SHA-256: `7889118561773be2afabe9b5d7696c105b41e412ec28f92154254990a4aaa7ec`.

- [Retained qualification evidence: docs/report/animal_foundation_validation.json](animal_foundation_validation.json) (SHA-256 `62aea5043cd03eb408d198873770bc33dd5a9ab074117b7ef8c0262a9f897dc2`).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md) (source SHA-256 `3a0a899e96cfe7d95bdef41012516f39ce2b68606212efecafe1d909b6ccd045`).

- [Canonical scientific account: reports/science/animal-sample-chronology.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-sample-chronology.md) (source SHA-256 `0f4b689193ff2e872be0155dc77e48be083f917812248c6b29cb6b364c390545`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
