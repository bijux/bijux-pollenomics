# Why we have not joined Bjäresjösjön pollen to nearby archaeology

We checked the user's Bjäresjösjön lake lead against the retained official lake
registry, the Neotoma–LandClim site identity review, SEAD record intervals and
the published Swedish land-use windows. We can identify the modern water body
and reproduce nearby **display context**. We cannot yet say that those records
describe the same historical pollen core or an independently observed land-use
event at that lake.

## The lake and core decision

The [source-bound screen](bjaresjo-context/report.json)
finds one SMHI SVAR lake, official water-surface name **Bjäresjö**, registry
ID `614958-137018`, representative point `55.459405° N, 13.751743° E`, and
current mapped area `0.022251 km²`. This is modern hydrographic identity. It
does not supply historical basin geometry or a coring location. The registry
lists nearby `neotoma-pollen:28871` and LandClim `BJARE` as proximity leads.

The [Neotoma–LandClim source ledger](../../docs/report/source-relations/neotoma/landclim-site-identity/site-comparison.csv)
places Neotoma site `28871` and the same-name `BJARE` sequence **1.02697 km**
apart. Its core identity is `not_established` and radius transfer is
`refused`. A name or nearby point cannot supply the missing physical-core,
age-model or historical-basin link. We therefore refused a core-linked
pollen–archaeology or LRA parameter join.

## The nearby SEAD context we could verify

Using the official lake representative point and unrounded WGS84 distances,
we found [371 distinct SEAD interval features](bjaresjo-context/nearby-sead.csv)
at 13 site identities within 20 km. Each row retains its source record ID,
site UUID, distance, numeric display endpoints and exact chronology claim ID.
The nearest source site, `4215`, is about **0.341 km** away. The pinned
[SEAD interval review](../../docs/report/source-relations/sead/interval-sets/README.md)
authenticates the normalized record layer, and the
[age-basis review](../../docs/report/source-relations/sead/chronology-claim-review/README.md)
assigns every selected claim the `chronology_display_only` role and refuses
event propagation. The capture's scientific release status is `refused`.
These are linked display intervals, not 371 independent archaeological
events, measured vegetation observations or a cleared source release.

We recomputed overlap with all 25 [modeled LandClim windows](../../docs/report/countries/sweden/sweden_land_use_synthesis_v66.json)
for this named target. The [window ledger](bjaresjo-context/window-overlap.csv)
matches the existing Swedish synthesis count on every window. The 350–700 BP
window overlaps **266 interval features from 11 SEAD sites** within 20 km;
the 0–100 BP window overlaps **zero**. A record interval can overlap several
modeled windows, and many features come from one site. We used interval
endpoints for a source display check only; this does not qualify historical
land use, a chronology for the pollen core, or an archaeological weight in a
lake ranking.

## Our decision and next evidence

We retained the spatial and nominal time screen, but set the ecological and
event join to **refused**. The unresolved physical-core identity, historical
basin and selected age model prevent a lake-specific LRA or pollen comparison.
The SEAD reviews separately withhold scientific chronology propagation and
the current capture release. The modeled LandClim grid is also a model output,
not independent vegetation truth. We have not changed a fieldwork rank or
interpreted cereal pollen, animal movement or human impact from these counts.

To reopen this decision, a source owner needs to bind the Neotoma core and
`BJARE` sequence (or identify a different physical core), its selected age
model and basin history, and permitted use. A qualified SEAD record/event
review must then identify a relevant source concept, age uncertainty and
analytical right before we define a weighting rule or compare it with pollen.
The open [research-needs register](../needed/README.md) retains that request.

We generated this screen with
`bijux_pollenomics_dev.source_completion.bjaresjo_context`. From the
repository root, replay into an absent destination under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.bjaresjo_context \
  --repository . --output artifacts/jobs/bjaresjo-context-replay
```

Compare its three output files byte for byte with the governed result directory.
The [machine report](bjaresjo-context/report.json)
pins every source SHA-256, the official lake and refused core decision, the
SEAD release posture and the exact output hashes.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Modern Bjäresjö lake identity and nearby dated SEAD display context are source bound.

**Unsupported claim.** A joined BJARE/Neotoma historical pollen core or measured land-use event at the lake.

**Actual verification performed.** Retained lake, core-proximity, SEAD and window consumer checks are reported; index did not rerun.

**Remaining input or review.** The modern lake and nearby SEAD intervals are identified, but Neotoma 28871 versus LandClim BJARE core identity, dated basin and independent event meaning are refused. Resolver: Lake/core and SEAD source owners plus qualified spatial/chronology reviewer Reopen when: One physical core and an independent permitted context observation are matched on site and time support.

**Cause category.** data|comparability|qualified review

**Consequence.** Keep archaeological counts as proximity context, not independent vegetation or causal history.

**Precise next acceptance route.** One physical core and an independent permitted context observation are matched on site and time support. Then update reports/needed/README.md.

**Negative or refused result.** Core-linked pollen and event propagation refused.

**Matched denominator.** 25 published windows and 371 SEAD display intervals from 13 sites within 20 km; Neotoma 28871 and BJARE 1.02697 km apart.

Retained evidence: [reports/science/bjaresjo-context/report.json](bjaresjo-context/report.json), [docs/report/source-relations/neotoma/landclim-site-identity/site-comparison.csv](../../docs/report/source-relations/neotoma/landclim-site-identity/site-comparison.csv).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-claim-semantic-sha256: 16048a08a12886f1827bf82bde9c589d048c7e9548e9d62407315b2687854475 -->
<!-- scientific-authored-source-sha256: a49c6d6530dd543ae4dc3c4ca0e4bcabe37af8e363b28bd6d18b1245723118d1 -->
<!-- scientific-verification-and-limits:end -->
