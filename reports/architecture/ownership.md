# How we own research reports

The [research library](../README.md) explains a question, our result and its limits. The
[claim index](../evidence-index.md) connects an interpretation to numeric evidence; the
[open evidence register](../needed/README.md) names missing sources and decisions.
`docs/report/` holds governed outputs from several producers. The [public science
pages](../../docs/public/pollenomics/science/index.md) and [PDF
briefings](../../presentation/README.md) are reader routes to rights-safe explanations.
Moving a governed output also means updating its producer, manifest, tests and incoming
citations.

The [navigation registry](../../docs/report/report_surface_registry.json) and
[narrative-quality review](../../docs/report/report_narrative_quality_review.json) are
secondary consumers of governed result bytes. Their path and content checks do not rerun
the scientific producers or measure reader comprehension.

## One path, one accountable role

The [ownership inventory](../../configs/ci/report-ownership.json) names every tracked
`docs/report/` path and exactly one role. The current inventory is the authority for counts
and path membership; a role declaration by itself is neither a fresh reproduction receipt
nor scientific approval.

| Role | Responsibility | Evidence needed beyond declaration |
| --- | --- | --- |
| Publisher partition | Country, region and foundation files assigned by the [publisher policy](../../configs/ci/reproducible-report-build.json) | Bound publisher partitions, assembly and exact final comparison |
| Generated domain owner | Named source, method or study product with an exact output map | [Configured command](../../configs/ci/report-owner-execution.json), closed code/data inputs, bounded execution and matching output in each required lane |
| Retained source | Authenticated original-R source bundle | Its separate certificate and exact source inventory; it is not a newly generated R result |
| Maintained code or editorial account | Checked-in Python/R producer source or Markdown reader account | Reviewed role and source kind, clean Git bytes and source-transport receipt before reducers read it |
| Maintained study configuration | The two reviewed authored pollen-study design JSON files | Exact independently admitted path set, finite duplicate-free JSON objects and clean Git bytes; scientific approval of the design remains separate |
| Unresolved | Missing producer, source, capture or execution custody | The named missing evidence; an output hash or role change cannot substitute for it |

The publisher consumes independently verified owner files to build portal and cross-tree
summaries, then removes those inputs from its own output. Maintained source accounts and the
certified original-R bundle enter the reducer as **source inputs**, each with distinct
identity checks. The [maintained-source
validator](../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild/maintained_sources.py)
admits the reviewed Python/R code, Markdown accounts and two authored study configurations.
The [age-interval design](../../docs/report/pollen-reconstruction/age-interval-sensitivity/config.json)
and [Swedish direct-pollen design](../../docs/report/pollen-reconstruction/swedish-direct-pollen/config.json)
declare fixed exploratory choices. Their transport does not approve those choices or turn
development scores into confirmatory evidence. Numeric products cannot become maintained
sources by a role-label change. The [original-R
validator](../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild/original_r_reference.py)
keeps that certificate separate. Final verification combines the independently owned outputs
and source receipts and compares both complete lanes with tracked `docs/report/`. The
remaining unresolved paths still prevent a whole-tree no-difference claim.

A retained isolated publisher membership check at Git product
`d535ca7f3bed0ead63e5f96e45658c435ed6613a` produced exactly the then-declared 709 publisher
paths, with path-set SHA-256
`e2670ba1efa03ec4dd8a54b2c013e494d7ef133922b0d6cdc0902f412e4b707b`. It established that
publisher membership at that source revision. It did not establish an installed release,
current complete-tree byte equality or two independent assembly lanes.

## Follow the domain evidence

The inventory records **who must account for a file**. The following domain accounts explain
what reproduced bytes mean and what remains open:

| Domain | Reader account and governed evidence | Boundary |
| --- | --- | --- |
| Pollen reconstruction and Nordic predictions | [Method correspondence](../science/method-correspondence.md), [observed-pollen synthesis](../science/pollen-prediction.md), [Nordic development](../../docs/report/regions/nordic/pollen-development/README.md) | Preparation, count-blind prediction, scoring and age support have distinct sources; development scores are not independent vegetation validation. |
| Historical LandClim and chronology | [Publication correspondence](../science/publication-correspondence.md), [LandClim input account](../../docs/report/publication-replay/landclim-study-inputs/README.md), [Solsø lineage](../../docs/report/countries/denmark/solsoe-source-lineage/README.md) | A core or window correspondence does not recover the historical R input chain, basin, PPE or admitted LRA sample. |
| Source relations and custody | [Source cohorts](../science/source-cohorts.md), [Neotoma](../../docs/report/source-relations/neotoma/README.md), [SEAD](../../docs/report/source-relations/sead/README.md) | Matching normalized or relational rows does not authenticate an original HTTP capture, permission or ecological event. |
| Context and vegetation | [Vegetation-reference decision](../science/vegetation-reference.md), [HYDE account](../science/hyde-cropland-source-account.md), [EMPD2–NFI pairing](../../docs/report/validation/empd2-nfi-pairing/README.md) | Modeled context and candidate pairings are distinct from measured vegetation accuracy. |
| Constructed method checks | [Synthetic validation](../../docs/report/synthetic-validation/README.md), [covariance](../../docs/report/method-certification/fixed-site-covariance/README.md), [joint draws](../../docs/report/method-certification/joint-site-draws/README.md) | Deterministic fixtures test code contracts; they do not supply empirical ecological accuracy. |

Detailed machine products, literal denominators and per-family refusal reasons remain with
those accounts and the paths they cite. The [source requests](../needed/source-requests.md)
and [scientific review register](../needed/scientific-review.md) identify the exact missing
source or qualified decision. A closed local producer route does not settle those decisions.

## Check a declaration and reproduce its own output

From the repository root, the stdlib ownership check reads tracked path membership, role
assignments, source paths and generated-owner dependency cycles without executing studies:

```sh
python -m bijux_pollenomics_dev.ci.report_rebuild.ownership --repository .
```

`--require-resolved` additionally refuses every unresolved path. Even a resolved inventory
does not replace source qualification, producer execution, independent owner receipts or
final two-lane comparison. The [execution
configuration](../../configs/ci/report-owner-execution.json) selects only maintained
modules, named source-file arguments, exact output maps and finite time bounds. It refuses a
substituted command, foreign module origin, self-fed output, missing or extra output,
changed tracked oracle, unsafe path or generated-owner cycle. Directory producers must
export their complete declared set; a single-file producer owns exactly one output. A
missing expected input becoming present reopens its source closure.

Some preparation writers carry upstream profiles into a larger retained stage before
exporting their smaller owned output set. For example, the [Abborrtjärnen age-input
preparer](../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/pollen_age_support/abborrtjarne.py)
keeps all five stage products, checks the two copied profiles against declared inputs, and
exports only its three owned files. Its stage and output checks are distinct from prediction
or scoring.

`make build-report-rebuild-owner` takes `REBUILD_LANE`, `REBUILD_OWNER_ID` and an absent
`REBUILD_EVIDENCE_ROOT`. Assembly takes `REBUILD_OWNER_IDS` and
`REBUILD_OWNER_ARTIFACTS_ROOT`; final verification additionally takes
`REBUILD_REFERENCE_OWNERS_ROOT` and `REBUILD_REPLAY_OWNERS_ROOT`. The [Make
routes](../../makes/pollenomics-verification.mk) and validated execution configuration bind
these to the same partition plan. The CI workflow derives its matrix and artifact namespaces
from that configuration; publisher artifacts remain separate. A subset proof covers only its
named files. Final assembly refuses an omitted owner rather than treating an unbuilt result
as reproduced.

Some owners require a qualified external source store. Set `REBUILD_SOURCE_ROOT` for those
selected owners in the scheduler, owner build, assembly and verifier. The [LegacyAge
descriptor](../../configs/ci/qualified-report-sources/legacyage.json), [depth-allocation
descriptor](../../configs/ci/qualified-report-sources/legacyage-depth-allocation.json) and
[Namibia publisher-table
descriptor](../../configs/ci/qualified-report-sources/namibia-modern-pollen-vegetation.json)
have different source and capture requirements; their validators refuse an absent or
substituted store. A source receipt is not the source bytes. Their
[ABBO/DALMUT](../../docs/report/source-relations/neotoma/legacyage-chronology/README.md),
[Solsø](../../docs/report/countries/denmark/solsoe-source-lineage/legacyage-chronology/README.md)
and [Namibia](../science/namibia-pollen-vegetation-paper.md) accounts state the resulting
scoped joins and exclusions.

The [root verifier](../verify.py) checks the reader pages and selected identities; the
[scientific verifier](../../docs/report/pollen-reconstruction/verify_report.py) checks its
own governed results. The full report-tree comparison is a separate acceptance decision.
Local `artifacts/` holds execution products; source identities and lasting results belong
with their domain owners before a run is retired. A byte match does not establish rights,
historical population completeness, scientific review or reader comprehension.
