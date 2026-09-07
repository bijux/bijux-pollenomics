"""Repository materialization service for compact AADR accountability."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import md5, sha256
import json
import os
from pathlib import Path, PurePosixPath
import re

from bijux_pollenomics.adna.species.homo_sapiens.materialization.reconciliation import (
    reconcile_aadr_panels,
)
from bijux_pollenomics.adna.species.homo_sapiens.release_manifest import (
    validate_release_manifest_identity,
)

from ..source_rows import load_aadr_source_table
from .models import AadrReleaseManifestIdentity
from .projection import build_aadr_source_accountability_receipt
from .publication import write_aadr_source_accountability_receipt
from .validation import validate_aadr_source_accountability_receipt

_MANIFEST_NAME = "release_manifest.json"
_REPOSITORY_DATA_IDENTITY = "data"


@dataclass(frozen=True, slots=True)
class AadrSourceAccountabilityMaterialization:
    """Identity and content of one published compact accountability receipt."""

    output_path: Path
    receipt: Mapping[str, object]
    byte_count: int
    sha256: str


@dataclass(frozen=True, slots=True)
class _AadrPanelInput:
    dataset_name: str
    filename: str
    physical_path: Path
    expected_byte_count: int
    expected_md5: str


def materialize_aadr_source_accountability(
    data_root: Path,
    version: str,
) -> AadrSourceAccountabilityMaterialization:
    """Validate one governed AADR release and publish its compact receipt."""
    source_release = _validate_release_version(version)
    root = Path(data_root)
    _validate_data_root(root)
    release_dir = root / "aadr" / source_release
    manifest_path = release_dir / _MANIFEST_NAME
    manifest_bytes = _read_governed_file(
        manifest_path,
        governed_root=root,
        label="AADR release manifest",
    )
    manifest_payload = _decode_manifest(manifest_bytes)

    panel_inventory = _validated_panel_inventory(
        manifest_payload,
        release_dir=release_dir,
    )
    panel_sha256 = {
        panel.physical_path: _validate_panel_snapshot(panel, governed_root=root)
        for panel in panel_inventory
    }
    validate_release_manifest_identity(manifest_payload, release_dir)
    source_tables = tuple(
        load_aadr_source_table(
            panel.physical_path,
            source_release=source_release,
            dataset_name=panel.dataset_name,
            logical_source_path=(
                f"{_REPOSITORY_DATA_IDENTITY}/aadr/{source_release}/"
                f"{panel.dataset_name}/{panel.filename}"
            ),
            expected_sha256=panel_sha256[panel.physical_path],
        )
        for panel in panel_inventory
    )
    reconciliation = reconcile_aadr_panels(source_tables)
    receipt = build_aadr_source_accountability_receipt(
        reconciliation,
        release_manifest=AadrReleaseManifestIdentity(
            logical_path=(
                f"{_REPOSITORY_DATA_IDENTITY}/aadr/{source_release}/{_MANIFEST_NAME}"
            ),
            source_release=source_release,
            sha256=sha256(manifest_bytes).hexdigest(),
            byte_count=len(manifest_bytes),
        ),
    )
    validate_aadr_source_accountability_receipt(receipt)

    output_path = (
        root
        / "adna"
        / "species"
        / "homo_sapiens"
        / "review"
        / f"aadr_{source_release}_source_accountability.json"
    )
    published = write_aadr_source_accountability_receipt(
        output_path,
        receipt,
        governed_root=root,
    )
    return AadrSourceAccountabilityMaterialization(
        output_path=output_path,
        receipt=receipt,
        byte_count=len(published),
        sha256=sha256(published).hexdigest(),
    )


def _validate_release_version(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or "\\" in value
        or Path(value).name != value
        or value in {".", ".."}
    ):
        raise ValueError("AADR release version must be one safe path component")
    return value


def _validate_data_root(path: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        raise ValueError(
            "AADR accountability data root must be a non-symlink directory"
        )


def _read_governed_file(
    path: Path,
    *,
    governed_root: Path,
    label: str,
) -> bytes:
    _validate_governed_input_path(path, governed_root=governed_root, label=label)
    if not path.is_file():
        raise ValueError(f"{label} must be a regular non-symlink file: {path}")
    return path.read_bytes()


def _validate_governed_input_path(
    path: Path,
    *,
    governed_root: Path,
    label: str,
) -> None:
    root = Path(os.path.abspath(governed_root))
    candidate = Path(os.path.abspath(path))
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} must remain under the AADR data root") from exc
    if not relative.parts:
        raise ValueError(f"{label} cannot be the AADR data root")

    resolved_root = root.resolve(strict=True)
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f"{label} cannot use a symlink path")
        if current.exists():
            try:
                current.resolve(strict=True).relative_to(resolved_root)
            except ValueError as exc:
                raise ValueError(
                    f"{label} must remain under the AADR data root"
                ) from exc


def _decode_manifest(content: bytes) -> dict[str, object]:
    try:
        payload = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("AADR release manifest must be valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("AADR release manifest must be a JSON object")
    return payload


def _validated_panel_inventory(
    manifest: Mapping[str, object],
    *,
    release_dir: Path,
) -> tuple[_AadrPanelInput, ...]:
    declared: set[str] = set()
    identities: dict[str, _AadrPanelInput] = {}
    anno_files = manifest.get("anno_files")
    if not isinstance(anno_files, list):
        raise ValueError("AADR release manifest anno_files must be a list")
    for index, item in enumerate(anno_files):
        if not isinstance(item, dict):
            raise ValueError(f"AADR anno_files[{index}] must be an object")
        dataset_name = item.get("dataset_name")
        filename = item.get("filename")
        if not isinstance(dataset_name, str) or not isinstance(filename, str):
            raise ValueError("AADR panel identity must contain text names")
        expected_byte_count = item.get("filesize")
        if (
            isinstance(expected_byte_count, bool)
            or not isinstance(expected_byte_count, int)
            or expected_byte_count < 0
        ):
            raise ValueError("AADR panel identity requires a nonnegative filesize")
        expected_md5 = item.get("md5")
        if (
            not isinstance(expected_md5, str)
            or re.fullmatch(r"[0-9a-fA-F]{32}", expected_md5) is None
        ):
            raise ValueError("AADR panel identity requires a valid MD5 digest")
        relative = f"{dataset_name}/{filename}"
        if relative in declared:
            raise ValueError("AADR release manifest panel identities must be unique")
        declared.add(relative)
        identities[relative] = _AadrPanelInput(
            dataset_name=dataset_name,
            filename=filename,
            physical_path=release_dir / dataset_name / filename,
            expected_byte_count=expected_byte_count,
            expected_md5=expected_md5.casefold(),
        )

    downloaded_files = manifest.get("downloaded_files")
    if not isinstance(downloaded_files, list):
        raise ValueError("AADR release manifest downloaded_files must be a list")
    downloaded: list[str] = []
    for index, item in enumerate(downloaded_files):
        if not isinstance(item, str):
            raise ValueError(f"AADR downloaded_files[{index}] must be text")
        path = PurePosixPath(item)
        if (
            item != path.as_posix()
            or path.is_absolute()
            or len(path.parts) != 2
            or any(part in {"", ".", ".."} for part in path.parts)
        ):
            raise ValueError(
                f"AADR downloaded_files[{index}] is not a canonical panel path"
            )
        downloaded.append(item)
    if len(downloaded) != len(set(downloaded)):
        raise ValueError("AADR release manifest downloaded_files must be unique")
    if set(downloaded) != declared:
        raise ValueError(
            "AADR downloaded_files inventory must exactly match anno_files identities"
        )

    return tuple(panel for _relative, panel in sorted(identities.items()))


def _validate_panel_snapshot(
    panel: _AadrPanelInput,
    *,
    governed_root: Path,
) -> str:
    content = _read_governed_file(
        panel.physical_path,
        governed_root=governed_root,
        label="AADR panel",
    )
    if len(content) != panel.expected_byte_count:
        raise ValueError(
            f"AADR release manifest filesize mismatch for {panel.physical_path}"
        )
    actual_md5 = md5(content, usedforsecurity=False).hexdigest()
    if actual_md5 != panel.expected_md5:
        raise ValueError(
            f"AADR release manifest md5 mismatch for {panel.physical_path}"
        )
    return sha256(content).hexdigest()


__all__ = [
    "AadrSourceAccountabilityMaterialization",
    "materialize_aadr_source_accountability",
]
