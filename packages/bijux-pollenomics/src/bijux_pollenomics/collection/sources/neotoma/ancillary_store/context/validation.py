"""Authenticate ancillary context evidence without opening numerical native entities."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import validate_regular_namespace

from ...capture.facets.models import NeotomaFacetScopeInputs
from ...capture.parent_scope import _roster
from ...capture.receipts import _object, _read, _safe_root
from ...resource_catalogue.archive.files import _digest
from ...resource_catalogue.archive.inventory import read_archive_inventory
from ...resource_catalogue.archive.original_metadata import metadata_inventory
from ...resource_catalogue.publication import load_neotoma_resource_catalogue
from ...resource_catalogue.source_projection import _same

SCHEMA = "neotoma-ancillary-source-context.v1"
MAX_BYTES = 512 * 1024 * 1024
MAX_FILES = 20000
MAX_MEMBER_BYTES = 16 * 1024 * 1024
_FIELDS = {
    "schema_version",
    "native_archive",
    "exposure_authority",
    "legacy_rosters",
    "files",
    "source_bytes",
    "scientific_admission",
    "native_body_copies",
    "current_scope_verification",
    "pre_get_scope_reconstructed",
    "historical_snapshot_replaced",
}
_LEGACY_SCOPE = {
    "parent_scope_verification": "not_recorded_legacy_capture",
    "use_scope": "original_capture_identity_only",
}


@dataclass(frozen=True)
class NeotomaAncillaryContext:
    """Pinned resolvers, not replayed parent obligations or scientific approval."""

    manifest: dict[str, Any]
    current_scope_inputs: dict[str, NeotomaFacetScopeInputs]
    legacy_rosters: dict[str, Path]


def native_context(
    directory: Path, digest: str
) -> tuple[dict[str, Any], Path, dict[str, Path], dict[str, Path]]:
    """Resolve only source-declared metadata dependencies inside the native archive."""
    native = read_archive_inventory(directory, expected_manifest_sha256=digest)
    catalogue_pin = native.manifest["catalogue_manifest_sha256"]
    catalogue = load_neotoma_resource_catalogue(
        native.root / "catalogue", expected_manifest_sha256=catalogue_pin
    )
    current_pin = catalogue["expected_roster_sha256"]
    current_path = native.root / "catalogue/source-inventory.json"
    roster = _roster(current_path, current_pin)
    required = roster.get("source_metadata_capture_manifest_sha256")
    if (
        not isinstance(required, list)
        or not required
        or not all(_digest(x) for x in required)
    ):
        raise ValueError("Ancillary context metadata source declarations are malformed")
    required = set(required)
    historical_required = set()
    for row in roster["resources"]:
        lookup = row.get("current_metadata_lookup")
        if lookup is not None:
            if not isinstance(lookup, dict) or not _digest(
                lookup.get("manifest_sha256")
            ):
                raise ValueError("Ancillary context metadata lookup is malformed")
            required.add(lookup["manifest_sha256"])
        locator = row.get("metadata_locator")
        if (
            isinstance(locator, dict)
            and locator.get("source_kind")
            == "retained_relational_dataset_metadata_not_current_HTTP"
        ):
            if not _digest(locator.get("response_sha256")):
                raise ValueError(
                    "Ancillary context historical metadata identity is malformed"
                )
            historical_required.add(locator["response_sha256"])
    descriptors = catalogue["capture_descriptors"]
    if any(
        pin not in native.capture_sources
        or descriptors[pin]["capture_kind"] != "metadata"
        for pin in required
    ):
        raise ValueError("Ancillary context metadata resolver closure is incomplete")
    historical: dict[str, Path] = {}
    original_pin = None
    if historical_required:
        if native.original_relational_root is None:
            raise ValueError(
                "Ancillary context historical metadata resolver is incomplete"
            )
        original, members = metadata_inventory(native.original_relational_root)
        if not _same(original, native.manifest["original_metadata"]):
            raise ValueError("Ancillary context original metadata witness differs")
        original_pin = original["manifest_sha256"]
        historical = {
            pin: native.original_relational_root / relative
            for relative, pin in members.items()
            if relative != "manifest.json" and pin in historical_required
        }
        if set(historical) != historical_required:
            raise ValueError(
                "Ancillary context historical metadata resolver is incomplete"
            )
    claim = {
        "manifest_sha256": digest,
        "catalogue_manifest_sha256": catalogue_pin,
        "current_roster_sha256": current_pin,
        "metadata_capture_manifest_sha256s": sorted(required),
        "historical_metadata_part_sha256s": sorted(historical_required),
        "original_relational_manifest_sha256": original_pin,
        "reviewed_exposure_metadata_sha256": roster.get(
            "reviewed_exposure_metadata_sha256"
        ),
    }
    return (
        claim,
        current_path,
        {pin: native.capture_sources[pin] for pin in sorted(required)},
        historical,
    )


def evidence_member(content: bytes, digest: str, relative: str) -> dict[str, Any]:
    """Bind copied original bytes, never a reconstructed JSON serialization."""
    if not _digest(digest) or sha256(content).hexdigest() != digest:
        raise ValueError("Ancillary context evidence identity differs")
    _object(content)
    return {"path": relative, "sha256": digest, "bytes": len(content)}


def load_neotoma_ancillary_context(
    directory: Path, *, expected_manifest_sha256: str, native_archive_directory: Path
) -> NeotomaAncillaryContext:
    """Authenticate a closed context and its independently pinned native foundation."""
    root = _safe_root(directory)
    raw = _read(root / "manifest.json", MAX_MEMBER_BYTES)
    if sha256(raw).hexdigest() != expected_manifest_sha256:
        raise ValueError("Ancillary context manifest identity differs")
    manifest = _object(raw)
    if (
        set(manifest) != _FIELDS
        or manifest["schema_version"] != SCHEMA
        or manifest["scientific_admission"] != "not_asserted"
        or type(manifest["native_body_copies"]) is not int
        or manifest["native_body_copies"] != 0
        or manifest["current_scope_verification"]
        != "resolver_identity_only_parent_obligations_not_replayed"
        or manifest["pre_get_scope_reconstructed"] is not False
        or manifest["historical_snapshot_replaced"] is not False
        or not isinstance(manifest["files"], dict)
        or not isinstance(manifest["legacy_rosters"], dict)
        or not manifest["legacy_rosters"]
        or len(manifest["files"]) + 1 > MAX_FILES
        or type(manifest["source_bytes"]) is not int
    ):
        raise ValueError("Ancillary context schema or scientific claims differ")
    authority = manifest["exposure_authority"]
    if (
        not isinstance(authority, dict)
        or set(authority) != {"path", "sha256", "bytes"}
        or not _digest(authority.get("sha256"))
    ):
        raise ValueError("Ancillary context exposure authority identity is malformed")
    expected = {f"evidence/exposure/{authority['sha256']}.json": authority}
    legacy_paths: dict[str, Path] = {}
    for pin, member in manifest["legacy_rosters"].items():
        if (
            not _digest(pin)
            or not isinstance(member, dict)
            or set(member) != {"path", "sha256", "bytes", *_LEGACY_SCOPE}
            or any(member[key] != value for key, value in _LEGACY_SCOPE.items())
        ):
            raise ValueError("Ancillary context legacy identity or use scope differs")
        relative = f"rosters/{pin}.json"
        if member.get("sha256") != pin:
            raise ValueError("Ancillary context legacy roster identity differs")
        expected[relative] = {key: member[key] for key in ("path", "sha256", "bytes")}
        legacy_paths[pin] = root / relative
    expected_files = {}
    for relative, member in expected.items():
        if (
            member["path"] != relative
            or type(member["bytes"]) is not int
            or not 0 <= member["bytes"] <= MAX_MEMBER_BYTES
        ):
            raise ValueError("Ancillary context evidence member is malformed")
        expected_files[relative] = {key: member[key] for key in ("sha256", "bytes")}
    if (
        not _same(manifest["files"], expected_files)
        or manifest["source_bytes"]
        != sum(member["bytes"] for member in expected_files.values())
        or manifest["source_bytes"] + len(raw) > MAX_BYTES
    ):
        raise ValueError("Ancillary context file or byte population differs")
    sizes = validate_regular_namespace(
        root,
        {"manifest.json", *expected_files},
        max_files=MAX_FILES,
        max_bytes=MAX_BYTES,
    )
    for relative, member in expected_files.items():
        if sizes[relative] != member["bytes"]:
            raise ValueError("Ancillary context evidence size differs")
        if relative.startswith("rosters/"):
            _roster(root / relative, member["sha256"])
        else:
            evidence_member(
                _read(root / relative, member["bytes"]), member["sha256"], relative
            )
    native = manifest["native_archive"]
    if not isinstance(native, dict) or not _digest(native.get("manifest_sha256")):
        raise ValueError("Ancillary context native foundation is malformed")
    claim, current, captures, historical = native_context(
        native_archive_directory, native["manifest_sha256"]
    )
    if not _same(claim, native) or claim["reviewed_exposure_metadata_sha256"] not in (
        None,
        authority["sha256"],
    ):
        raise ValueError(
            "Ancillary context native foundation or exposure authority differs"
        )
    return NeotomaAncillaryContext(
        manifest,
        {
            claim["current_roster_sha256"]: NeotomaFacetScopeInputs(
                current,
                captures,
                historical,
                root / authority["path"]
                if claim["reviewed_exposure_metadata_sha256"] is not None
                else None,
            )
        },
        legacy_paths,
    )
