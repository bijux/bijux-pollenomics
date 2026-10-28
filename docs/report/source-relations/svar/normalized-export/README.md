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

**Supported claim.** The recovered SVAR export retains exact normalized bytes and a two-feature provider identity lead while preserving current zero-candidate refusal.

**Unsupported claim.** Live endpoint availability or matching count does not prove raw capture parity, supported acquisition rights, full identity equivalence or admitted lake ranking.

**Actual verification performed.** Read custody receipt, source population disagreement and provider/rights review; no WFS recapture or 261 MB geometry parsing.

**Remaining input or review.** Both full identity sets, versioned official source route, approved access/rights and qualified registry review remain required.

**Cause category.** Missing original capture and unresolved geometry rights/version identity.

**Consequence.** The 42 net count difference cannot be presented as an omitted lake list, and 99 derived features cannot restore old ranks.

**Precise next acceptance route.** Obtain an approved provider route and versioned layer identity comparison, reconcile the candidate subset, then conduct qualified review before ranking.

**Negative or refused result.** raw_wfs_capture_bound_to_export=false, source_population_reconciled=false, qualified_review_accepted=false; 0 ranked candidates.

**Matched denominator.** 40,565 normalized export lake claims versus 40,523 review source lakes; 99 derived features; 2 live feature identity checks; 0 admitted candidates; 42 is net count difference.

- [Retained qualification evidence: docs/report/source-relations/svar/normalized-export/report.json](report.json) (SHA-256 `ab082b7899ce947b7bef8c0f8c58fc030aed79b54ee14edf50c81bf5e18f9baf`).

- [Retained qualification evidence: docs/report/countries/sweden/sweden_lake_evidence_richness_v66.json](../../../countries/sweden/sweden_lake_evidence_richness_v66.json) (SHA-256 `52d63f4a264017606928d88b01b58ae00149bc64eaa070ec63a983133e59c596`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
