# Country Onboarding Contract

Adding a new country should be mostly a matter of data presence and publication
configuration. It should not require one-off renderer surgery, file-tree churn,
or custom scope code.

## Current Published Country Roster

`Sweden`, `Norway`, `Finland`, `Denmark`

## Required Surfaces

- `published country roster entry`
- `world geography bundle`
- `Europe-plus geography bundle when applicable`
- `country bundle under docs/report/countries/<country-slug>/`
- `subset validation row proving world -> region -> country lineage`

## Code Contracts

- the country is admitted through the published country roster rather than through one-off renderer edits
- world, Europe-plus, Nordic, and country scope derivation must continue to flow from build_published_geography_plan()
- country output directories must continue to derive from docs/report/countries/<country-slug>/ without custom path branches

## Data Contracts

- animal, human, and contextual rows must already resolve to the added country through governed political-entity filtering
- world outputs remain the governing parent surface; new country outputs are filtered descendants, not locally curated forks
- subset validation must prove that the new country bundle does not drift outside its parent regional or world evidence surface

## Documentation Contracts

- reader-facing report pages must continue to explain country bundles as narrower views of one broader product model
- the country onboarding playbook and geography-output handbook must remain accurate after the roster expands
- new country publication must not require a second report tree or scope-specific prose branch

## Test Contracts

- publication geography tests must keep proving world, regional, and country lineage for the expanded roster
- repository contract tests must keep requiring the onboarding contract and geography subset validation surfaces
- docs breadth and report portal tests must keep the broader world-to-country explanation visible after the expansion

## Current Configuration Points

- Published country roster: `packages/bijux-pollenomics/src/bijux_pollenomics/config.py`
- Geography scope plan: `packages/bijux-pollenomics/src/bijux_pollenomics/reporting/geography.py`
- Country bundle generation: `packages/bijux-pollenomics/src/bijux_pollenomics/reporting/service.py`
- Reader-facing playbook: `Future-Country Onboarding Playbook` at `docs/03-bijux-pollenomics-maintain/bijux-pollenomics-dev/future-country-onboarding-playbook.md`

## Example

The contract is satisfied when adding `Germany` only requires the country to be
present in the published country roster and the underlying data, while the
world, Europe-plus, and country outputs all derive automatically from the same
scope rules.
