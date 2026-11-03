# OpenLand member intake decision

The private `openland/original/LandCover_OpenLand.zip` has SHA-256 `7ed602f3b480a995cd2e1ff6dc445e994442100b1f626a953185849305e2434b`. The [source-reconciliation audit](../source-reconciliation/README.md) verifies the original intake receipts and archives against the private source store. The [member ledger](members.csv) records its 51 ZIP directory entries and one role, rights posture, source route, and decision for each. The [report](report.json) binds the archive identity, this consumer's source, the existing OpenLand authority, the local LandClim receipt, and the [pinned upstream tree metadata](upstream-tree.json). No archive member was copied into this report.

The primary upstream source is [Behnaz Pirzamanbein's pinned repository](https://github.com/BehnazP/SpatioCompo_entireHolocene_EU/tree/894d44d58f66bb5c273491d98c3ec23a35e6a796), associated with [Githumbi et al. (2022)](https://doi.org/10.3389/fevo.2022.795794). The [source README](https://github.com/BehnazP/SpatioCompo_entireHolocene_EU/blob/894d44d58f66bb5c273491d98c3ec23a35e6a796/README.md) identifies the 25 CSV slices, their coniferous, broadleaved, and unforested/open modeled columns, attribution requirement, and CC BY-SA 4.0 data terms. The upstream [LICENSE](https://github.com/BehnazP/SpatioCompo_entireHolocene_EU/blob/894d44d58f66bb5c273491d98c3ec23a35e6a796/LICENSE) states GPL 3.0 for upstream code. The source archive's own local R script is not an upstream Git member; its rights are unresolved.

All 25 modeled CSV members and the PDF are byte identical to pinned upstream Git blobs. The CSVs route to the existing OpenLand source authority for **private modeled-source review only**. The PDF is a reference with unresolved member-specific rights. The archive also contains one local interpolated GeoPackage, one local script, one project configuration file, 14 private editor-state files, and eight directories. The GeoPackage has no pinned upstream member identity and is excluded. The ZIP directory and full archive hash were checked; the large GeoPackage and private editor-state contents were not extracted or executed.

The [primary paper](https://doi.org/10.3389/fevo.2022.795794) describes spatial statistical reconstructions based on pollen-derived REVEALS estimates and KK10 covariates. It cites PANGAEA `931856` for REVEALS inputs, while the local LandClim II authority identifies PANGAEA `937075`. [Primary DOI metadata](doi-lineage.md) now confirms that `931856` was obsoleted by `937075`; the former has restricted access and unknown licensing terms, while the successor is CC BY 4.0. This establishes dataset lineage, not exact row or input identity or transferred rights. The ledger therefore counts **zero independent vegetation benchmarks** and does not create a second LandClim authority. Raw pollen counts are absent from the admitted CSV role. Member-level public redistribution, map display, export, propagation, and scientific benchmark use remain unapproved.

Reproduce the decision with the development package environment and an explicitly supplied private archive:

```sh
python -m bijux_pollenomics_dev.source_completion.openland_intake \
  --repository . \
  --archive ../bijux-pollenomics-data/openland/original/LandCover_OpenLand.zip \
  --upstream-tree docs/report/source-relations/openland-intake/upstream-tree.json \
  --output artifacts/jobs/openland-intake/replay-check
```

The command requires an absent output directory and the exact pinned archive SHA-256. Its CSV and JSON can be compared byte for byte with this governed report. Default focused tests use only the tracked upstream metadata and synthetic member decisions. They do not require a private archive.

## Member coordinate, time and measurement dispositions

The following dispositions cover all 51 exact `member_path` entries in the
[member ledger](members.csv), grouped by its `semantic_role`. They supplement
the existing identity, rights, source-route and deduplication decisions.

| Ledger role | Entries | Coordinate, time and measurement disposition |
| --- | ---: | --- |
| `pollen_derived_modeled_cover_slice` | 25 | CRS is not established by this intake; `Lon`/`Lat` headers do not supply a CRS declaration. Time windows and the interpretation as modeled coniferous, broadleaved and open-cover proportions belong to the existing source authority described below. These are not sample ages, raw pollen counts or measured vegetation. |
| `source_documentation` | 1 | The PDF is a cited source reference. CRS, observation-age and measurement admission are inapplicable to its reference-only member role; it does not independently authenticate the CSVs' spatial or temporal support. |
| `local_interpolated_derivative` | 1 | The excluded GeoPackage's CRS, time support, measures and derivation remain unverified. Its payload was not inspected, and none are inferred from the container or local script. |
| `local_processing_script` | 1 | Reference-only code with unresolved local rights; no output CRS, calendar or measures are inferred from it or admitted by executing it. |
| `local_project_configuration` | 1 | Excluded project configuration; scientific CRS, age and measures are inapplicable to this role. |
| `local_private_project_state` | 14 | Excluded private editor state; scientific CRS, age and measures are inapplicable to this role. |
| `container` | 8 | Directory entries contain no member observations; CRS, age and measures are inapplicable. |

For the 25 modeled slices, the maintained
[OpenLand authority](../../../../packages/bijux-pollenomics/src/bijux_pollenomics/collection/sources/open_land/authority.py)
binds exact member names to `SOURCE_WINDOWS_BP` and the source column vocabulary.
Its first four label/window mappings are 50/0–100, 225/100–350, 550/350–700 and
1000/700–1200 BP; later windows follow that authority's explicit mapping.
Filename labels are not interval midpoints and do not authorize a ±250 BP
calendar reconstruction. These declared modeled windows do not establish
sample chronology, age uncertainty or exact historical input membership.

The pinned upstream repository and Githumbi et al. citation above remain the
source attribution for the modeled members. All ledger rights decisions,
zero public member admissions and zero independent vegetation benchmarks are
preserved. These are accounting dispositions, not new normalization, source-use
permission or scientific admission.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Author/source lineage, transformations and distinct modeled products; chronology and historical run admission remain separate.

**Supported claim.** The 51-entry OpenLand intake distinguishes exact upstream modeled CSVs from private/local derivative and project-state members.

**Unsupported claim.** Pollen-derived modeled cover is not independent vegetation truth; upstream data/code terms do not license a mixed private archive or local script.

**Actual verification performed.** Read all member roles, rights posture and pinned upstream identity in report.json/members.csv; no archive extraction, script execution or source recapture. A separate source-built execution used commit 5c120dcb67d31b50d9da6d7bf5efb41dcb0ddf87. The unchanged OpenLand producer and independent archive and copy-chain observer both exited 0, and the complete run exited 0. The member CSV matched exactly, with byte-checker exit 0. The report byte checker exited 2 because one source-attribution digest changed. The independent observer verified that this digest was the only report difference, preserved all scientific and rights values, and exited 0. The producer generated members.csv and report.json. The upstream-tree and DOI-lineage files were copies of retained declared inputs; they are not fresh HTTP retrievals or proof of original acquisition. The archive still contains 51 entries, including 25 modeled CSVs and 26 exact upstream blobs. There were 27 selected ZIP member reads and no GeoPackage or editor payload reads or LRA calls. An authored capsule retains 2,209 public members and all 66,430 ordered input identities. The payloads of 4,356 bytecodes, 59,886 runtime authorities and three private archive or intake authorities are omitted. The capsule does not establish fresh bytecode compilation, new native retention execution, public member rights, PANGAEA row equivalence, independent vegetation truth, ecological or human acceptance, or LRA admission. The original scientific ownership acceptance criteria have been restored verbatim. The SLU guide, HYDE country products, ABBO age-control report, Swedish cohort screen, OpenLand intake and Neotoma publication-attribution owners remain unresolved because their required original acquisition/copy custody or source-use authority has not been independently established. Genuine current executions, exact-byte checks and retained source captures remain scoped evidence; they do not discharge those original conditions. No numerical result, source chronology, permission, qualified human decision or LRA admission has changed.

**Remaining input or review.** Exact input-row relation, member-specific rights and scientific role decisions remain required before public use.

**Cause category.** Mixed archive rights and dependent modeled inputs.

**Consequence.** 25 CSVs route to private modeled-source review without a second LandClim authority.

**Precise next acceptance route.** Qualify each intended member and its derivation/use rights, then bind exact REVEALS inputs before any export or benchmark claim.

**Negative or refused result.** 0 public member admissions/independent vegetation benchmarks; local GeoPackage excluded; local script/PDF rights unresolved.

**Matched denominator.** 51 entries: 25 modeled slices, 1 PDF, 1 local derivative, 1 script, 1 configuration, 14 private-state files, 8 directories; 26 exact upstream blobs.

- [Retained qualification evidence: docs/report/source-relations/openland-intake/report.json](report.json) (SHA-256 `dbe01c0f556eca264e5523a895e19dfe15719ad99adc01f537c27082b6fa6243`).

- [Retained qualification evidence: docs/report/source-relations/openland-intake/members.csv](members.csv) (SHA-256 `9bd4f430895d3b0c76522e2f44e7e9d5a4613ece4cafbf5d632c3feafc42c9df`).

- [Retained qualification evidence: docs/report/source-relations/openland-intake/upstream-tree.json](upstream-tree.json) (SHA-256 `4bbd8f7a11b6fc01083dab358143f01b8f06192c8562592758e451436f75eae1`).

- [Retained qualification evidence: reports/science/source-lineage/openland-member-custody.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-lineage/openland-member-custody.json) (SHA-256 `dc437a7dee28a31b1ea341be1e76e0397d54ab0d93a0f6ad146bcbf99116365f`).

- [Retained qualification evidence: reports/science/source-cohorts/openland-original-acceptance.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/openland-original-acceptance.json) (SHA-256 `43d6b2a53cfa2837272faafc83040bf06cf66fca866f5172e7df3455db6401b5`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
