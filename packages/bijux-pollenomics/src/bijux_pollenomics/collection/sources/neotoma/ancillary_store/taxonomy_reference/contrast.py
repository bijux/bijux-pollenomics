"""Compare explicitly stored frontier leads with dated global reference fields."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import (
    BoundedInputTree,
    DirectoryAnchor,
    OwnedTreeWriter,
    read_regular_file,
)
from bijux_pollenomics.core.owned_tree import build_staging_output_dir

from ...capture.linked_resources.ancestry import storage
from ...capture.linked_resources.ancestry.chain.models import COLLECTIONS, SCHEMA
from ...capture.linked_resources.ancestry.models import MAX_BYTES as CHAIN_MAX_BYTES
from ...capture.linked_resources.ancestry.models import MAX_PARTS
from ...publication.ownership import publish_owned_source_tree
from ...resource_catalogue.archive.files import encoded_json
from .contracts import (
    MAX_BYTES,
    NeotomaTaxonomyReferenceContrast,
    digest,
    native_id,
)
from .reading import _archive, _originals, projections


def plain(value: Any) -> Any:
    """Serialize only detached typed reference results as ordinary JSON values."""
    from collections.abc import Mapping

    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: plain(getattr(value, field.name)) for field in fields(value)
        }
    if isinstance(value, Mapping):
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(item) for item in value]
    return value


def _recorded(row: Any) -> dict[str, Any]:
    if (
        not isinstance(row, dict)
        or type(row.get("target_kind")) is not str
        or row.get("target_kind") not in {"taxon", "publication"}
        or row.get("target_key")
        != f"{row['target_kind']}-{native_id(row.get('native_id'))}"
        or row.get("GET_authorized") is not False
        or row.get("scientific_admission") != "not_asserted"
        or not isinstance(row.get("current_root_dataset_ids"), list)
        or any(native_id(value) != value for value in row["current_root_dataset_ids"])
        or row["current_root_dataset_ids"]
        != sorted(set(row["current_root_dataset_ids"]))
        or type(row.get("current_use_role")) is not str
        or type(row.get("status")) is not str
    ):
        raise ValueError("Recorded frontier identity, roots or source posture differs")
    # Preserve selected recorded witness facts; do not forward arbitrary source
    # fields, source-body paths or newly asserted current verification flags.
    result = {
        name: row[name]
        for name in (
            "target_key",
            "target_kind",
            "native_id",
            "current_root_dataset_ids",
            "current_use_role",
            "status",
        )
    }
    if "additional_parent_hops_from_seed" in row:
        value = row["additional_parent_hops_from_seed"]
        if value is not None and (type(value) is not int or value < 0):
            raise ValueError("Recorded frontier hop count differs")
        result["additional_parent_hops_from_seed"] = value
    return result


def _references(metadata: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, dict[tuple[Any, ...], list[int]]] = {}
    for row in metadata.values():
        identity = row["publicationid"]
        if identity is not None:
            key = row["publication"], row["citation"], row["publicationYear"]
            grouped.setdefault(identity, {}).setdefault(key, []).append(row["taxonid"])
    return {
        identity: [
            {
                "publicationid": identity,
                "publication": key[0],
                "citation": key[1],
                "publicationYear": key[2],
                "source_taxon_ids": sorted(identities),
            }
            for key, identities in sorted(
                variants.items(), key=lambda item: encoded_json(item[0])
            )
        ]
        for identity, variants in grouped.items()
    }


@contextmanager
def _comparison(
    directory: Path, anchor: str, chain_directory: Path, chain_anchor: str
) -> Iterator[tuple[NeotomaTaxonomyReferenceContrast, Any]]:
    if not digest(chain_anchor):
        raise ValueError("Independent recorded frontier manifest anchor required")
    with (
        _archive(directory, anchor) as (reference_tree, manifest, provenance),
        BoundedInputTree(
            chain_directory, max_bytes=CHAIN_MAX_BYTES, max_files=MAX_PARTS + 1
        ) as chain,
    ):
        header = storage._manifest(
            chain.root, chain_anchor, collections=COLLECTIONS, schema=SCHEMA
        )
        if set(chain.files) != {
            "manifest.json",
            *(part["path"] for part in header["parts"]),
        }:
            raise ValueError("Recorded frontier closed namespace differs")
        selected = [
            part for part in header["parts"] if part["collection"] == "frontier"
        ]
        if not selected:
            raise ValueError(
                "No explicitly stored frontier; delta inheritance is not inferred"
            )
        frontier: list[tuple[dict[str, Any], dict[str, Any]]] = []
        seen = set()
        for part in selected:
            for offset, value in enumerate(
                storage._part(chain.root, part, schema=SCHEMA)
            ):
                recorded = _recorded(value)
                if recorded["target_key"] in seen or len(frontier) >= 10000:
                    raise ValueError(
                        "Recorded frontier target population is duplicated or oversized"
                    )
                seen.add(recorded["target_key"])
                frontier.append(
                    (recorded, {"part_sha256": part["sha256"], "row_offset": offset})
                )
        captures = header.get("new_capture_manifest_sha256s")
        if (
            not isinstance(captures, list)
            or len(captures) > 10000
            or any(not digest(value) for value in captures)
            or len(set(captures)) != len(captures)
        ):
            raise ValueError("Recorded frontier capture-epoch pointers differ")
        if header.get("scientific_admission") != "not_asserted":
            raise ValueError("Recorded frontier scientific posture differs")
        chain.check()
        taxa, metadata, _, generated = projections(
            _originals(reference_tree, manifest, provenance)
        )
        if generated != provenance["source_generated_at"]:
            raise ValueError("Dated reference refresh epoch differs")
        references = _references(metadata)
        rows = []
        for recorded, position in frontier:
            kind, identity = recorded["target_kind"], recorded["native_id"]
            variants = references.get(identity, []) if kind == "publication" else []
            taxon = (
                {"taxon": taxa[str(identity)], "metadata": metadata[str(identity)]}
                if kind == "taxon" and str(identity) in taxa
                else None
            )
            outcome = "not_observed_in_reference_projection"
            if taxon is not None:
                outcome = "dated_taxon_lookup_available"
            elif variants:
                if any(row["citation"] for row in variants):
                    outcome = "classification_citation_text_available"
                elif any(row["publication"] for row in variants):
                    outcome = "classification_publication_fallback_only"
                else:
                    outcome = "observed_publication_id_only"
            rows.append(
                {
                    "target_key": recorded["target_key"],
                    "target_kind": kind,
                    "native_id": identity,
                    "recorded_frontier": recorded,
                    "recorded_frontier_position": position,
                    "outcome": outcome,
                    "reference_taxon": taxon,
                    "classification_references": variants,
                }
            )
        outcomes = Counter(row["outcome"] for row in rows)
        summary = {
            "frozen_frontier_rows": len(rows),
            "taxon_targets": sum(row["target_kind"] == "taxon" for row in rows),
            "publication_targets": sum(
                row["target_kind"] == "publication" for row in rows
            ),
            "dated_taxon_matches": outcomes["dated_taxon_lookup_available"],
            "citation_text_available_targets": outcomes[
                "classification_citation_text_available"
            ],
            "publication_fallback_only_targets": outcomes[
                "classification_publication_fallback_only"
            ],
            "publication_id_only_targets": outcomes["observed_publication_id_only"],
            "unmatched_targets": outcomes["not_observed_in_reference_projection"],
        }
        result = NeotomaTaxonomyReferenceContrast(
            anchor,
            chain_anchor,
            provenance["source_revision"],
            generated,
            tuple(rows),
            summary,
            tuple(captures),
            provenance["commit_utc"],
            {
                name: (row["intake_start"], row["intake_end"])
                for name, row in provenance["transport"].items()
            },
        )

        def check() -> None:
            reference_tree.check()
            chain.check()

        check()
        yield result, check
        check()


def contrast_neotoma_taxonomy_reference_frontier(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    chain_directory: Path,
    expected_chain_manifest_sha256: str,
) -> NeotomaTaxonomyReferenceContrast:
    """Contrast stored leads only; absent reference IDs do not certify live absence."""
    with _comparison(
        directory,
        expected_manifest_sha256,
        chain_directory,
        expected_chain_manifest_sha256,
    ) as (result, _):
        return result


def write_neotoma_taxonomy_reference_contrast(
    directory: Path,
    *,
    reference_directory: Path,
    expected_manifest_sha256: str,
    chain_directory: Path,
    expected_chain_manifest_sha256: str,
) -> NeotomaTaxonomyReferenceContrast:
    """Publish a finite recorded contrast while original input/output seals remain live."""
    final = Path(directory).absolute()
    if final.exists():
        raise FileExistsError(final)
    with (
        DirectoryAnchor(final.parent) as parent,
        _comparison(
            reference_directory,
            expected_manifest_sha256,
            chain_directory,
            expected_chain_manifest_sha256,
        ) as (result, check),
    ):
        raw = encoded_json(plain(result))
        if len(raw) > MAX_BYTES:
            raise ValueError("Taxonomy reference contrast exceeds its byte bound")
        parent.check()
        staging = build_staging_output_dir(final)
        with OwnedTreeWriter(staging, max_bytes=MAX_BYTES, max_files=1) as writer:
            writer.write_bytes("frontier-contrast.json", raw)

            def validate(location: Path) -> None:
                parent.check()
                check()
                if (
                    read_regular_file(
                        location / "frontier-contrast.json", max_bytes=len(raw)
                    )
                    != raw
                ):
                    raise ValueError("Taxonomy reference contrast readback differs")
                check()
                parent.check()

            publish_owned_source_tree(
                writer, staging=staging, final=final, validate=validate
            )
        return result
