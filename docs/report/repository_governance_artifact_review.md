# Repository governance artifact review

| Artifact | Action | Surface kind | Reason |
| --- | --- | --- | --- |
| `docs/report/animal_publication_release_gate.json` | `keep` | `claim_gate` | This file blocks strong public claims when traceability or chronology support is missing. |
| `docs/report/animal_foundation_validation.json` | `keep` | `validation` | This file checks sample, site, coordinate, and source structure instead of just formatting. |
| `data/adna/governance/source_library/project_sample_site_review.json` | `keep` | `evidence_review` | This file surfaces site-assignment weakness project by project. |
| `data/adna/governance/source_library/project_sample_chronology_review.json` | `keep` | `evidence_review` | This file surfaces chronology extraction weakness project by project. |
| `docs/report/animal_point_support_packets.json` | `keep` | `traceability` | This file keeps published points anchored to sample, site, and coordinate support. |
| `docs/report/animal_atlas_readiness.json` | `reframe` | `coverage_summary` | The current name reads stronger than the underlying point depth and must always sit beside unresolved and blocked counts. |
| `docs/report/animal_sample_database_review.json` | `reframe` | `public_posture` | This file should describe partial recovery posture, not broad readiness or region-agnostic support. |
| `data/adna/governance/cross_species_map_readiness.json` | `reframe` | `coverage_summary` | This file is useful only when readers can also see how many rows remain unresolved or refused. |
| `docs/report/animal_output_audit.json` | `retire` | `publication_accounting` | This file counts shipped public surfaces but says little about evidence depth and should not lead the scientific story. |
