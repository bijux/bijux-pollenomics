---
title: Neotoma Ancillary Source Resources
audience: developer
type: reference
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-11-17
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
| `country-authority/076f80f077ae128ea2d9ec548db8947c00e162725cafebbe05668fe065266ef8/` | `076f80f077ae128ea2d9ec548db8947c00e162725cafebbe05668fe065266ef8` |
| `context/` | `6c237ad7b262afe495434ca98430b80b356f444fdc3506e7897f24936b747d46` |
| `capsules/4dce35d83202e4c8a9f04783056723e2fa2b7c1b88c9eaed42154a9b8c72fd0a/` | `4dce35d83202e4c8a9f04783056723e2fa2b7c1b88c9eaed42154a9b8c72fd0a` |
| `capsules/e5afd23fed399ab1d0ae5d8970d2cf36e4240fb9c0c083a64df220d11ffcd1aa/` | `e5afd23fed399ab1d0ae5d8970d2cf36e4240fb9c0c083a64df220d11ffcd1aa` |
| `capsules/7a7b2627d91d24b0bc9eaaaa8a8afb35d00277ad88dea36e8f0f86115bf318e3/` | `7a7b2627d91d24b0bc9eaaaa8a8afb35d00277ad88dea36e8f0f86115bf318e3` |
| `capsules/2a4f894bbedcd297f9e8c529fcec90b09481ffb8662c1d78deb22e3cf1747c8d/` | `2a4f894bbedcd297f9e8c529fcec90b09481ffb8662c1d78deb22e3cf1747c8d` |
| `capsules/5492d1b8c9e2e70455a149ec3314c4becd76f01821a21324999a543ce9ff9a52/` | `5492d1b8c9e2e70455a149ec3314c4becd76f01821a21324999a543ce9ff9a52` |
| `linked-evidence/76fbc45ac0613ef1b3df21d9f56c3b629c028a361e6b515bc226689bbc5fb42f/` | `76fbc45ac0613ef1b3df21d9f56c3b629c028a361e6b515bc226689bbc5fb42f` |
| `taxon-ancestry/84a831c05c7d018392293747925a4229faf4be935a1552ef6bdbf4587d1d0662/` | `84a831c05c7d018392293747925a4229faf4be935a1552ef6bdbf4587d1d0662` |
| `unit-metadata/bde7f113db4f43716ec678a885b02ddb0a6a3af1ff4b4a1f6f8c66b213d654e9/` | `bde7f113db4f43716ec678a885b02ddb0a6a3af1ff4b4a1f6f8c66b213d654e9` |
| `reference-tables/69176cd69e97efb1df19065eaafa585fb9dd87ab5c53e453555e6a999c68bdf9/` | `69176cd69e97efb1df19065eaafa585fb9dd87ab5c53e453555e6a999c68bdf9` |

The linked-evidence manifest is named `evidence-manifest.json`; the country
authority capture uses `capture-manifest.json`. The other root manifests are named
`manifest.json`. Keep independent expected digests rather
than trusting a digest read from the product being checked. Capsule resolvers
map manifest digests to exact directories. Linked-evidence resolvers are
separate explicit dependencies; readers do not guess sibling locations.

The shared context binds the native archive and the original and current
rosters. Capsules retain original captures, including their recorded source
epochs. Historical captures without contemporaneous parent-scope attestations
remain explicitly historical; current metadata cannot reconstruct a missing
pre-request attestation.

The `5492d1b8…` capsule retains 24 direct linked-resource captures and 2,732
source-entry occurrences in 5,514 files (34,530,932 bytes). Its maintained
publication and full replay completed on 16 November 2026, followed by an
independent check of every published member's digest and byte count. Its index
preserves individually timed responses, original acquisition outcomes and
source-proof references; it asserts no transactional provider snapshot or
scientific admission. It copies no native pollen/count response bodies.

Use this capsule together with the four earlier capsules above for the existing
ancestry baseline's captured direct evidence and predecessor facets. Native
archive, context and linked-evidence bindings remain separate independently
pinned inputs. These retained responses do not collect the 195 unresolved
ancestry leads below.

## Country Reference Metadata

The country-authority capture retains four exact-name, rank-1 country responses:
Denmark (`1061`), Finland (`1411`), Norway (`3307`) and Sweden (`5392`). Each source
record reports parent `0`. These are reference metadata, separately qualified
from the unchanged HTTP capture outcomes. They do not establish a complete
geopolitical dictionary, interpret territorial geometry or assign countries to
pollen records. The earlier truncated global dictionary is not a complete
country authority.

Use the maintained country-authority reader with the independent manifest pin:

```python
from pathlib import Path
from bijux_pollenomics.collection.sources.neotoma.capture.country_authority import (
    qualify_neotoma_country_authority,
    read_neotoma_country_authority_body,
    replay_neotoma_country_authority,
)

pin = "076f80f077ae128ea2d9ec548db8947c00e162725cafebbe05668fe065266ef8"
directory = Path("data/neotoma/ancillary-resources/country-authority") / pin
capture = replay_neotoma_country_authority(directory, expected_manifest_sha256=pin)
qualification = qualify_neotoma_country_authority(directory, expected_manifest_sha256=pin)
denmark = read_neotoma_country_authority_body(
    directory, expected_manifest_sha256=pin, country="Denmark"
)
```

The ten capture files preserve their original bytes. The
[qualification packet](https://github.com/bijux/bijux-pollenomics/blob/d461e34b80bfca71f1f4b7d16e4db228aeed0bd9/reports/science/source-cohorts/neotoma-country-authority-qualification.json)
records the maintained reader revision and country identities; it makes
no new provider request or scientific-admission claim.

## Dataset-Linked Environment Records

The dataset-filtered environment queries cover all 515 eligible sites in the
bound current roster. Their 1,225 returned rows match every requested native
site, collection-unit and dataset identity. Ten protected sites and two sites
without an established current parent remain outside this query population.

These archives live under `context-resources/<manifest-sha256>/`:

| Manifest SHA-256 | Sites | Native owner rows |
| --- | ---: | ---: |
| `6768f132375fba0e33bad406201e2a65aff3e4edbf4c5e0fd194abdab5d56c1c` | 4 | 10 |
| `92014d9d9e65846e63fdd263dedfeca659408f711bfd9a01ab7fcd9c96fcb647` | 128 | 335 |
| `bd1935f3bb3b29545d279cc32243eeb80643e01d553e630b60793d2fd6f39c81` | 128 | 525 |
| `1ba54364670f3abc84a2f2e5704b4ad55db66a47b432b3f2892e83edb65576ec` | 128 | 228 |
| `ab6f25eb90c5fe7106f79c40902cad19e02b8f526bcc66bb846baf745a1d8000` | 127 | 127 |

The native fields are `siteid`, `collectionunitid`, `datasetid` and `depenvt`.
Missing environment labels retain their source nulls. Owner-row coverage does
not establish dated basin geometry, shoreline history, water depth or a
reconstruction's applicable source radius.

On 16 November 2026 the maintained context reader requalified all five archives
against their original and current native owner bindings: 515 response bodies,
113,238 source bytes and 1,225 owner rows. The 157 null environment labels remain
null. This was an offline readback with no new requests or refetches. The
[qualification account](https://github.com/bijux/bijux-pollenomics/blob/d461e34b80bfca71f1f4b7d16e4db228aeed0bd9/reports/science/source-cohorts/neotoma-environment-qualification.json)
binds the source and reader identities; it admits source context, not dated basin
geometry or reconstruction suitability.

The older context archive
`df7ffd0712ec6ea7f6b46b8dfd3a31a05be5811ed2d09666f9309308c064670c`
retains four site-filtered environment responses with refused foreign-parent
profiles and four modern lake-candidate queries. Its original responses and
refusals remain separate from the dataset-filtered records. Modern candidates
and empty queries retain their source limitations.

Context readers require independently anchored original and current
`NeotomaContextArchiveBindings`. Select `dataset_depositional_environment` for
the dataset-filtered records. The 128-request archives require an explicit
caller budget within the existing context-protocol ceilings; the default
eight-request budget remains a separate, narrower choice. A budget refusal
does not establish missing source data.

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
| Qualified facet batch | `selection.read_neotoma_ancillary_facets` | Only explicitly selected entities, each parsed from its authenticated buffer |
| One linked HTTP entity | `selection.read_neotoma_ancillary_linked_entity` | The selected entity and its selected native source witness |
| One qualified linked record | `selection.read_neotoma_ancillary_linked` | The same authenticated buffers as the linked entity reader |
| Unit metadata | `unit_metadata.read_neotoma_unit_metadata_inventory` | None |
| Selected unit | `unit_metadata.read_neotoma_unit_metadata` | One selected unit body |
| Reference metadata | `reference_tables.read_neotoma_reference_archive_inventory` | None |
| Selected reference table | `reference_tables.read_neotoma_reference_archive_table` | One complete selected table body |
| Context metadata | `context_resources.read_neotoma_context_resource_inventory` | None |
| Selected context HTTP entity | `context_resources.read_neotoma_context_resource_entity` | One selected context body |
| Selected qualified context | `context_resources.read_neotoma_context_resource` | The selected authenticated body |
| Full context verification | `context_resources.load_neotoma_context_resource_archive` | All owned context bodies, subject to exposure restrictions |

The opt-in qualified facet batch accepts up to 128 distinct observation IDs
and retains at most 64 MiB of selected body bytes. It checks all selected body
identities before reading, then validates each body and native schema under one
operation-owned source lifetime. It returns only after the complete selection
and final checks succeed. Metadata and previously selected body identity checks
are repeated across selections, so total work can grow quadratically with the
number of selected bodies; no fixed runtime or memory ceiling follows from the
body-byte limit. This path requires an ordinary, single-link source body and may
refuse a batch if global current-scope preflight cannot be established. Its
physical drift checks do not prove atomic capture or scientific admission.

Selected facet and linked reads require exact observation identities. Linked
reads additionally require the precise occurrence identity. The source witness
must actually contain that native target at the recorded JSON pointer. A
rehashed index or plausible label cannot supply the missing relationship.

Capsule publication and selected facet/linked consumers keep their independently
pinned context and catalogue dependencies stable through preparation, body
access, parsing and return. Changed permission metadata refuses the operation;
an earlier successful check cannot authorize a later read after that change.
The same lifetime rule applies while ancestry replays an older baseline under
a separately authenticated current context.

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

## Browse Captured Metadata

Regenerate a map with the current reader to browse the captured metadata;
previously generated maps retain their packaged reader. **Native datasets**
remains the default listing. **Metadata population** also offers capture scope,
facet slots, captured observations, linked occurrences and supporting archive
entries. These populations have their own paged counts and literal search;
they are never added to native dataset, site or scientific totals. Global
linked metadata is not silently restricted by a native-country filter.

Selected metadata details retain source identities, epochs and qualification
limits as text. They neither load nor offer downloads of ancillary entity
bodies, and they supply no new biological, ecological or scientific admission.
On a source-only map with no scientific country controls, **Metadata country**
controls the separate, opt-in metadata geometry. On maps with scientific
country controls, metadata geometry continues to follow those controls.
Unassigned geometry requires its separate switch; an unavailable location is
never replaced with an invented point.

A source-only map keeps its scientific countries, layers and points at zero.
Its visible **Neotoma source resources** button opens the metadata reader
without opening the map tools. Its compact summary sits below the map, leaving
metadata geometry unobscured. The tools retain their own reader button.
Escape closes the reader and restores focus to the button that opened it; on
mobile, another Escape can then close the tools. Search accepts literal `?`
without opening the map help behind the reader.

## Recorded Taxon Ancestry

The immutable `taxon-ancestry/` baseline above derives from 2,735 retained direct
source entries across 25 captures. Its independently bound source evidence has
2,738 target slots; three protected contact targets remain outside those acquired
entries. The baseline retains 2,190 seed taxa, 4,382 literal parent/citation field
occurrences, 2,351 known taxon nodes and 174 referenced publication nodes. Its
eleven content-addressed parts contain 16,007,737 bytes; the manifest and parts
together contain 18,212,538 bytes.

The 195 unresolved source leads are 161 additional parent taxa and 34 publication
details. Publishing their recorded pointers does not fetch those entities. The
18 literal self-edges remain explicit. No multi-node cycle or conflicting parent
was found in this retained projection; uncollected ancestors can still change the
known graph. Biological ranks, ecological groups and reconstruction admission
remain separate from these source relationships.

The API owner is
`bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry`.
Use `read_neotoma_taxon_ancestry_target` with the independently retained manifest
digest, a `kind` of `taxon` or `publication`, and the exact positive native ID.
It reads selected published metadata parts and reports
`current_roles_revalidated=False`, `native_source_fields_revalidated=False` and
`GET_authorized=False`. A recorded pointer supplies neither current body-access
authority nor a new collection decision.

`load_neotoma_taxon_ancestry` performs complete source replay with explicit
`NeotomaTaxonAncestrySources`: evidence, original direct captures, predecessor
facets, context and native archive each require their independently pinned
resolvers. The relationship product embeds no native response bodies. Complete
source replay therefore requires the independently bound native archive,
context, linked evidence and capture resolvers. The five capsules listed above
now retain the baseline's existing direct captures and predecessor facets;
their presence does not replace current owner checks or supply uncollected
frontier responses.

The separately maintained `ancestry.chain` API authenticates later source-backed
layers against a permanently frozen seed baseline, historical/current owner and
PI duties, and baseline-relative depth limits. Newly discovered parents remain
additional nodes rather than becoming new seeds. Its selected metadata reader
also retains explicit limits on current-role and native-body authority. The
finite HTTP producer is available as `ancestry.chain.acquisition`; actual
collection of the 195 leads remains open.

## Collect An Explicit Ancestry Frontier

`capture_neotoma_taxon_ancestry_frontier` accepts one explicit tuple of unique
frontier target keys and independently pinned `NeotomaTaxonAncestryChainSources`.
The resolver binds the frozen baseline, original evidence and captures, current
context and native archive, and any preceding chain layers and source epochs.
Supply these dependencies explicitly; a selected metadata reader's recorded
pointer does not authorize collection.

```python
from pathlib import Path

from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.acquisition import (
    capture_neotoma_taxon_ancestry_frontier,
)

captured = capture_neotoma_taxon_ancestry_frontier(
    Path("artifacts/neotoma/frontier-capture"),
    sources=sources,
    parent_chain_sha256=parent_pin,
    target_keys=selected_frontier_keys,
)
```

Here `sources`, `parent_pin` and `selected_frontier_keys` come from the explicitly
reviewed source selection. Use `None` for `parent_pin` only when extending the
frozen baseline directly. Every selected target must have a permitted native
child witness and satisfy all known incoming roots' historical and current
owner and PI duties. Protected, foreign, already attempted and out-of-bound
targets refuse before native baseline replay or HTTP requests. The producer
does not recursively collect newly discovered pointers or rebase their depth.

| Per-invocation limit | Ceiling |
| --- | ---: |
| explicit target keys / attempts per target | 16 / 1 |
| complete response entity | 2 MiB |
| aggregate response reservation | 16 × (2 MiB + one incomplete-response sentinel byte) |
| owned output tree | 64 MiB |
| individual control document | 1 MiB |
| transport timeout | 60 seconds |
| cooperative operation budget | default 900 seconds; explicit selection up to 3,600 seconds |

Smaller request and response budgets must still reserve every selected response.
The default operation budget remains 900 seconds. Pass an explicit
`NeotomaTaxonFrontierCaptureLimits(wall_seconds=3600)` from the same acquisition
module through `capture_limits` to select the larger finite allowance.
An outer deadline owner must instead pass its current positive remaining
allowance at invocation, within the same ceiling, and keep its own guard
authoritative. The SDK starts a separate relative clock after entry; it does
not inherit the outer absolute deadline.
The operation budget is checked between stages; it is not a hard interrupt for
filesystem operations or an arbitrary supplied transport callback. These limits
do not increase the cumulative chain limits or grant provider quota. Before a
run, account for provider limits and reserve capacity for other collection work.

The official [API reference](https://api.neotomadb.org/api-docs/) describes native
taxon and publication detail routes. The producer retains source HTTP failures,
empty responses and refused source formats without retrying them or claiming
source absence. A closed capture is checked through fresh chain readers before
and after publication. Within that invocation, those readers borrow immutable
baseline facts already authenticated by its still-live original source owner.
They reconstruct current all-root and PI duties and replay each new capture's
receipts and bodies; physical or permission changes refuse continued use. No
native response bodies or cross-invocation qualifications are cached. Public
standalone chain derivation and loading still replay their complete sources.

Its destination must be a new canonical literal path outside every consumed
source tree. Existing and competing entries are preserved; failed owned
candidates remain available for investigation.

Preserve source identifiers, literal parent/citation fields, receipts and reuse
attribution. Neotoma's [data-use policy](https://www.neotomadb.org/data/data-use-and-embargo-policy)
requires credit to Neotoma, the constituent database, original investigators
and primary publications, with the relevant site/dataset citation information.
The [taxonomy manual](https://open.neotomadb.org/manual/taxonomy-related-tables-1.html)
also includes physical parameters and biometric measures in its taxon table.
A source ancestry link does not establish a biological rank, forest/open-land
class, applicable PPE or an admitted LRA input.

Publication detail can report a singleton all-null dataset-association
placeholder. Preserve it as unavailable association metadata. An identified
association can have an unknown `primary` flag. Neither case changes a native
identifier to zero or changes unknown primary status to false. Successful empty
detail responses likewise do not certify source absence.

For LRA, bind counts, taxonomy, pollen denominator, selected chronology, dated
basin geometry, applicable PPE and fall speeds, uncertainty and permitted use
separately. Downloaded source context cannot supply a missing qualified decision.

## Selected recorded ancestry in Atlas

`AtlasTaxonAncestryArchiveInput` connects an explicitly pinned ancestry-chain
archive to the existing Atlas supporting-metadata reader. Supply its directory,
manifest SHA-256, a `chain_sources` mapping of exact chain and baseline manifest
pins to their local directories, and a nonempty immutable tuple of
`("taxon", native_id)` or `("publication", native_id)` targets. Target identities must be unique
within the selection; IDs must be positive JavaScript-safe integers. Resolver bindings
are copied into an immutable mapping; local paths are not published.

Configure that input through `AtlasAncillaryArchivesInput.taxon_ancestry` alongside
any independently configured supporting archives. Each explicit target is read
through `read_neotoma_taxon_chain_target`; this adapter does not enumerate the
whole graph, fetch source details or open native entity bodies. Missing targets,
resolvers, changed manifest pins and foreign selected locators refuse projection.

The existing `supporting_archives` and `supporting_entries` populations use
`archive_kind="taxon_ancestry"` and `index_population="targets"`. Target selectors
are `target_key`, `kind` and `native_id`; recorded nodes retain their SDK-native
`target_kind` field. The selected index has its own projection digest, distinct
from the independently pinned source-chain manifest. Source header pins, baseline
identity and capture epochs remain attached. This is a selected subset, not a
replacement count for all known taxa, publications, source requests or frontier
leads. Existing resource, site, observation and ancillary populations retain
their own denominators.

The archive explicitly reports `SELECTED_RECORDED_TARGETS_ONLY`:
`current_roles_revalidated=False`, `native_source_fields_revalidated=False`,
`native_entity_bodies_opened=0`, `GET_authorized=False` and
`scientific_admission="not_asserted"`. A field named current in a recorded node
belongs to its recorded epoch; this display does not authenticate current use
permission. Literal parent and citation edges are not biological synonymy,
applicable reconstruction parameters or admitted scientific observations.

The ordinary lazy indexed reader owns filtering and selected metadata readback.
It offers no ancestry source-body download or acquisition authority. Leaving
`taxon_ancestry` unconfigured preserves the other three supporting families and
their published metadata. An actual chain must still be separately materialized,
qualified and explicitly supplied before these software interfaces change a
published Atlas.

The [recorded source atlas snapshot](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-integrity/neotoma/recorded-source-atlas/README.md)
now carries an explicit selection of 16 captured targets from chain
`0e7e37196a8eabc771b336bec25f981bfc6a291148dc519b9ce6c4f8212e2064`.
The refreshed 105-file static publication preserves the prior 1,258-resource / 527-site
metadata population and five supporting archives, adding one ancestry archive.
The selected ancestry projection exposes native IDs and literal recorded
fields, not taxon names or publication titles. Source-body access and current
permission remain separate. All 16 selected targets were opened at both 390 and 1,440 pixels in the
qualified local-file reader, with designated native JSON label/value scrolling
and complete long source-button text. The account preserves earlier refused
attempts separately. HTTP hosting and downloads remain unqualified.

## Retained Parent And Citation Details

The [recorded ancestry continuation](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-integrity/neotoma/ancestry-continuation/README.md)
retains a later closed capture of seven taxon details and five classification
references, pinned by `244769f271142c2f11d6f7cd11874d2fa8df6e5328e45ba6ff3851e6a06a402c`.
All twelve received details passed native source qualification. The account
preserves their literal names, parent/citation fields and source-quality limits.
These responses now have a separately qualified normalized successor,
`cf525a56c96f57f4aab43894326500b8ca080800544a3e0fea288296b393db0d`,
with 172 unresolved frontier leads and zero GETs during normalization. The
16-target Atlas above still selects the preceding `0e7e371…` chain; the dated
reference contrast remains bound to that preceding chain's fixed 182-lead set.
Neither has been refreshed by this normalization, and scientific admission is
not implied.

The [recorded ancestry account](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-integrity/neotoma/ancestry-captures/README.md)
links 13 captured taxon details and three taxon-reference publication details
to their unchanged responses, receipts and normalized chain.

- Capture: `taxon-ancestry/captures/20b13b13b7eab2cc6f932ac49fd249b0d6ea8d86b4e81824f5f7e7faf59a9009/`,
  expected manifest SHA-256 `20b13b13b7eab2cc6f932ac49fd249b0d6ea8d86b4e81824f5f7e7faf59a9009`
  (`capture-manifest.json`; 34 files, 115,852 bytes).
- Chain: `taxon-ancestry/chains/0e7e37196a8eabc771b336bec25f981bfc6a291148dc519b9ce6c4f8212e2064/`,
  expected manifest SHA-256 `0e7e37196a8eabc771b336bec25f981bfc6a291148dc519b9ce6c4f8212e2064`
  (`manifest.json`; five files, 592,574 bytes).

Keep the baseline pin above as a separate explicit metadata resolver. The
selected SDK/Atlas metadata route does not read the supporting detail bodies,
revalidate current source roles, authorize GETs or admit a taxon/PPE mapping.
The chain's `new_GETs` is zero; its summary retains the earlier 16 captured
HTTP requests. Its frozen frontier has 182 unresolved leads, including three
newly exposed taxon pointers. Full resource closure remains open.
