# Animal intake recovery review

- Public posture: `sample_recovery_still_partial_and_project_gaps_explicit`
- Tracked projects: `40`
- Ready for publication review: `11`
- Blocked projects: `23`
- Implausibly low recovery projects: `0`

## Sample Evidence Depth

The four mutually exclusive buckets partition `1468` species-normalized sample rows. The project source master has `1468` final rows; alignment is `aligned`. A site-only row has no normalized chronology; a site-and-chronology row has no coordinate text. The final bucket has coordinate text, not necessarily an approved mapped point.

- sample identity only: `0`
- sample with site: `789`
- sample with site and chronology: `356`
- sample with site chronology and coordinates: `323`

## Top Gap Projects

| Project | Species | Gap status | Minimum gap | Reasons |
| --- | --- | --- | ---: | --- |
| `PRJEB31621` | `Bos taurus` | `minimum_expected_floor_met` | `0` | `site_assignment_gap; chronology_gap` |
| `PRJEB75467` | `Bos taurus` | `minimum_expected_floor_met` | `0` | `site_assignment_gap; chronology_gap` |
| `PRJNA705960` | `Bos taurus` | `minimum_expected_floor_met` | `0` | `site_assignment_gap; chronology_gap; coordinate_precision_gap; missing_primary_paper_linkage` |
| `SRP073444` | `Camelus dromedarius` | `minimum_expected_floor_met` | `0` | `chronology_gap` |
| `SRS1407451` | `Canis lupus familiaris` | `recovered_to_exact_expected_count` | `0` | `site_assignment_gap; chronology_gap; coordinate_precision_gap` |
| `PRJEB43564` | `Equus asinus` | `extractable_sources_but_no_governed_samples` | `0` | `missing_primary_paper_linkage` |
| `PRJEB50952` | `Equus asinus` | `extractable_sources_but_no_governed_samples` | `0` | `missing_primary_paper_linkage` |
| `PRJEB52590` | `Equus asinus` | `extractable_sources_but_no_governed_samples` | `0` | `missing_primary_paper_linkage` |
| `PRJEB52849` | `Equus asinus` | `extractable_sources_but_no_governed_samples` | `0` | `coordinate_precision_gap; missing_primary_paper_linkage` |
| `PRJEB10854` | `Equus caballus` | `extractable_sources_but_no_governed_samples` | `0` | `missing_primary_paper_linkage` |
| `PRJEB19970` | `Equus caballus` | `minimum_expected_floor_met` | `0` | `site_assignment_gap; chronology_gap` |
| `PRJEB31613` | `Equus caballus` | `minimum_expected_floor_met` | `0` | `chronology_gap` |
| `PRJEB56293` | `Equus caballus` | `extractable_sources_but_no_governed_samples` | `0` | `missing_primary_paper_linkage` |
| `PRJEB7537` | `Equus caballus` | `extractable_sources_but_no_governed_samples` | `0` | `missing_primary_paper_linkage` |
| `PRJEB81815` | `Felis catus` | `minimum_expected_floor_met` | `0` | `site_assignment_gap; chronology_gap` |
| `PRJEB36540` | `Ovis aries` | `minimum_expected_floor_met` | `0` | `chronology_gap` |
| `PRJEB41594` | `Ovis aries` | `minimum_expected_floor_met` | `0` | `chronology_gap` |
| `PRJEB61808` | `Ovis aries` | `extractable_sources_but_no_governed_samples` | `0` | `missing_primary_paper_linkage` |
| `PRJEB69690` | `Ovis aries` | `extractable_sources_but_no_governed_samples` | `0` | `missing_primary_paper_linkage` |
| `PRJEB81145` | `Ovis aries` | `extractable_sources_but_no_governed_samples` | `0` | `missing_primary_paper_linkage` |

## Direct Links

- project_recovery_stage_review: `data/adna/governance/source_library/project_recovery_stage_review.json`
- project_expected_sample_yield_review: `data/adna/governance/source_library/project_expected_sample_yield_review.json`
- paper_expected_sample_yield_review: `data/adna/governance/source_library/paper_expected_sample_yield_review.json`
- species_project_deficit_ledger: `data/adna/governance/source_library/species_project_deficit_ledger.json`
- manual_curation_worklist: `data/adna/governance/source_library/manual_curation_worklist.json`
- source_recovery_progress: `data/adna/governance/source_library/source_recovery_progress.json`
- missing_source_queue: `data/adna/governance/source_library/missing_source_queue.json`
- source_recovery_release_guard: `data/adna/governance/source_library/source_recovery_release_guard.json`


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Actual normalized animal entity/map populations and distinct chronology/event acceptance boundaries.

**Supported claim.** The intake account separates sample evidence depth from project recovery and preserves incomplete source capture/site/chronology work.

**Unsupported claim.** Coordinate text or a minimum expected sample floor is not an admitted mapped point, complete paper recovery or publication approval.

**Actual verification performed.** Read the project/gap account and four mutually exclusive evidence-depth buckets; reconciled 1468 species-normalized samples with the source master. No extraction or source download was run.

**Remaining input or review.** Source paper linkage, site/chronology evidence and coordinate precision require native project/sample resolution; ready for publication review remains a request for review.

**Cause category.** Partial source intake and evidence-depth recovery.

**Consequence.** A project can meet its sample floor while remaining unpublishable because chronology or locality evidence is weak.

**Precise next acceptance route.** Resolve the named project gaps from authentic supplementary/native records, retain exact sample identities, and rerun source recovery and publication guards without promoting coordinate text alone.

**Negative or refused result.** 23 projects remain blocked; PRJEB31613 retains a chronology gap despite minimum floor met. Zero implausibly-low-recovery flags does not mean zero source gaps.

**Matched denominator.** 40 tracked projects: 11 ready for publication review and 23 blocked are named statuses, not an asserted exhaustive two-way partition.1468 samples=0 identity-only+789 site-only+356 site/chronology+323 with coordinate text.

- [Retained qualification evidence: docs/report/animal_intake_recovery_review.json](animal_intake_recovery_review.json) (SHA-256 `b18e3340a62396e03a13a2232ec984160569706d69c6228237ff713aacf99db0`).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md).

- [Canonical scientific account: reports/science/animal-sample-chronology.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-sample-chronology.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
