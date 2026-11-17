"""Publish exact retained Git projections with portable, explicitly limited provenance."""

from __future__ import annotations

from contextlib import ExitStack
from hashlib import sha1, sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import (
    BoundedInputTree,
    DirectoryAnchor,
    OwnedTreeWriter,
)
from bijux_pollenomics.core.owned_tree import build_staging_output_dir

from ...publication.ownership import publish_owned_source_tree
from ...resource_catalogue.archive.files import encoded_json
from .contracts import (
    MAX_BYTES,
    MAX_FILES,
    MAX_METADATA,
    NAMES,
    POSTURE,
    RAW,
    REPOSITORY,
    SCHEMA,
    NeotomaTaxonomyReferenceFile,
    NeotomaTaxonomyReferenceManifest,
    NeotomaTaxonomyReferenceSource,
    decode,
    git_membership,
)
from .reading import EVIDENCE, _archive, _originals, projections


def _transport(
    raw: bytes, name: str, source: NeotomaTaxonomyReferenceSource
) -> dict[str, Any]:
    record = decode(raw)
    url = RAW + source.revision + "/data/" + name
    if (
        not isinstance(record, dict)
        or record.get("url") != url
        or record.get("url_effective") != url
        or type(record.get("http_code")) is not int
        or record["http_code"] != 200
        or type(record.get("ssl_verify_result")) is not int
        or record["ssl_verify_result"] != 0
        or type(record.get("num_redirects")) is not int
        or record["num_redirects"] != 0
        or type(record.get("size_download")) is not int
        or record["size_download"] != source.files[name].bytes
        or type(record.get("time_total")) not in (int, float)
        or not 0 <= record["time_total"] <= 3600
    ):
        raise ValueError("Taxonomy reference retained GitHub transport differs")
    return {
        "source_record_sha256": sha256(raw).hexdigest(),
        "requested_url": url,
        "effective_url": record["url_effective"],
        "http_status": record["http_code"],
        "tls_verify_result": record["ssl_verify_result"],
        "redirect_count": record["num_redirects"],
        "download_bytes": record["size_download"],
        "elapsed_seconds": record["time_total"],
        "intake_start": source.intake_intervals[name][0],
        "intake_end": source.intake_intervals[name][1],
    }


def write_neotoma_taxonomy_reference_archive(
    directory: Path, *, source_provenance: NeotomaTaxonomyReferenceSource
) -> NeotomaTaxonomyReferenceManifest:
    """Retain attributed originals; supplied pins do not establish live authority."""
    if type(source_provenance) is not NeotomaTaxonomyReferenceSource:
        raise ValueError(
            "Explicit independently pinned taxonomy reference source required"
        )
    source = source_provenance
    final = Path(directory).absolute()
    if final.exists():
        raise FileExistsError(final)
    entries = [("originals/" + name, source.files[name], MAX_BYTES) for name in NAMES]
    entries += [
        ("evidence/" + name + ".json", source.git_metadata[name], MAX_METADATA)
        for name in EVIDENCE
    ]
    entries += [
        ("transport/" + name, source.transport[name], MAX_METADATA) for name in NAMES
    ]
    if (
        len({pin.path for _, pin, _ in entries}) != len(entries)
        or sum(pin.bytes for _, pin, _ in entries) > MAX_BYTES
    ):
        raise ValueError("Taxonomy reference input population is aliased or oversized")
    with ExitStack() as stack:
        parent = stack.enter_context(DirectoryAnchor(final.parent))
        trees = {}
        for name, pin, limit in entries:
            if pin.bytes > limit:
                raise ValueError(
                    "Taxonomy reference member exceeds its role byte bound"
                )
            trees[name] = stack.enter_context(
                BoundedInputTree(
                    pin.path.parent,
                    max_bytes=pin.bytes,
                    max_files=1,
                    selected=pin.path.name,
                )
            )

        def read(name: str, pin: NeotomaTaxonomyReferenceFile) -> bytes:
            raw = trees[name].read(pin.path, max_bytes=pin.bytes)
            if len(raw) != pin.bytes or sha256(raw).hexdigest() != pin.sha256:
                raise ValueError(
                    "Taxonomy reference independently pinned input differs"
                )
            return raw

        evidence = {
            name: read("evidence/" + name + ".json", source.git_metadata[name])
            for name in EVIDENCE
        }
        git = git_membership(evidence, source.revision)
        buffers = {"evidence/" + name + ".json": raw for name, raw in evidence.items()}
        originals = {}
        for name in NAMES:
            pin = source.files[name]
            raw = read("originals/" + name, pin)
            blob = sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            if git[name]["size"] != len(raw) or git[name]["sha"] != blob:
                raise ValueError(
                    "Taxonomy reference original bytes differ from Git membership"
                )
            buffers["originals/" + name] = raw
            originals[name] = {
                "bytes": len(raw),
                "sha256": pin.sha256,
                "git_blob": blob,
            }
        _, _, _, generated = projections(
            {name: buffers["originals/" + name] for name in NAMES}
        )
        provenance = {
            **POSTURE,
            "source_repository": REPOSITORY,
            "source_revision": source.revision,
            "commit_utc": decode(evidence["commit"])["committer"]["date"],
            "source_generated_at": generated,
            "git_metadata": {
                name: {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
                for name, raw in evidence.items()
            },
            "originals": originals,
            "transport": {
                name: _transport(
                    read("transport/" + name, source.transport[name]), name, source
                )
                for name in NAMES
            },
            "transport_scope": "portable_projection_of_retained_github_transport",
            "removed_transport_fields": [
                "filename_effective",
                "local_ip",
                "local_port",
                "other_unselected_transport_fields",
            ],
            "git_membership_scope": "independently_pinned_commit_metadata_and_reconstructed_trees_not_signed_commit_verification",
            "attribution": source.attribution,
            "rights_reference": "https://www.neotomadb.org/data/data-use-and-embargo-policy",
        }
        buffers["provenance.json"] = encoded_json(provenance)
        files = {
            name: {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
            for name, raw in buffers.items()
        }
        source_bytes = sum(len(raw) for raw in buffers.values())
        manifest = {
            "schema_version": SCHEMA,
            "files": files,
            "source_bytes": source_bytes,
            **POSTURE,
        }
        raw_manifest = encoded_json(manifest)
        anchor = sha256(raw_manifest).hexdigest()
        if source_bytes + len(raw_manifest) > MAX_BYTES or len(files) + 1 > MAX_FILES:
            raise ValueError(
                "Taxonomy reference closed archive exceeds its finite budget"
            )
        parent.check()
        staging = build_staging_output_dir(final)
        with OwnedTreeWriter(
            staging, max_bytes=MAX_BYTES, max_files=MAX_FILES
        ) as writer:
            for name, raw in buffers.items():
                writer.write_bytes(name, raw)
            writer.write_bytes("manifest.json", raw_manifest)

            def validate(location: Path) -> None:
                parent.check()
                for tree in trees.values():
                    tree.check()
                with _archive(location, anchor) as (tree, checked, checked_provenance):
                    _, _, _, actual_generated = projections(
                        _originals(tree, checked, checked_provenance)
                    )
                    if actual_generated != generated:
                        raise ValueError("Taxonomy reference refresh epoch differs")
                for original in trees.values():
                    original.check()
                parent.check()

            publish_owned_source_tree(
                writer, staging=staging, final=final, validate=validate
            )
        return NeotomaTaxonomyReferenceManifest(anchor, manifest)
