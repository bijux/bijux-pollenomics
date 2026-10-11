# Why two camel accessions remain outside the animal chronology map

## Our decision

We treat two `SRP073444` BioSamples, `SAMN04631877` and `SAMN04631967`, as
unresolved physical specimen identities. Their [governed sample rows](../../data/adna/governance/source_library/projects/SRP073444/sample_master.json)
have distinct accessions but share the paper label `Palm143`. We refuse their
sample identity before evaluating whether their coordinates are mappable. A
nearby or missing coordinate cannot resolve whether they are independent
specimens.

## What we ran and observed

We replayed the source-sample chronology producer for the [world](../../docs/report/world/world_animal_sample_chronology_context.json),
[Europe-plus](../../docs/report/regions/europe-plus/europe-plus_animal_sample_chronology_context.json)
and [Nordic](../../docs/report/regions/nordic/nordic_animal_sample_chronology_context.json)
publication scopes. Each now has **7** `sample_identity_not_final` refusals and
**372** `source_coordinate_not_mappable` refusals, rather than the earlier
5/374 split. The total remains **1,475** source rows, **557** admitted display
nodes and **918** refused rows. World projects all 557 nodes; Europe-plus and
Nordic each project 14. The two Palm143 rows remain refused in every scope.

For each scope, the owning map producer changed only the chronology payload,
map contract, summary and bundle. The [source replay regression](../../packages/bijux-pollenomics/tests/unit/reporting/adna/sample_chronology_context/test_repository_data.py)
checks the exact source-derived payload and its contract through all three
published surfaces. We retained the existing 29 September 2026 bundle date
while replaying its source correction from that day; no new source record or
map feature was admitted.

## What the result permits

These layers are source-sample chronology context for display. We have not
inferred ecological events, independently measured vegetation, a pollen-core
chronology or a spatially precise ancient animal distribution from them. A
source owner must establish the physical identity of the shared `Palm143`
label before either accession could be reconsidered as a distinct specimen.
