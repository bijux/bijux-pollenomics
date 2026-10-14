# OpenLand REVEALS DOI lineage

The OpenLand paper cites [PANGAEA 931856](https://doi.org/10.1594/PANGAEA.931856)
for its REVEALS inputs. The [DataCite record for 931856](https://api.datacite.org/dois/10.1594%2FPANGAEA.931856)
explicitly identifies [PANGAEA 937075](https://doi.org/10.1594/PANGAEA.937075)
as its successor (`IsObsoletedBy`). Both records have the same dataset title.
The exact metadata fields and response SHA-256 values retrieved on 2026-09-29
are retained in [doi-lineage.json](doi-lineage.json).

| DOI | DataCite rights statement | Consequence for this intake |
| --- | --- | --- |
| 10.1594/PANGAEA.931856 | Access restricted; licensing terms unknown and author contact requested | Its citation does not grant access to or redistribution of the superseded dataset. |
| 10.1594/PANGAEA.937075 | CC BY 4.0 | The published successor has a distinct license and version identity. It does not license a separate OpenLand derivative or establish that its rows equal the older inputs. |

The supersession relation establishes **dataset lineage**, not byte or row
identity. The 25 OpenLand CSV members match the pinned OpenLand Git blobs, as
shown by the [member ledger](members.csv). No recovered input-level join binds
those members to a specific 931856 release row or to 937075's June 2021
archive. OpenLand's spatial estimates are derived from pollen-based REVEALS
inputs and remain unsuitable as independent vegetation truth. Keep the CSVs
under the existing private modeled-source review decision until their own
rights and scientific relationship are qualified.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Author/source lineage, transformations and distinct modeled products; chronology and historical run admission remain separate.

**Supported claim.** Two retained DataCite records establish 931856 IsObsoletedBy 937075 with distinct rights declarations.

**Unsupported claim.** DOI supersession does not establish byte/row equivalence or transfer successor licensing to an OpenLand derivative.

**Actual verification performed.** Read the exact DOI-lineage response fields and intake role decision; no DOI lookup or numerical source join rerun.

**Remaining input or review.** An input-level join and derivative-specific permission/scientific role review remain missing.

**Cause category.** Dataset lineage is narrower than version/rights equivalence.

**Consequence.** The older restricted record is not replaced silently by an openly licensed successor.

**Precise next acceptance route.** Obtain exact release/member correspondence and qualified derivative rights before changing private modeled-source status.

**Negative or refused result.** 931856 licensing unknown/access restricted; 937075 CC BY 4.0 does not supply independent vegetation truth.

**Matched denominator.** 2 DOI records/1 explicit supersession relation; 25 OpenLand CSV slices remain dependent modeled context; 0 recovered input-level joins.

Qualified authored reader SHA-256: `8225ab762f9431a05d1583818746d3b12e6402500a20321c398798a2f55c8a2a`.

- [Retained qualification evidence: docs/report/source-relations/openland-intake/doi-lineage.json](doi-lineage.json) (SHA-256 `52421cacb6bf4f0ec580e7f2d0f2665ab0e87a1184efff6b887247513e3afa27`).

- [Retained qualification evidence: docs/report/source-relations/openland-intake/report.json](report.json) (SHA-256 `6ede25d42a64a041139aab7a32ed6abfb3e2fb19ec0caf932647b7377455e52b`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md) (source SHA-256 `ffcac6cb938189c61113cf92453c4ee1c79fcd9a69305d4bf15fec387bbca898`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
