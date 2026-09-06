"""Candidate and governed static-input admission for atlas media."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil as shutil
import subprocess as subprocess  # nosec B404
from typing import cast

from .contracts import AtlasMediaError, AtlasMediaPlan

_GIT_TIMEOUT_SECONDS = 30


def _git(repository_root: Path, *arguments: str) -> str:
    executable = shutil.which("git")
    if executable is None:
        raise AtlasMediaError("git executable is unavailable")
    try:
        completed = subprocess.run(  # nosec B603
            (executable, *arguments),
            cwd=repository_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise AtlasMediaError(f"git {' '.join(arguments)} timed out") from error
    if completed.returncode != 0:
        raise AtlasMediaError(f"git {' '.join(arguments)} failed")
    return completed.stdout.strip()


def _require_candidate(plan: AtlasMediaPlan) -> None:
    observed = {
        "repository_head": _git(plan.repository_root, "rev-parse", "HEAD"),
        "repository_tree": _git(plan.repository_root, "rev-parse", "HEAD^{tree}"),
        "atlas_output_commit": _git(
            plan.repository_root,
            "log",
            "-1",
            "--format=%H",
            "--",
            plan.atlas_document,
        ),
    }
    expected = plan.candidate.as_json()
    for field, value in observed.items():
        if expected[field] != value:
            raise AtlasMediaError(f"candidate identity mismatch: {field}")
    # The renderer consumes immutable candidate blobs, so unrelated tracked edits
    # may proceed concurrently. Every governed input is still required to match
    # HEAD exactly before and after rendering.
    _require_governed_inputs_at_head(plan)


def _require_governed_inputs_at_head(plan: AtlasMediaPlan) -> None:
    """Require every media input and declared static chunk to equal candidate HEAD."""
    paths = _governed_input_paths(plan)
    repository_root = plan.repository_root.resolve()
    for relative_path in paths:
        try:
            resolved = (repository_root / relative_path).resolve(strict=True)
        except OSError as error:
            raise AtlasMediaError(
                f"governed input is absent: {relative_path}"
            ) from error
        if repository_root not in resolved.parents or not resolved.is_file():
            raise AtlasMediaError(f"governed input escapes repository: {relative_path}")
    tracked = _git(
        plan.repository_root, "ls-files", "--error-unmatch", "--", *paths
    ).splitlines()
    if set(tracked) != set(paths):
        raise AtlasMediaError("governed input inventory is not fully tracked at HEAD")
    index_rows = _git(plan.repository_root, "ls-files", "-s", "--", *paths).splitlines()
    index_blobs = {
        row.split("\t", maxsplit=1)[1]: row.split(maxsplit=2)[1] for row in index_rows
    }
    current_blobs = _git(plan.repository_root, "hash-object", "--", *paths).splitlines()
    if len(current_blobs) != len(paths) or any(
        index_blobs.get(path) != digest
        for path, digest in zip(paths, current_blobs, strict=True)
    ):
        raise AtlasMediaError("governed input bytes differ from candidate HEAD")


def _governed_input_paths(plan: AtlasMediaPlan) -> list[str]:
    """Enumerate document, story, local dependencies, and declared atlas chunks."""
    try:
        manifest = json.loads(
            _candidate_blobs(plan, [plan.atlas_manifest])[plan.atlas_manifest].decode(
                "utf-8"
            )
        )
        scope = manifest["scope_slug"]
        fields = manifest["assets"]["fields"]
        records = manifest["assets"]["records"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise AtlasMediaError(
            "cannot enumerate governed static atlas inputs"
        ) from error
    if (
        not isinstance(scope, str)
        or not isinstance(fields, list)
        or not isinstance(records, list)
    ):
        raise AtlasMediaError("cannot enumerate governed static atlas inputs")
    paths = [plan.atlas_document, plan.atlas_manifest, plan.storyboard_manifest]
    atlas_parent = Path(plan.atlas_manifest).parent
    for sequence, values in enumerate(records):
        if not isinstance(values, list) or len(values) != len(fields):
            raise AtlasMediaError("static atlas asset table row is invalid")
        row = dict(zip(fields, values, strict=True))
        domain = row.get("domain")
        digest = row.get("sha256")
        if not isinstance(domain, str) or not isinstance(digest, str):
            raise AtlasMediaError("static atlas asset table identity is invalid")
        paths.append(
            (
                atlas_parent / f"{scope}.atlas-{domain}.{sequence:04d}.{digest[:16]}.js"
            ).as_posix()
        )
    local_asset_prefix = (atlas_parent / "_map_assets").as_posix()
    local_assets = _git(
        plan.repository_root,
        "ls-tree",
        "-r",
        "--name-only",
        plan.candidate.repository_head,
        "--",
        local_asset_prefix,
    ).splitlines()
    paths.extend(path for path in local_assets if path)
    if len(paths) != len(set(paths)):
        raise AtlasMediaError("governed input inventory contains duplicate paths")
    return paths


def _atlas_manifest_identity(plan: AtlasMediaPlan) -> dict[str, str]:
    try:
        value = json.loads(
            (plan.repository_root / plan.atlas_manifest).read_text(encoding="utf-8")
        )
        identity = {
            field: value[field] for field in ("build_id", "scope_slug", "version")
        }
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError) as error:
        raise AtlasMediaError("atlas identity is unavailable") from error
    if any(not isinstance(item, str) or not item for item in identity.values()):
        raise AtlasMediaError("atlas identity is invalid")
    return cast("dict[str, str]", identity)


def _governed_static_assets(plan: AtlasMediaPlan) -> list[dict[str, object]]:
    paths = [
        relative
        for relative in _governed_input_paths(plan)
        if relative != plan.storyboard_manifest
    ]
    blobs = _candidate_blobs(plan, paths)
    assets: list[dict[str, object]] = []
    for relative in paths:
        path = plan.repository_root / relative
        if path.is_symlink():
            raise AtlasMediaError(f"governed static asset is a symlink: {relative}")
        payload = blobs[relative]
        assets.append(
            {
                "path": f"/{relative}",
                "byte_count": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return sorted(assets, key=lambda asset: cast(str, asset["path"]))


def _candidate_blob_identity(plan: AtlasMediaPlan, relative: str) -> tuple[int, str]:
    """Hash the exact candidate commit blob, never mutable worktree bytes."""
    payload = _candidate_blobs(plan, [relative])[relative]
    return len(payload), hashlib.sha256(payload).hexdigest()


def _candidate_blobs(
    plan: AtlasMediaPlan, relative_paths: list[str]
) -> dict[str, bytes]:
    """Read exact regular-file blobs from the candidate commit in one batch."""
    if not relative_paths or len(relative_paths) != len(set(relative_paths)):
        raise AtlasMediaError("candidate blob inventory is empty or duplicated")
    tree_rows = _git(
        plan.repository_root,
        "ls-tree",
        "-r",
        plan.candidate.repository_head,
        "--",
        *relative_paths,
    ).splitlines()
    modes: dict[str, tuple[str, str]] = {}
    for row in tree_rows:
        try:
            metadata, path = row.split("\t", maxsplit=1)
            mode, object_type, _object_id = metadata.split()
        except ValueError as error:
            raise AtlasMediaError("candidate tree inventory is invalid") from error
        modes[path] = (mode, object_type)
    if set(modes) != set(relative_paths) or any(
        mode not in {"100644", "100755"} or object_type != "blob"
        for mode, object_type in modes.values()
    ):
        raise AtlasMediaError("candidate governed inputs are not regular files")
    executable = shutil.which("git")
    if executable is None:
        raise AtlasMediaError("git executable is unavailable")
    requests = b"".join(
        f"{plan.candidate.repository_head}:{relative}\n".encode()
        for relative in relative_paths
    )
    try:
        completed = subprocess.run(  # nosec B603
            (executable, "cat-file", "--batch"),
            cwd=plan.repository_root,
            check=False,
            input=requests,
            capture_output=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as error:
        raise AtlasMediaError("candidate blob batch read timed out") from error
    if completed.returncode != 0:
        raise AtlasMediaError("candidate blob batch read failed")
    blobs: dict[str, bytes] = {}
    offset = 0
    for relative in relative_paths:
        header_end = completed.stdout.find(b"\n", offset)
        if header_end < 0:
            raise AtlasMediaError("candidate blob batch header is truncated")
        header = completed.stdout[offset:header_end].split()
        if len(header) != 3 or header[1] != b"blob":
            raise AtlasMediaError(f"candidate blob is unavailable: {relative}")
        try:
            byte_count = int(header[2])
        except ValueError as error:
            raise AtlasMediaError("candidate blob byte count is invalid") from error
        start = header_end + 1
        end = start + byte_count
        if end >= len(completed.stdout) or completed.stdout[end : end + 1] != b"\n":
            raise AtlasMediaError("candidate blob batch payload is truncated")
        blobs[relative] = completed.stdout[start:end]
        offset = end + 1
    if offset != len(completed.stdout):
        raise AtlasMediaError("candidate blob batch contains trailing data")
    return blobs


def _materialize_candidate_inputs(plan: AtlasMediaPlan) -> Path:
    """Write one immutable candidate-byte snapshot for all parsing and serving."""
    relative_paths = _governed_input_paths(plan)
    blobs = _candidate_blobs(plan, relative_paths)
    snapshot_root = plan.artifact_root / "candidate-inputs"
    if snapshot_root.exists():
        raise AtlasMediaError("candidate input snapshot already exists")
    snapshot_root.mkdir(parents=True)
    resolved_root = snapshot_root.resolve()
    for relative in relative_paths:
        destination = snapshot_root / relative
        resolved_parent = destination.parent.resolve()
        if (
            resolved_root != resolved_parent
            and resolved_root not in resolved_parent.parents
        ):
            raise AtlasMediaError("candidate input snapshot path escapes its root")
        destination.parent.mkdir(parents=True, exist_ok=True)
        pending = destination.with_suffix(destination.suffix + ".pending")
        pending.write_bytes(blobs[relative])
        pending.replace(destination)
    return snapshot_root
