"""Require synthetic source provenance and content-bound fixture declarations."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics.collection.sources.neotoma.production import (
    load_validated_neotoma_raw_archive,
)
from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from bijux_pollenomics.evidence.sources.neotoma.contract import SURFACE_ID_FIELDS

from ...engine.errors import LRARefusal
from ..models import canonical_bytes
from ..reading import NeotomaEvidence, checked_directory, json_object


def synthetic_origin(evidence: NeotomaEvidence) -> str:
    """The raw snapshot itself must bind every synthetic-origin declaration."""
    manifest = json_object((evidence.raw_root / "manifest.json").read_bytes())
    fixture = manifest.get("synthetic_fixture_id")
    if not isinstance(fixture, str) or not fixture or fixture != fixture.strip():
        raise LRARefusal(
            "synthetic_source_origin_required", "Raw fixture identity absent"
        )
    documents = [manifest]
    documents.extend(
        json_object((evidence.raw_root / part["filename"]).read_bytes())
        for part in manifest["parts"]
    )
    if any(
        row.get("data_kind") != "synthetic"
        or row.get("synthetic_fixture_id") != fixture
        for row in documents
    ):
        raise LRARefusal(
            "synthetic_source_origin_required",
            "Every raw receipt must declare the same synthetic fixture origin",
        )
    return fixture


def verify_raw_projection(evidence: NeotomaEvidence) -> dict[str, Any]:
    """Replay the existing source producer; hashes alone do not prove derivation.

    Country inputs belong to the marked raw fixture declaration. Reading them
    back from normalized rows would let those rows authorize their own lineage.
    String country inputs retain the existing producer's review-blocked posture;
    this function never manufactures a boundary attribution decision.
    """
    manifest = evidence.manifest()
    raw = json_object((evidence.raw_root / "manifest.json").read_bytes())
    countries = raw.get("synthetic_country_by_site_id")
    if not isinstance(countries, dict) or any(
        not isinstance(key, str)
        or not key
        or not isinstance(value, str)
        or value not in {"SE", "DK", "NO", "FI", "UNASSIGNED"}
        for key, value in countries.items()
    ):
        raise LRARefusal(
            "synthetic_country_inputs_required",
            "Raw fixture must declare its complete country-input mapping",
        )
    rows, source_id = load_validated_neotoma_raw_archive(evidence.raw_root)
    if source_id != manifest["source_snapshot_id"]:
        raise LRARefusal(
            "raw_snapshot_binding_mismatch", "Raw snapshot changed before replay"
        )
    replay = build_neotoma_relational_snapshot(
        rows,
        source_snapshot_id=source_id,
        build_id=manifest["build_id"],
        country_by_site_id=countries,
    )
    sites = cast(list[dict[str, Any]], replay["sites"])
    if set(countries) != {str(row["source_site_id"]) for row in sites}:
        raise LRARefusal(
            "synthetic_country_inventory_mismatch",
            "Country inputs must cover exact source sites",
        )
    surfaces = {}
    for surface in SURFACE_ID_FIELDS:
        expected = replay[surface]
        observed = [row.payload() for row in evidence.rows(surface)]
        encoded = canonical_bytes(expected)
        if canonical_bytes(observed) != encoded:
            raise LRARefusal("source_projection_replay_mismatch", surface)
        surfaces[surface] = {
            "row_count": len(observed),
            "canonical_rows_sha256": hashlib.sha256(encoded).hexdigest(),
        }
    reconciliation = json_object(
        (evidence.normalized_root / manifest["reconciliation"]["path"]).read_bytes()
    )["reconciliation"]
    if canonical_bytes(reconciliation) != canonical_bytes(replay["reconciliation"]):
        raise LRARefusal("source_projection_replay_mismatch", "reconciliation")
    evidence.assert_unchanged()
    return {
        "status": "exact_source_replay_match",
        "producer": "build_neotoma_relational_snapshot",
        "source_snapshot_id": source_id,
        "country_input_sha256": hashlib.sha256(canonical_bytes(countries)).hexdigest(),
        "surfaces": surfaces,
        "reconciliation_sha256": hashlib.sha256(
            canonical_bytes(reconciliation)
        ).hexdigest(),
    }


def evidence_files(
    template: dict[str, Any], input_root: Path
) -> tuple[Path, dict[str, tuple[str, bytes]]]:
    root = checked_directory(input_root)
    files: dict[str, tuple[str, bytes]] = {}
    for item in template.get("evidence", []):
        relative = Path(item["path"])
        path = root / relative
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or any(parent.is_symlink() for parent in (path, *path.parents))
            or not path.is_file()
        ):
            raise LRARefusal("invalid_projection_evidence_path", str(relative))
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != item["sha256"]:
            raise LRARefusal("evidence_digest_mismatch", item["evidence_id"])
        if item["evidence_id"] in files:
            raise LRARefusal("duplicate_evidence_id", item["evidence_id"])
        files[item["evidence_id"]] = (relative.as_posix(), content)
    return root, files


def verify_declarations(
    template: dict[str, Any], files: dict[str, tuple[str, bytes]], fixture: str
) -> None:
    expected = {
        "taxa": template["taxa"],
        "parameters": template["parameters"],
        "geometry": {
            "basins": {
                role: template[role]["basin"]
                for role in ("regional", "local")
                if role in template
            },
            "rings": template.get("rings", []),
        },
        "decision": template["temporal_matching"],
    }
    for role, values in expected.items():
        entries = [item for item in template["evidence"] if item["role"] == role]
        if len(entries) != 1:
            raise LRARefusal("ambiguous_fixture_declaration", role)
        document = json_object(files[entries[0]["evidence_id"]][1])
        if (
            document.get("data_kind") != "synthetic"
            or document.get("synthetic_fixture_id") != fixture
            or canonical_bytes(document.get("declared_values"))
            != canonical_bytes(values)
        ):
            raise LRARefusal("fixture_declaration_mismatch", role)
        if role == "parameters" and any(
            not isinstance(document.get(field), str) or not document[field].strip()
            for field in (
                "reference_taxon",
                "normalization",
                "parameter_domain",
                "citation",
            )
        ):
            raise LRARefusal("incomplete_fixture_parameter_provenance", role)


def assert_files_unchanged(root: Path, files: dict[str, tuple[str, bytes]]) -> None:
    for relative, content in files.values():
        path = root / relative
        if (
            any(parent.is_symlink() for parent in (path, *path.parents))
            or path.read_bytes() != content
        ):
            raise LRARefusal("projection_evidence_changed", relative)
