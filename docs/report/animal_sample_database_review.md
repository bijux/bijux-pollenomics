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

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md) (source SHA-256 `3a0a899e96cfe7d95bdef41012516f39ce2b68606212efecafe1d909b6ccd045`).

- [Canonical scientific account: reports/science/animal-sample-chronology.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-sample-chronology.md) (source SHA-256 `0f4b689193ff2e872be0155dc77e48be083f917812248c6b29cb6b364c390545`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
