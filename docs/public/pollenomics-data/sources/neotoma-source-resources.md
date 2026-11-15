---
title: Neotoma Native Source Resources
audience: developer
type: how-to
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-11-15
---

# Neotoma Native Source Resources

Use `data/neotoma/source-resources/` for portable access to the separately
captured Nordic discovery population. The archive contains its own catalogue,
raw response bodies, receipts, capture plans, source metadata and original
dataset-metadata witnesses. It requires no acquisition-folder resolvers and
performs no network requests when read.

The host wheel supplies the readers. The repository supplies these source
bytes; installing the wheel alone does not install the archive.

## Pin The Source Population

| Identity | Value |
| --- | --- |
| archive manifest SHA-256 | `d34559cf88a41c45deadcb4e3def5a5fdf765d51092063bd29d033615cdaeaff` |
| compact catalogue manifest SHA-256 | `5ac1dd118ba97e08d9e52220248049c779db895d094a5f450ab215d5709ec1ec` |
| files, including the archive manifest | 8,452 |
| total bytes | 297,697,093 |
| resource identities / source sites | 1,258 / 527 |
| current and DOI-frozen version slots | 2,516 |
| source capture descriptors | 68 |

This is a bounded discovery population assembled from retained spatial and
source-country queries. It is not a census of all Neotoma records or all Nordic
territories. Source-reported country, boundary assignment and disagreements
remain separate fields. An unassigned or non-point source stays discoverable
without inventing a location.

The download index records 2,458 available HTTP source entities and 58 slots
blocked by exposure role. Available entities include provider `NoRecordFound`
and successful empty responses. Those states do not establish available
numerical observations. Source-format qualification, scientific admission,
reuse permissions and independent validation are separate questions.

## Read One Selected Resource

Run examples from the repository root, or replace the relative archive path
with the location of an unchanged copy. Supply the independently known anchor;
reading a digest out of the same untrusted manifest does not authenticate it.

```python
from pathlib import Path

from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive import (
    read_neotoma_source_archive_resource,
)

archive = Path("data/neotoma/source-resources")
anchor = "d34559cf88a41c45deadcb4e3def5a5fdf765d51092063bd29d033615cdaeaff"

selected = read_neotoma_source_archive_resource(
    archive,
    expected_manifest_sha256=anchor,
    dataset_id=54000,
    version="current",
    include_native_body=True,
)
assert selected["dataset_id"] == 54000
assert selected["scientific_admission"] == "not_asserted"
assert isinstance(selected["native_body"], bytes)
```

The typed reader checks the selected resource's exposure role, original capture
lineage and supported source format. It raises `ValueError` when that selection
has no qualified numerical payload. For example, the DOI-frozen response for
dataset 53100 is a provider `NoRecordFound` entity.

For source investigation, `read_neotoma_source_archive_entity` accepts the same
archive, anchor, dataset and version arguments and returns the authenticated
complete HTTP entity, including empty or unsupported source responses. It
also returns `native_body` bytes. It does not bypass protected exposure roles
or turn an unsupported response into a method input. Keep the original bytes
when exporting: decoding and reserializing JSON produces a different entity.

Both selected readers authenticate archive metadata and the selected source
entity. Their returned `archive.integrity_scope` is
`archive_metadata_and_selected_source_entity`, with
`unselected_source_bodies_verified` equal to `False`. They do not read other
numerical source bodies. Original source metadata needed for the selected
identity may be checked as part of its custody proof.

## Verify The Complete Archive

Use the complete validator when receiving or restoring an archive copy:

```python
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive import (
    load_neotoma_source_archive,
)

manifest = load_neotoma_source_archive(
    archive, expected_manifest_sha256=anchor
)
assert manifest["scientific_admission"] == "not_asserted"
```

This operation authenticates every member and replays the source relationships;
it intentionally reads the whole archive. Extra, missing, changed or unsafe
members are refused. Keep notes and derived products outside the closed
archive namespace. Git attributes preserve native bodies and archive metadata
without newline conversion.

## Bind Atlas Metadata Explicitly

Pass this typed dependency as `source_resource_catalogue` to
`reporting.service.generate_multi_country_map` or the maintained report-tree
publisher:

```python
from bijux_pollenomics.reporting.map_document.source_resources import (
    AtlasResourceArchiveInput,
    AtlasResourceCatalogueInput,
)

source_resource_catalogue = AtlasResourceCatalogueInput(
    directory=archive / "catalogue",
    expected_manifest_sha256=(
        "5ac1dd118ba97e08d9e52220248049c779db895d094a5f450ab215d5709ec1ec"
    ),
    archive=AtlasResourceArchiveInput(
        directory=archive,
        expected_manifest_sha256=anchor,
        published_base_url="/data/neotoma/source-resources/",
    ),
)
```

The configured public route must actually serve the unchanged archive files.
Binding it authenticates the metadata and download index; it does not publish
files to a server. The source-resource layer carries its own population and
does not change the original pollen Atlas's scientific membership, sample
counts, time support or denominator. Reader-interface availability and a full
Atlas publication require their own verification.

## Choose Method Inputs Separately

For LRA, inspect exact dataset, collection-unit and sample identities; native
taxon concepts; measurement units and denominator; alternative chronologies;
basin geometry and period; applicable PPE and fall speeds; and permitted use.
Preserve conflicting and missing values. Current and DOI-frozen responses are
different source epochs, not interchangeable versions of a selected scientific
input set. A metadata or schema match does not choose an age model, approve a
basin radius, harmonize a taxon or certify independent vegetation accuracy.

Ancillary endpoint captures and linked references are separate resources. The
native archive described here does not certify completion of their census or
recursively resolve every reference exposed by the provider.
