# Country Onboarding Contract

Adding a new country should be mostly a matter of data presence and publication
configuration. It should not require one-off renderer surgery, file-tree churn,
or custom scope code.

## Required Surfaces

- `published country roster entry`
- `world geography bundle`
- `Europe-plus geography bundle when applicable`
- `country bundle under docs/report/countries/<country-slug>/`
- `subset validation row proving world -> region -> country lineage`

## Current Configuration Points

- Published country roster: `packages/bijux-pollenomics/src/bijux_pollenomics/config.py`
- Geography scope plan: `packages/bijux-pollenomics/src/bijux_pollenomics/reporting/geography.py`
- Country bundle generation: `packages/bijux-pollenomics/src/bijux_pollenomics/reporting/service.py`

## Example

The contract is satisfied when adding `Germany` only requires the country to be
present in the published country roster and the underlying data, while the
world, Europe-plus, and country outputs all derive automatically from the same
scope rules.
