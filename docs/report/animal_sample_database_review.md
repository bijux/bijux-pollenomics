# Animal sample database review

- Public posture: `partial_sample_owned_animal_evidence_surface`
- Sample database claim supported: `true`
- Nordic view supported now: `true`
- Region-agnostic contract ready: `false`
- World-map expansion posture: `not_supported_until_source_capture_site_resolution_and_chronology_depth_are_materially_stronger`

## Counts

- Tracked projects: `40`
- Tracked papers: `18`
- Tracked supplements: `75`
- Sample rows: `1468`
- Site evidence rows: `553`
- Sample site rows: `1475`
- Chronology rows: `1475`
- Coordinate rows: `308`
- Published atlas points: `165`
- Published country bundles: `4`
- Papers with archived supplements: `18`
- Mapped sample share: `0.2193`
- Projects blocked in intake recovery: `23`
- Projects ready for publication review: `11`
- Implausibly low recovery projects: `0`

## Thresholds

- Minimum published atlas points: `10`
- Minimum supplement-backed papers: `5`
- Minimum mapped sample share: `0.05`
- Minimum normalized chronology rows: `100`
- Minimum region-agnostic point floor: `25`
- Minimum region-agnostic mapped share: `0.2`

## Posture Findings


## Direct Links

- project_registry: `data/adna/governance/source_library/project_registry.json`
- paper_registry: `data/adna/governance/source_library/paper_registry.json`
- supplement_registry: `data/adna/governance/source_library/supplement_registry.json`
- sample_foundation_truth: `data/adna/governance/animal_sample_foundation_truth.json`
- sample_database_contract: `data/adna/governance/animal_sample_product_contract.json`
- sample_query_example: `docs/report/countries/sweden/sweden_animal_adna_v66_samples.md`
- site_review: `data/adna/governance/source_library/project_sample_site_review.json`
- locality_conflicts: `data/adna/governance/source_library/sample_locality_conflict_ledger.json`
- locality_curation_workflow: `data/adna/governance/source_library/sample_locality_manual_curation_workflow.json`
- locality_substitution_ledger: `data/adna/governance/source_library/project_locality_substitution_ledger.json`
- locality_normalization_dictionary: `data/adna/governance/source_library/site_name_normalization_dictionary.json`
- locality_completeness: `data/adna/governance/source_library/project_locality_completeness.json`
- chronology_review: `data/adna/governance/source_library/project_sample_chronology_review.json`
- chronology_conflicts: `data/adna/governance/source_library/sample_chronology_conflict_ledger.json`
- chronology_precision_audit: `data/adna/governance/source_library/sample_chronology_precision_audit.json`
- date_evidence_gap_queue: `data/adna/governance/source_library/date_evidence_gap_queue.json`
- project_recovery_stage_review: `data/adna/governance/source_library/project_recovery_stage_review.json`
- project_expected_sample_yield_review: `data/adna/governance/source_library/project_expected_sample_yield_review.json`
- paper_expected_sample_yield_review: `data/adna/governance/source_library/paper_expected_sample_yield_review.json`
- species_project_deficit_ledger: `data/adna/governance/source_library/species_project_deficit_ledger.json`
- manual_curation_worklist: `data/adna/governance/source_library/manual_curation_worklist.json`
- source_recovery_progress: `data/adna/governance/source_library/source_recovery_progress.json`
- missing_source_queue: `data/adna/governance/source_library/missing_source_queue.json`
- source_recovery_release_guard: `data/adna/governance/source_library/source_recovery_release_guard.json`
- animal_intake_recovery_review: `docs/report/animal_intake_recovery_review.json`
- coordinate_provenance_example: `data/adna/species/ovis_aries/normalized/coordinate_provenance.json`
- point_evidence_review: `docs/report/animal_point_evidence_review.md`
- atlas_evidence_rows: `docs/report/world/world_animal_atlas_evidence.json`
- atlas_map: `docs/report/world/world_map.html`
- country_output_summary: `docs/report/published_reports_summary.json`

## Current Blockers

- foundation_validation_not_yet_clean
- unresolved_site_assignment_rows_remain
- coordinate_provenance_refusals_remain
- published_points_still_depend_on_named_site_geocoding


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Actual normalized animal entity/map populations and distinct chronology/event acceptance boundaries.

**Supported claim.** The database review supports a partial sample-owned animal metadata surface while explicitly refusing region-agnostic readiness and broader world-map expansion.

**Unsupported claim.** Meeting numerical readiness floors is not reference grade, global representativeness or scientific admission of every mapped source.

**Actual verification performed.** Read counts, readiness thresholds and four blockers; checked 1468 samples, 165 features and 322 mapped share 0.2193. No source database or threshold evaluation was rerun.

**Remaining input or review.** Primary paper linkage, unresolved sample sites, coordinate refusals and named-site geocoding need source-owner and qualified scientific resolution.

**Cause category.** Partial sample database with source-depth and publication limits.

**Consequence.** A supported database structure/Nordic view does not authorize expanding scientific claims to world coverage.

**Precise next acceptance route.** Resolve native source/sample/site/chronology gaps and replay the database/publication contracts, then independently review geographic representativeness before broader deployment.

**Negative or refused result.** region_agnostic_contract_ready false; world expansion unsupported; 23 intake projects blocked. The historic 170/331 atlas no longer describes the current 165/322 surface.

**Matched denominator.** 40 tracked projects, 18 papers, 75 supplements; 1468 normalized samples versus 1475 sample-site/chronology rows; 553 site-evidence/308 coordinate rows; 165 features/322 mapped samples; 4 country bundles.

Qualified authored reader SHA-256: `0a640897fe81eb48dbf6cb963acf55be3a78e247f3be6034f87696dccd4230d0`.

- [Retained qualification evidence: docs/report/animal_sample_database_review.json](animal_sample_database_review.json) (SHA-256 `2ccfbe1b1c17555e341378d3b4582d14e9447145f2a5f5da20a4544e3f80a610`).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md) (source SHA-256 `fdca2e23ab7891334135a9b72600149ec44ac2b4c8f5e7452da1ccec7289281d`).

- [Canonical scientific account: reports/science/animal-sample-chronology.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-sample-chronology.md) (source SHA-256 `0f4b689193ff2e872be0155dc77e48be083f917812248c6b29cb6b364c390545`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
