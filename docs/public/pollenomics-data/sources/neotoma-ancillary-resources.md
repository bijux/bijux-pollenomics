---
title: Neotoma Ancillary Source Resources
audience: developer
type: reference
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-11-15
---

# Neotoma Ancillary Source Resources

Use `data/neotoma/ancillary-resources/` with the separate
[native source archive](neotoma-source-resources.md). These products preserve
endpoint responses and their source relationships. Source-format qualification
does not admit a reconstruction input or establish vegetation accuracy.

The published facet census covers eight declared endpoints for each of the
1,258 resources in the retained discovery population: `chronologies`, `contacts`,
`doi`, `lithology`, `projects`, `publications`, `sites` and `taxa`. Its 10,064 slots
include 9,824 newly received entities, eight retained entities and 232 protected
slots with no request. Empty, unsupported and refused results stay in their
original denominators. This is completion of that bounded endpoint census,
not geographic or global Neotoma completeness.

## Resolve Immutable Dependencies

| Directory under `data/neotoma/ancillary-resources/` | Independent manifest SHA-256 |
| --- | --- |
| `context/` | `6c237ad7b262afe495434ca98430b80b356f444fdc3506e7897f24936b747d46` |
| `capsules/4dce35d83202e4c8a9f04783056723e2fa2b7c1b88c9eaed42154a9b8c72fd0a/` | `4dce35d83202e4c8a9f04783056723e2fa2b7c1b88c9eaed42154a9b8c72fd0a` |
| `capsules/e5afd23fed399ab1d0ae5d8970d2cf36e4240fb9c0c083a64df220d11ffcd1aa/` | `e5afd23fed399ab1d0ae5d8970d2cf36e4240fb9c0c083a64df220d11ffcd1aa` |
| `capsules/7a7b2627d91d24b0bc9eaaaa8a8afb35d00277ad88dea36e8f0f86115bf318e3/` | `7a7b2627d91d24b0bc9eaaaa8a8afb35d00277ad88dea36e8f0f86115bf318e3` |
| `capsules/2a4f894bbedcd297f9e8c529fcec90b09481ffb8662c1d78deb22e3cf1747c8d/` | `2a4f894bbedcd297f9e8c529fcec90b09481ffb8662c1d78deb22e3cf1747c8d` |
| `linked-evidence/76fbc45ac0613ef1b3df21d9f56c3b629c028a361e6b515bc226689bbc5fb42f/` | `76fbc45ac0613ef1b3df21d9f56c3b629c028a361e6b515bc226689bbc5fb42f` |
| `unit-metadata/bde7f113db4f43716ec678a885b02ddb0a6a3af1ff4b4a1f6f8c66b213d654e9/` | `bde7f113db4f43716ec678a885b02ddb0a6a3af1ff4b4a1f6f8c66b213d654e9` |
| `reference-tables/69176cd69e97efb1df19065eaafa585fb9dd87ab5c53e453555e6a999c68bdf9/` | `69176cd69e97efb1df19065eaafa585fb9dd87ab5c53e453555e6a999c68bdf9` |

The linked-evidence manifest is named `evidence-manifest.json`; the other root
manifests are named `manifest.json`. Keep independent expected digests rather
than trusting a digest read from the product being checked. Capsule resolvers
map manifest digests to exact directories. Linked-evidence resolvers are
separate explicit dependencies; readers do not guess sibling locations.

The shared context binds the native archive and the original and current
rosters. Capsules retain original captures, including their recorded source
epochs. Historical captures without contemporaneous parent-scope attestations
remain explicitly historical; current metadata cannot reconstruct a missing
pre-request attestation.

## Choose A Reader By Its Integrity Scope

The API owners are under
`bijux_pollenomics.collection.sources.neotoma.ancillary_store`.

| Need | API owner and entry point | Entity bodies read |
| --- | --- | --- |
| Capsule metadata | `capsule.read_neotoma_ancillary_capsule_inventory` | None |
| Full capsule verification | `capsule.load_neotoma_ancillary_capsule` | All owned entities, subject to exposure restrictions |
| Current joined metadata | `federation.load_neotoma_ancillary_federation` | None |
| One facet HTTP entity | `selection.read_neotoma_ancillary_facet_entity` | The selected entity |
| One qualified facet | `selection.read_neotoma_ancillary_facet` | The selected entity, parsed from the authenticated buffer |
| One linked HTTP entity | `selection.read_neotoma_ancillary_linked_entity` | The selected entity and its selected native source witness |
| One qualified linked record | `selection.read_neotoma_ancillary_linked` | The same authenticated buffers as the linked entity reader |
| Unit metadata | `unit_metadata.read_neotoma_unit_metadata_inventory` | None |
| Selected unit | `unit_metadata.read_neotoma_unit_metadata` | One selected unit body |
| Reference metadata | `reference_tables.read_neotoma_reference_archive_inventory` | None |
| Selected reference table | `reference_tables.read_neotoma_reference_archive_table` | One complete selected table body |

Selected facet and linked reads require exact observation identities. Linked
reads additionally require the precise occurrence identity. The source witness
must actually contain that native target at the recorded JSON pointer. A
rehashed index or plausible label cannot supply the missing relationship.

Every recorded root owner is checked before deduplication. Current known
protected principal-investigator dependencies restrict contact access, including
dependencies outside an older capture's recorded roots. A shared contact does
not reclassify another dataset. Whole-unit and site dependencies retain their
own stronger exposure obligations. Protected source bodies remain inaccessible
through typed and forensic readers alike.

Metadata inventory authenticates declarations, source controls and applicable
current parent metadata. It does not authenticate every declared entity hash
against the body or certify a body-derived source profile. Use an explicit full
replay when that stronger claim is needed. Selected operations do not read
unselected numerical bodies.

## Preserve Missing And Partial Source Evidence

The unit archive contains eight speleothem collection units; it is not an
inventory of every Nordic collection unit. Native field values and explicit
unit tokens remain source metadata, not an approved basin radius or chronology.

The reference archive contains a complete `variableunits` response with 244
native identifiers and an incomplete 2 MiB `geopoliticalunits` prefix. The latter
is available for forensic inspection and refused by the typed table reader. It
does not establish a country dictionary or an absent country.

The linked-evidence state retains 105,628 source-proof occurrences for 2,738
direct contact, publication and taxon targets, including explicitly requested
source-reported higher taxa. That state establishes source links; it does not
mean every global detail entity or every transitive ancestor was collected.

Publication detail can report a singleton all-null dataset-association
placeholder. Preserve it as unavailable association metadata. An identified
association can have an unknown `primary` flag. Neither case changes a native
identifier to zero or changes unknown primary status to false. Successful empty
detail responses likewise do not certify source absence.

For LRA, bind counts, taxonomy, pollen denominator, selected chronology, dated
basin geometry, applicable PPE and fall speeds, uncertainty and permitted use
separately. Downloaded source context cannot supply a missing qualified decision.
