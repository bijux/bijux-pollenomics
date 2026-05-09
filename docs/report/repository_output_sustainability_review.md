# Repository output sustainability review

| Surface | Current posture | Action | Finding |
| --- | --- | --- | --- |
| `report_root_navigation` | `reader_portal_governed` | `keep` | the report root now routes readers through portal families instead of leaving them in a bare artifact spill |
| `generated_root_diagnostics` | `policy_gated` | `keep_only_with_explicit_role` | new root outputs are now governed by an explicit publication policy instead of being justified only by emitter convenience |
| `legacy_diagnostic_overlap` | `one_retirement_still_named` | `retire_or_reframe` | the governance review still names 1 root artifact for retirement or reframing |
| `world_to_country_publication_balance` | `derived_scope_family` | `keep` | world, regional, and country outputs now share one scope lineage instead of multiplying separate product trees |

## Balance Counts

- Runtime Python files: `227`
- Tracked data files: `1532`
- Report files: `270`
- Maintainer root review files: `21`
