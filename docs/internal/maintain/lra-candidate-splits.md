---
title: LRA candidate split guard
audience: maintainers
type: validation procedure
status: preparation only
owner: bijux-pollenomics-dev
---

# LRA candidate split guard

`bijux_pollenomics_dev.lra_validation.split_guard.build_candidate_split`
accepts **identity-only** records. Each row must have exactly `record_id`,
`site_id`, nullable `core_id` and `publication_id`, `alias_ids`, `country`,
`spatial_block_id`, `kind` (`pollen`, `vegetation` or `derived`) and
`dependency_ids`. Outcome values and extra fields are refused. The caller must
declare the complete cross-database alias and derived-product dependency graph;
an unknown dependency is refused rather than assumed independent.

An `alias_ids` value may name another row's record, site, core or publication
ID, or a source-qualified alias shared by at least two rows. A one-sided
reference is sufficient. An alias that resolves to unrelated identity groups
or occurs only once without a matching identity is refused. IDs must be
source-qualified before use so unrelated sources cannot collide by short label.

The guard links records sharing a site, core, publication or alias. It holds
the entire connected component out, optionally with every site in its
predeclared spatial block. A component that crosses spatial-block IDs is
refused for review. All train records are checked against the transitive
dependencies of the held-out records, including regional products.

For `withheld_pollen_prediction`, the split exposes **no** test pollen input.
For `local_pollen_available`, the caller must name one raw local pollen record
from the test group. It is exposed separately as an allowed test input, never
as a train record. The test vegetation record must be named explicitly for
the local-pollen vegetation target. The withheld-pollen target may instead
anchor on a pollen-only site, which has no measured vegetation score. The
deterministic result separates held-out pollen and vegetation record IDs and
lists train/test IDs, groups, block, target and an identity-only input hash. It carries
`candidate_unreviewed`, not benchmark approval.

For a file output, run
`python -m bijux_pollenomics_dev.lra_validation.split_guard PLAN.json`
through the managed job runner. The JSON plan has the exact keys `records`,
`test_record_id`, `target`, `local_pollen_record_id` (null when withheld),
`holdout_spatial_block` (Boolean), and an absolute `output_path` in an existing
directory. The command publishes the manifest once and refuses replacement.

This utility does not choose eligible reference rows, fold groups, block size,
spatial buffers, time support, taxon/PPE mappings or acceptance thresholds.
Final split manifests require the qualified reviewed reference and frozen
benchmark policy described by the v3 benchmark contract. No final-test labels
may be opened because this utility returned a manifest.
