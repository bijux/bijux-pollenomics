# Dated Neotoma taxonomy reference

The taxonomy-reference API retains official Git projections separately from
Neotoma API detail captures. It provides reusable native-ID/name/parent and
classification-reference lookups while preserving each original data file.
It describes the global Neotoma vocabulary, including measurement and unknown
categories. Membership does not establish Swedish occurrence, a regional pollen
panel, sample observations, biological equivalence or PPE suitability.

The upstream source is the
[Neotoma Taxonomy Viewer](https://github.com/NeotomaDB/Taxonomy-Viewer).
The three supported projections are `data/taxa_snapshot.json`,
`data/taxon_metadata.json` and `data/all_synonyms.json`. Their common Git revision
does not establish a transactionally consistent database instant. This API
performs no network requests and copies no upstream viewer program.

## Retained source and lookup

Import the interfaces from
`bijux_pollenomics.collection.sources.neotoma.ancillary_store.taxonomy_reference`.
`NeotomaTaxonomyReferenceSource` binds independently supplied file sizes/hashes,
the retained official commit/root-tree/data-tree metadata, genuine GitHub transport
records and intake intervals. `write_neotoma_taxonomy_reference_archive` checks
those bindings and Git tree membership before publishing an absent output through
the existing owned source publisher. A supplied metadata dictionary is not a live
API, permission or scientific authority.

`read_neotoma_taxonomy_reference_inventory` authenticates the archive metadata
without opening the three original projections. Its
`source_entity_bodies_verified` flag is false.
`read_neotoma_taxonomy_reference_taxa` accepts a unique tuple of explicit positive
native IDs and returns records in that order. Each call authenticates and decodes
the required originals once for the whole batch. Unknown requested IDs are
refused; they are not reported as absent from the living database. Returned
records are detached and recursively immutable, with no global cache or extended
source lease.

The literal `taxon` and `metadata` mappings preserve native field names. In
particular, metadata `publication` can contain source fallback text while
`citation` remains null. Keep both. A classification citation does not establish
a primary dataset paper, geographic occurrence or pollen-model attribution.

Global synonym assertions preserve source group position, assertion position,
directional valid/invalid IDs, names, type and both dates. Repeated triples are
retained; source positions distinguish the assertions. They are not silently
deduplicated or promoted to biological, dataset-specific morphotype or PPE
equivalence. Null and self-parent pointers remain literal native values.

Database record creation/modification and validation dates are metadata dates,
not sample ages, chronology support or geological validity intervals. The
snapshot refresh timestamp, Git commit timestamp and local intake intervals also
remain distinct. Metadata and synonyms receive no invented independent refresh
timestamp. There is no source-status field in these projections.

## Provenance and limits

The archive contains three unchanged originals, pinned Git metadata evidence,
portable provenance and a closed manifest. Genuine raw transport records remain
in the caller's retained research custody. Public provenance labels its selected
transport facts as a projection and records each raw record's SHA-256. Local
filenames, workstation paths, local addresses/ports and unselected curl fields
are omitted. The projection is neither an original transport record nor a
fabricated Neotoma per-entity HTTP receipt.

Git membership checks reconstruct tree identities and join the independently
pinned commit metadata to its data tree and blobs. They do not reconstruct or
verify a signed commit object, query GitHub again, or establish upstream database
completeness. The source-specific archive is bounded to 64 MiB and 16 files;
metadata members have a 1 MiB limit, JSON depth is bounded, and projection rows and
assertions have explicit finite bounds. The separate API-prefix reference-table
protocol and its existing limits are unchanged.

Scientific admission, current-role revalidation and status availability are
explicitly false/not asserted. No detail captures, dataset/site records,
observation counts, analytical selections or Atlas scientific counters are
added by reference lookup. Native capture obligations and missing context remain
open even when an older reference contains the same ID.

Preserve Neotoma, constituent database and applicable contributor/reference
attribution under the
[Neotoma data-use policy](https://www.neotomadb.org/data/data-use-and-embargo-policy).
The viewer repository's code license and database data policy are separate
questions. This interface retains source data and provenance; it does not copy
or execute upstream viewer code or infer dataset associations from citations.

## Recorded-frontier comparison and local commands

`contrast_neotoma_taxonomy_reference_frontier` joins an independently anchored
chain's explicitly stored frontier parts to the dated reference. It authenticates
the chain manifest and selected parts through the existing content-addressed
reader. It opens no native capture bodies, replays no baseline, and does not
reconstruct an inherited delta frontier. A chain delta with no explicit frontier
parts is refused rather than interpreted as zero outstanding context.

Every recorded target is retained, including reference misses. A miss means that
the ID was not observed in this older projection; it is not proof of absence from
current Neotoma. Taxon IDs and classification-publication IDs are distinct join
domains. A non-null publication pointer with no citation or fallback text remains
an observed ID only. When text is available, all differing literal
publication/citation/year variants retain their source taxon-ID links; no
representative biological authority is selected.

The result binds both input manifest hashes, the reference Git revision, its
snapshot refresh timestamp, the retained commit timestamp and separate intake
intervals. Recorded new-capture manifest pointers remain pointers, not inferred
capture datetimes. Root/use-role and capture-status fields are labeled recorded
context; current roles and native source fields are not revalidated. A contrast
of the frozen 182-lead snapshot does not update that frontier, discharge a native
capture obligation or materialize the later captured continuation.

`write_neotoma_taxonomy_reference_contrast` writes one bounded
`frontier-contrast.json` through the existing owned source publisher while input
and output seals remain live. The same interfaces are available locally:

```text
python -m bijux_pollenomics.collection.sources.neotoma.ancillary_store.taxonomy_reference.command_line --help
```

The module offers `retain`, `lookup` and `contrast-frontier`. `retain` requires an
independently SHA-256-pinned local source plan with `revision`, `files`,
`git_metadata`, `transport`, `intake_intervals` and `attribution`. Each file record
has a local `path`, finite `bytes` and `sha256`; source-plan paths are not copied
into public provenance. `git_metadata` binds `commit`, `root_tree` and `data_tree`;
the projection/transport maps use the three exact supported filenames.

`lookup` takes an archive, its manifest SHA-256 and repeated `--taxon-id` values.
Its JSON output retains the archive pin, literal nulls and positional synonym
assertions. `contrast-frontier` additionally requires `--chain`, the chain's
manifest SHA-256 and an absent `--output` directory. All verbs are local source
consumers: none acquires data, performs current permission decisions, modifies
the source graph or changes existing Atlas dataset/site/numerical denominators.
