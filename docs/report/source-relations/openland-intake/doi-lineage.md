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

**Actual verification performed.** Read the exact DOI-lineage response fields and intake role decision; no DOI lookup or numerical source join rerun. A separate source-built execution used commit 5c120dcb67d31b50d9da6d7bf5efb41dcb0ddf87. The unchanged OpenLand producer and independent archive and copy-chain observer both exited 0, and the complete run exited 0. The member CSV matched exactly, with byte-checker exit 0. The report byte checker exited 2 because one source-attribution digest changed. The independent observer verified that this digest was the only report difference, preserved all scientific and rights values, and exited 0. The producer generated members.csv and report.json. The upstream-tree and DOI-lineage files were copies of retained declared inputs; they are not fresh HTTP retrievals or proof of original acquisition. The archive still contains 51 entries, including 25 modeled CSVs and 26 exact upstream blobs. There were 27 selected ZIP member reads and no GeoPackage or editor payload reads or LRA calls. An authored capsule retains 2,209 public members and all 66,430 ordered input identities. The payloads of 4,356 bytecodes, 59,886 runtime authorities and three private archive or intake authorities are omitted. The capsule does not establish fresh bytecode compilation, new native retention execution, public member rights, PANGAEA row equivalence, independent vegetation truth, ecological or human acceptance, or LRA admission.

**Remaining input or review.** An input-level join and derivative-specific permission/scientific role review remain missing.

**Cause category.** Dataset lineage is narrower than version/rights equivalence.

**Consequence.** The older restricted record is not replaced silently by an openly licensed successor.

**Precise next acceptance route.** Obtain exact release/member correspondence and qualified derivative rights before changing private modeled-source status.

**Negative or refused result.** 931856 licensing unknown/access restricted; 937075 CC BY 4.0 does not supply independent vegetation truth.

**Matched denominator.** 2 DOI records/1 explicit supersession relation; 25 OpenLand CSV slices remain dependent modeled context; 0 recovered input-level joins.

- [Retained qualification evidence: docs/report/source-relations/openland-intake/doi-lineage.json](doi-lineage.json) (SHA-256 `52421cacb6bf4f0ec580e7f2d0f2665ab0e87a1184efff6b887247513e3afa27`).

- [Retained qualification evidence: docs/report/source-relations/openland-intake/report.json](report.json) (SHA-256 `dbe01c0f556eca264e5523a895e19dfe15719ad99adc01f537c27082b6fa6243`).

- [Retained qualification evidence: reports/science/source-lineage/openland-member-custody.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-lineage/openland-member-custody.json) (SHA-256 `dc437a7dee28a31b1ea341be1e76e0397d54ab0d93a0f6ad146bcbf99116365f`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
