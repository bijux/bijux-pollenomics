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

Retained Neotoma metadata supplies a more specific provenance lead. Dataset
`53999` (EPD E# 2789) at site `28871` belongs to collection unit `39240`, whose
provider fields name **C3 core**, handle `BJARE`, and a central-lake location
at 1.7 m water depth. Its GPS fields are null: the Neotoma point above is
**site metadata**; measured C3 GPS is not supplied. The dataset note records a 2017
Landclim Project contribution by Gaillard-Lemdahl. These fields are retained
in `data/neotoma/relational/surfaces/{datasets,collection_units,sites}/part-00001.json`;
the retained publication response identifies primary publication `17362`.

The [paper by Gaillard et al. (1991), printed page 108](https://page-one.springer.com/pdf/preview/10.1007/978-94-011-3592-4_14)
independently identifies central core C3 as the pollen and multiproxy sequence,
and distinguishes C3 and C4 for upper-metre lead-210 dating. Its published **site** coordinates,
55°27′ N, 13°45′ E, convert exactly to LandClim metadata row 974's
55.45° N, 13.75° E. This agreement is a source-point provenance clue; it does
not establish coordinate origin, datum, or a correction to either point.
These metadata and preview pages do not establish that the selected LandClim
samples and chronology are precisely the Neotoma C3 sequence. The **1.02697 km**
discrepancy and radius-transfer refusal remain.

The same page describes a roughly circular lake, maximum diameter 200 m,
area about 2 ha and maximum depth 1.7 m. It reports peat accumulation from
9700 BP until lake formation around 2700 BP, then about 4 m of lake sediment;
these are the paper's BP labels, without calibration or epoch conversion here.
It places outlet canalization between 1812 and 1888, piped drainage from 1970,
and catchment reduction from about 25 to 15 ha between 1809 and 1915.
These published changes make static basin transfer conditional. They do not
supply a dated basin outline, time-varying radius, full chronology or current
field conditions; 1991 is the publication year, not a measurement date.

The private two-page publisher preview was captured once with HTTP 200 and
complete body on 26 October 2026: 463,767 bytes, SHA-256
`ed9dcf75889735a3da4739d0d071fdcd0dd435be128fc3093fd4fcdccac12acb`.
The PDF and capture manifest are retained under the canonical private-source
locator `reference-sources/bjaresjo/springer-978-94-011-3592-4-14-preview/`.
Printed page 108 was checked against its rendered source image. This factual
citation does not redistribute the figure or establish an open licence.

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
The open research-needs register retains that request.

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

**Precise next acceptance route.** One physical core and an independent permitted context observation are matched on site and time support. Record the accepted evidence in this scientific account.

**Negative or refused result.** Core-linked pollen and event propagation refused.

**Matched denominator.** 25 published windows and 371 SEAD display intervals from 13 sites within 20 km; Neotoma 28871 and BJARE 1.02697 km apart.

Retained evidence: [reports/science/bjaresjo-context/report.json](bjaresjo-context/report.json), [docs/report/source-relations/neotoma/landclim-site-identity/site-comparison.csv](../../docs/report/source-relations/neotoma/landclim-site-identity/site-comparison.csv).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
