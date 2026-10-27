# Recovered SMHI SVAR normalized export

The [custody receipt](report.json) identifies a 261,041,034-byte normalized
Sweden lake GeoJSON export preserved in the private source store under
`svar/normalized-export-2026-09-08/`. The export SHA-256 is
`d9a1943d1a35e7ab6d48e06156fef625e7c62c8bc410cecf9d8f592ccb07dfd8`.
Its associated manifest and summary were copied byte-for-byte with it. The
receipt SHA-256 is
`ab082b7899ce947b7bef8c0f8c58fc030aed79b54ee14edf50c81bf5e18f9baf`.
This is a preserved normalized export, not a newly acquired provider capture.
The original raw WFS pages are not retained with it.

The export manifest and summary claim **40,565 lakes** on 8 September 2026.
The current governed candidate review instead cites **40,523** source lakes
and contains 99 derived features. The current
[lake report](../../../countries/sweden/sweden_lake_evidence_richness_v66.md)
admits **zero** candidates because its governing normalized registry is absent.
The source populations differ by 42; the receipt does not identify why. Neither
the recovered export nor the 99-feature subset is promoted to the governed
registry. Qualified source, identity and publication review remains outstanding.

## Measured normalized-file census

The separately [retained aggregate census](feature-census.json) records the
completed maintained streaming consumer and independent reader on source commit
`5c120dcb67d31b50d9da6d7bf5efb41dcb0ddf87`. Both returned native zero.
They measured 40,565 Feature objects: 37,516 Polygon and 3,049 MultiPolygon,
with no missing or null geometry. `record_id` and `sjoid` each have 40,565
distinct nonempty strings and no duplicates; `sj_uuid` and `sj_vatten_id`
each have 40,564 distinct nonempty strings and one unusable value.

All 99 candidate-subset rows have exactly one full-file match and typed
agreement for the seven declared identity/area/country/layer fields. This
does not equate subset Point geometries with source polygons or repeat the
nearest-pollen selection. The measured total agrees with the export claim
and differs by 42 from the historical 40,523 review; the identities and cause
of that difference remain unproven without its complete historical ID set.

The public witness contains aggregate counts and redacted join checks. Raw
properties, coordinates, native ID values and the private feature ledger are
not published. Geometry topology, effective basin area, provider units/CRS,
source dates as lake chronology, WFS parity, rights, qualified human review
and ranking remain unqualified. The current ranked-candidate count stays zero.
This authored evidence retention adds no new native execution claim.

## Provider identity and rights

On 1 October 2026, the still reachable [SMHI SVAR WFS endpoint](https://vattenwebb.smhi.se/svarwebb/svar.map?SERVICE=WFS&REQUEST=GetCapabilities)
advertised `ms:lakes` through WFS 2.0. Three bounded requests returned:

| Request | Observed response |
| --- | --- |
| [`GetCapabilities`](https://vattenwebb.smhi.se/svarwebb/svar.map?SERVICE=WFS&REQUEST=GetCapabilities) | `ms:lakes`; no usable layer metadata URL; empty fees and access constraints |
| [`GetFeature` hits](https://vattenwebb.smhi.se/svarwebb/svar.map?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=ms:lakes&RESULTTYPE=hits) | `numberMatched=40565`, `numberReturned=0` |
| [`GetFeature` first two](https://vattenwebb.smhi.se/svarwebb/svar.map?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=ms:lakes&COUNT=2) | `SJOID` values `736633-154404`, `752140-168146`; both feature rows say `VERSION=SVAR2016_3` |

The two returned `SJOID` and `SJ_UUID` pairs occur in the preserved export in
the same order: `736633-154404` / `648487F4-D6EA-4A94-B887-DB65C076AEBF`
and `752140-168146` / `A93F4FCE-DFEF-4AC8-8CBE-7B9F144BF009`. This is a
two-feature identity check, not a full comparison or proof that all 40,565
features are unchanged. The live count corroborates the export count; the
40,523 review has no retained full identity inventory, so these requests
cannot identify the 42-record difference or its cause. The `VERSION` values
identify the two returned rows, not a pinned revision of the live service.

The service capabilities leave `Fees` and `AccessConstraints` empty and point
their layer metadata URL to the nonpublic `HYPEMAPHOST` placeholder. SMHI's
[current hydrografi description](https://www.smhi.se/data/sjoar-och-vattendrag/hydrografi)
says lake and watercourse geometries depend on Lantmäteriet data that are not
open and therefore are supplied as a view service, not open WFS. SMHI's
[general open-data terms](https://www.smhi.se/data/om-smhis-data/villkor-for-anvandning)
grant Creative Commons Attribution 4.0 for its *open data* and direct users to
documented APIs. Neither those terms nor this old WFS response establishes that
the lake geometry layer is open or that this endpoint is a supported acquisition
route. The live endpoint is thus a source lead, not a rights-qualified new
registry. No provider geometry is published here.

Lantmäteriet's separate [Hydrografi Nedladdning licence, version 1.0,
22 April 2025](https://www.lantmateriet.se/globalassets/geodata/geodataprodukter/licensvillkor-hydrografi-nedladdning.pdf)
establishes a specific route for qualifying environmental research. Section
2.2 requires acceptance of the terms and an approved access application;
section 3.3 defines eligible noncommercial research whose results become
public and for which this product is needed. Sections 4.2–4.4 permit internal
processing and set conditions for redistribution and attribution. This route
does not establish that this project has been approved, that the old SMHI
`ms:lakes` export was licensed under these terms, or that the two products have
identical lake identities. The next source decision is an approved access
route and a versioned layer-to-layer identity comparison. The difference of
42 between the two reported lake counts is a net count difference; without
both full ID sets, it is not an omitted-lake list.

## Provider response and documented identities

A response from SMHI's hydrology service, supplied on **27 October 2026**,
identifies the older source as SVAR2016 and names SVAR2022 as the latest
version in that reply. The original message timestamp and message ID were
not supplied. This is a received, partially resolving response, rather than
an unanswered enquiry or an approval of the retained export. SMHI says older
lake versions are not readily available and offers further investigation
if the download dates can be supplied. No historical snapshot or full
replacement layer accompanies the response.

The linked [SVAR2016 documentation, Hydrologi 128](https://www.smhi.se/publikationer-fran-smhi/sok-publikationer/2021-04-15-arbete-med-svar-version-2016-svenskt-vattenarkiv-en-databas-vid-smhi)
is dated **27 November 2017** within the PDF; its website publication date
is a separate fact. Sections 5.1–5.1.2 and Appendix 6, printed pages 27–29,
document these database meanings:

| Documented object | Meaning and boundary |
| --- | --- |
| Lake `SJOID` | Older identifiers derive from RT90 outlet coordinates; new lake identifiers use SWEREF 99. Moving an outlet during correction retains the lake and outlet identities. |
| `SJ_T` lake table | `SJ_UUID` and `SJ_VattenID` describe the lake. |
| `vy_y` water surfaces | A lake can have several surfaces. This table has `VYID`, similarly named surface identifiers and a separate `EU_CD` waterbody identifier. |
| `SJ_AREAL_T` | `AREAL` is in km²; `DAT` records the area date. |

The report also specifies SWEREF 99 database storage. These definitions
do not authenticate the export response CRS, axis order, the WFS `AREA` or
`SJVattenID` field mappings, or a WA/EU identifier alias. The exact `_3`
revision, surface aggregation and split/merge rules remain unresolved.

The provider's [SVAR2022 report, Hydrologi 131](https://www.smhi.se/publikationer-fran-smhi/sok-publikationer/2024-05-21-svar-2022)
describes changed products, geometry and attributes. The reply says that
SVAR2022 is not connected to the lake directory and anticipates later
Vattenwebb availability; this expectation is not a verified release date.
Its indicated geometry coverage is waterbodies under the Water Framework
Directive, which cannot be assumed equivalent to the retained lake export.
The linked hydrography page's viewing-service restriction and general
open-data terms above therefore remain separate. Exact-layer permission
for analysis, derived publication and modified-geometry redistribution,
including third-party conditions and a supported acquisition route, is
still needed.

## Population dates and acquisition evidence

The retained records distinguish metadata dates from download evidence:

| Existing record | Recorded population and date | What the date establishes |
| --- | --- | --- |
| [Governed manifest](../../../../../data/svar/raw/svar_lake_registry_manifest.json) and [summary](../../../../../data/svar/normalized/svar_summary.json) | 40,565; `generated_on: 2026-06-22` | A metadata date, without original timed HTTP responses or complete request/page custody. |
| [Candidate review](../../../../../data/svar/review/lake_candidate_registry_review.json) | Source count 40,523; 99 review members; `generated_on: 2026-08-01` | A review declaration, not evidence of a second complete download or its acquisition date. |
| Preserved export manifest and summary in the existing source store | 40,565; `generated_on: 2026-09-08` | The metadata accompanying the exact normalized file identified above, without its original WFS pages. |
| Bounded provider observations recorded above | 1 October 2026; hits 40,565 and two returned features | The scope of those later observations, not the acquisition time or complete identity of either historical population. |

The manifests retain the service URL, type `lakes` and page size 250, but
do not recover the original full queries, filters, pagination responses or
download timestamps. No filesystem modification date is used as an
acquisition date. The measured 40,565-feature census and its 99 subset joins
remain reusable evidence; they do not supply the historical 40,523 IDs.
The next provider clarification needs this honest provenance inventory,
the `_3` and identity rules, exact-layer terms and a supported route with
comparable coverage. The net difference of 42 remains unexplained; zero
ranked candidates and all existing field decisions remain unchanged.

To replay the byte and refusal checks, supply the private source-store root and
write a disposable receipt under `artifacts/`, then compare the resulting JSON
with the governed receipt:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/source-relations/svar/normalized-export/verify.py \
  --repository . --source-root /path/to/bijux-pollenomics-data \
  --output artifacts/svar-normalized-export/replay
cmp docs/report/source-relations/svar/normalized-export/report.json \
  artifacts/svar-normalized-export/replay/report.json
```

The next admissible action is to recover the source capture or a new official
registry with version and rights, reconcile its lake identities with the
candidate subset, and obtain qualified review. Until that happens, the public
[Sweden lake page](../../../../public/nordic-atlas/sweden-lake-priorities/index.md)
must show the current zero-candidate refusal rather than old rank values.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-native/context/propagation evidence: source units and eligibility/refusal populations do not become pollen observations or ecological events.

**Supported claim.** The recovered SVAR export retains exact normalized bytes and a two-feature provider identity lead while preserving current zero-candidate refusal. A separate maintained streaming census and independent reader measure the retained normalized file's 40,565 features and exact seven-field matches for all 99 subset rows, without ranking admission.

**Unsupported claim.** Live endpoint availability or matching count does not prove raw capture parity, supported acquisition rights, full identity equivalence or admitted lake ranking.

**Actual verification performed.** Read custody receipt, source population disagreement and provider/rights review; no WFS recapture or 261 MB geometry parsing. The maintained source-built isolated-standard-library verifier and independent native source observer both returned zero on ada0128d4b96a0c0655e7b8c24ba81329f34a2cb. Complete source/refusal receipt is byte-identical to publication; all3507 original inputs remain explicit. Exact261041034BGeoJSON and two private metadata files were hashed, not geometrically parsed;40565 remains source metadata claim against40523review/99subset/zero ranks. The42difference and WFS/export linkage, rights and qualified source review remain unresolved. No new provider capture, ranking or native-retention outcome. Separately, the maintained streaming consumer and independent source reader on source commit `5c120dcb67d31b50d9da6d7bf5efb41dcb0ddf87` both returned native zero. They measured 40,565 Feature objects (37,516 Polygon and 3,049 MultiPolygon), no missing geometry, 40,565 distinct nonempty record_id and sjoid values, and 40,564 distinct nonempty sj_uuid and sj_vatten_id values with one unusable value each. All 99 subset rows have exactly one full match and typed agreement for all seven declared fields. The earlier hash-only operation remains distinct; no new WFS, model, ranking or metadata-retention native outcome is claimed.

**Remaining input or review.** The historical 40,523 review's complete identity set, a versioned official source route, approved access/rights, provider units/CRS and qualified registry review remain required. The current full normalized-file census and 99 typed subset joins do not supply those authorities.

**Cause category.** Missing original capture and unresolved geometry rights/version identity.

**Consequence.** The 42 net count difference cannot be presented as an omitted lake list, and 99 derived features cannot restore old ranks.

**Precise next acceptance route.** Obtain an approved versioned provider route and the historical review's full identity inventory; compare populations and provider geometry/units/CRS, then obtain qualified source/rights review before registry or ranking admission.

**Negative or refused result.** raw_wfs_capture_bound_to_export=false, source_population_reconciled=false, qualified_review_accepted=false; 0 ranked candidates.

**Matched denominator.** 40,565 normalized export lake claims versus 40,523 review source lakes; 99 derived features; 2 live feature identity checks; 0 admitted candidates; 42 is net count difference. Separately measured 40,565 normalized Feature objects: 37,516 Polygon plus 3,049 MultiPolygon; all 99 subset rows match one full feature across seven typed fields. Two native ID fields have 40,565 distinct nonempty values; two have 40,564 plus one unusable value each. These are descriptive source counts, not admitted lakes.

- [Retained qualification evidence: docs/report/source-relations/svar/normalized-export/report.json](report.json) (SHA-256 `ab082b7899ce947b7bef8c0f8c58fc030aed79b54ee14edf50c81bf5e18f9baf`).

- [Retained qualification evidence: docs/report/countries/sweden/sweden_lake_evidence_richness_v66.json](../../../countries/sweden/sweden_lake_evidence_richness_v66.json) (SHA-256 `52d63f4a264017606928d88b01b58ae00149bc64eaa070ec63a983133e59c596`).

- [Retained qualification evidence: reports/science/source-lineage/svar-normalized-source.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-lineage/svar-normalized-source.json) (SHA-256 `dd03a001e5d03e442b0805d7f09adf3e81fc3424e65d5bada651bd996522cbf9`).

- [Retained qualification evidence: docs/report/source-relations/svar/normalized-export/feature-census.json](feature-census.json) (SHA-256 `5ce50017af55e496ca391d34997ce5f182296f8e9db82ea20c118016d30ff0db`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
