# SEAD relational and Nordic map custody

The [custody report](report.json) revalidates the governed SEAD full-evidence
acquisition against its pinned admission and boundary authority. The source
validator recomputes all 86 declared parent-child joins from the captured table
payloads. Every join is complete, with no orphan child key, duplicate join key,
or unexplained row loss. Its 37,634 null foreign-key references remain explicit
source nulls; they are not counted as orphans or filled with invented parents.

The [replay producer](../../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/sead_public_custody.py)
joins the 2,069 captured assigned site IDs and UUIDs to the governed country
decisions, [normalized GeoJSON](../../../../../data/sead/normalized/nordic_environmental_sites.geojson),
the matching CSV export, and [Nordic map traceability](../../../regions/nordic/nordic_point_traceability.json).
The normalized lineage file must bind both exports to the same admitted
acquisition. The report map's GeoJSON must match the normalized source byte for
byte. For each site, the raw UUID, CSV UUID, GeoJSON popup UUID, site ID, source
URL, country and coordinates must agree. CSV coordinates follow the export's
six-decimal rendering. The 103 country-review and 23 unassigned decisions
remain outside the published site set. The report retains source file hashes,
the 86-edge accountability ledger, and a digest of all site/UUID/country
bindings without duplicating the raw table payloads.

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
