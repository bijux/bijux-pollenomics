# Animal sample database review

- Public posture: `partial_sample_owned_animal_evidence_surface`
- Sample database claim supported: `true`
- Nordic view supported now: `false`
- Region-agnostic contract ready: `false`
- World-map expansion posture: `not_supported_until_source_capture_site_resolution_and_chronology_depth_are_materially_stronger`

## Counts

- Tracked projects: `40`
- Tracked papers: `18`
- Tracked supplements: `5`
- Sample rows: `242`
- Site evidence rows: `10`
- Sample site rows: `207`
- Chronology rows: `207`
- Coordinate rows: `10`
- Published atlas points: `2`
- Published country bundles: `4`
- Papers with archived supplements: `1`
- Mapped sample share: `0.0083`

## Thresholds

- Minimum published atlas points: `10`
- Minimum supplement-backed papers: `5`
- Minimum mapped sample share: `0.05`
- Minimum normalized chronology rows: `100`
- Minimum region-agnostic point floor: `25`
- Minimum region-agnostic mapped share: `0.2`

## Posture Findings

- published_atlas_point_count_below_minimum_reading_depth
- supplement_backed_paper_coverage_still_too_low
- mapped_sample_share_still_too_low

## Direct Links

- project_registry: `data/adna/governance/source_library/project_registry.json`
- paper_registry: `data/adna/governance/source_library/paper_registry.json`
- supplement_registry: `data/adna/governance/source_library/supplement_registry.json`
- sample_foundation_truth: `data/adna/governance/animal_sample_foundation_truth.json`
- sample_database_contract: `data/adna/governance/animal_sample_product_contract.json`
- sample_query_example: `docs/report/sweden/sweden_animal_adna_v66_samples.md`
- site_review: `data/adna/governance/source_library/project_sample_site_review.json`
- chronology_review: `data/adna/governance/source_library/project_sample_chronology_review.json`
- coordinate_provenance_example: `data/adna/species/ovis_aries/normalized/coordinate_provenance.json`
- point_support_packets: `docs/report/animal_point_support_packets.md`
- atlas_evidence_rows: `docs/report/nordic-atlas/nordic-atlas_animal_atlas_evidence.json`
- atlas_map: `docs/report/nordic-atlas/nordic-atlas_map.html`
- country_output_summary: `docs/report/published_reports_summary.json`

## Current Blockers

- foundation_validation_not_yet_clean
- unresolved_site_assignment_rows_remain
- region_only_geography_rows_remain
- published_points_still_depend_on_named_site_geocoding
