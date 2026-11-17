"""Authenticate dated projection files once for an explicit native-ID selection."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime
from hashlib import sha1, sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import BoundedInputTree

from .contracts import (
    MAX_BYTES,
    MAX_FILES,
    MAX_METADATA,
    MAX_ROWS,
    NAMES,
    POSTURE,
    REPOSITORY,
    SCHEMA,
    NeotomaTaxonomyReferenceInventory,
    NeotomaTaxonomyReferenceTaxon,
    NeotomaTaxonomySynonymAssertion,
    decode,
    digest,
    git_membership,
    native_id,
    utc,
)

EVIDENCE = ("commit", "root_tree", "data_tree")
MEMBERS = {
    "provenance.json",
    *("originals/" + name for name in NAMES),
    *("evidence/" + name + ".json" for name in EVIDENCE),
}
PROVENANCE_FIELDS = {
    "source_repository",
    "source_revision",
    "commit_utc",
    "source_generated_at",
    "git_metadata",
    "originals",
    "transport",
    "transport_scope",
    "attribution",
    "rights_reference",
    "removed_transport_fields",
    "git_membership_scope",
    *POSTURE,
}


def _read(tree: BoundedInputTree, name: str, expected: Mapping[str, Any]) -> bytes:
    raw = tree.read(tree.root / name, max_bytes=expected["bytes"])
    if sha256(raw).hexdigest() != expected["sha256"]:
        raise ValueError("Taxonomy reference member hash differs")
    return raw


def _provenance(value: Any) -> dict[str, Any]:
    if (
        not isinstance(value, dict)
        or set(value) != PROVENANCE_FIELDS
        or value["source_repository"] != REPOSITORY
        or not digest(value["source_revision"], 40)
        or any(
            type(value[key]) is not type(expected) or value[key] != expected
            for key, expected in POSTURE.items()
        )
        or value["transport_scope"]
        != "portable_projection_of_retained_github_transport"
        or value["git_membership_scope"]
        != "independently_pinned_commit_metadata_and_reconstructed_trees_not_signed_commit_verification"
        or type(value["attribution"]) is not str
        or not value["attribution"].strip()
        or value["rights_reference"]
        != "https://www.neotomadb.org/data/data-use-and-embargo-policy"
        or value["removed_transport_fields"]
        != [
            "filename_effective",
            "local_ip",
            "local_port",
            "other_unselected_transport_fields",
        ]
        or not isinstance(value["git_metadata"], dict)
        or set(value["git_metadata"]) != set(EVIDENCE)
        or not isinstance(value["originals"], dict)
        or set(value["originals"]) != set(NAMES)
        or not isinstance(value["transport"], dict)
        or set(value["transport"]) != set(NAMES)
    ):
        raise ValueError("Taxonomy reference provenance or source posture differs")
    utc(value["commit_utc"])
    utc(value["source_generated_at"])
    for name, row in value["transport"].items():
        url = (
            "https://raw.githubusercontent.com/NeotomaDB/Taxonomy-Viewer/"
            + value["source_revision"]
            + "/data/"
            + name
        )
        if (
            not isinstance(row, dict)
            or set(row)
            != {
                "source_record_sha256",
                "requested_url",
                "effective_url",
                "http_status",
                "tls_verify_result",
                "redirect_count",
                "download_bytes",
                "elapsed_seconds",
                "intake_start",
                "intake_end",
            }
            or not digest(row["source_record_sha256"])
            or row["requested_url"] != url
            or row["effective_url"] != url
            or type(row["http_status"]) is not int
            or row["http_status"] != 200
            or type(row["tls_verify_result"]) is not int
            or row["tls_verify_result"] != 0
            or type(row["redirect_count"]) is not int
            or row["redirect_count"] != 0
            or type(row["download_bytes"]) is not int
            or row["download_bytes"] != value["originals"][name]["bytes"]
            or type(row["elapsed_seconds"]) not in (int, float)
            or not 0 <= row["elapsed_seconds"] <= 3600
        ):
            raise ValueError("Taxonomy reference portable transport differs")
        start = datetime.fromisoformat(utc(row["intake_start"]).replace("Z", "+00:00"))
        end = datetime.fromisoformat(utc(row["intake_end"]).replace("Z", "+00:00"))
        if start > end:
            raise ValueError("Taxonomy reference intake interval is reversed")
    return value


@contextmanager
def _archive(
    directory: Path, anchor: str
) -> Iterator[tuple[BoundedInputTree, dict[str, Any], dict[str, Any]]]:
    if not digest(anchor):
        raise ValueError("Independent taxonomy reference manifest anchor required")
    with BoundedInputTree(directory, max_bytes=MAX_BYTES, max_files=MAX_FILES) as tree:
        raw = tree.read(tree.root / "manifest.json", max_bytes=MAX_METADATA)
        if sha256(raw).hexdigest() != anchor:
            raise ValueError("Taxonomy reference manifest identity differs")
        manifest = decode(raw)
        if (
            not isinstance(manifest, dict)
            or set(manifest) != {"schema_version", "files", "source_bytes", *POSTURE}
            or manifest["schema_version"] != SCHEMA
            or not isinstance(manifest["files"], dict)
            or set(manifest["files"]) != MEMBERS
            or any(
                type(manifest[key]) is not type(expected) or manifest[key] != expected
                for key, expected in POSTURE.items()
            )
            or set(tree.files) != {"manifest.json", *MEMBERS}
            or set(tree.directories) != {"", "originals", "evidence"}
        ):
            raise ValueError("Taxonomy reference manifest or namespace differs")
        total = 0
        for name, row in manifest["files"].items():
            if (
                not isinstance(row, dict)
                or set(row) != {"bytes", "sha256"}
                or type(row["bytes"]) is not int
                or not 0
                < row["bytes"]
                <= (MAX_BYTES if name.startswith("originals/") else MAX_METADATA)
                or not digest(row["sha256"])
                or tree.files[name][4] != row["bytes"]
            ):
                raise ValueError("Taxonomy reference file declaration differs")
            total += row["bytes"]
        if (
            type(manifest["source_bytes"]) is not int
            or manifest["source_bytes"] != total
            or total + len(raw) > MAX_BYTES
        ):
            raise ValueError("Taxonomy reference aggregate byte count differs")
        provenance = _provenance(
            decode(_read(tree, "provenance.json", manifest["files"]["provenance.json"]))
        )
        evidence = {
            name: _read(
                tree,
                "evidence/" + name + ".json",
                manifest["files"]["evidence/" + name + ".json"],
            )
            for name in EVIDENCE
        }
        git = git_membership(evidence, provenance["source_revision"])
        if provenance["commit_utc"] != decode(evidence["commit"])["committer"]["date"]:
            raise ValueError("Taxonomy reference retained commit timestamp differs")
        for name in EVIDENCE:
            if (
                provenance["git_metadata"][name]
                != manifest["files"]["evidence/" + name + ".json"]
            ):
                raise ValueError("Taxonomy reference metadata provenance pin differs")
        for name in NAMES:
            expected = manifest["files"]["originals/" + name]
            if (
                provenance["originals"][name]
                != {**expected, "git_blob": git[name]["sha"]}
                or expected["bytes"] != git[name]["size"]
            ):
                raise ValueError("Taxonomy reference original Git listing differs")
        tree.check()
        yield tree, manifest, provenance
        tree.check()


def read_neotoma_taxonomy_reference_inventory(
    directory: Path, *, expected_manifest_sha256: str
) -> NeotomaTaxonomyReferenceInventory:
    """Authenticate metadata and declarations without opening original projections."""
    with _archive(directory, expected_manifest_sha256) as (_, manifest, provenance):
        return NeotomaTaxonomyReferenceInventory(manifest, provenance)


def _text(value: Any, *, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if type(value) is not str or len(value) > 65536:
        raise ValueError("Taxonomy reference native text is malformed or oversized")


def _nullable_id(value: Any) -> None:
    if value is not None:
        native_id(value)


def projections(
    buffers: Mapping[str, bytes],
) -> tuple[dict[str, Any], dict[str, Any], list[Any], str]:
    """Validate literal source shape without deduplicating or interpreting dates."""
    snapshot, metadata, synonyms = (decode(buffers[name]) for name in NAMES)
    if not isinstance(snapshot, dict) or set(snapshot) != {"generated_at", "taxa"}:
        raise ValueError("Taxonomy reference snapshot shape differs")
    generated = utc(snapshot["generated_at"])
    taxa = snapshot["taxa"]
    if (
        not isinstance(taxa, dict)
        or not isinstance(metadata, dict)
        or not 0 < len(taxa) <= MAX_ROWS
        or set(taxa) != set(metadata)
    ):
        raise ValueError("Taxonomy reference native-ID populations differ")
    for key, row in taxa.items():
        if (
            not isinstance(row, dict)
            or set(row)
            != {
                "taxonid",
                "taxonname",
                "highertaxonid",
                "taxagroupid",
                "recdatecreated",
                "recdatemodified",
            }
            or key != str(native_id(row["taxonid"]))
        ):
            raise ValueError("Taxonomy reference native taxon owner differs")
        _nullable_id(row["highertaxonid"])
        if row["highertaxonid"] is not None and str(row["highertaxonid"]) not in taxa:
            raise ValueError("Taxonomy reference parent ID is absent")
        for name in ("taxonname", "taxagroupid"):
            _text(row[name])
        for name in ("recdatecreated", "recdatemodified"):
            _text(row[name], nullable=True)
        meta = metadata[key]
        if (
            not isinstance(meta, dict)
            or set(meta)
            != {
                "taxonid",
                "author",
                "publicationid",
                "publication",
                "citation",
                "publicationYear",
                "validatorid",
                "validatorName",
                "validatedate",
            }
            or type(meta["taxonid"]) is not int
            or meta["taxonid"] != row["taxonid"]
        ):
            raise ValueError("Taxonomy reference classification metadata owner differs")
        for name in ("publicationid", "validatorid"):
            _nullable_id(meta[name])
        for name in set(meta) - {"taxonid", "publicationid", "validatorid"}:
            _text(meta[name], nullable=True)
    if not isinstance(synonyms, list) or len(synonyms) > MAX_ROWS:
        raise ValueError("Taxonomy reference synonym group population differs")
    valid = set()
    count = 0
    for group in synonyms:
        if (
            not isinstance(group, dict)
            or set(group) != {"valid_id", "valid_name", "taxagroupid", "synonyms"}
            or str(native_id(group["valid_id"])) not in taxa
            or group["valid_id"] in valid
            or not isinstance(group["synonyms"], list)
        ):
            raise ValueError("Taxonomy reference synonym group owner differs")
        valid.add(group["valid_id"])
        _text(group["valid_name"])
        _text(group["taxagroupid"])
        for row in group["synonyms"]:
            count += 1
            if (
                count > MAX_ROWS
                or not isinstance(row, dict)
                or set(row)
                != {
                    "invalid_id",
                    "invalid_name",
                    "synonymtypeid",
                    "synonymtype",
                    "recdatecreated",
                    "recdatemodified",
                }
                or str(native_id(row["invalid_id"])) not in taxa
            ):
                raise ValueError("Taxonomy reference synonym assertion differs")
            _nullable_id(row["synonymtypeid"])
            for name in set(row) - {"invalid_id", "synonymtypeid"}:
                _text(row[name], nullable=True)
    return taxa, metadata, synonyms, generated


def _originals(
    tree: BoundedInputTree, manifest: dict[str, Any], provenance: dict[str, Any]
) -> dict[str, bytes]:
    buffers = {}
    for name in NAMES:
        raw = _read(tree, "originals/" + name, manifest["files"]["originals/" + name])
        if (
            sha1(
                b"blob " + str(len(raw)).encode() + b"\0" + raw, usedforsecurity=False
            ).hexdigest()
            != provenance["originals"][name]["git_blob"]
        ):
            raise ValueError("Taxonomy reference original Git blob identity differs")
        buffers[name] = raw
    return buffers


def read_neotoma_taxonomy_reference_taxa(
    directory: Path, *, expected_manifest_sha256: str, taxon_ids: tuple[int, ...]
) -> tuple[NeotomaTaxonomyReferenceTaxon, ...]:
    """Return selected dated facts; public calls authenticate their own originals."""
    if (
        type(taxon_ids) is not tuple
        or not 0 < len(taxon_ids) <= 10000
        or any(native_id(value) != value for value in taxon_ids)
        or len(set(taxon_ids)) != len(taxon_ids)
    ):
        raise ValueError(
            "Taxonomy reference selection must be an explicit unique ID tuple"
        )
    with _archive(directory, expected_manifest_sha256) as (tree, manifest, provenance):
        taxa, metadata, synonyms, generated = projections(
            _originals(tree, manifest, provenance)
        )
        if generated != provenance["source_generated_at"] or any(
            str(value) not in taxa for value in taxon_ids
        ):
            raise ValueError("Taxonomy reference selected ID or refresh epoch differs")
        assertions: dict[int, list[NeotomaTaxonomySynonymAssertion]] = {}
        selected_ids = set(taxon_ids)
        for position, group in enumerate(synonyms):
            for offset, row in enumerate(group["synonyms"]):
                assertion = NeotomaTaxonomySynonymAssertion(
                    position,
                    offset,
                    group["valid_id"],
                    group["valid_name"],
                    group["taxagroupid"],
                    row,
                )
                for key in {group["valid_id"], row["invalid_id"]} & selected_ids:
                    assertions.setdefault(key, []).append(assertion)
        return tuple(
            NeotomaTaxonomyReferenceTaxon(
                value,
                taxa[str(value)],
                metadata[str(value)],
                tuple(assertions.get(value, ())),
                generated,
                provenance["source_revision"],
            )
            for value in taxon_ids
        )
