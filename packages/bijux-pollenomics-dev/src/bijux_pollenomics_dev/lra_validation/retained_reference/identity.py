"""Authenticate the maintained reference identity and its complete regular bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

from bijux_pollenomics_dev.ci.lra_reference.contracts import ReferenceRefusal
from bijux_pollenomics_dev.ci.lra_reference.evidence import (
    file_inventory,
    validate_bundle,
)
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import (
    SourceCapsule,
    validated_descriptor,
)

PROFILE = Path(__file__).with_name("reference_profile.json")
_BUNDLE_PREFIX = "data/method-certification/source-locked-linux-r/reference-bundle"


class _ReferenceIdentity(dict[str, Any]):
    """Keep the scoped source reader private while public evidence remains plain JSON."""

    def __init__(self, document: dict[str, Any], source: SourceCapsule | None) -> None:
        super().__init__(document)
        self.source = source


def _source_transport(bundle: Path, profile: dict[str, Any]) -> SourceCapsule | None:
    """Only the exact indexed repository bundle may detach historical source bodies."""
    if len(bundle.parents) < 4:
        return None
    repository = bundle.parents[3]
    if repository / _BUNDLE_PREFIX != bundle:
        return None
    members = {
        name: {"sha256": row["sha256"], "bytes": row["byte_count"]}
        for name, row in profile["files"].items()
        if name != "certificate.json"
    }
    try:
        source = validated_descriptor(repository, _BUNDLE_PREFIX, members)
    except ReportRebuildError as error:
        raise ValueError(str(error)) from error
    if source.detached != frozenset(
        {
            "source-domains/r_support.R",
            "source-domains/run_source_domains.py",
            "source-domains/source_domains.R",
            "source-lock.json",
        }
    ):
        raise ValueError("Retained reference source transport population differs")
    return source


def read_member(bundle: Path, name: str, identity: dict[str, Any]) -> bytes:
    """Read only the authenticated member bytes selected for a comparison."""
    source = identity.source if isinstance(identity, _ReferenceIdentity) else None
    if source is not None and name in source.detached:
        try:
            payload = source.read_source(name)
        except ReportRebuildError as error:
            raise ValueError(str(error)) from error
    else:
        path = bundle / name
        if (
            any(member.is_symlink() for member in (path, *path.parents))
            or not path.resolve(strict=True).is_relative_to(bundle.resolve(strict=True))
            or not path.is_file()
        ):
            raise ValueError("Retained comparison member is not confined and regular")
        payload = path.read_bytes()
    if {
        "sha256": hashlib.sha256(payload).hexdigest(),
        "byte_count": len(payload),
    } != identity["files"].get(name):
        raise ValueError("Retained comparison member bytes changed: " + name)
    return payload


def load_profile() -> dict[str, Any]:
    """Load the distinct maintained profile without replacing the canonical reference."""
    profile = json.loads(PROFILE.read_bytes())
    if (
        profile.get("schema_version") != "source-locked-retained-reference.v1"
        or profile.get("required_profiles")
        != {
            "core_source_compatibility": 25,
            "prospective_optimized_love": 18,
            "source_domains_corrected_forward": 23,
        }
        or len(profile.get("files", {})) != 143
    ):
        raise ValueError("Maintained retained reference profile differs")
    for name, row in profile["files"].items():
        path = PurePosixPath(name)
        if (
            path.is_absolute()
            or ".." in path.parts
            or path.as_posix() != name
            or "\\" in name
            or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"])
            or type(row["byte_count"]) is not int
            or row["byte_count"] < 0
        ):
            raise ValueError("Maintained reference member identity differs")
    return dict(profile)


def authenticate_bundle(bundle: Path) -> dict[str, Any]:
    """Require the exact source/runtime/case bundle before consuming any vector."""
    bundle = bundle.absolute()
    if (
        any(path.is_symlink() for path in (bundle, *bundle.parents))
        or not bundle.is_dir()
    ):
        raise ValueError("Retained reference requires a confined regular directory")
    profile = load_profile()
    source_transport = _source_transport(bundle, profile)
    if source_transport is not None:
        try:
            files: dict[str, dict[str, Any]] = file_inventory(
                bundle, source_transport=source_transport
            )
        except (ReportRebuildError, ReferenceRefusal) as error:
            raise ValueError(str(error)) from error
    else:
        files = {}
        for path in sorted(bundle.rglob("*")):
            if path.is_symlink() or not path.resolve(strict=True).is_relative_to(
                bundle
            ):
                raise ValueError("Retained reference member is not confined")
            if path.is_dir():
                continue
            if not path.is_file():
                raise ValueError("Retained reference member is not regular")
            payload = path.read_bytes()
            files[path.relative_to(bundle).as_posix()] = {
                "sha256": hashlib.sha256(payload).hexdigest(),
                "byte_count": len(payload),
            }
    if files != profile["files"]:
        raise ValueError("Retained reference member population or bytes changed")
    certificate = json.loads((bundle / "certificate.json").read_bytes())
    if (
        files["certificate.json"]["sha256"] != profile["certificate_sha256"]
        or certificate["source_commit"] != profile["source_commit"]
        or certificate["source_tree"] != profile["source_tree"]
        or certificate["lock_sha256"] != profile["source_lock_sha256"]
        or certificate["required_profiles"] != profile["required_profiles"]
        or any(
            certificate["r_runtime"].get(key) != value
            for key, value in profile["r_runtime"].items()
        )
    ):
        raise ValueError("Retained certificate source/runtime identity differs")
    validate_bundle(
        bundle,
        target_sha=profile["source_commit"],
        expected_lock_sha256=profile["source_lock_sha256"],
        source_transport=source_transport,
    )
    lock = json.loads(
        read_member(
            bundle,
            "source-lock.json",
            _ReferenceIdentity({"files": files}, source_transport),
        )
    )
    if any(
        lock["reference"].get(key) != profile["public_reference"][key]
        for key in ("package", "version", "sha256")
    ):
        raise ValueError("Public retained reference identity differs")
    return _ReferenceIdentity(
        {
            "reference_id": profile["reference_id"],
            "certificate_sha256": profile["certificate_sha256"],
            "source_commit": profile["source_commit"],
            "source_tree": profile["source_tree"],
            "source_lock_sha256": profile["source_lock_sha256"],
            "public_reference": profile["public_reference"],
            "r_runtime": profile["r_runtime"],
            "files": files,
            "required_profiles": profile["required_profiles"],
        },
        source_transport,
    )
