# Sweden lake evidence richness

The lake-ranking surface is blocked and contains `0` admitted candidates.

- Availability status: `blocked`
- Refusal reason: `governing_svar_registry_missing`
- Governing surface: `data/svar/normalized/sweden_lake_registry.geojson`
- Candidate derivation: No SVAR lake candidates were admitted because the derived review subset exists without its governing normalized registry.

No derived review subset is promoted to a scientific ranking while its governing registry is unavailable.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Swedish observed pollen/modeled land use/archaeological context has separate provenance and no causal or ecological validation.

**Supported claim.** This reader correctly reports a blocked lake-ranking surface with zero admitted candidates because the governing normalizedSVARregistry is missing.

**Unsupported claim.** A derived review subset is not an authenticated governing lake population and cannot be promoted to ranking,scientific suitability or a sampling recommendation.

**Actual verification performed.** Read the machine availability/refusal fields and checked candidate_count 0,emptyassessments,derived_subset_admitted false and the named missing governing surface. No ranking or registry capture was run.

**Remaining input or review.** The exact governing normalizedSVARregistry with source identity,coverage and qualified review is missing; source/temporal context approval remains separate.

**Cause category.** Absent governing lake-registry authority.

**Consequence.** No admitted lake score or comparative evidence richness exists under the current authority contract; absence of a ranking is preserved.

**Precise next acceptance route.** Authenticate data/svar/normalized/sweden_lake_registry.geojson and its complete native population/custody,then rerun candidate derivation without substituting the derived subset.

**Negative or refused result.** availability_status blocked;refusal governing_svar_registry_missing;candidate_source svar_registry_authority_unavailable.

**Matched denominator.** 0 admitted candidates and 0 assessments across declared 10,20,30,40,50 km bands; source-context record counts are not candidate or independent measurement counts.

- [Retained qualification evidence: docs/report/countries/sweden/sweden_lake_evidence_richness_v66.json](sweden_lake_evidence_richness_v66.json) (SHA-256 `52d63f4a264017606928d88b01b58ae00149bc64eaa070ec63a983133e59c596`).

- [Canonical scientific account: reports/science/sweden-lake-trajectory.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/sweden-lake-trajectory.md).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
