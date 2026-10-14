"""Authenticate one named two-site operational URL transition, with no data waiver."""

from __future__ import annotations

import copy
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
from typing import Any

CERTIFICATE = "data/neotoma/source-selection-reference/selection-custody.json"
CERTIFICATE_SHA256 = "a1e77040087e80b35f458a9033a97b237636f302db2a6ebad887de7032df08dd"
EXPECTED_EXPORTS = (
    (
        "12",
        "8284262561d27ad8d1d49c5561ef60c1a3a6c884f55d547db60640ef3d893780",
        "5b7b6db1b2f21878807f33fe1f008e760099f15afa0aa64c704f5ff142e5ae8f",
    ),
    (
        "3009",
        "e6f66cf65da67d3d4a701de51d1500e0f670fb849c6f59c032eb1c41a6011647",
        "83a18e2b5955023fdfad5d76f4cc6af7e8c6fdeed019525caf56785e7ebf2b58",
    ),
)


def _hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key in export custody")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ValueError("Nonfinite JSON value in export custody: " + value)


def _object(raw: bytes) -> dict[str, Any]:
    value: Any = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
    if not isinstance(value, dict):
        raise ValueError("Export custody requires a JSON object")
    json.dumps(value, allow_nan=False)
    return value


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode()


def _file(repository: Path, relative: str) -> Path:
    rel = PurePosixPath(relative)
    if rel.is_absolute() or ".." in rel.parts or rel.as_posix() != relative:
        raise ValueError("Export custody path escapes repository")
    path = repository / relative
    if (
        not path.is_file()
        or any(
            p.is_symlink()
            for p in [path, *path.parents]
            if p.is_relative_to(repository)
        )
        or path.resolve() != path
    ):
        raise ValueError("Export custody requires confined regular files")
    return path


def _reference(
    repository: Path,
    path: str,
    storage_sha256: str,
    content_sha256: str,
    content_bytes: int,
) -> bytes:
    stored = _file(repository, path).read_bytes()
    if (
        _hash(stored) != storage_sha256
        or type(content_bytes) is not int
        or not 0 < content_bytes <= 5 * 1024**2
    ):
        raise ValueError("Export reference storage identity/work bound differs")
    with gzip.GzipFile(fileobj=io.BytesIO(stored)) as stream:
        raw = stream.read(content_bytes + 1)
    if len(raw) != content_bytes or _hash(raw) != content_sha256:
        raise ValueError("Export reference original bytes differ")
    return raw


def validate_selection_transition(
    reference: dict[str, Any],
    exported: dict[str, Any],
    reference_url: str,
    export_url: str,
) -> str:
    """Permit the one declared leaf; preserve types, fields, objects and array order."""
    original = copy.deepcopy(reference)
    current = copy.deepcopy(exported)
    if not isinstance(original.get("selection"), dict) or not isinstance(
        current.get("selection"), dict
    ):
        raise ValueError("Export selection object missing")
    if (
        original["selection"].get("shared_url") != reference_url
        or current["selection"].get("shared_url") != export_url
        or not isinstance(reference_url, str)
        or not isinstance(export_url, str)
        or reference_url == export_url
    ):
        raise ValueError("Named shared URL transition differs")
    original["selection"]["shared_url"] = None
    current["selection"]["shared_url"] = None
    if _canonical(original) != _canonical(current):
        raise ValueError("Export changed outside /selection/shared_url")
    return _hash(_canonical(original))


def validate_neotoma_export_custody(repository: Path) -> None:
    """Bind original physical exports, current captured exports and native manifest."""
    if not repository.is_absolute() or repository.resolve(strict=True) != repository:
        raise ValueError("Real absolute repository required")
    certificate_raw = _file(repository, CERTIFICATE).read_bytes()
    if _hash(certificate_raw) != CERTIFICATE_SHA256:
        raise ValueError("Named Neotoma export custody certificate differs")
    proof = _object(certificate_raw)
    if (
        proof["schema_version"] != "neotoma-export-selection-custody.v1"
        or tuple(
            (row["site_id"], row["reference_sha256"], row["export_sha256"])
            for row in proof["exports"]
        )
        != EXPECTED_EXPORTS
    ):
        raise ValueError("Named two-export scope differs")
    manifest = proof["source_manifest"]
    if _hash(_file(repository, manifest["path"]).read_bytes()) != manifest["sha256"]:
        raise ValueError("Original native manifest differs")
    capture_ref = proof["browser_capture"]
    capture_raw = _file(repository, capture_ref["path"]).read_bytes()
    if _hash(capture_raw) != capture_ref["sha256"]:
        raise ValueError("Current physical browser capture differs")
    capture = _object(capture_raw)
    if (
        capture["source_candidate"] != capture_ref["source_candidate"]
        or capture["scientific_admission"] is not False
    ):
        raise ValueError("Browser capture source/admission differs")
    members = {row["path"]: row for row in capture["files"]}
    for row in proof["exports"]:
        original = _reference(
            repository,
            row["reference_path"],
            row["reference_storage_sha256"],
            row["reference_sha256"],
            row["content_bytes"],
        )
        current = _file(repository, row["export_path"]).read_bytes()
        member = members[row["captured_member"]]
        captured = _file(
            repository,
            str(PurePosixPath(capture_ref["path"]).parent / row["captured_member"]),
        ).read_bytes()
        if (
            _hash(current) != row["export_sha256"]
            or current != captured
            or _hash(captured) != member["sha256"]
            or len(captured) != member["bytes"]
        ):
            raise ValueError("Named current/captured export bytes differ")
        if (
            validate_selection_transition(
                _object(original),
                _object(current),
                row["reference_shared_url"],
                row["export_shared_url"],
            )
            != row["all_other_ordered_json_sha256"]
        ):
            raise ValueError("Original non-URL export fields differ")


def validate_retained_readiness(repository: Path, report: dict[str, Any]) -> None:
    """Prove every readiness field is unchanged apart from the two actual digests."""
    validate_neotoma_export_custody(repository)
    proof = _object(_file(repository, CERTIFICATE).read_bytes())
    reference = proof["reference_readiness_report"]
    original = _object(
        _reference(
            repository,
            reference["path"],
            reference["storage_sha256"],
            reference["content_sha256"],
            reference["content_bytes"],
        )
    )
    validate_readiness_transition(original, report)


def validate_readiness_transition(
    reference: dict[str, Any], report: dict[str, Any]
) -> None:
    """Permit exactly the two known metadata digests, never any scientific change."""
    original = copy.deepcopy(reference)
    for site, before, after in EXPECTED_EXPORTS:
        if (
            original["source_identity"]["export_sha256"][site] != before
            or report["source_identity"]["export_sha256"][site] != after
        ):
            raise ValueError("Readiness export identity differs from named custody")
        original["source_identity"]["export_sha256"][site] = after
    if _canonical(original) != _canonical(report):
        raise ValueError(
            "Native readiness science changed outside the two export digests"
        )
