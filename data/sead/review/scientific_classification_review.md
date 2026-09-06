# SEAD qualified scientific classification review

This packet prepares source-native SEAD taxonomy and ecocodes for qualified human review. No derived mapping is accepted, no reviewer is impersonated, and propagation remains refused.

## Governed identity

- Source run: `sead-full-evidence-39bfff6a-ce80714e`
- Build: `sha256:ce80714e4c9e9974b24913e5da50f49854670ed642879c1ca5076499e1d56725`
- Acquisition manifest SHA-256: `6fc2428046d148f9ce6c158f982afbbbbaea39de2132850a4fb8f41acf8a4c14`
- Parent admission SHA-256: `168ad1efe6fa68cdb7789246a6cce16670377cdbacd14d1673beaab8ddd1ebd1`
- Evidence manifest SHA-256: `c6c709ddcdadf736f157636874e0cebfb152f90d83d0b90a25e3cfd9dfed1510`
- Evidence file-set SHA-256: `5bf783db87b9bb49ef4ffde39c940d80ace09eaf7723138cf6034e027591c621`

## Review posture

- Candidate mappings: `1,974`
- Accepted mappings: `0`
- Accepted qualified mappings: `0`
- Status: `pending_qualified_scientific_review` / `not_accepted`
- Propagation: `refused` (`source_classification_not_accepted`)

The complete row-level worksheet is `scientific_classification_candidates.csv`. Its target concepts, groups, roles, evidence references, reviewer, and decision date are intentionally empty.

## Source-native taxonomic and ecocode inventory

- Taxon relations: `1,974`
- Ecocode rows: `9260`
- Unique taxon-definition pairs: `9251`
- Taxa with ecocodes: `1466`
- Taxa without ecocodes: `508`

| Native ecocode system | Rows | Taxa | Definitions |
| --- | ---: | ---: | ---: |
| Bugs Ecocodes | 2535 | 1286 | 22 |
| Koch Ecology Codes | 6552 | 866 | 201 |
| Arnolds & van der Maarel (plants) | 173 | 173 | 30 |

The 173 plant-system rows are review priorities, not accepted ecological or pollen mappings. Bugs and Koch ecocodes must not be silently translated into pollen groups.

## Citation authority audit

- Captured bibliography source rows: `1114`
- Chronology-linked bibliography source rows: `1113`
- Site/sample bibliography relations: `39024`
- Accepted classification authorities: `0`

| Ecocode system | Bibliography ID | Status | Reason |
| --- | ---: | --- | --- |
| Bugs Ecocodes | None | missing | ecocode_system_has_no_bibliography_authority |
| Koch Ecology Codes | None | missing | ecocode_system_has_no_bibliography_authority |
| Arnolds & van der Maarel (plants) | 5555 | conflicting | plant_system_points_to_beetle_reference |

The plant system references bibliography ID 5555, whose captured title concerns Central European Ptinidae beetles. It is retained as a conflicting source assertion, not accepted as plant-classification authority.

## Chronology authority gaps

- Claims: `25109`
- Comparable and eligible: `14264`
- Context-only: `10144`
- Unresolved: `641`
- Refused: `10845`
- Post-1950 BP values retained as source-native context and refused from numeric BP comparison: `60`
- Relative periods requiring governed mapping: `10057`
- Analysis-entity ages with unspecified basis: `641`
- Geochronology rows with unknown calibration posture: `87`

`chronology_not_comparable` is an umbrella reason over the refused population. The three specific authority-gap counts are nested within it and must not be added to it.

## Event consequence

- Source observations: `177763`
- Eligible events: `0`
- Refused events: `177763`
- Every observation is refused for `source_classification_not_accepted`.
- Other refusal reasons overlap; they are not mutually exclusive totals.

This packet does not establish arrival, migration, causation, or propagation.

## Qualified reviewer checklist

- Verify source-supported rank without increasing taxonomic resolution.
- Provide a citation or governed authority for every accepted mapping.
- Keep direct crops, qualified crop types, and indicators distinct.
- Review multi-role membership with observation-ID deduplication.
- Record reviewer identity, decision date, rationale, confidence, and evidence references.
- Accept no mapping by omission, label similarity, or batch default.
