"""Consume one separately retained, source-locked Linux reference packet."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .identity import PROFILE, authenticate_bundle

PACKET = "data/method-certification/source-locked-linux-r"
_MANIFEST_SHA256 = "5380e1ca4ff6cb240afe80659ed0a89eedda1d869689919f5a49cc15dc48d0c7"
_PROFILE_SHA256 = "308251ed20fe9e8f30bf2b5d2f2a9248648dc5bcc05ad3d89d47a20b23dd889d"


def _read(path: Path) -> bytes:
    """Retained packet inputs must be physical, independently owned source files."""
    if (
        any(member.is_symlink() for member in (path, *path.parents))
        or not path.is_file()
        or path.stat().st_nlink != 1
    ):
        raise ValueError("Repository reference source must be regular and independent")
    return path.read_bytes()


def _snapshot(repository: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    packet = repository.absolute() / PACKET
    manifest = _read(packet / "source.json")
    if hashlib.sha256(manifest).hexdigest() != _MANIFEST_SHA256:
        raise ValueError("Repository reference source manifest changed")
    if hashlib.sha256(_read(PROFILE)).hexdigest() != _PROFILE_SHA256:
        raise ValueError("Repository reference profile changed")
    source = json.loads(manifest)
    if {path.name for path in packet.iterdir()} != {
        "source.json",
        "reference-bundle",
        *source["authority_files"],
    }:
        raise ValueError("Repository reference packet population changed")
    captured = {"source.json": manifest}
    for name, expected in source["authority_files"].items():
        payload = _read(packet / name)
        if hashlib.sha256(payload).hexdigest() != expected:
            raise ValueError("Repository reference recovery authority changed")
        captured[name] = payload
    for path in (packet / "reference-bundle").rglob("*"):
        if not path.is_dir() or path.is_symlink():
            _read(path)
    return source, captured


def authenticate_repository_reference(repository: Path) -> dict[str, Any]:
    """Authenticate retained bytes without running current calculations or native R."""
    source, before = _snapshot(repository)
    bundle = repository.absolute() / PACKET / "reference-bundle"
    accepted = authenticate_bundle(bundle)
    certificate = json.loads(_read(bundle / "certificate.json"))
    if (
        accepted["certificate_sha256"] != source["certificate_sha256"]
        or accepted["source_commit"] != source["source_commit"]
        or accepted["source_tree"] != source["source_tree"]
        or len(certificate["source_files"]) != source["recorded_tracked_source_count"]
        or set(certificate["source_files"]) != set(certificate["tracked_git_blobs"])
        or len(certificate["generated_source_files"])
        != source["separate_generated_version_count"]
        or len(accepted["files"]) != source["member_count"]
        or sum(row["byte_count"] for row in accepted["files"].values())
        != source["member_bytes"]
    ):
        raise ValueError("Repository reference recorded source authority differs")
    if (
        _snapshot(repository) != (source, before)
        or authenticate_bundle(bundle) != accepted
    ):
        raise ValueError("Repository reference source changed during authentication")
    return {
        **accepted,
        "source_packet_manifest_sha256": _MANIFEST_SHA256,
        "retained_qualification": source["qualification"],
        "historical_boundary": source["historical_boundary"],
    }


def repository_reference_bundle(repository: Path) -> Path:
    """Select only the fixed repository packet for the existing comparison consumer."""
    authenticate_repository_reference(repository)
    return repository.absolute() / PACKET / "reference-bundle"
