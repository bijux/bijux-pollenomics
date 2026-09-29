---
title: Nordic forest-inventory reference access
audience: scientific reviewer
type: source access review
status: candidate; no measured reference admitted
owner: bijux-pollenomics-docs
last_reviewed: 2026-09-22
---

# Nordic forest-inventory reference access

National forest inventories measure trees and forest plots. Their plot values
could help test a **local, contemporary tree-vegetation estimand** after a
defensible pollen-to-plot spatial and temporal match. They do not directly
measure regional REVEALS cover, all vegetation, historical p1–p10 states, or
pollen counts. A public download or nearby point is not an admitted paired
reference.

| Country and primary source | What the inspected source establishes | Access and scientific decision for this study |
| --- | --- | --- |
| Sweden — [SLU NFI microdata](https://www.slu.se/en/about-slu/organisation/departments/forest-resource-management/miljoanalys/nfi/our-data/) and its [calibration guide](https://www.slu.se/globalassets/slu.se/om-slu/organisation/institutioner/skoglig-resurshushallning/riksskogstaxeringen/dokument/dokument/info-data-for-calibration.pdf) | Downloadable **2007–2025 temporary forest-plot subset** prepared for remote-sensing validation. The separately captured calibration guide states CC0 for its described subset and warns against geographic-area totals or means. | Candidate local tree-plot validation only. Existing [EMPD2–NFI review](empd2-nfi-review.md) has 16 proximity leads and **0 admitted pairs**; collection time, sample identity, basin support, compatible tree variables, taxa/PPE and leakage remain unresolved. Do not extrapolate this subset to Nordic regional cover. |
| Finland — [Luke VMI11 catalogue](https://opendata.luke.fi/dataset/doi-10-23729-f2a5333b-196e-46cc-aeaa-15f1ad161315) | Describes selected **2009–2013 temporary forest-plot** variables, excluding boundary plots; the subset is unsuitable for unbiased national forest-resource statistics. Its catalogue says **license not specified**. | Candidate only. Confirm the authoritative release's reuse terms and exact variables before acquiring outcomes or joining pollen; no admissible plot reference established. The local HTTP capture redirected to a Fairdata JavaScript page and did **not** preserve the catalogue text, so the linked Luke catalogue remains the source for these statements. |
| Norway — [NIBIO NFI description](https://www.nibio.no/en/about-eng/our-divisions/division-of-forest-and-forest-resources/national-forest-inventory) | Describes permanent plots visited on a five-year rotation and tree measurements within **250 m²** plots. | Candidate source family only. The inspected page provides no plot-level download, reuse license or site-level matching data; verify these with NIBIO before any acquisition or benchmark label. |
| Denmark — [University of Copenhagen NFI data policy](https://ign.ku.dk/samarbejde-med-ign/forskningsbaseret-raadgivning/skovovervaagning/Skovstatistik_datapolitik_20141027.pdf) | Its **October 2014** policy says individual plot/point data are never publicly released. Research use needs a project description and signed data agreement, with disclosure controls on results. | No public individual-plot cohort can be inferred from this policy. Confirm current policy and arrange an approved research extraction if this source is needed. Aggregates cannot silently become independent site labels. |

The exact-byte private-source capture is
`reference-sources/empd2-nfi/nfi/nordic-access.json` relative to the private
source store; see the [custody manifest](../../../report/validation/empd2-nfi-pairing/private-source-custody.json).
Its SHA-256 is `b0ab87f8016b561d84cdff16e74500df1b2f1e4013f4600a3d7e0ec0942d6825`,
produced by managed job `v3-20260922-nordic-nfi-access-capture001`
(exit 0; 3.300 seconds; unchanged read set). Captured SLU HTML SHA-256 is
`a0632bbff92e79c490a6bceb4fa21d69133d7fee7221c93e5b340de6c0b0b375`,
NIBIO HTML is `3ae1e97f5dec256f2a324832131b40063b4f5a8769c538366a329fffca425ec0`,
and the Danish PDF is `ab0a563eafe4755414b44d43b0262322a645983996c873777ff830fb937b9f5f`.
The Finnish redirect page SHA-256 is
`f789c22acaa5c5ca4a3095479c6084bb87ceadbf7f1372305955a12ee1f2a1d1`;
it is evidence of the redirect only. The policy's 2014 date and live catalogue
content require revalidation before a data-access decision.

**Admission denominator:** four country-level source leads inspected, zero
country-level measured reference cohorts admitted here, zero new pollen–plot
pairs admitted. Sweden's 16 proximity leads remain separate review items, not
16 labels. No vegetation or pollen held-out metric, selected model, or
four-country scientific acceptance follows from this access review.

The next eligible step is a reviewer-approved estimand and matching protocol:
observation year and footprint, independent pollen sample/core identity,
tree-variable units and taxonomic/PPE crosswalk, rights for each exact release,
grouped site and spatial-block leakage policy, and a predeclared minimum
independent-pair count and non-null thresholds. Only then may an admissible
cohort and untouched final labels be frozen.
