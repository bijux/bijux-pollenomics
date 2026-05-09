---
title: Future-Country Onboarding Playbook
audience: maintainer
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-05-09
---

# Future-Country Onboarding Playbook

Adding a future country such as `Germany` must be operationally boring. If it
still requires renderer surgery, ad hoc path additions, or special-case prose,
the repository has failed its own geography model.

## The Governing Rule

Country publication is a narrower view of one broader product. The work is
therefore four contracts at once, not one loose checkbox.

## Code Contract

- admit the country through the published country roster
- let `build_published_geography_plan()` derive the world, region, and country lineage
- keep output ownership under `docs/report/countries/<country-slug>/`
- do not add scope-specific renderer branches just because a new country exists

## Data Contract

- confirm that animal, human, and contextual rows resolve to the country through governed political-entity logic
- keep world as the governing parent surface and treat the country as a filtered descendant
- pass subset validation so the new country bundle does not drift outside its parent regional or world evidence surface

## Documentation Contract

- keep the report portal and data handbook describing one world-to-country product model
- update geography explanations only where the broader model materially changes
- do not create a second country-specific mini-handbook just to explain routine onboarding

## Test Contract

- keep publication geography tests proving world, regional, and country lineage
- keep repository-contract tests requiring the onboarding contract and subset validation outputs
- keep docs-breadth and report-portal tests proving that the broader explanation still survives after the new country arrives

## Practical Reading Order

1. [country onboarding contract](../../../report/publication_country_onboarding_contract.md)
2. [publication geography registry](../../../report/publication_geography_registry.md)
3. [publication geography subset validation](../../../report/publication_geography_subset_validation.md)
4. [repository extension review](../../../report/repository_extension_review.md)

If those surfaces still look coherent after a new country lands, the onboarding
work was probably done correctly.
