"""Checksummed run-specific evidence for deterministic atlas galleries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .contracts import AtlasMediaError
from .gallery import _validate_execution_receipts, canonical_json_bytes, sha256_file


def build_run_evidence_index(
    root: Path,
    *,
    gallery_manifest_path: Path,
    capture_receipt_path: Path,
    execution_receipts: list[dict[str, object]],
) -> dict[str, object]:
    """Bind run-specific receipts and logs without contaminating gallery identity."""
    _validate_execution_receipts(execution_receipts)
    gallery = _artifact_identity(root, gallery_manifest_path)
    gallery_checksum_path = gallery_manifest_path.with_suffix(".sha256")
    gallery_checksum = _artifact_identity(root, gallery_checksum_path)
    capture = _artifact_identity(root, capture_receipt_path)
    try:
        gallery_value = json.loads(gallery_manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AtlasMediaError(
            "gallery manifest is unreadable for run evidence"
        ) from error
    gallery_content_sha = gallery_value.get("content_sha256")
    gallery_content = {
        key: value for key, value in gallery_value.items() if key != "content_sha256"
    }
    expected_content_sha = hashlib.sha256(
        canonical_json_bytes(gallery_content)
    ).hexdigest()
    expected_gallery_checksum = f"{gallery['sha256']}  {gallery_manifest_path.name}\n"
    try:
        observed_gallery_checksum = gallery_checksum_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise AtlasMediaError(
            "gallery checksum is unreadable for run evidence"
        ) from error
    if (
        not isinstance(gallery_content_sha, str)
        or not _is_sha256(gallery_content_sha)
        or gallery_content_sha != expected_content_sha
        or observed_gallery_checksum != expected_gallery_checksum
    ):
        raise AtlasMediaError("gallery content identity is invalid for run evidence")
    expected_execution_paths = sorted(
        str(receipt["path"]) for receipt in execution_receipts
    )
    if gallery_value.get("command_execution_receipts") != expected_execution_paths:
        raise AtlasMediaError("gallery command receipt inventory differs")
    artifacts: dict[str, dict[str, object]] = {
        str(capture["path"]): capture,
    }
    for identity in _gallery_output_identities(root, gallery_value):
        if str(identity["path"]) in artifacts:
            raise AtlasMediaError("run evidence artifact path is duplicated")
        artifacts[str(identity["path"])] = identity
    for execution in execution_receipts:
        execution_path = root / str(execution["path"])
        identity = _artifact_identity(root, execution_path)
        if (
            identity["byte_count"] != execution["byte_count"]
            or identity["sha256"] != execution["sha256"]
        ):
            raise AtlasMediaError("command execution receipt changed before indexing")
        artifacts[str(identity["path"])] = identity
        try:
            value = json.loads(execution_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise AtlasMediaError("command execution receipt is unreadable") from error
        for prefix in ("stdout", "stderr"):
            log_name = value.get(f"{prefix}_log")
            if not isinstance(log_name, str) or Path(log_name).name != log_name:
                raise AtlasMediaError("command execution log path is invalid")
            log_identity = _artifact_identity(root, root / log_name)
            if log_identity["byte_count"] != value.get(
                f"{prefix}_byte_count"
            ) or log_identity["sha256"] != value.get(f"{prefix}_sha256"):
                raise AtlasMediaError("command execution log differs from its receipt")
            if str(log_identity["path"]) in artifacts:
                raise AtlasMediaError("run evidence artifact path is duplicated")
            artifacts[str(log_identity["path"])] = log_identity
    browser_log = _artifact_identity(root, root / "brave-browser.log")
    if str(browser_log["path"]) in artifacts:
        raise AtlasMediaError("run evidence artifact path is duplicated")
    artifacts[str(browser_log["path"])] = browser_log
    content: dict[str, object] = {
        "schema_version": "atlas-media-run-evidence.v1",
        "gallery_content_sha256": gallery_content_sha,
        "gallery_manifest": gallery,
        "gallery_checksum": gallery_checksum,
        "capture_receipt": capture,
        "run_artifacts": sorted(artifacts.values(), key=lambda row: str(row["path"])),
    }
    return {
        **content,
        "content_sha256": hashlib.sha256(canonical_json_bytes(content)).hexdigest(),
    }


def _gallery_output_identities(
    root: Path, gallery: dict[str, object]
) -> list[dict[str, object]]:
    stories = gallery.get("stories")
    if not isinstance(stories, list):
        raise AtlasMediaError("gallery story inventory is invalid for run evidence")
    expected: dict[str, tuple[int, str]] = {}
    expected_frames: set[str] = set()
    expected_media: set[str] = set()
    for story in stories:
        if not isinstance(story, dict):
            raise AtlasMediaError("gallery story row is invalid for run evidence")
        capture_frames = story.get("capture_frames")
        assets = story.get("assets")
        if not isinstance(capture_frames, list) or not isinstance(assets, list):
            raise AtlasMediaError(
                "gallery output inventory is invalid for run evidence"
            )
        for row, path_field, digest_field, prefix, inventory in (
            *(
                (frame, "file", "png_sha256", "frames/", expected_frames)
                for frame in capture_frames
            ),
            *((asset, "path", "sha256", "media/", expected_media) for asset in assets),
        ):
            if not isinstance(row, dict):
                raise AtlasMediaError("gallery output row is invalid for run evidence")
            path = row.get(path_field)
            byte_count = row.get("byte_count")
            digest = row.get(digest_field)
            if (
                not isinstance(path, str)
                or not path.startswith(prefix)
                or Path(path).is_absolute()
                or ".." in Path(path).parts
                or path in expected
                or isinstance(byte_count, bool)
                or not isinstance(byte_count, int)
                or byte_count <= 0
                or not isinstance(digest, str)
                or not _is_sha256(digest)
            ):
                raise AtlasMediaError(
                    "gallery output identity is invalid for run evidence"
                )
            expected[path] = (byte_count, digest)
            inventory.add(path)
    observed_frames = {
        path.relative_to(root).as_posix()
        for path in (root / "frames").rglob("*.png")
        if path.is_file()
    }
    observed_media = {
        path.relative_to(root).as_posix()
        for path in (root / "media").rglob("*")
        if path.is_file()
    }
    if observed_frames != expected_frames or observed_media != expected_media:
        raise AtlasMediaError("gallery output file inventory differs before indexing")
    identities: list[dict[str, object]] = []
    for relative, (byte_count, digest) in expected.items():
        identity = _artifact_identity(root, root / relative)
        if identity["byte_count"] != byte_count or identity["sha256"] != digest:
            raise AtlasMediaError("gallery output bytes differ before indexing")
        identities.append(identity)
    return identities


def write_run_evidence_index(root: Path, index: dict[str, object]) -> tuple[Path, Path]:
    """Atomically publish a checksummed run-evidence index."""
    payload = canonical_json_bytes(index)
    path = root / "run-evidence-index.json"
    pending = root / "run-evidence-index.json.pending"
    pending.write_bytes(payload)
    pending.replace(path)
    checksum = root / "run-evidence-index.sha256"
    pending_checksum = root / "run-evidence-index.sha256.pending"
    pending_checksum.write_text(
        f"{hashlib.sha256(payload).hexdigest()}  {path.name}\n", encoding="utf-8"
    )
    pending_checksum.replace(checksum)
    return path, checksum


def _artifact_identity(root: Path, path: Path) -> dict[str, object]:
    resolved_root = root.resolve()
    if path.is_symlink():
        raise AtlasMediaError("run evidence artifact must not be a symlink")
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise AtlasMediaError("run evidence artifact is unavailable") from error
    if resolved_root not in resolved.parents or not resolved.is_file():
        raise AtlasMediaError("run evidence artifact escapes its root")
    return {
        "path": resolved.relative_to(resolved_root).as_posix(),
        "byte_count": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


__all__ = ["build_run_evidence_index", "write_run_evidence_index"]
