# SEAD relational and Nordic map custody

The [custody report](report.json) revalidates the governed SEAD full-evidence
acquisition against its pinned admission and boundary authority. The source
validator recomputes all 86 declared parent-child joins from the captured table
payloads. Every join is complete, with no orphan child key, duplicate join key,
or unexplained row loss. Its 37,634 null foreign-key references remain explicit
source nulls; they are not counted as orphans or filled with invented parents.

The replay producer at
`packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/sead_public_custody.py`
joins the 2,069 captured assigned site IDs and UUIDs to the governed country
decisions, normalized GeoJSON at
`data/sead/normalized/nordic_environmental_sites.geojson`,
the matching CSV export, and [Nordic map traceability](../../../regions/nordic/nordic_point_traceability.json).
The normalized lineage file must bind both exports to the same admitted
acquisition. The [report map's GeoJSON](../../../regions/nordic/nordic_environmental_sites.geojson)
must match the normalized source byte for byte. For each site, the raw UUID,
CSV UUID, GeoJSON popup UUID, site ID, source
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


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-native/context/propagation evidence: source units and eligibility/refusal populations do not become pollen observations or ecological events.

**Supported claim.** The custody report preserves 86 relational joins and 2,069 assigned site UUID/country/source-to-map bindings for its retained source scope.

**Unsupported claim.** Complete foreign-key custody does not make source nulls known parents or archaeology context an admitted ecological event.

**Actual verification performed.** Read all join summaries and site/country exclusions, then inspected the actual current maintained custody replay: native exit 0 in 61.591 seconds, observed child RSS 1,121,730,560 bytes and 2,130 pinned inputs unchanged. Only the current Nordic traceability input hash changed; all 86 joins, 2,069 UUID/site bindings, 37,634 nulls, 126 exclusions and numerical/source-role fields are unchanged. This is relational source-to-map verification, with no new browser, model or scientific admission.

**Remaining input or review.** Qualified excluded-coordinate, chronology, taxonomy, event, propagation and rights decisions remain separate.

**Cause category.** Presentation and relational custody do not decide scientific meaning.

**Consequence.** 37,634 null foreign keys remain explicit nulls while 126 excluded country decisions remain outside publication.

**Precise next acceptance route.** Resolve source-specific meaning/age/use questions before any scientific admission and rerun custody on changed source/map bytes.

**Negative or refused result.** 0 orphan or unexplained-loss joins in the pinned review; source/scientific release refusals remain unchanged.

**Matched denominator.** 86 declared joins, 37,634 null references, 2,069 assigned sites; SE 1,925, DK 59, NO 45, FI 40; 103 review/23 unassigned excluded.

Qualified authored reader SHA-256: `b4f02181ab2bfe6927d57095de74da12d2d60b8be6137e9e3c0105fa1e654842`.

- [Retained qualification evidence: docs/report/source-relations/sead/public-custody/report.json](report.json) (SHA-256 `fa5257291cf4890691a90c437b717012f9366b7ba26c2cb43ce855a5e088615f`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
