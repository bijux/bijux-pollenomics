# SEAD relational and Nordic map custody

The [custody report](report.json) revalidates the governed SEAD full-evidence
acquisition against its pinned admission and boundary authority. The source
validator recomputes all 86 declared parent-child joins from the captured table
payloads. Every join is complete, with no orphan child key, duplicate join key,
or unexplained row loss. Its 37,634 null foreign-key references remain explicit
source nulls; they are not counted as orphans or filled with invented parents.

The [replay producer](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/sead_public_custody.py)
then joins the 2,069 captured assigned site IDs and UUIDs to the governed
country decisions, [Nordic site map input](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/data/sead/normalized/nordic_environmental_sites.geojson),
and [Nordic map traceability](../../../regions/nordic/nordic_point_traceability.json).
It requires the UUID popup value, site ID, source URL, country, coordinates,
and traceability title to match exactly for every site. The 103 country-review
and 23 unassigned decisions remain outside the published site set. The report
retains source file hashes, the 86-edge accountability ledger, and a digest of
all site/UUID/country bindings without duplicating the raw table payloads.

This is source and presentation custody. The captured acquisition's release
posture and the source taxonomy, chronology, propagation, and independent
vegetation admission questions remain separate. The result does not promote
archaeology context to a lake event.

## Reproduce

From the repository root, use a fresh output directory:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.sead_public_custody \
  --repository . \
  --output artifacts/jobs/sead-public-custody/reproduction
```
